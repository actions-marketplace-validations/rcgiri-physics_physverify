"""1D heat equation u_t = alpha u_xx on [0, 1] with u = 0 at both ends, explicit (FTCS) scheme.

The time step follows the grid, dt = r dx^2 / alpha with r = 0.25, so the
expected order in dx is 2 (second order in space, first order in time).
"""

from __future__ import annotations

import math

import numpy as np

from ..checks import Check
from ..order import check_order
from ._common import BugInfo, families

NAME = "heat1d"
ALPHA = 0.7
T_END = 0.1
R = 0.25
LEVELS = (9, 17, 33, 65, 129)  # nodes; dx = 1 / (N - 1)

BUGS = {
    "dx_off_by_one": BugInfo(
        "grid spacing taken as 1/N instead of 1/(N-1) for N nodes",
        families("mms", "reference"),
    ),
    "alpha_ignored": BugInfo(
        "diffusivity left out of the diffusion term (alpha = 1 used)",
        families("mms", "reference"),
    ),
    "extra_time_step": BugInfo(
        "one more time step than needed, an O(dt) shift that FTCS truncation error hides",
        families(),  # deliberate blind spot: dt ~ dx^2, so the shift has the same order as the scheme's own error
    ),
    "unstable_dt": BugInfo(
        "time step uses r = 0.6, beyond the FTCS stability limit of 0.5",
        families("mms", "reference"),
    ),
}


def u_manufactured(x, t):
    return np.exp(-t) * (np.sin(math.pi * x) + 0.5 * np.sin(3.0 * math.pi * x))


def source_manufactured(x, t, alpha=ALPHA):
    """u_t - alpha u_xx, differentiated by hand for the manufactured solution above."""
    spatial = np.sin(math.pi * x) + 0.5 * np.sin(3.0 * math.pi * x)
    spatial_xx = -(math.pi**2) * np.sin(math.pi * x) - 0.5 * (3.0 * math.pi) ** 2 * np.sin(3.0 * math.pi * x)
    return np.exp(-t) * (-spatial - alpha * spatial_xx)


def solve(n_nodes, bugs, u0, source=None):
    """FTCS to T_END; returns the nodal values at the end."""
    x = np.linspace(0.0, 1.0, n_nodes)
    dx_nominal = 1.0 / (n_nodes - 1)
    r_used = 0.6 if "unstable_dt" in bugs else R
    dt_nominal = r_used * dx_nominal**2 / ALPHA
    n_steps = math.ceil(T_END / dt_nominal)
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
                new[1:-1] += dt * source(x[1:-1], i * dt)
            new[0] = new[-1] = 0.0
            u = new
    return x, u


def checks(bugs=frozenset()) -> list[Check]:
    def run_mms():
        hs, errs = [], []
        for n in LEVELS:
            x, u = solve(n, bugs, lambda xx: u_manufactured(xx, 0.0), source=source_manufactured)
            hs.append(1.0 / (n - 1))
            with np.errstate(all="ignore"):
                errs.append(float(np.max(np.abs(u - u_manufactured(x, T_END)))))
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

    return [Check("mms", "FTCS", run_mms), Check("reference", "FTCS eigenmode decay", run_reference)]
