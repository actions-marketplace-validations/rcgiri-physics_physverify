"""Adapter for projectile-simulation/src/projectile_sim_v1.py (class Projectile, forward Euler).

simulate() returns only positions and runs until landing, with no source hook,
so there is no MMS or patch check (row 25 of the audit plan). Positions at a
fixed time are compared with the closed-form vacuum and linear-drag solutions
from the README and with an RK4 reference for quadratic drag; the landing range
is compared with the vacuum formula v0^2 sin(2 angle) / g. Forward Euler is
first order by design, so order 1 is the pass mark.
"""

from __future__ import annotations

import math

import numpy as np

from physverify.checks import Check
from physverify.loaders import load_module_from_path
from physverify.order import check_order
from physverify.steppers import integrate_fixed, rk4
from . import sibling_project

ENV_VAR = "PHYSVERIFY_PROJECTILE_DIR"
FOLDER = "projectile-simulation"
MASS, RADIUS, V0, ANGLE = 0.145, 0.037, 30.0, 45.0
T_END = 2.0
NS = (200, 400, 800, 1600)


def source_path():
    return sibling_project(ENV_VAR, FOLDER) / "src" / "projectile_sim_v1.py"


def load():
    return load_module_from_path("projectile_sim_v1_under_test", source_path(), stubs=("matplotlib", "matplotlib.pyplot"))


def exact_position(mode, t, k, g=9.81):
    vx0 = V0 * math.cos(math.radians(ANGLE))
    vy0 = V0 * math.sin(math.radians(ANGLE))
    if mode == "vacuum":
        return np.array([vx0 * t, vy0 * t - 0.5 * g * t * t])
    if mode == "linear":
        decay = 1.0 - math.exp(-k * t)
        return np.array([vx0 / k * decay, (vy0 + g / k) / k * decay - g * t / k])
    # quadratic: no closed form; RK4 on the README's equations with a fine step
    def f(_t, z):
        speed = math.hypot(z[2], z[3])
        return np.array([z[2], z[3], -k * speed * z[2], -g - k * speed * z[3]])

    return integrate_fixed(f, [0.0, 0.0, vx0, vy0], 0.0, t, 20000, rk4)[:2]


def drag_constant(mode, viscosity=1.81e-5, cd=0.47, rho=1.225):
    if mode == "linear":
        return 6.0 * math.pi * viscosity * RADIUS / MASS
    if mode == "quadratic":
        return 0.5 * rho * math.pi * RADIUS**2 * cd / MASS
    return 0.0


def position_check(module, mode) -> Check:
    def run():
        ball = module.Projectile(mass=MASS, radius=RADIUS)
        expected = exact_position(mode, T_END, drag_constant(mode))
        hs, errs = [], []
        for n in NS:
            _, xs, ys = ball.simulate(V0, ANGLE, mode=mode, dt=T_END / n)
            hs.append(T_END / n)
            errs.append(float(np.max(np.abs(np.array([xs[n], ys[n]]) - expected))))
        return check_order(hs, errs, 1.0, scale=float(np.max(np.abs(expected))))

    return Check("reference", f"v1 {mode}/euler position at t = {T_END:g}", run)


def range_check(module) -> Check:
    def run():
        ball = module.Projectile(mass=MASS, radius=RADIUS)
        exact = V0 * V0 * math.sin(math.radians(2 * ANGLE)) / 9.81
        hs, errs = [], []
        for dt in (0.02, 0.01, 0.005, 0.0025):
            _, xs, _ = ball.simulate(V0, ANGLE, mode="vacuum", dt=dt)
            hs.append(dt)
            errs.append(abs(xs[-1] - exact))
        return check_order(hs, errs, 1.0, scale=exact)

    return Check("limit", "v1 vacuum/euler range", run)


def checks(module=None) -> list[Check]:
    module = module or load()
    return [position_check(module, m) for m in ("vacuum", "linear", "quadratic")] + [range_check(module)]
