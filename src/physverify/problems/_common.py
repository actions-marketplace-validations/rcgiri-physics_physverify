"""Pieces shared by the seeded-bug problems."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..steppers import euler, rk4


@dataclass(frozen=True)
class BugInfo:
    description: str
    # Families of check that should flag this bug, from reasoning about what
    # each check can see. An empty set documents a deliberate blind spot.
    expected: frozenset


def families(*names: str) -> frozenset:
    return frozenset(names)


# Stepper bugs apply to every ODE problem.
STEPPER_BUGS = {
    "euler_instead_of_rk4": BugInfo(
        "stepper silently falls back to forward Euler while claiming RK4",
        families("mms", "reference", "invariant"),
    ),
    "rk4_weights": BugInfo(
        "RK4 final combination uses weights 1,1,1,1 instead of 1,2,2,1 (inconsistent scheme)",
        families("mms", "reference", "invariant"),
    ),
    "rk4_full_step_stage2": BugInfo(
        "RK4 stage 2 uses a full step instead of a half step",
        families("mms", "reference"),
    ),
}


def rk4_with_bugs(f, t, y, h, bugs):
    if "euler_instead_of_rk4" in bugs:
        return euler(f, t, y, h)
    k1 = f(t, y)
    if "rk4_full_step_stage2" in bugs:
        k2 = f(t + 0.5 * h, y + h * k1)
    else:
        k2 = f(t + 0.5 * h, y + 0.5 * h * k1)
    k3 = f(t + 0.5 * h, y + 0.5 * h * k2)
    k4 = f(t + h, y + h * k3)
    if "rk4_weights" in bugs:
        return y + (h / 6.0) * (k1 + k2 + k3 + k4)
    return y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def make_integrate(rhs, bugs, method="rk4"):
    """Build an `integrate(source, y0, t_end, n)` for a solver with an optional source hook."""

    def integrate(source, y0, t_end, n):
        h = t_end / n
        y = np.array(y0, dtype=float)

        def forced(t, state):
            return rhs(t, state) + source(t)

        for i in range(n):
            t = i * h
            if method == "rk4":
                y = rk4_with_bugs(forced, t, y, h, bugs)
            elif method == "euler":
                y = euler(forced, t, y, h)
            else:
                raise ValueError(method)
        return y

    return integrate
