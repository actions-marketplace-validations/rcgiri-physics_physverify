"""Claim: the RK4 step in decay.py is not fourth order. Expected verdict: not decidable.

The claim file reads `half_life` as the decay rate. decay.py documents that its parameter is the
half-life (rate = ln 2 / half_life), so the reference below solves a different equation and the control
fails: the test itself is wrong, and nothing can be said about the claim until the reference is fixed.
"""
import numpy as np

import decay  # the code under test
from physverify import Check, ManufacturedODE, mms_order_study

CLAIM = {
    "text": "the k3 stage is evaluated with the wrong slope, so the method is not fourth order",
    "source": "an AI code review (example)",
    "file": "decay.py",
    "line": 22,
    "reference": "Butcher, Numerical Methods for ODEs, sec. 23: the classical RK4 tableau is fourth order",
    "impact": "unknown",
}

RATE = 1.0  # mistake kept on purpose: decay.py takes a half-life, not a rate
NS = [10, 20, 40, 80, 160]


def reference_rhs(t, y):
    return -RATE * y


def study(manufactured):
    mms = ManufacturedODE(manufactured, reference_rhs)
    run = lambda s, y0, t_end, n: decay.integrate(s, y0, t_end, n, half_life=RATE)  # noqa: E731
    return lambda: mms_order_study(run, mms, 1.0, NS, 4)


def control():
    return Check("mms", "RK4 is fourth order on a slowly varying solution", study(lambda t: np.array([1.0 + 0.5 * t])))


def checks():
    return [Check("mms", "RK4 is fourth order on an oscillating solution", study(lambda t: np.array([np.cos(3.0 * t)])))]
