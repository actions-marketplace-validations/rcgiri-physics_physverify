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
