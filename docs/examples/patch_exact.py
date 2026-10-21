"""A patch test: a straight-line solution that the midpoint method must reproduce to round-off."""
import numpy as np

from physverify.studies import patch_study


def make(buggy):
    def integrate(source, y0, t_end, n):
        h, y = t_end / n, np.array(y0, dtype=float)

        def f(t, y):
            return np.array([y[1], -y[0]]) + source(t)

        for k in range(n):
            t = k * h
            tm = t + (0.4 if buggy else 0.5) * h  # bug: the midpoint stage is evaluated at the wrong time
            y = y + h * f(tm, y + 0.5 * h * f(t, y))
        return y
    return integrate


def rhs_ref(t, y):
    return np.array([y[1], -y[0]])


for buggy in (False, True):
    r = patch_study(make(buggy), rhs_ref, np.array([0.5, -0.3]), np.array([0.8, 1.1]), 1.0, [10, 20, 40])
    print("buggy:  " if buggy else "correct:", r.status, "-", r.message)
