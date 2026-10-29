"""Awkward input must give a clear FAIL, ERROR or INCONCLUSIVE, never a PASS (improvement plan A6)."""

import numpy as np
import pytest

from physverify import check_order, ode_checks
from physverify.checks import ERROR, FAIL, INCONCLUSIVE
from physverify.cli import main
from physverify.demo import make_solver, reference_rhs
from physverify.mms import ManufacturedODE
from physverify.report import run_checks

HS = np.array([0.1, 0.05, 0.025, 0.0125])


def _checks(integrate):
    mms = ManufacturedODE(lambda t: np.array([np.sin(t), np.cos(t)]), reference_rhs)
    return ode_checks("awkward", integrate, rhs_ref=reference_rhs, mms=mms, y0_free=np.array([1.0, 0.0]),
                      t_end=1.0, ns=(10, 20, 40, 80), order=2.0)


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_non_finite_errors_fail(bad):
    r = check_order(HS, np.array([1e-2, bad, 6e-4, 1.5e-4]), 2)
    assert r.status == FAIL and "non-finite" in r.message


def test_equal_step_sizes_are_inconclusive():
    r = check_order(np.full(3, 0.1), np.array([1.0, 0.5, 0.25]), 2)
    assert r.status == INCONCLUSIVE and "same" in r.message


@pytest.mark.parametrize("hs", [np.zeros(3), np.array([0.1, -0.05, 0.025]), np.array([0.1, np.nan, 0.025])])
def test_zero_negative_or_nan_step_sizes_are_inconclusive(hs):
    r = check_order(hs, np.array([1.0, 0.5, 0.25]), 2)
    assert r.status == INCONCLUSIVE and "positive" in r.message


def test_mismatched_lengths_are_inconclusive():
    assert check_order(HS, np.array([1.0, 0.5]), 2).status == INCONCLUSIVE


@pytest.mark.parametrize("integrate", [
    lambda s, y0, t, n: np.full(2, np.nan),  # solver returns NaN
    lambda s, y0, t, n: np.zeros(3),         # wrong shape
    lambda s, y0, t, n: 1 / 0,               # solver raises
], ids=["nan", "wrong-shape", "raises"])
def test_broken_solver_never_passes(integrate):
    for o in run_checks(_checks(integrate)):
        assert o.result.status in (FAIL, ERROR, INCONCLUSIVE), o.result


def test_correct_solver_still_passes():
    assert all(o.result.ok for o in run_checks(_checks(make_solver())))


def test_spec_with_no_checks_is_an_error(tmp_path, capsys):
    spec = tmp_path / "verify_empty.py"
    spec.write_text("def checks():\n    return []\n")
    assert main(["run", str(spec)]) == 2
    assert "no checks" in capsys.readouterr().err


def test_spec_that_does_not_import_is_an_error(tmp_path, capsys):
    spec = tmp_path / "verify_broken.py"
    spec.write_text("import a_module_that_does_not_exist\n")
    assert main(["run", str(spec)]) == 2
    assert "cannot load" in capsys.readouterr().err


def test_demo_passes_the_good_solver_and_fails_the_broken_one(capsys):
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "4 of 4 checks passed" in out and "0 of 4 checks passed" in out


# --- found in a code review (2026-10-29) ---------------------------------------------------------


def test_identity_failure_with_a_scalar_against_an_array_is_reported():
    from physverify.identities import check_identity

    r = check_identity([("scalar vs array", 1.0, np.array([1.0, 1.0, 2.0]))])
    assert r.status == FAIL and "index (2,)" in r.message and "2.0" in r.message.split("expected")[-1]


def test_smoke_finds_scripts_under_a_folder_named_build(tmp_path):
    from physverify.smoke import _scripts

    project = tmp_path / "build" / "project"  # a skip-list name above the project must not hide its scripts
    (project / "venv").mkdir(parents=True)
    (project / "run.py").write_text("print(1)\n")
    (project / "venv" / "lib.py").write_text("print(1)\n")
    assert [p.name for p in _scripts(project)] == ["run.py"]


def test_mcp_server_answers_a_message_that_is_not_an_object():
    import io
    import json

    from physverify.agent import INVALID_REQUEST, mcp_main

    out = io.StringIO()
    mcp_main(io.StringIO('[1, 2]\n42\n{"jsonrpc": "2.0", "id": 7, "method": "ping"}\n'), out)
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert [r.get("error", {}).get("code") for r in replies[:2]] == [INVALID_REQUEST, INVALID_REQUEST]
    assert replies[2] == {"jsonrpc": "2.0", "id": 7, "result": {}}


@pytest.mark.parametrize("event", ["[]", '{"tool_input": "x.py"}', '{"tool_input": {"file_path": 3}}'])
def test_hook_ignores_events_of_the_wrong_shape(event):
    import io

    from physverify.agent import hook_main

    assert hook_main(io.StringIO(event), io.StringIO()) == 0


def test_hook_resolves_a_relative_path_against_the_session_folder(tmp_path, monkeypatch):
    import io
    import json

    from physverify.agent import hook_main

    session = tmp_path / "session"
    session.mkdir()
    (session / "verify_broken.py").write_text("def checks():\n    raise RuntimeError('ran')\n")
    monkeypatch.chdir(tmp_path)  # the hook process may start elsewhere
    event = {"cwd": str(session), "tool_input": {"file_path": "solver.py"}}
    assert hook_main(io.StringIO(json.dumps(event)), io.StringIO()) == 2


def test_scan_reports_numpy_aliases_added_back_in_numpy_2_as_notes(tmp_path):
    from physverify.scan import NOTE, WARN, scan

    (tmp_path / "m.py").write_text("import numpy as np\na = np.bool(1)\nb = np.long\nc = np.float(1)\n")
    levels = {f.message.split()[0]: f.level for f in scan(tmp_path, stages=("api",))[0]}
    assert levels == {"np.bool": NOTE, "np.long": NOTE, "np.float": WARN}


def test_constants_scan_skips_integers_too_large_for_a_float(tmp_path):
    from physverify import constants

    (tmp_path / "big.py").write_text(f"x = {10 ** 400}\npi = 3.14\n")
    assert [n.constant for n in constants.scan(tmp_path / "big.py")] == ["pi"]


def test_verdict_with_no_comparisons_is_inconclusive():
    from physverify.stochastic.stats import verdict

    assert verdict([]).status == INCONCLUSIVE
