"""Observed order of accuracy from errors at several resolutions."""

from __future__ import annotations

import numpy as np

from .checks import EXACT, FAIL, INCONCLUSIVE, PASS, OrderResult


def pairwise_orders(hs, errors) -> np.ndarray:
    """p_i = log(e_i / e_{i+1}) / log(h_i / h_{i+1}) for consecutive resolutions."""
    hs = np.asarray(hs, dtype=float)
    errs = np.asarray(errors, dtype=float)
    return np.log(errs[:-1] / errs[1:]) / np.log(hs[:-1] / hs[1:])


def fit_order(hs, errors) -> float:
    """Least-squares slope of log(error) against log(h)."""
    return float(np.polyfit(np.log(hs), np.log(errors), 1)[0])


def check_order(
    hs,
    errors,
    expected: float,
    *,
    tol_low: float = 0.3,
    tol_high: float = 1.0,
    floor: float = 1e-12,
    fit_points: int = 4,
) -> OrderResult:
    """Compare the observed order of convergence with the order the code claims.

    PASS      fitted order lies in [expected - tol_low, expected + tol_high]
    EXACT     every error is below `floor`, so the order cannot be measured
    FAIL      order too low or too high, error plateau, or non-finite error
    INCONCLUSIVE  fewer than two resolutions are above the noise floor

    `floor` is an absolute error level below which round-off dominates; the
    default suits solutions of size about 1 to 10.
    """
    hs = np.asarray(hs, dtype=float)
    errs = np.asarray(errors, dtype=float)
    order = np.argsort(-hs)  # coarse to fine
    hs, errs = hs[order], errs[order]
    base = dict(expected=float(expected), hs=tuple(hs), errors=tuple(errs))

    if not np.all(np.isfinite(errs)):
        return OrderResult(FAIL, "non-finite error: the solution diverged or produced NaN", **base)

    measurable = errs > floor
    if not measurable.any():
        return OrderResult(EXACT, f"error below {floor:g} at every resolution; order not measurable", **base)

    h_m, e_m = hs[measurable], errs[measurable]
    if len(e_m) < 2:
        return OrderResult(INCONCLUSIVE, "fewer than 2 resolutions above the noise floor", **base)

    if e_m[-2] / e_m[-1] < 1.2:
        return OrderResult(
            FAIL,
            f"error does not decrease with resolution (about {e_m[-1]:.3g} at the finest level)",
            fitted=0.0,
            **base,
        )

    h_f, e_f = h_m[-fit_points:], e_m[-fit_points:]
    p = fit_order(h_f, e_f)
    if p < expected - tol_low:
        msg = f"observed order {p:.2f} is below the expected {expected:g}"
        status = FAIL
    elif p > expected + tol_high:
        msg = f"observed order {p:.2f} is above the expected {expected:g}; check the expected order"
        status = FAIL
    else:
        msg = f"observed order {p:.2f} (expected {expected:g})"
        status = PASS
    return OrderResult(status, msg, fitted=p, **base)
