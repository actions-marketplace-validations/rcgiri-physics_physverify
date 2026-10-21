"""A midpoint (RK2) solver, correct and with a one-character bug, checked by a manufactured solution."""
import numpy as np

from physverify import ManufacturedODE, mms_order_study

OMEGA = 2.0


def rhs(t, y):  # the code under test: a harmonic oscillator
    return np.array([y[1], -OMEGA**2 * y[0]])


def integrate(source, y0, t_end, n, buggy=False):
    """Midpoint method on y' = rhs(t, y) + source(t)."""
    h, y = t_end / n, np.array(y0, dtype=float)

    def f(t, y):
        return rhs(t, y) + source(t)

    for k in range(n):
        t = k * h
        k1 = f(t, y)
        mid = y + (h if buggy else h / 2) * k1  # bug: a full step instead of half a step
        y = y + h * f(t + h / 2, mid)
    return y


def reference_rhs(t, y):  # written again from the physics, not copied from the code
    return np.array([y[1], -4.0 * y[0]])


mms = ManufacturedODE(lambda t: np.array([np.sin(1.3 * t) + 0.2, 1.3 * np.cos(1.3 * t)]), reference_rhs)
ns = [10, 20, 40, 80, 160]
print("correct:", mms_order_study(integrate, mms, 1.0, ns, 2).message)
print("buggy:  ", mms_order_study(lambda s, y0, T, n: integrate(s, y0, T, n, buggy=True), mms, 1.0, ns, 2).message)
