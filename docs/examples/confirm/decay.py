"""Radioactive decay with a source, N' = -(ln 2 / half_life) N + s(t), advanced with classical RK4.

Written for the docs; it is correct. Its parameter is the half-life, not the decay rate.
"""
import math

import numpy as np


def integrate(source, y0, t_end, n, half_life=1.0):
    """n RK4 steps from t = 0 to t_end."""
    rate = math.log(2) / half_life
    h, y = t_end / n, np.array(y0, dtype=float)

    def f(t, y):
        return -rate * y + source(t)

    for k in range(n):
        t = k * h
        k1 = f(t, y)
        k2 = f(t + h / 2, y + h / 2 * k1)
        k3 = f(t + h / 2, y + h / 2 * k2)
        k4 = f(t + h, y + h * k3)
        y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return y
