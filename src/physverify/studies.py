"""Order studies other than MMS, and a helper that bundles them for an ODE code."""

from __future__ import annotations

from typing import Callable

import numpy as np

from .checks import FAIL, PASS, Check, OrderResult, Result
from .mms import ManufacturedODE, max_abs_error, mms_order_study, mms_trajectory_study, zero_source
from .order import check_exact, check_order
from .steppers import integrate_fixed, rk4


def reference_study(integrate, rhs_ref, y0, t_end, ns, expected_order, ref_factor=16, **kw) -> OrderResult:
    """Compare with a reference solution from an independent right-hand side.

    The reference is RK4 on `rhs_ref` with ref_factor times the finest step
    count, so its own error is negligible next to the code under test.
    """
    y_ref = integrate_fixed(rhs_ref, y0, 0.0, t_end, ref_factor * max(ns), rk4)
    kw.setdefault("scale", float(np.max(np.abs(y_ref))))
    hs, errs = [], []
    for n in ns:
        hs.append(t_end / n)
        errs.append(max_abs_error(integrate(zero_source, y0, t_end, n), y_ref))
    return check_order(hs, errs, expected_order, **kw)


def invariant_study(integrate, quantity, y0, t_end, ns, expected_order, **kw) -> OrderResult:
    """Relative drift of a conserved quantity at t_end as the step shrinks.

    Drift is only required to shrink at least as fast as the scheme's order.
    RK4 on a pendulum, for example, drifts in energy at about order 5, so a
    drift that converges faster than expected is not a failure here.
    """
    kw.setdefault("tol_high", float("inf"))
    q0 = float(quantity(np.asarray(y0, dtype=float)))
    scale = max(abs(q0), 1.0)
    hs, errs = [], []
    for n in ns:
        with np.errstate(all="ignore"):
            y_end = np.asarray(integrate(zero_source, y0, t_end, n), dtype=float)
            drift = abs(float(quantity(y_end)) - q0) / scale
        hs.append(t_end / n)
        errs.append(drift)
    return check_order(hs, errs, expected_order, **kw)


def linear_manufactured(rhs_ref: Callable, y0, slope) -> ManufacturedODE:
    """u(t) = y0 + slope * t, with its forcing taken from the reference operator."""
    y0 = np.asarray(y0, dtype=float)
    slope = np.asarray(slope, dtype=float)
    return ManufacturedODE(lambda t: y0 + slope * t, rhs_ref, du=lambda t: slope)


def patch_study(integrate, rhs_ref, y0, slope, t_end, ns, *, floor=1e-11) -> OrderResult:
    """Exactness test for an ODE code: a manufactured solution linear in t.

    Every consistent explicit Runge-Kutta method (Euler, midpoint, RK4, ...)
    reproduces u(t) = y0 + slope * t exactly, whatever the step: each stage
    lands on u at its own stage time, so each stage derivative is exactly
    `slope`, and weights that sum to one return y0 + slope * (t + h). So any
    error above round-off is a bug, including bugs whose error shrinks at the
    scheme's own order (an extra step for Euler, a wrong stage time) that every
    order-of-convergence check accepts. See docs/patch.md.

    It does not see a wrong but consistent stepper (Euler in place of RK4 is
    still exact here): the order studies cover that.
    """
    mms = linear_manufactured(rhs_ref, y0, slope)
    exact = mms.value(t_end)
    hs, errs = [], []
    for n in ns:
        y_end = integrate(mms.forcing, mms.value(0.0), t_end, n)
        hs.append(t_end / n)
        errs.append(max_abs_error(y_end, exact))
    return check_exact(hs, errs, floor=floor, scale=float(np.max(np.abs(exact))))


def smoke_check(label, integrate, rhs_ref, y0, t_end, n, *, rtol=1e-3) -> Check:
    """What an ordinary unit test would do: one run, compared with a reference within a tolerance.

    Not one of the verification families. It is here so that the benchmark can
    report what a plain test would have caught (see physverify.compare).
    """

    def run():
        y_ref = integrate_fixed(rhs_ref, y0, 0.0, t_end, 16 * n, rk4)
        y = np.asarray(integrate(zero_source, y0, t_end, n), dtype=float)
        return close_result(y, y_ref, rtol)

    return Check("smoke", label, run)


def close_result(value, expected, rtol) -> Result:
    value = np.asarray(value, dtype=float)
    expected = np.asarray(expected, dtype=float)
    with np.errstate(all="ignore"):
        err = float(np.max(np.abs(value - expected)) / max(float(np.max(np.abs(expected))), 1e-300))
    if np.isfinite(err) and err <= rtol:
        return Result(PASS, f"relative difference {err:.2g} within {rtol:g}")
    return Result(FAIL, f"relative difference {err:.3g} exceeds {rtol:g}")


def ode_checks(
    label: str,
    integrate: Callable,
    *,
    rhs_ref: Callable,
    mms: ManufacturedODE,
    y0_free,
    t_end: float,
    ns,
    order: float,
    quantity: Callable | None = None,
    floor: float = 1e-12,
    patch: tuple | None = None,
    integrate_trajectory: Callable | None = None,
) -> list[Check]:
    """The standard bundle for an ODE code: MMS, reference solution, invariant.

    patch                 (y0, slope) of a linear manufactured solution; adds the exactness check
    integrate_trajectory  same contract as `integrate` but returning every state; adds an MMS
                          check on the largest error over the whole run
    """
    checks = [
        Check("mms", label, lambda: mms_order_study(integrate, mms, t_end, ns, order, floor=floor)),
        Check("reference", label, lambda: reference_study(integrate, rhs_ref, y0_free, t_end, ns, order, floor=floor)),
    ]
    if integrate_trajectory is not None:
        checks.append(
            Check(
                "mms",
                f"{label} (whole trajectory)",
                lambda: mms_trajectory_study(integrate_trajectory, mms, t_end, ns, order, floor=floor),
            )
        )
    if quantity is not None:
        checks.append(
            Check("invariant", label, lambda: invariant_study(integrate, quantity, y0_free, t_end, ns, order, floor=floor))
        )
    if patch is not None:
        p_y0, p_slope = patch
        checks.append(Check("patch", label, lambda: patch_study(integrate, rhs_ref, p_y0, p_slope, t_end, ns)))
    return checks
