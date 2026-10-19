"""The command line, the JSON and HTML reports, and the pytest plugin."""

import json
import shutil
import sys
from pathlib import Path

import pytest

from physverify.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def example_dir(tmp_path):
    for name in ("damped_oscillator.py", "verify_damped_oscillator.py"):
        shutil.copy(EXAMPLES / name, tmp_path / name)
    yield tmp_path
    sys.modules.pop("damped_oscillator", None)  # each test gets its own copy of the solver
    if str(tmp_path) in sys.path:
        sys.path.remove(str(tmp_path))


def break_solver(folder):
    path = folder / "damped_oscillator.py"
    text = path.read_text()
    path.write_text(text.replace("damping = 2.0 * GAMMA", "damping = 2.0 * GAMMA * 1.1"))


def test_run_passes_on_the_correct_example_and_writes_json_and_html(example_dir, capsys):
    out_json, out_html = example_dir / "r.json", example_dir / "r.html"
    code = main(["run", str(example_dir / "verify_damped_oscillator.py"), "--json", str(out_json), "--html", str(out_html)])
    assert code == 0
    data = json.loads(out_json.read_text())
    assert data["summary"]["not_ok"] == 0 and data["summary"]["total"] == 4
    assert {c["family"] for c in data["checks"]} == {"mms", "reference", "patch"}
    page = out_html.read_text()
    assert page.startswith("<!doctype html>") and "<svg" in page and "4 of 4 checks passed" in page


def test_run_reports_a_seeded_bug_with_exit_code_1(example_dir, capsys):
    break_solver(example_dir)
    code = main(["run", str(example_dir / "verify_damped_oscillator.py"), "--json", "-"])
    assert code == 1
    data = json.loads(capsys.readouterr().out)
    failed = {c["family"] for c in data["checks"] if not c["ok"]}
    assert failed == {"mms", "reference", "patch"}
    assert all(c["error"] and c["h"] for c in data["checks"])


def test_run_exits_2_on_a_spec_without_checks(tmp_path, capsys):
    spec = tmp_path / "verify_nothing.py"
    spec.write_text("x = 1\n")
    assert main(["run", str(spec)]) == 2
    assert "does not define checks()" in capsys.readouterr().err


def test_json_has_no_nan(example_dir, capsys):
    """JSON has no NaN; non-finite numbers become null."""
    main(["run", str(example_dir / "verify_damped_oscillator.py"), "--json", "-"])
    text = capsys.readouterr().out
    assert "NaN" not in text and "Infinity" not in text
    json.loads(text)


def test_pytest_plugin_collects_checks_and_reports_failures(example_dir, pytester, monkeypatch):
    src = str(Path(__file__).resolve().parents[1] / "src")
    monkeypatch.setenv("PYTHONPATH", src)
    for name in ("damped_oscillator.py", "verify_damped_oscillator.py"):
        shutil.copy(example_dir / name, pytester.path / name)
    # Block the entry-point copy of the plugin by name, then load it explicitly. Without the block,
    # pytest stops with "Plugin already registered" whenever physverify's metadata is visible
    # (an installed package, or a stale src/physverify.egg-info); with it, this runs either way.
    plugin_args = ("-p", "no:physverify", "-p", "physverify.pytest_plugin", "-q")
    result = pytester.runpytest_subprocess(*plugin_args)
    result.assert_outcomes(passed=4)

    break_solver(pytester.path)
    result = pytester.runpytest_subprocess(*plugin_args)
    result.assert_outcomes(failed=4)
    result.stdout.fnmatch_lines(["*FAIL: error does not decrease*"])
