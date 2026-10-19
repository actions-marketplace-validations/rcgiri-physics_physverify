"""Projectile with vacuum, linear and quadratic drag. State: [x, y, vx, vy].

The reference operator follows the equations in the projectile-simulation
README, written separately from the solver below. One parameter is taken from
the code rather than the README: the linear drag coefficient b = 0.01 N s/m
(the README says b = 6*pi*eta*r, which gives a much smaller value).
"""

from __future__ import annotations

import math

import numpy as np

from ..checks import Check
from ..mms import ManufacturedODE
from ..order import check_order
from ..studies import ode_checks
from ._common import STEPPER_BUGS, BugInfo, families, make_integrate, rk4_with_bugs

NAME = "projectile"
PARAMS = dict(m=0.45, r=0.11, Cd=0.47, rho=1.225, g=9.81, b=0.01)
MODES = ("vacuum", "linear", "quadratic")

BUGS = {
    "gravity_sign": BugInfo(
        "gravity accelerates the projectile upward",
        families("mms", "reference", "invariant", "limit"),
    ),
    "linear_drag_missing_mass": BugInfo(
        "linear drag coefficient is b instead of b/m",
        families("mms", "reference"),
    ),
    "quad_drag_factor_half": BugInfo(
        "quadratic drag is missing the factor 1/2",
        families("mms", "reference"),
    ),
    "quad_drag_speed_from_vx": BugInfo(
        "speed in the quadratic drag uses |vx| instead of |v|",
        families("mms", "reference"),
    ),
    "quad_drag_abs_vx": BugInfo(
        "x drag uses |vx| instead of vx, which is wrong only when the projectile moves backwards",
        families("mms"),
    ),
    "landing_no_interp": BugInfo(
        "range is read from the last step before landing, with no interpolation",
        families("limit"),
    ),
    "angle_not_converted": BugInfo(
        "launch angle in degrees is passed to sin/cos unconverted",
        families("limit"),
    ),
    **STEPPER_BUGS,
}


def rhs_reference(mode: str, p=PARAMS):
    m, r, Cd, rho, g, b = p["m"], p["r"], p["Cd"], p["rho"], p["g"], p["b"]
    area = math.pi * r * r

    def f(t, z):
        vx, vy = z[2], z[3]
        ax, ay = 0.0, -g
        if mode == "linear":
            ax -= (b / m) * vx
            ay -= (b / m) * vy
        elif mode == "quadratic":
            c = 0.5 * rho * Cd * area / m
            speed = math.hypot(vx, vy)
            ax -= c * speed * vx
            ay -= c * speed * vy
        return np.array([vx, vy, ax, ay])

    return f


def rhs_seeded(mode: str, bugs, p=PARAMS):
    m, r, Cd, rho, g, b = p["m"], p["r"], p["Cd"], p["rho"], p["g"], p["b"]
    area = math.pi * r * r
    k_lin = b if "linear_drag_missing_mass" in bugs else b / m
    k_quad = (rho * Cd * area / m) if "quad_drag_factor_half" in bugs else 0.5 * rho * Cd * area / m
    gravity = g if "gravity_sign" in bugs else -g

    def f(t, z):
        vx, vy = z[2], z[3]
        ax, ay = 0.0, gravity
        if mode == "linear":
            ax -= k_lin * vx
            ay -= k_lin * vy
        elif mode == "quadratic":
            speed = abs(vx) if "quad_drag_speed_from_vx" in bugs else math.hypot(vx, vy)
            vx_used = abs(vx) if "quad_drag_abs_vx" in bugs else vx
            ax -= k_quad * speed * vx_used
            ay -= k_quad * speed * vy
        return np.array([vx, vy, ax, ay])

    return f


def energy_vacuum(z, p=PARAMS):
    return 0.5 * p["m"] * (z[2] ** 2 + z[3] ** 2) + p["m"] * p["g"] * z[1]


def manufactured(mode: str) -> ManufacturedODE:
    """x_m(t) = t lets a code with no time argument see t through x (see adapters).

    vx_m changes sign near t = 0.8 so that code paths for a projectile moving
    backwards are exercised. y_m is above ground until t = 1.5, so a code that
    runs until landing stops soon after the measurement time t = 1. Slow
    time dependence matters: through the x-as-time trick an error in x changes
    the forcing, and a fast-varying vx_m amplified Euler's O(h) error until the
    run blew up.
    """

    def u(t):
        return np.array(
            [
                t,
                7.5 * t - 5.0 * t * t,
                1.0 - 1.4 * t + 0.3 * np.sin(t),
                7.5 - 10.0 * t + np.sin(2.0 * t),
            ]
        )

    return ManufacturedODE(u, rhs_reference(mode))


MMS_T_END = 1.0
NS_RK4 = (10, 20, 40, 80, 160)
NS_EULER = (40, 80, 160, 320, 640)
Y0_FREE = np.array([0.0, 0.0, 10.0, 12.0])  # moves forwards the whole time, lands after ~2.4 s


def range_seeded(v0, angle_deg, dt, bugs, mode="vacuum"):
    """Horizontal range from a launch at the origin, integrated with RK4 until landing."""
    rad = angle_deg if "angle_not_converted" in bugs else math.radians(angle_deg)
    f = rhs_seeded(mode, bugs)
    z = np.array([0.0, 0.0, v0 * math.cos(rad), v0 * math.sin(rad)])
    t = 0.0
    while t < 100.0:  # a launch that has not landed after 100 s is not a ballistic flight
        z_new = rk4_with_bugs(f, t, z, dt, bugs)
        t += dt
        if z_new[1] < 0.0:
            if "landing_no_interp" in bugs:
                return z[0]
            frac = z[1] / (z[1] - z_new[1])
            return z[0] + frac * (z_new[0] - z[0])
        z = z_new
    raise RuntimeError("projectile never landed within 100 s")


def range_vacuum_exact(v0, angle_deg, g=PARAMS["g"]):
    return v0 * v0 * math.sin(2.0 * math.radians(angle_deg)) / g


def range_dts(v0, angle_deg, counts=(10, 20, 40, 80, 160), g=PARAMS["g"]):
    """Step sizes that put the landing in the middle of a step.

    With the landing at a fixed phase inside a step the interpolation error is a
    smooth function of dt. Otherwise it jumps around and an order fit is
    meaningless.
    """
    flight_time = 2.0 * v0 * math.sin(math.radians(angle_deg)) / g
    return [flight_time / (n + 0.5) for n in counts]


def range_check(range_fn, v0=30.0, angle_deg=40.0, label="vacuum/rk4 range") -> Check:
    """Vacuum range against v0^2 sin(2a)/g. Linear interpolation of the landing gives order 2."""

    def run():
        exact = range_vacuum_exact(v0, angle_deg)
        dts = range_dts(v0, angle_deg)
        errs = [abs(range_fn(v0, angle_deg, dt) - exact) for dt in dts]
        return check_order(dts, errs, 2.0, floor=1e-12)

    return Check("limit", label, run)


def checks(bugs=frozenset()) -> list[Check]:
    out: list[Check] = []
    for mode in MODES:
        for method, ns, order in (("rk4", NS_RK4, 4.0), ("euler", NS_EULER, 1.0)):
            if method == "euler" and "euler_instead_of_rk4" in bugs:
                continue  # the bug only replaces RK4
            if method == "euler" and any(b in bugs for b in ("rk4_weights", "rk4_full_step_stage2")):
                continue
            integrate = make_integrate(rhs_seeded(mode, bugs), bugs, method)
            out += ode_checks(
                f"{mode}/{method}",
                integrate,
                rhs_ref=rhs_reference(mode),
                mms=manufactured(mode),
                y0_free=Y0_FREE,
                t_end=MMS_T_END,
                ns=ns,
                order=order,
                quantity=energy_vacuum if mode == "vacuum" else None,
            )
    out.append(range_check(lambda v0, a, dt: range_seeded(v0, a, dt, bugs)))
    return out
