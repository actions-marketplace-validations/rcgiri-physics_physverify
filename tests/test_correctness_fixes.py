"""Regression tests for false verdicts found in the 2026-11 review (each was reproduced before the fix)."""

import numpy as np
import pytest

from physverify import check_order, invariant_study
from physverify.mms import complex_step_derivative
from physverify.operators import check_uniform_state
from physverify.report import load_spec
from physverify.steps import check_step_independence
from physverify.stochastic.stats import t_critical


def test_stale_solver_is_reloaded(tmp_path):
    """The MCP server loads specs repeatedly in one process; an edited solver must be seen."""
    solver = tmp_path / "pv_tmp_solver.py"
    solver.write_text("VALUE = 1\n")
    (tmp_path / "verify_tmp.py").write_text(
        "from physverify import Check, Result\nimport pv_tmp_solver\n"
        "def checks():\n    return [Check('limit', 'value', lambda: Result('PASS', str(pv_tmp_solver.VALUE)))]\n")
    first = load_spec(tmp_path / "verify_tmp.py")[0].run().message
    solver.write_text("VALUE = 2\n")
    second = load_spec(tmp_path / "verify_tmp.py")[0].run().message
    assert (first, second) == ("1", "2")


def _euler(y0, omega, t_end, n):
    y = np.array(y0, dtype=float)
    h = t_end / n
    for _ in range(n):
        y = y + h * np.array([y[1], -omega**2 * y[0]])
    return y


def test_tiny_invariant_is_not_exact():
    """An energy of about 1e-21 J drifting under Euler must not be reported EXACT for a claimed order 4."""
    m, omega, a = 1e-26, 1.0, 1e-3

    def integrate(source, y0, t_end, n):
        return _euler(y0, omega, t_end, n)

    def energy(y):
        return 0.5 * m * (y[1] ** 2 + omega**2 * y[0] ** 2)

    r = invariant_study(integrate, energy, [a, 0.0], 1.0, [50, 100, 200, 400], 4)
    assert not r.ok


def test_small_solution_floor_scales():
    hs = [0.1, 0.05, 0.025, 0.0125]
    errs = [1e-20 * h for h in hs]  # first order, solution of size 1e-18
    r = check_order(hs, errs, 4, scale=1e-18)
    assert r.status == "FAIL"


def test_points_near_floor_left_out_of_fit():
    """A correct order-4 series whose finest errors sit just above the floor still passes."""
    hs = np.array([0.1, 0.05, 0.025, 0.0125, 0.00625])
    errs = 1.0 * hs**4
    errs[-2:] = [9e-12, 5e-12]  # round-off stops the decrease just above the floor
    r = check_order(hs, errs, 4)
    assert r.ok, r.message
    assert "round-off" in r.message


def test_value_proportional_to_dt_fails():
    dts = [0.1, 0.05, 0.025, 0.0125]
    assert not check_step_independence(lambda dt: 3.0 * dt, dts).ok
    assert not check_step_independence(lambda dt: dt**0.5, dts).ok
    assert check_step_independence(lambda dt: 1.0 + dt, dts).ok


def test_t_critical_few_degrees_of_freedom():
    assert t_critical(1e-3, 1.0) == pytest.approx(636.62, rel=1e-3)
    assert t_critical(0.05, 10.0) == pytest.approx(2.228, rel=1e-3)


def test_uniform_state_zero_component_round_off():
    state = (np.full(5, 1.0), np.zeros(5))
    assert check_uniform_state(lambda s: (s[0], s[1] + 1e-17), state).ok
    assert not check_uniform_state(lambda s: (s[0], s[1] + 1e-6), state).ok


def test_complex_step_rejects_non_analytic_u():
    assert complex_step_derivative(lambda t: np.sin(t), 0.3) == pytest.approx(np.cos(0.3))
    with pytest.raises(ValueError):
        complex_step_derivative(lambda t: abs(t) ** 2, 0.5)
    with pytest.raises(ValueError):
        complex_step_derivative(lambda t: np.maximum(np.real(t), 0.0) ** 2, 0.5)
