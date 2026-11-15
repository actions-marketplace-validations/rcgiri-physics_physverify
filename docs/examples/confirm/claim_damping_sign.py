"""Claim: the damping term in oscillator.py has the wrong sign. Expected verdict: confirmed."""
import numpy as np

import oscillator  # the code under test
from physverify import Check, ManufacturedODE, mms_order_study

CLAIM = {
    "text": "rhs() adds +gamma*v, so the damping pumps energy in instead of removing it",
    "source": "a person reading the code (example)",
    "file": "oscillator.py",
    "line": 10,
    "reference": "Taylor, Classical Mechanics, sec. 5.4: m x'' + b x' + k x = 0, friction opposes the velocity",
    "impact": "used",  # the script's own run sets gamma = 0.3
}

OMEGA, GAMMA = 2.0, 0.5
NS = [10, 20, 40, 80, 160]


def manufactured(t):  # any smooth function; the forcing is built so that it solves the reference equation
    return np.array([np.sin(1.3 * t) + 0.2, 1.3 * np.cos(1.3 * t)])


def reference_rhs(gamma):  # written from the textbook equation, not from oscillator.py
    return lambda t, y: np.array([y[1], -OMEGA**2 * y[0] - gamma * y[1]])


def study(gamma):
    mms = ManufacturedODE(manufactured, reference_rhs(gamma))
    run = lambda s, y0, t_end, n: oscillator.integrate(s, y0, t_end, n, omega=OMEGA, gamma=gamma)  # noqa: E731
    return lambda: mms_order_study(run, mms, 1.0, NS, 2)


def control():
    # without damping the sign of the damping term does not matter, so this must pass
    return Check("mms", "midpoint rule is second order with gamma = 0 (no damping)", study(0.0))


def checks():
    return [Check("mms", f"midpoint rule is second order with gamma = {GAMMA} (damping on)", study(GAMMA))]
