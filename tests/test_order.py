import numpy as np

from physverify.checks import EXACT, FAIL, INCONCLUSIVE, PASS
from physverify.order import check_exact, check_order, fit_order, pairwise_orders

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


def test_check_exact_accepts_round_off_level_errors():
    result = check_exact(HS, [3e-16, 1e-15, 5e-16, 2e-15])
    assert result.status == EXACT and result.ok


def test_check_exact_rejects_a_small_error_that_converges_at_the_expected_order():
    """An error that shrinks at a perfectly good order is still a failure when the answer should be exact."""
    errs = [3.0 * h for h in HS]  # first order, so check_order(expected=1) would pass it
    assert check_order(HS, errs, 1.0).status == PASS
    result = check_exact(HS, errs)
    assert result.status == FAIL and "exact" in result.message


def test_check_exact_reports_the_order_of_a_failing_error():
    result = check_exact(HS, [3.0 * h for h in HS])
    assert abs(result.fitted - 1.0) < 1e-9 and "order 1.00" in result.message


def test_check_exact_fails_on_non_finite_error():
    assert check_exact(HS, [1e-15, float("nan"), 1e-15, 1e-15]).status == FAIL


def test_only_points_above_the_floor_are_fitted():
    hs = [0.2, 0.1, 0.05, 0.025, 0.0125]
    errs = [3.0 * h**4 for h in hs]
    errs[-1] = 5e-15  # round-off: must not drag the fit down
    assert check_order(hs, errs, 4.0).status == PASS
