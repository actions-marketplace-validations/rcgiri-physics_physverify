"""Kepler problem: a body in the inverse-square field of a fixed mass. State: [x, y, vx, vy].

Two invariants (energy and angular momentum) and a limit (Kepler's third law:
after one period the orbit closes) give checks that tell bugs apart. A force
that is central but not inverse-square keeps angular momentum and loses energy;
a force that is not central loses both.

The reference operator uses the vector form -GM r / |r|^3; the solver below
writes it as a magnitude times a unit vector, as many codes do.
"""

from __future__ import annotations

import math

import numpy as np

from physverify.checks import Check
from physverify.mms import ManufacturedODE
from physverify.order import check_order
from physverify.studies import close_result, invariant_study, ode_checks, smoke_check
from ._common import STEPPER_BUGS, BugInfo, families, make_integrate

NAME = "kepler"
GM = 1.0
ECC = 0.5  # orbit for the free runs: semi-major axis 1, released at periapsis
SOFTENING = 1e-3

BUGS = {
    "inverse_r_force": BugInfo(
        "force magnitude GM/r instead of GM/r^2",
        families("mms", "reference", "invariant", "limit", "patch"),
        "wrong orbit; energy drifts, angular momentum is still conserved (the force is still central)",
    ),
    "y_force_sign": BugInfo(
        "the y component of the force has the wrong sign",
        families("mms", "reference", "invariant", "limit", "patch"),
        "force no longer central: energy and angular momentum both drift",
    ),
    "gm_one_percent": BugInfo(
        "GM is 1% too large in the force (for example a unit-conversion constant)",
        families("mms", "reference", "invariant", "limit", "patch"),
        "error plateaus; the energy computed with the true GM drifts; the orbit does not close",
    ),
    "softening_left_on": BugInfo(
        f"gravitational softening r^2 + eps^2 with eps = {SOFTENING:g} left on",
        families("mms", "reference", "patch"),
        "a small plateau (relative size about eps^2 / r^2 = 1e-6); visible only once the "
        "truncation error is smaller than that",
    ),
    **STEPPER_BUGS,
}


def rhs_reference(gm=GM):
    def f(t, z):
        x, y, vx, vy = z
        r3 = (x * x + y * y) ** 1.5
        return np.array([vx, vy, -gm * x / r3, -gm * y / r3])

    return f


def rhs_seeded(bugs, gm=GM):
    gm_used = gm * 1.01 if "gm_one_percent" in bugs else gm
    eps2 = SOFTENING**2 if "softening_left_on" in bugs else 0.0

    def f(t, z):
        x, y, vx, vy = z
        r = math.sqrt(x * x + y * y + eps2)
        magnitude = gm_used / r if "inverse_r_force" in bugs else gm_used / (r * r)
        ux, uy = x / r, y / r
        ay = magnitude * uy if "y_force_sign" in bugs else -magnitude * uy
        return np.array([vx, vy, -magnitude * ux, ay])

    return f


def energy(z, gm=GM):
    x, y, vx, vy = z
    return 0.5 * (vx * vx + vy * vy) - gm / math.sqrt(x * x + y * y)


def angular_momentum(z):
    x, y, vx, vy = z
    return x * vy - y * vx


def periapsis_state(ecc=ECC, a=1.0, gm=GM):
    rp = a * (1.0 - ecc)
    return np.array([rp, 0.0, 0.0, math.sqrt(gm * (1.0 + ecc) / rp)])


def period(a=1.0, gm=GM):
    return 2.0 * math.pi * math.sqrt(a**3 / gm)


def manufactured() -> ManufacturedODE:
    """A smooth path that stays between r = 0.7 and r = 1.3, away from the singularity."""

    def u(t):
        return np.array(
            [
                np.cos(t) + 0.2 * np.sin(2.0 * t),
                0.9 * np.sin(t),
                -np.sin(t) + 0.3 * np.cos(1.5 * t),
                0.8 * np.cos(t) + 0.1 * t,
            ]
        )

    return ManufacturedODE(u, rhs_reference())


MMS_T_END = 1.0
NS_RK4 = (20, 40, 80, 160, 320)
Y0_FREE = periapsis_state()
PATCH = (np.array([1.0, 0.5, 0.2, -0.3]), np.array([0.3, 0.4, -0.2, 0.1]))
ORBIT_NS = (100, 200, 400, 800, 1600)  # steps per period for the closure check


def closure_check(integrate, label="orbit closes after one period") -> Check:
    """Kepler's third law: after T = 2 pi sqrt(a^3 / GM) the state returns to the start."""

    def run():
        y0, t = periapsis_state(), period()
        hs = [t / n for n in ORBIT_NS]
        errs = [float(np.max(np.abs(integrate(lambda s: 0.0, y0, t, n) - y0))) for n in ORBIT_NS]
        return check_order(hs, errs, 4.0, scale=float(np.max(np.abs(y0))))

    return Check("limit", label, run)


def checks(bugs=frozenset()) -> list[Check]:
    rhs = rhs_seeded(bugs)
    integrate = make_integrate(rhs, bugs, "rk4")
    out = ode_checks(
        "rk4",
        integrate,
        rhs_ref=rhs_reference(),
        mms=manufactured(),
        y0_free=Y0_FREE,
        t_end=MMS_T_END,
        ns=NS_RK4,
        order=4.0,
        quantity=energy,
        patch=PATCH,
        integrate_trajectory=make_integrate(rhs, bugs, "rk4", trajectory=True),
    )
    out.append(
        Check(
            "invariant",
            "rk4 angular momentum",
            lambda: invariant_study(integrate, angular_momentum, Y0_FREE, MMS_T_END, NS_RK4, 4.0),
        )
    )
    out.append(closure_check(integrate))
    return out


SMOKE_N = 200
SMOKE_RTOL = 1e-3


def smoke_checks(bugs=frozenset()) -> list[Check]:
    """Plain tests: one run against a reference, energy conserved, each within 0.1%."""
    rhs = rhs_seeded(bugs)
    integrate = make_integrate(rhs, bugs, "rk4")

    def run_energy():
        y = integrate(lambda t: 0.0, Y0_FREE, MMS_T_END, SMOKE_N)
        return close_result(energy(y), energy(Y0_FREE), SMOKE_RTOL)

    return [
        smoke_check("rk4", integrate, rhs_reference(), Y0_FREE, MMS_T_END, SMOKE_N, rtol=SMOKE_RTOL),
        Check("smoke", "energy conserved", run_energy),
    ]
