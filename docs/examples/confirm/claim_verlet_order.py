"""Claim: velocity Verlet in verlet.py is only first order. Expected verdict: rejected."""
import numpy as np

import verlet  # the code under test
from physverify import Check, reference_study

CLAIM = {
    "text": "line 13 uses the old acceleration in the velocity update, so the method is only first order",
    "source": "an AI code review (example)",
    "file": "verlet.py",
    "line": 13,
    "reference": "Hairer, Lubich and Wanner, Geometric Numerical Integration, sec. I.1.4: Stormer-Verlet is second order",
    "impact": "used",
}

NS = [10, 20, 40, 80, 160]


def reference_rhs(omega):  # x'' = -omega^2 x, written from the equation of motion
    return lambda t, y: np.array([y[1], -omega**2 * y[0]])


def study(omega):
    run = lambda s, y0, t_end, n: verlet.integrate(s, y0, t_end, n, omega=omega)  # noqa: E731
    return lambda: reference_study(run, reference_rhs(omega), np.array([1.0, 0.5]), 1.0, NS, 2)


def control():
    # a free particle has no acceleration, so old and new acceleration agree and the result must be exact
    return Check("reference", "free particle (omega = 0): straight-line motion", study(0.0))


def checks():
    return [Check("reference", "velocity Verlet is second order on the harmonic oscillator (omega = 2)", study(2.0))]
