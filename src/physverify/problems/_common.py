"""Pieces shared by the seeded-bug problems."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..steppers import euler, rk4


@dataclass(frozen=True)
class BugInfo:
    description: str  # what is changed in the code
    # Families of check that should flag this bug, from reasoning about what
    # each check can see. An empty set documents a deliberate blind spot.
    expected: frozenset
    symptom: str = ""  # what the error should look like, written before running the checks


def families(*names: str) -> frozenset:
    return frozenset(names)


# Stepper bugs apply to every ODE problem.
STEPPER_BUGS = {
    "euler_instead_of_rk4": BugInfo(
        "stepper silently falls back to forward Euler while claiming RK4",
        families("mms", "reference", "invariant"),
        "order 1 instead of 4. Euler is consistent, so the linear patch solution is still exact",
    ),
    "rk4_weights": BugInfo(
        "RK4 final combination uses weights 1,1,1,1 instead of 1,2,2,1 (inconsistent scheme)",
        families("mms", "reference", "invariant", "patch"),
        "weights sum to 2/3, so the step is too short: the error does not shrink",
    ),
    "rk4_full_step_stage2": BugInfo(
        "RK4 stage 2 uses a full step instead of a half step",
        families("mms", "reference", "patch"),
        "order drops (to 2 here); the linear patch solution is not reproduced",
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
    t4 = t + 0.5 * h if "rk4_stage4_time" in bugs else t + h
    k4 = f(t4, y + h * k3)
    if "rk4_weights" in bugs:
        return y + (h / 6.0) * (k1 + k2 + k3 + k4)
    return y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def make_integrate(rhs, bugs, method="rk4", trajectory=False):
    """Build an `integrate(source, y0, t_end, n)` for a solver with an optional source hook.

    With trajectory=True it returns all n + 1 states instead of the last one.
    """

    def integrate(source, y0, t_end, n):
        h = t_end / n
        y = np.array(y0, dtype=float)
        states = [y]

        def forced(t, state):
            return rhs(t, state) + source(t)

        steps = n + 1 if (method == "euler" and "euler_extra_step" in bugs) else n
        for i in range(steps):
            t = i * h
            if method == "rk4":
                y = rk4_with_bugs(forced, t, y, h, bugs)
            elif method == "euler":
                y = euler(forced, t, y, h)
            else:
                raise ValueError(method)
            states.append(y)
        if trajectory:
            return np.array(states)
        return y

    return integrate
