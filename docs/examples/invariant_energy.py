"""Energy of a harmonic oscillator: velocity Verlet keeps it to O(h^2); a wrong velocity update does not."""
import numpy as np

from physverify.studies import invariant_study


def make(buggy):
    def integrate(source, y0, t_end, n):  # velocity Verlet for x'' = -x
        h = t_end / n
        x, v = np.array(y0, dtype=float)
        for _ in range(n):
            a = -x
            x = x + h * v + 0.5 * h * h * a
            a_new = -x
            v = v + (h * a if buggy else 0.5 * h * (a + a_new))  # bug: only the old acceleration
        return np.array([x, v])
    return integrate


def energy(y):
    return 0.5 * (y[0] ** 2 + y[1] ** 2)


for buggy in (False, True):
    r = invariant_study(make(buggy), energy, np.array([1.0, 0.0]), 10.0, [50, 100, 200, 400], 2)
    print("buggy:  " if buggy else "correct:", r.status, "-", r.message)
