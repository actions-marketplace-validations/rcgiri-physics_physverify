"""Does a result respond to the numerical controls the way it should?

- `check_step_independence`: a physical quantity at a fixed physical time must settle as the time step shrinks.
  A missing factor of dt shows as a value that grows without limit, and the check reports the power of dt.
- `check_tolerance_response`: the error of an adaptive solver must fall as its tolerance is tightened. An error the
  embedded estimate cannot see (a boundary value frozen during the Runge-Kutta stages) stalls instead.

Both came from the corpus session of 2026-11-06: an active-particle model with x += p instead of x += p dt (mean
squared displacement 118, 435, 2739 at dt = 0.1, 0.05, 0.02 against an exact 1.011), and an RKF solver whose error on
u = x sin t moved only from 5.4e-4 to 5.2e-5 while the tolerance went from 1e-6 to 1e-11.
"""

from __future__ import annotations

import numpy as np

from .checks import FAIL, INCONCLUSIVE, PASS, Result


def _power(xs, ys):
    return float(np.polyfit(np.log(xs), np.log(ys), 1)[0])


def check_step_independence(run, dts, *, rtol: float = 0.05, z: float = 4.0) -> Result:
    """`run(dt)` returns a scalar at a fixed physical time, or (value, standard_error) for a Monte Carlo estimate.

    Give at least three steps. PASS if every value is within `rtol` of the finest one (plus `z` standard errors), or
    if the changes between neighbouring steps shrink. FAIL if they do not shrink, and report value ~ dt^k.
    Choose steps small enough that a correct code is already converging; a value at dt = 1 may be far from it.
    """
    dts = sorted((float(d) for d in dts), reverse=True)
    if len(dts) < 3:
        raise ValueError("check_step_independence needs at least three time steps")
    vals, errs = [], []
    for dt in dts:
        out = run(dt)
        v, e = out if isinstance(out, (tuple, list)) else (out, 0.0)
        vals.append(float(v))
        errs.append(float(e))
    vals, errs = np.array(vals), np.array(errs)
    shown = ", ".join(f"{v:.4g} at dt={d:g}" for v, d in zip(vals, dts))
    if not np.all(np.isfinite(vals)):
        return Result(FAIL, f"the quantity is not finite for some time steps: {shown}")
    margin = rtol * abs(vals[-1]) + z * np.hypot(errs, errs[-1])
    if np.all(np.abs(vals - vals[-1]) <= margin):
        return Result(PASS, f"the quantity does not depend on the time step within {rtol:g} relative: {shown}")
    changes = np.abs(np.diff(vals))
    noise = z * np.hypot(errs[:-1], errs[1:])
    if changes[-1] <= changes[0] + noise[0] + noise[-1] and changes[-1] < changes[0]:
        return Result(PASS, f"the quantity settles as the time step shrinks (change {changes[0]:.3g} -> {changes[-1]:.3g}): {shown}")
    if np.all(vals != 0):
        k = _power(dts, np.abs(vals))
        return Result(FAIL, f"the quantity at a fixed physical time does not settle as dt shrinks: {shown}; it behaves"
                            f" like dt^{k:.2f}. A rate or velocity used without its factor of dt gives a negative power")
    return Result(FAIL, f"the quantity at a fixed physical time does not settle as dt shrinks: {shown}")


def check_tolerance_response(run, tols, *, min_slope: float = 0.5, floor: float = 0.0) -> Result:
    """`run(tol)` returns the solver's error against an exact solution at that tolerance.

    Give tolerances spanning at least three decades. FAIL if error ~ tol^s with s below `min_slope` (a correct adaptive
    solver of order p has s near p/(p+1) or above). The error must come from time stepping only, so use a problem the
    spatial scheme solves exactly, such as u = x sin t with u_t = u_xx + x cos t, u(0,t) = 0, u(1,t) = sin t.
    Errors at or below `floor` (round-off, or a known spatial error) are left out of the fit.
    """
    tols = sorted(float(t) for t in tols)
    if len(tols) < 3 or tols[-1] / tols[0] < 1e3:
        raise ValueError("check_tolerance_response needs at least three tolerances spanning three decades")
    errs = np.array([abs(float(run(t))) for t in tols])
    shown = ", ".join(f"{e:.3g} at tol={t:g}" for e, t in zip(errs, tols))
    if not np.all(np.isfinite(errs)):
        return Result(FAIL, f"the error is not finite for some tolerances: {shown}")
    use = errs > floor
    if use.sum() < 3 or tols[np.nonzero(use)[0][-1]] / tols[np.nonzero(use)[0][0]] < 1e2:
        return Result(INCONCLUSIVE, f"too few errors above the floor {floor:g} to fit a slope: {shown}")
    s = _power(np.array(tols)[use], errs[use])
    if s < min_slope:
        return Result(FAIL, f"the error barely follows the tolerance: {shown}; error ~ tol^{s:.2f}, below {min_slope:g}."
                            " Something the error estimate cannot see limits the accuracy, for example a boundary"
                            " value not updated during the Runge-Kutta stages")
    return Result(PASS, f"the error follows the tolerance as tol^{s:.2f}: {shown}")
