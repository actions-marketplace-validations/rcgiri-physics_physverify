"""Planar double pendulum. State: [theta1, theta2, omega1, omega2], angles from the downward vertical.

The reference operator uses the explicit closed-form accelerations (no matrix
solve) so that it is written differently from a typical mass-matrix solver.
"""

from __future__ import annotations

import math

import numpy as np

from ..checks import FAIL, PASS, Check, Result
from ..mms import ManufacturedODE
from ..studies import close_result, ode_checks, smoke_check
from ._common import STEPPER_BUGS, BugInfo, families, make_integrate

NAME = "pendulum"
PARAMS = dict(m1=1.0, m2=0.8, L1=1.0, L2=0.7, g=9.81)

BUGS = {
    "coupling_sign": BugInfo(
        "centripetal coupling term of the first equation has the wrong sign",
        families("mms", "reference", "invariant", "patch"),
        "error plateaus; energy not conserved",
    ),
    "mass_matrix_missing_cos": BugInfo(
        "mass matrix entry m2*L2*cos(theta1-theta2) is missing its cosine",
        families("mms", "reference", "invariant", "patch"),
        "error plateaus; energy not conserved",
    ),
    "gravity_mass_missing": BugInfo(
        "gravity on the first equation uses m1 instead of m1+m2",
        families("mms", "reference", "invariant", "limit", "patch"),
        "error plateaus; energy not conserved; normal-mode frequencies wrong",
    ),
    "rk4_stage4_time": BugInfo(
        "RK4 evaluates its fourth stage at t + h/2 instead of t + h",
        families("mms", "patch"),
        "visible only when the right-hand side depends on time: the free pendulum is autonomous, "
        "so the reference and invariant checks cannot see it; the forced (MMS) runs drop to order 1",
    ),
    "swapped_lengths": BugInfo(
        "second equation uses L2 where L1 belongs in the omega1^2 term",
        families("mms", "reference", "invariant", "patch"),
        "error plateaus; energy not conserved",
    ),
    "small_angle_gravity": BugInfo(
        "gravity on the second pendulum uses theta2 instead of sin(theta2)",
        families("mms", "reference", "invariant", "patch"),
        "error plateaus at large angles; small-oscillation frequencies unchanged",
    ),
    **STEPPER_BUGS,
}


def rhs_reference(p=PARAMS):
    m1, m2, L1, L2, g = p["m1"], p["m2"], p["L1"], p["L2"], p["g"]

    def f(t, y):
        t1, t2, w1, w2 = y
        d = t1 - t2
        den = 2.0 * m1 + m2 - m2 * math.cos(2.0 * d)
        a1 = (
            -g * (2.0 * m1 + m2) * math.sin(t1)
            - m2 * g * math.sin(t1 - 2.0 * t2)
            - 2.0 * math.sin(d) * m2 * (w2 * w2 * L2 + w1 * w1 * L1 * math.cos(d))
        ) / (L1 * den)
        a2 = (
            2.0
            * math.sin(d)
            * (w1 * w1 * L1 * (m1 + m2) + g * (m1 + m2) * math.cos(t1) + w2 * w2 * L2 * m2 * math.cos(d))
        ) / (L2 * den)
        return np.array([w1, w2, a1, a2])

    return f


def energy_reference(y, p=PARAMS):
    m1, m2, L1, L2, g = p["m1"], p["m2"], p["L1"], p["L2"], p["g"]
    t1, t2, w1, w2 = y
    kinetic = 0.5 * m1 * (L1 * w1) ** 2 + 0.5 * m2 * (
        (L1 * w1) ** 2 + (L2 * w2) ** 2 + 2.0 * L1 * L2 * w1 * w2 * math.cos(t1 - t2)
    )
    potential = -(m1 + m2) * g * L1 * math.cos(t1) - m2 * g * L2 * math.cos(t2)
    return kinetic + potential


def rhs_seeded(bugs, p=PARAMS):
    """Mass-matrix form M(theta) alpha = f(theta, omega), with optional bugs."""
    m1, m2, L1, L2, g = p["m1"], p["m2"], p["L1"], p["L2"], p["g"]

    def f(t, y):
        t1, t2, w1, w2 = y
        d = t1 - t2
        c = 1.0 if "mass_matrix_missing_cos" in bugs else math.cos(d)
        mass = np.array([[(m1 + m2) * L1, m2 * L2 * c], [L1 * math.cos(d), L2]])
        sign = 1.0 if "coupling_sign" in bugs else -1.0
        gravity_mass = m1 if "gravity_mass_missing" in bugs else (m1 + m2)
        L_w1 = L2 if "swapped_lengths" in bugs else L1
        sin_t2 = t2 if "small_angle_gravity" in bugs else math.sin(t2)
        force = np.array(
            [
                sign * m2 * L2 * w2 * w2 * math.sin(d) - gravity_mass * g * math.sin(t1),
                L_w1 * w1 * w1 * math.sin(d) - g * sin_t2,
            ]
        )
        a1, a2 = np.linalg.solve(mass, force)
        return np.array([w1, w2, a1, a2])

    return f


def manufactured() -> ManufacturedODE:
    def u(t):
        return np.array(
            [
                0.8 * np.sin(t),
                -0.5 + 0.6 * np.cos(1.3 * t),
                0.2 + 0.7 * np.cos(0.9 * t),
                0.4 * np.sin(1.1 * t),
            ]
        )

    return ManufacturedODE(u, rhs_reference())


def small_oscillation_omegas(p=PARAMS):
    """Normal-mode angular frequencies about the hanging equilibrium (closed form)."""
    m1, m2, L1, L2, g = p["m1"], p["m2"], p["L1"], p["L2"], p["g"]
    s = (m1 + m2) * (L1 + L2)
    disc = math.sqrt(s * s - 4.0 * m1 * (m1 + m2) * L1 * L2)
    w_sq = [g * (s - disc) / (2.0 * m1 * L1 * L2), g * (s + disc) / (2.0 * m1 * L1 * L2)]
    return [math.sqrt(x) for x in w_sq]


def linearized_omegas(rhs, eps=1e-6):
    """Angular frequencies from a finite-difference Jacobian of `rhs` at rest at the bottom."""
    jac = np.zeros((4, 4))
    for j in range(4):
        step = np.zeros(4)
        step[j] = eps
        jac[:, j] = (np.asarray(rhs(0.0, step), float) - np.asarray(rhs(0.0, -step), float)) / (2 * eps)
    eig = np.linalg.eigvals(jac)
    return sorted(abs(eig.imag))[::2], max(abs(eig.real))


def frequency_check(rhs, label="small-oscillation frequencies", tol=1e-5) -> Check:
    def run():
        omegas, growth = linearized_omegas(rhs)
        expected = small_oscillation_omegas()
        if growth > 1e-6:
            return Result(FAIL, f"equilibrium is not neutrally stable (growth rate {growth:.3g})")
        err = max(abs(a - b) / b for a, b in zip(omegas, expected))
        if err > tol:
            return Result(FAIL, f"frequencies {omegas} differ from {expected} (relative error {err:.2g})")
        return Result(PASS, f"frequencies match the closed form (relative error {err:.1e})")

    return Check("limit", label, run)


MMS_T_END = 1.0
NS_RK4 = (10, 20, 40, 80, 160)
Y0_FREE = np.array([0.4, 0.3, 0.0, 0.0])  # moderate amplitude, released from rest
PATCH = (np.array([0.3, -0.2, 0.5, -0.4]), np.array([0.5, -0.4, 0.3, 0.6]))
SMOKE_N = 80
SMOKE_RTOL = 1e-3


def checks(bugs=frozenset()) -> list[Check]:
    rhs = rhs_seeded(bugs)
    out = ode_checks(
        "rk4",
        make_integrate(rhs, bugs, "rk4"),
        rhs_ref=rhs_reference(),
        mms=manufactured(),
        y0_free=Y0_FREE,
        t_end=MMS_T_END,
        ns=NS_RK4,
        order=4.0,
        quantity=energy_reference,
        patch=PATCH,
        integrate_trajectory=make_integrate(rhs, bugs, "rk4", trajectory=True),
    )
    out.append(frequency_check(rhs))
    return out


def smoke_checks(bugs=frozenset()) -> list[Check]:
    """Plain unit tests: one run against a reference, and energy conserved, each within 0.1%."""
    rhs = rhs_seeded(bugs)
    integrate = make_integrate(rhs, bugs, "rk4")

    def run_energy():
        y = integrate(lambda t: 0.0, Y0_FREE, MMS_T_END, SMOKE_N)
        return close_result(energy_reference(y), energy_reference(Y0_FREE), SMOKE_RTOL)

    return [
        smoke_check("rk4", integrate, rhs_reference(), Y0_FREE, MMS_T_END, SMOKE_N, rtol=SMOKE_RTOL),
        Check("smoke", "energy conserved", run_energy),
    ]
