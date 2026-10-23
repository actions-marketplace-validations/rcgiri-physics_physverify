import numpy as np

from physverify.checks import FAIL, PASS
from physverify.mms import ManufacturedODE, complex_step_derivative, mms_order_study
from pvbench.problems._common import make_integrate


def test_complex_step_derivative_is_exact_to_roundoff():
    def u(t):
        return np.array([np.sin(2.0 * t) * np.exp(t), t**3, np.cos(t) / (1.0 + t * t)])

    t = 0.7
    expected = np.array(
        [
            np.exp(t) * (np.sin(2 * t) + 2 * np.cos(2 * t)),
            3 * t**2,
            (-np.sin(t) * (1 + t * t) - 2 * t * np.cos(t)) / (1 + t * t) ** 2,
        ]
    )
    assert np.max(np.abs(complex_step_derivative(u, t) - expected)) < 1e-14


def _problem():
    """y' = -y^2 + 0.3 y with a manufactured solution, as a 2-component system."""

    def rhs(t, y):
        return np.array([-y[0] ** 2 + 0.3 * y[1], -0.5 * y[1] + y[0]])

    def u(t):
        return np.array([1.0 + 0.5 * np.sin(t), 0.8 * np.cos(2 * t)])

    return rhs, u


def test_correct_code_converges_at_design_order():
    rhs, u = _problem()
    mms = ManufacturedODE(u, rhs)
    integrate = make_integrate(rhs, frozenset(), "rk4")
    result = mms_order_study(integrate, mms, 1.0, (10, 20, 40, 80, 160), 4.0)
    assert result.status == PASS, result.message


def test_wrong_right_hand_side_is_caught_when_reference_is_independent():
    rhs, u = _problem()

    def wrong(t, y):
        return np.array([-y[0] ** 2 + 0.3 * y[1], -0.55 * y[1] + y[0]])  # 10% off in one coefficient

    mms = ManufacturedODE(u, rhs)  # forcing from the correct operator
    integrate = make_integrate(wrong, frozenset(), "rk4")
    result = mms_order_study(integrate, mms, 1.0, (10, 20, 40, 80, 160), 4.0)
    assert result.status == FAIL, result.message


def test_forcing_built_from_the_code_under_test_hides_a_wrong_right_hand_side():
    """Why the reference operator must be independent: this is the trap, documented."""
    rhs, u = _problem()

    def wrong(t, y):
        return np.array([-y[0] ** 2 + 0.3 * y[1], -0.55 * y[1] + y[0]])

    mms = ManufacturedODE(u, wrong)  # forcing computed from the wrong operator itself
    integrate = make_integrate(wrong, frozenset(), "rk4")
    result = mms_order_study(integrate, mms, 1.0, (10, 20, 40, 80, 160), 4.0)
    assert result.status == PASS, result.message


def test_wrong_stepper_order_is_caught():
    rhs, u = _problem()
    mms = ManufacturedODE(u, rhs)
    integrate = make_integrate(rhs, frozenset(["euler_instead_of_rk4"]), "rk4")
    result = mms_order_study(integrate, mms, 1.0, (10, 20, 40, 80, 160), 4.0)
    assert result.status == FAIL and abs(result.fitted - 1.0) < 0.2
