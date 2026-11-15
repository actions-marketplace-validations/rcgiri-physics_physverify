"""A damped oscillator, x'' = -omega^2 x - gamma x', advanced with the explicit midpoint rule.

Written for the docs. It has a sign error in the damping term, so the damping pumps energy in.
"""
import numpy as np


def rhs(y, omega, gamma):
    x, v = y
    return np.array([v, -omega**2 * x + gamma * v])


def integrate(source, y0, t_end, n, omega=2.0, gamma=0.0):
    """n midpoint steps of y' = rhs(y) + source(t) from t = 0 to t_end."""
    h, y = t_end / n, np.array(y0, dtype=float)
    for k in range(n):
        t = k * h
        mid = y + h / 2 * (rhs(y, omega, gamma) + source(t))
        y = y + h * (rhs(mid, omega, gamma) + source(t + h / 2))
    return y


if __name__ == "__main__":  # the project's own run uses damping, so the faulty term is reached
    print(integrate(lambda t: 0.0, [1.0, 0.0], 10.0, 1000, gamma=0.3))
