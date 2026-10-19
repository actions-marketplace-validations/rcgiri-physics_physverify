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


def check_exact(hs, errors, *, floor: float = 1e-12) -> OrderResult:
    """Require the error to be at round-off level at every resolution.

    For a manufactured solution that lies inside the scheme's discrete solution
    space (a "patch test": for example, polynomials a finite-difference stencil
    differentiates exactly), a correct code reproduces it to round-off whatever
    the step sizes. Order of convergence cannot see an error that is as small
    as the scheme's own truncation error and shrinks at the same rate; this
    can, because the expected error is zero rather than small.

    EXACT  every error is at most `floor`
    FAIL   some error is larger, or non-finite
    """
    hs = np.asarray(hs, dtype=float)
    errs = np.asarray(errors, dtype=float)
    order = np.argsort(-hs)
    hs, errs = hs[order], errs[order]
    base = dict(expected=float("inf"), hs=tuple(hs), errors=tuple(errs))
    if not np.all(np.isfinite(errs)):
        return OrderResult(FAIL, "non-finite error: the solution diverged or produced NaN", **base)
    worst = float(errs.max())
    if worst <= floor:
        return OrderResult(EXACT, f"reproduced to round-off (largest error {worst:.2g}), as designed", **base)
    msg = f"expected an exact solution to round-off, but the error reaches {worst:.3g}"
    measurable = errs > floor
    fitted = float("nan")
    if measurable.sum() >= 3:
        fitted = fit_order(hs[measurable], errs[measurable])
        msg += f" and shrinks at about order {fitted:.2f}"
    return OrderResult(FAIL, msg, fitted=fitted, **base)


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
