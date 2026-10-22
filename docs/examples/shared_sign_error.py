"""A reference that shares the code's mistake passes; an independent check catches it.

The solver below should solve x'' = -omega^2 x (a spring), but has the sign of the
force wrong. A reference right-hand side copied from the solver has the same wrong
sign, so the order checks pass. Energy conservation is derived from the physics,
not from the code, and fails.
"""

import numpy as np

from physverify import ManufacturedODE, invariant_study, mms_order_study, reference_study

OMEGA = 2.0


def rhs(t, y):
    return np.array([y[1], +(OMEGA**2) * y[0]])  # bug: the force should be -omega^2 x


def integrate(source, y0, t_end, n):  # midpoint method with a source-term hook
    h, y = t_end / n, np.array(y0, dtype=float)
    for i in range(n):
        t = i * h
        mid = y + 0.5 * h * (rhs(t, y) + source(t))
        y = y + h * (rhs(t + 0.5 * h, mid) + source(t + 0.5 * h))
    return y


def copied_rhs(t, y):  # written by looking at the solver: the same sign error
    return np.array([y[1], +(OMEGA**2) * y[0]])


def energy(y):  # from the physics: kinetic plus spring energy is constant
    return 0.5 * y[1] ** 2 + 0.5 * OMEGA**2 * y[0] ** 2


ns = (20, 40, 80, 160)
y0 = np.array([1.0, 0.0])
mms = ManufacturedODE(lambda t: np.array([np.sin(t), np.cos(t)]), copied_rhs)
print("mms, copied reference:      ", mms_order_study(integrate, mms, 1.0, ns, 2.0).status)
print("reference, copied reference:", reference_study(integrate, copied_rhs, y0, 1.0, ns, 2.0).status)
print("energy conservation:        ", invariant_study(integrate, energy, y0, 1.0, ns, 2.0).status)
