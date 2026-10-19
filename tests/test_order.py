import numpy as np

from physverify.checks import EXACT, FAIL, INCONCLUSIVE, PASS
from physverify.order import check_order, fit_order, pairwise_orders

HS = [0.1, 0.05, 0.025, 0.0125]


def test_pairwise_and_fit_recover_known_order():
    errs = [3.0 * h**4 for h in HS]
    assert np.allclose(pairwise_orders(HS, errs), 4.0)
    assert abs(fit_order(HS, errs) - 4.0) < 1e-12


def test_correct_order_passes():
    result = check_order(HS, [3.0 * h**4 for h in HS], 4.0)
    assert result.status == PASS and result.ok
    assert abs(result.fitted - 4.0) < 1e-9


def test_order_too_low_fails():
    result = check_order(HS, [0.5 * h for h in HS], 4.0)
    assert result.status == FAIL and "below" in result.message


def test_order_too_high_fails_unless_upper_tolerance_is_widened():
    errs = [3.0 * h**4 for h in HS]
    assert check_order(HS, errs, 2.0).status == FAIL
    assert check_order(HS, errs, 2.0, tol_high=float("inf")).status == PASS


def test_plateau_fails():
    result = check_order(HS, [2e-2, 2e-2, 1.9e-2, 1.9e-2], 4.0)
    assert result.status == FAIL and "does not decrease" in result.message


def test_roundoff_level_errors_are_exact_not_failures():
    result = check_order(HS, [1e-15, 3e-16, 2e-15, 1e-15], 4.0)
    assert result.status == EXACT and result.ok


def test_non_finite_error_fails():
    assert check_order(HS, [1e-3, 1e-4, float("nan"), 1e-6], 4.0).status == FAIL
    assert check_order(HS, [1e-3, 1e-4, float("inf"), 1e-6], 4.0).status == FAIL


def test_single_measurable_point_is_inconclusive():
    errs = [1e-6, 1e-14, 1e-15, 1e-15]
    assert check_order(HS, errs, 4.0).status == INCONCLUSIVE


def test_input_order_does_not_matter():
    errs = [3.0 * h**4 for h in HS]
    result = check_order(HS[::-1], errs[::-1], 4.0)
    assert result.status == PASS


def test_only_points_above_the_floor_are_fitted():
    hs = [0.2, 0.1, 0.05, 0.025, 0.0125]
    errs = [3.0 * h**4 for h in hs]
    errs[-1] = 5e-15  # round-off: must not drag the fit down
    assert check_order(hs, errs, 4.0).status == PASS
