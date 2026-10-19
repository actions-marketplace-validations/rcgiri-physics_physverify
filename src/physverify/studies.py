"""Order studies other than MMS, and a helper that bundles them for an ODE code."""

from __future__ import annotations

from typing import Callable

import numpy as np

from .checks import Check, OrderResult
from .mms import ManufacturedODE, max_abs_error, mms_order_study, zero_source
from .order import check_order
from .steppers import integrate_fixed, rk4


def reference_study(integrate, rhs_ref, y0, t_end, ns, expected_order, ref_factor=16, **kw) -> OrderResult:
    """Compare with a reference solution from an independent right-hand side.

    The reference is RK4 on `rhs_ref` with ref_factor times the finest step
    count, so its own error is negligible next to the code under test.
    """
    y_ref = integrate_fixed(rhs_ref, y0, 0.0, t_end, ref_factor * max(ns), rk4)
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
) -> list[Check]:
    """The standard bundle for an ODE code: MMS, reference solution, invariant."""
    checks = [
        Check("mms", label, lambda: mms_order_study(integrate, mms, t_end, ns, order, floor=floor)),
        Check("reference", label, lambda: reference_study(integrate, rhs_ref, y0_free, t_end, ns, order, floor=floor)),
    ]
    if quantity is not None:
        checks.append(
            Check("invariant", label, lambda: invariant_study(integrate, quantity, y0_free, t_end, ns, order, floor=floor))
        )
    return checks
