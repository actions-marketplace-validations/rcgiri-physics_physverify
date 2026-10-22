"""`physverify demo`: the damped-oscillator example, shipped in the package.

It runs the checks on a correct midpoint solver, then on a copy whose damping
is 10% too large, so a first run needs only `pip install physverify`.
The same solver and spec, as files to copy, are in examples/ in the repository.
"""

from __future__ import annotations

import numpy as np

from .studies import ode_checks
from .mms import ManufacturedODE

OMEGA, GAMMA = 3.0, 0.4


def make_solver(damping_factor: float = 1.0):
    """Midpoint method for x'' = -omega^2 x - 2 gamma x', with an additive source term."""

    def rhs(t, y):
        damping = 2.0 * GAMMA * damping_factor
        return np.array([y[1], -(OMEGA**2) * y[0] - damping * y[1]])

    def integrate(source, y0, t_end, n_steps, trajectory=False):
        h = t_end / n_steps
        y = np.array(y0, dtype=float)
        states = [y]
        for i in range(n_steps):
            t = i * h
            k1 = rhs(t, y) + source(t)
            mid = y + 0.5 * h * k1
            y = y + h * (rhs(t + 0.5 * h, mid) + source(t + 0.5 * h))
            states.append(y)
        return np.array(states) if trajectory else y

    return integrate


def reference_rhs(t, y):
    """The equations, written from the physics, not copied from the solver."""
    return np.array([y[1], -(OMEGA**2) * y[0] - 2.0 * GAMMA * y[1]])


def checks(damping_factor: float = 1.0):
    integrate = make_solver(damping_factor)
    mms = ManufacturedODE(lambda t: np.array([np.sin(1.3 * t) + 0.2, 1.04 * np.cos(1.3 * t)]), reference_rhs)
    return ode_checks(
        "midpoint damped oscillator",
        integrate,
        rhs_ref=reference_rhs,
        mms=mms,
        y0_free=np.array([1.0, 0.0]),
        t_end=1.0,
        ns=(10, 20, 40, 80, 160),
        order=2.0,
        patch=(np.array([0.5, -0.3]), np.array([0.8, 1.1])),
        integrate_trajectory=lambda s, y0, t, n: integrate(s, y0, t, n, trajectory=True),
    )


def main() -> int:
    """Exit 0 when the correct solver passes and the broken one fails, as they should."""
    from .report import NOTE, run_checks, to_text

    print("1. A correct midpoint solver for a damped oscillator:\n")
    good = run_checks(checks())
    print(to_text(good))
    print("\n2. The same solver with the damping 10% too large (a typical slip):\n")
    bad = run_checks(checks(damping_factor=1.1))
    print(to_text(bad))
    ok = not any(o.result.failed for o in good) and any(o.result.failed for o in bad)
    print(f"\n{NOTE}")
    print("\nTo check your own solver, start a spec with:  physverify init verify_solver.py --solver mysolver --order 2")
    return 0 if ok else 1
