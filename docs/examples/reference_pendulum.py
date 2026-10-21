"""Compare a pendulum solver with an independent high-accuracy reference (no exact solution needed)."""
import numpy as np

from physverify.studies import reference_study

G, L = 9.81, 1.0


def integrate(source, y0, t_end, n):  # classical RK4, the code under test
    h, y = t_end / n, np.array(y0, dtype=float)

    def f(t, y):
        return np.array([y[1], -G / L * np.sin(y[0])]) + source(t)

    for k in range(n):
        t = k * h
        k1 = f(t, y)
        k2 = f(t + h / 2, y + h / 2 * k1)
        k3 = f(t + h / 2, y + h / 2 * k2)
        k4 = f(t + h, y + h * k3)
        y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return y


def reference_rhs(t, y):  # the pendulum equation, typed again from the textbook
    return np.array([y[1], -9.81 * np.sin(y[0])])


r = reference_study(integrate, reference_rhs, np.array([1.0, 0.0]), 2.0, [20, 40, 80, 160], 4)
print(r.status, "-", r.message)
