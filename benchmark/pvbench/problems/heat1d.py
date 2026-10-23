"""1D heat equation u_t = alpha u_xx on [0, 1] with u = 0 at both ends, explicit (FTCS) scheme.

Time step and grid are refined in several ways, because each way can hide
different bugs:

coupled      dt = r dx^2 / alpha with r = 0.25 (the usual stable choice); the
             expected order in dx is 2 (second order in space, first in time).
time-only    grid fixed, dt refined. The manufactured solution is cubic in x,
             which the three-point stencil differentiates exactly, so the grid
             adds no error of its own. Expected order 1. (To leading order: the
             time-stepping error is itself smoothed by the discrete Laplacian,
             a cross term of order dt * dx^2.)
space-only   the manufactured solution is linear in t, which forward Euler
             integrates exactly, so the time stepping adds no error of its own.
             Expected order 2, with the same kind of small cross term.
patch        cubic in x and linear in t: FTCS must reproduce it to round-off
             for any dx and dt. Any error at all is a bug.
"""

from __future__ import annotations

import math

import numpy as np

from physverify.checks import Check
from physverify.order import check_exact, check_order
from physverify.studies import close_result
from ._common import BugInfo, families

NAME = "heat1d"
ALPHA = 0.7
T_END = 0.1
R = 0.25
LEVELS = (9, 17, 33, 65, 129)  # nodes; dx = 1 / (N - 1)
TIME_ONLY_NODES = 33
TIME_ONLY_STEPS = (160, 320, 640, 1280, 2560)  # r = alpha dt / dx^2 from 0.45 down to 0.03
PATCH_NODES = (9, 17, 33)

BUGS = {
    "dx_off_by_one": BugInfo(
        "grid spacing taken as 1/N instead of 1/(N-1) for N nodes",
        families("mms", "reference", "patch"),
        "the grid is stretched by N/(N-1); error plateaus",
    ),
    "alpha_ignored": BugInfo(
        "diffusivity left out of the diffusion term (alpha = 1 used)",
        families("mms", "reference", "patch"),
        "solution decays at the wrong rate; error plateaus",
    ),
    "extra_time_step": BugInfo(
        "one more time step than needed",
        families("patch"),
        "an O(dt) error, the same order as FTCS's own, so no convergence-order check can tell it "
        "from truncation error",
    ),
    "unstable_dt": BugInfo(
        "time step uses r = 0.6, beyond the FTCS stability limit of 0.5",
        families("mms", "reference", "patch"),
        "the finest grids blow up (non-finite or huge errors); the patch check's coupled runs use the same dt",
    ),
    "source_time_shift": BugInfo(
        "the source term is evaluated at the end of the step, t + dt, instead of t",
        families("patch"),
        "an O(dt) error like FTCS's own, so the order studies pass; the exact patch solution is lost",
    ),
}


# Sources are differentiated by hand; the tests check them against finite differences.
# Coupled and space-only studies use smooth sine modes; time-only and patch use cubics in x.
def _sines(x):
    return np.sin(math.pi * x) + 0.5 * np.sin(3.0 * math.pi * x)


def _sines_xx(x):
    return -(math.pi**2) * np.sin(math.pi * x) - 0.5 * (3.0 * math.pi) ** 2 * np.sin(3.0 * math.pi * x)


def _cubic(x):
    return x - x**3  # zero at x = 0 and x = 1; second derivative -6x


def u_manufactured(x, t):
    return np.exp(-t) * _sines(x)


def source_manufactured(x, t, alpha=ALPHA):
    """u_t - alpha u_xx for u_manufactured."""
    return np.exp(-t) * (-_sines(x) - alpha * _sines_xx(x))


def u_time_only(x, t):
    return np.exp(-t) * _cubic(x)


def source_time_only(x, t, alpha=ALPHA):
    return np.exp(-t) * (-_cubic(x) + 6.0 * alpha * x)


def u_space_only(x, t):
    return (1.0 + t) * _sines(x)


def source_space_only(x, t, alpha=ALPHA):
    return _sines(x) - alpha * (1.0 + t) * _sines_xx(x)


def u_patch(x, t):
    return (1.0 + t) * _cubic(x)


def source_patch(x, t, alpha=ALPHA):
    return _cubic(x) + 6.0 * alpha * (1.0 + t) * x


def steps_for_coupled_dt(n_nodes, r=R):
    dx = 1.0 / (n_nodes - 1)
    return math.ceil(T_END / (r * dx**2 / ALPHA))


def solve(n_nodes, bugs, u0, source=None, n_steps=None):
    """FTCS to T_END; returns the nodal values at the end.

    With n_steps=None the time step follows the grid (the coupled choice).
    Passing n_steps fixes dt = T_END / n_steps independently of the grid.
    """
    x = np.linspace(0.0, 1.0, n_nodes)
    dx_nominal = 1.0 / (n_nodes - 1)
    if n_steps is None:
        r_used = 0.6 if "unstable_dt" in bugs else R
        n_steps = math.ceil(T_END / (r_used * dx_nominal**2 / ALPHA))
    dt = T_END / n_steps
    if "extra_time_step" in bugs:
        n_steps += 1
    dx = 1.0 / n_nodes if "dx_off_by_one" in bugs else dx_nominal
    alpha_used = 1.0 if "alpha_ignored" in bugs else ALPHA
    r = alpha_used * dt / dx**2
    u = u0(x).copy()
    with np.errstate(all="ignore"):
        for i in range(n_steps):
            lap = u[2:] - 2.0 * u[1:-1] + u[:-2]
            new = u.copy()
            new[1:-1] = u[1:-1] + r * lap
            if source is not None:
                t_source = (i + 1) * dt if "source_time_shift" in bugs else i * dt
                new[1:-1] += dt * source(x[1:-1], t_source)
            new[0] = new[-1] = 0.0
            u = new
    return x, u


def _error(u_fun, source, n_nodes, bugs, n_steps=None):
    x, u = solve(n_nodes, bugs, lambda xx: u_fun(xx, 0.0), source=source, n_steps=n_steps)
    with np.errstate(all="ignore"):
        return float(np.max(np.abs(u - u_fun(x, T_END))))


def checks(bugs=frozenset()) -> list[Check]:
    def run_coupled():
        hs = [1.0 / (n - 1) for n in LEVELS]
        errs = [_error(u_manufactured, source_manufactured, n, bugs) for n in LEVELS]
        return check_order(hs, errs, 2.0)

    def run_time_only():
        hs = [T_END / m for m in TIME_ONLY_STEPS]
        errs = [_error(u_time_only, source_time_only, TIME_ONLY_NODES, bugs, n_steps=m) for m in TIME_ONLY_STEPS]
        return check_order(hs, errs, 1.0)

    def run_space_only():
        hs = [1.0 / (n - 1) for n in LEVELS]
        errs = [_error(u_space_only, source_space_only, n, bugs) for n in LEVELS]
        return check_order(hs, errs, 2.0)

    def run_reference():
        hs, errs = [], []
        for n in LEVELS:
            x, u = solve(n, bugs, lambda xx: np.sin(math.pi * xx))
            exact = np.sin(math.pi * x) * math.exp(-ALPHA * math.pi**2 * T_END)
            hs.append(1.0 / (n - 1))
            with np.errstate(all="ignore"):
                errs.append(float(np.max(np.abs(u - exact))))
        return check_order(hs, errs, 2.0)

    def run_patch():
        # The grid and the time step are varied separately: the coupled choice on three grids,
        # then three time steps on one grid.
        errs = [_error(u_patch, source_patch, n, bugs) for n in PATCH_NODES]
        hs = [T_END / steps_for_coupled_dt(n) for n in PATCH_NODES]
        base = steps_for_coupled_dt(17)
        for factor in (1, 2, 4):
            errs.append(_error(u_patch, source_patch, 17, bugs, n_steps=factor * base))
            hs.append(T_END / (factor * base))
        return check_exact(hs, errs)

    return [
        Check("mms", "FTCS coupled dt ~ dx^2", run_coupled),
        Check("mms", "FTCS time-only refinement", run_time_only),
        Check("mms", "FTCS space-only refinement", run_space_only),
        Check("reference", "FTCS eigenmode decay", run_reference),
        Check("patch", "FTCS cubic in x, linear in t", run_patch),
    ]


SMOKE_NODES = 33
SMOKE_RTOL = 1e-2  # FTCS on 33 nodes is accurate to a few parts in a thousand here


def smoke_checks(bugs=frozenset()) -> list[Check]:
    """A plain unit test: one grid, the decaying sine mode, within 1%."""

    def run():
        x, u = solve(SMOKE_NODES, bugs, lambda xx: np.sin(math.pi * xx))
        exact = np.sin(math.pi * x) * math.exp(-ALPHA * math.pi**2 * T_END)
        return close_result(u, exact, SMOKE_RTOL)

    return [Check("smoke", "eigenmode decay on 33 nodes", run)]
