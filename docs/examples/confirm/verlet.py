"""Velocity Verlet for x'' = -omega^2 x. Written for the docs; it is correct."""
import numpy as np


def integrate(source, y0, t_end, n, omega=2.0):
    """n velocity-Verlet steps from t = 0 to t_end; `source` is not used (no forcing)."""
    h = t_end / n
    x, v = float(y0[0]), float(y0[1])
    a = -omega**2 * x
    for _ in range(n):
        x = x + h * v + 0.5 * h * h * a
        a_new = -omega**2 * x
        v = v + 0.5 * h * (a + a_new)
        a = a_new
    return np.array([x, v])
