"""sandbox.py deps --source / --prefix and the memory setting (issue 48). Docker is not called."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(monkeypatch, tmp_path, memory=None):
    monkeypatch.setenv("PHYSVERIFY_CORPUS", str(tmp_path))
    if memory:
        monkeypatch.setenv("PHYSVERIFY_MEMORY", memory)
    spec = importlib.util.spec_from_file_location("pv_sandbox_installs", ROOT / "sandbox" / "sandbox.py")
    sb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sb)
    calls = []
    monkeypatch.setattr(sb, "timed", lambda args, name, limit, keep=None: calls.append(args) or 0)
    monkeypatch.setattr(sb, "remove_stale", lambda name: None)
    monkeypatch.setattr(sb, "head", lambda repo: "abc")
    return sb, calls


def test_deps_default_is_wheels_only_target(monkeypatch, tmp_path):
    sb, calls = _load(monkeypatch, tmp_path)
    assert sb.main(["deps", "X1", "numpy"]) == 0
    args = calls[0]
    assert "--only-binary=:all:" in args and "--target=/deps" in args and "--memory=2g" in args


def test_deps_source_and_prefix(monkeypatch, tmp_path):
    sb, calls = _load(monkeypatch, tmp_path, memory="4g")
    assert sb.main(["deps", "--source", "--prefix", "X1", "git+https://example.org/p.git"]) == 0
    args = calls[0]
    assert "--only-binary=:all:" not in args and "--prefix=/deps" in args and "--target=/deps" not in args
    assert "--memory=4g" in args and "--memory-swap=4g" in args


def test_run_adds_prefix_paths(monkeypatch, tmp_path):
    sb, calls = _load(monkeypatch, tmp_path)
    (tmp_path / "repos" / "X1").mkdir(parents=True)
    (tmp_path / "deps" / "X1" / "lib" / "python3.13" / "site-packages").mkdir(parents=True)
    script = tmp_path / "a.py"
    script.write_text("print(1)\n")
    sb.main(["run", "X1", str(script)])
    args = calls[0]
    assert "PYTHONPATH=/deps:/deps/lib/python3.13/site-packages" in args and "LD_LIBRARY_PATH=/deps/lib" in args


def test_oom_note_names_the_setting(monkeypatch, tmp_path, capsys):
    sb, _ = _load(monkeypatch, tmp_path)
    assert sb.oom_note(137) == 137
    assert "PHYSVERIFY_MEMORY" in capsys.readouterr().out
