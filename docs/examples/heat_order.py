"""Order of a 1D explicit heat solver, u_t = u_xx + s on [0, 1] with u = 0 at both ends, by a manufactured solution.

u(x, t) = sin(pi x) exp(-t) + x (1 - x) t is not a solution of u_t = u_xx, but it is one of u_t = u_xx + s with
s = u_t - u_xx = -(1 - pi^2) sin(pi x) exp(-t) + x (1 - x) + 2 t. With dt = 0.25 dx^2 the scheme is second order
in dx. The buggy version takes the spacing as 1/(n + 1), from the number of points, instead of 1/n.
"""
import numpy as np

from physverify import check_order


def exact(x, t):
    return np.sin(np.pi * x) * np.exp(-t) + x * (1 - x) * t


def source(x, t):
    return -(1 - np.pi**2) * np.sin(np.pi * x) * np.exp(-t) + x * (1 - x) + 2 * t


def solve(n, buggy, t_end=0.1):
    x = np.linspace(0.0, 1.0, n + 1)        # n intervals
    dx = 1.0 / (n + 1) if buggy else 1.0 / n  # buggy: spacing taken from the number of points
    steps = int(round(t_end / (0.25 * dx * dx)))
    dt = t_end / steps
    u = exact(x, 0.0)
    for k in range(steps):
        t = k * dt
        lap = np.zeros_like(u)
        lap[1:-1] = (u[2:] - 2 * u[1:-1] + u[:-2]) / dx**2
        u = u + dt * (lap + source(x, t))
        u[0] = u[-1] = 0.0                      # exact boundary values
    return np.abs(u - exact(x, t_end)).max(), 1.0 / n


def study(buggy, ns=(10, 20, 40, 80)):
    errs, hs = zip(*(solve(n, buggy) for n in ns))
    return check_order(list(hs), list(errs), expected=2), list(hs), list(errs)


if __name__ == "__main__":
    for buggy in (False, True):
        r, _, _ = study(buggy)
        print("buggy:  " if buggy else "correct:", r.status, "-", r.message)
