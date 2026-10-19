import numpy as np
import pytest

from physverify.checks import EXACT, FAIL, PASS
from physverify.mms import ManufacturedODE, mms_trajectory_study
from physverify.order import check_order, effective_floor
from physverify.problems._common import make_integrate
from physverify.steppers import euler, midpoint, rk4
from physverify.studies import close_result, patch_study


def rhs(t, y):
    return np.array([y[1], -np.sin(y[0]) - 0.1 * y[1] * abs(y[1])])


def integrate_with(stepper, steps_extra=0):
    def integrate(source, y0, t_end, n):
        h = t_end / n
        y = np.array(y0, dtype=float)
        for i in range(n + steps_extra):
            y = stepper(lambda t, s: rhs(t, s) + source(t), i * h, y, h)
        return y

    return integrate


@pytest.mark.parametrize("stepper", [euler, midpoint, rk4])
def test_every_consistent_runge_kutta_method_reproduces_a_linear_solution(stepper):
    result = patch_study(integrate_with(stepper), rhs, [0.3, -0.5], [0.7, 0.4], 1.0, (5, 10, 20, 40))
    assert result.status == EXACT, result.message


def test_patch_catches_an_extra_step_that_keeps_the_order():
    result = patch_study(integrate_with(euler, steps_extra=1), rhs, [0.3, -0.5], [0.7, 0.4], 1.0, (10, 20, 40, 80))
    assert result.status == FAIL
    assert abs(result.fitted - 1.0) < 0.1  # same order as Euler itself


def test_patch_catches_a_wrong_right_hand_side():
    def wrong(t, y):
        return rhs(t, y) * np.array([1.0, 1.01])

    def integrate(source, y0, t_end, n):
        return make_integrate(wrong, frozenset())(source, y0, t_end, n)

    assert patch_study(integrate, rhs, [0.3, -0.5], [0.7, 0.4], 1.0, (10, 20, 40)).status == FAIL


def test_effective_floor_grows_only_for_large_solutions():
    assert effective_floor(1e-12, 1.0) == 1e-12
    assert effective_floor(1e-12, 10.0) == 1e-12
    assert effective_floor(1e-12, 1e6) == pytest.approx(1e-7)
    assert effective_floor(1e-12, float("nan")) == 1e-12


def test_scaled_floor_turns_large_round_off_into_exact():
    hs = [0.1, 0.05, 0.025]
    errs = [3e-9, 2e-9, 3e-9]  # round-off for a solution of size 1e5
    assert check_order(hs, errs, 4.0).status == FAIL
    assert check_order(hs, errs, 4.0, scale=1e5).status == EXACT


def test_trajectory_study_sees_an_error_that_cancels_at_the_end():
    """A code that is wrong in the middle of the run and right at the end."""
    mms = ManufacturedODE(lambda t: np.array([np.sin(t), np.cos(t)]), lambda t, y: np.array([y[1], -y[0]]))
    good = make_integrate(lambda t, y: np.array([y[1], -y[0]]), frozenset(), trajectory=True)

    def bad(source, y0, t_end, n):
        states = good(source, y0, t_end, n)
        states[n // 2] += 1e-3  # a wrong value reported half-way, final state untouched
        return states

    assert mms_trajectory_study(good, mms, 1.0, (10, 20, 40, 80), 4.0).status == PASS
    assert mms_trajectory_study(bad, mms, 1.0, (10, 20, 40, 80), 4.0).status == FAIL


def test_trajectory_study_rejects_the_wrong_number_of_states():
    mms = ManufacturedODE(lambda t: np.array([t]), lambda t, y: np.array([1.0]))
    with pytest.raises(ValueError):
        mms_trajectory_study(lambda s, y0, t, n: np.zeros((n, 1)), mms, 1.0, (4, 8), 1.0)


def test_close_result():
    assert close_result([1.0, 2.0], [1.0, 2.0005], 1e-3).ok
    assert not close_result([1.0, 2.1], [1.0, 2.0], 1e-3).ok
    assert not close_result([np.nan], [1.0], 1e-3).ok
