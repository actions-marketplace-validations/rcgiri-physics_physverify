"""Reference time steppers and a fixed-step driver.

These are used (a) to build independent reference solutions and (b) as the
stepper when only a right-hand side, not a whole solver, is under test.
"""

from __future__ import annotations

import numpy as np


def euler(f, t, y, h):
    return y + h * f(t, y)


def midpoint(f, t, y, h):
    k1 = f(t, y)
    return y + h * f(t + 0.5 * h, y + 0.5 * h * k1)


def rk4(f, t, y, h):
    k1 = f(t, y)
    k2 = f(t + 0.5 * h, y + 0.5 * h * k1)
    k3 = f(t + 0.5 * h, y + 0.5 * h * k2)
    k4 = f(t + h, y + h * k3)
    return y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


STEPPERS = {"euler": (euler, 1), "midpoint": (midpoint, 2), "rk4": (rk4, 4)}


def integrate_fixed(f, y0, t0, t1, n_steps, stepper=rk4):
    """Advance y' = f(t, y) from t0 to t1 in n_steps equal steps."""
    h = (t1 - t0) / n_steps
    y = np.array(y0, dtype=float)
    for i in range(n_steps):
        y = stepper(f, t0 + i * h, y, h)
    return y
