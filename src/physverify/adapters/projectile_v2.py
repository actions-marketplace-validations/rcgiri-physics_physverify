"""Adapter for projectile-simulation/src/projectile_sim_v2.py (class ProjectileV2).

The class has no time argument and no source-term hook, so the manufactured
forcing is injected by wrapping `_state_derivative` and reading time from x:
the manufactured solution has x_m(t) = t. The wrapped problem is then the
autonomous system  z' = f(z) + s(x), whose exact solution is the manufactured
one. The code itself is not modified.
"""

from __future__ import annotations

import math

import numpy as np

from ..checks import Check
from ..loaders import load_module_from_path
from ..mms import zero_source
from ..problems import projectile as P
from ..studies import ode_checks
from . import sibling_project

ENV_VAR = "PHYSVERIFY_PROJECTILE_DIR"
FOLDER = "projectile-simulation"


def source_path():
    return sibling_project(ENV_VAR, FOLDER) / "src" / "projectile_sim_v2.py"


def load():
    return load_module_from_path("projectile_sim_v2_under_test", source_path(), stubs=("matplotlib", "matplotlib.pyplot"))


def _new_sim(module):
    p = P.PARAMS
    return module.ProjectileV2(mass=p["m"], radius=p["r"], C_d=p["Cd"])


def make_integrate(module, mode: str, method: str, trajectory: bool = False):
    def integrate(source, y0, t_end, n):
        if y0[0] != 0.0 or y0[1] != 0.0:
            raise ValueError("ProjectileV2 always launches from the origin")
        sim = _new_sim(module)
        original = sim._state_derivative
        # simulate() runs until landing; stop a run that never lands instead of hanging
        budget = [8 * 10 * n]
        # In a forced run x = t, and past the measurement time the state no longer matters, so a
        # strong downward push ends the run (the linear patch solution would never land). Half a
        # step of margin keeps it out of the last measured step. Free runs are left alone.
        after = t_end + 0.5 * t_end / n if source is not zero_source else math.inf
        land = np.array([0.0, 0.0, 0.0, -1000.0])

        def wrapped(z, m):
            budget[0] -= 1
            if budget[0] < 0:
                raise RuntimeError("simulation ran 10x past the measurement time without landing")
            extra = land if z[0] > after else 0.0
            return original(z, m) + source(z[0]) + extra

        sim._state_derivative = wrapped
        v0 = math.hypot(y0[2], y0[3])
        angle = math.degrees(math.atan2(y0[3], y0[2]))
        states = sim.simulate(v0, angle, mode=mode, dt=t_end / n, method=method)
        return np.asarray(states[: n + 1]) if trajectory else states[n]

    return integrate


def checks(module=None) -> list[Check]:
    module = module or load()
    out: list[Check] = []
    for mode in P.MODES:
        for method, ns, order in (("rk4", P.NS_RK4, 4.0), ("euler", P.NS_EULER, 1.0)):
            out += ode_checks(
                f"{mode}/{method}",
                make_integrate(module, mode, method),
                rhs_ref=P.rhs_reference(mode),
                mms=P.manufactured(mode),
                y0_free=P.Y0_FREE,
                t_end=P.MMS_T_END,
                ns=ns,
                order=order,
                quantity=P.energy_vacuum if mode == "vacuum" else None,
                patch=P.PATCH,
                integrate_trajectory=make_integrate(module, mode, method, trajectory=True),
            )

    def range_fn(v0, angle, dt):
        trajectory = _new_sim(module).simulate(v0, angle, mode="vacuum", dt=dt, method="rk4")
        return trajectory[-1][0]

    out.append(P.range_check(range_fn, label="ProjectileV2 vacuum/rk4 range"))
    return out
