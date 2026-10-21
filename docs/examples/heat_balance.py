"""Heat budget of a 1D explicit heat solver with insulated walls: the total heat must not change."""
import numpy as np

from physverify.studies import balance_check


def initial(n):
    x = (np.arange(n) + 0.5) / n  # cell centres on [0, 1]
    return np.exp(-50 * (x - 0.3) ** 2)


def heat_change(n, buggy, steps=200):
    dx = 1.0 / n
    u = initial(n)
    dt = 0.4 * dx * dx
    for _ in range(steps):
        if buggy:  # "insulated" by copying the neighbour value after the update
            lap = np.zeros_like(u)
            lap[1:-1] = u[2:] - 2 * u[1:-1] + u[:-2]
            u = u + dt / dx**2 * lap
            u[0], u[-1] = u[1], u[-2]
        else:  # zero flux through both walls, written as fluxes between cells
            flux = np.zeros(n + 1)
            flux[1:-1] = -(u[1:] - u[:-1]) / dx
            u = u - dt / dx * (flux[1:] - flux[:-1])
    return (u.sum() - initial(n).sum()) * dx


for buggy in (False, True):
    r = balance_check(lambda n: heat_change(n, buggy), 0.0, [40, 80, 160], tol=1e-12)
    print("buggy:  " if buggy else "correct:", r.status, "-", r.message)
