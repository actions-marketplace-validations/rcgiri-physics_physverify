"""A physverify spec: the checks for examples/damped_oscillator.py.

    physverify run examples/verify_damped_oscillator.py --html report.html
    pytest examples/verify_damped_oscillator.py                            (physverify installed)
    pytest -p physverify.pytest_plugin examples/verify_damped_oscillator.py   (not installed; do not use -p when installed)

The reference right-hand side below is written independently of the solver.
"""

import numpy as np

import damped_oscillator as solver
from physverify import ManufacturedODE, ode_checks

OMEGA, GAMMA = 3.0, 0.4


def reference_rhs(t, y):
    return np.array([y[1], -(OMEGA**2) * y[0] - 2.0 * GAMMA * y[1]])


def checks():
    mms = ManufacturedODE(lambda t: np.array([np.sin(1.3 * t) + 0.2, 1.04 * np.cos(1.3 * t)]), reference_rhs)
    return ode_checks(
        "midpoint damped oscillator",
        solver.integrate,
        rhs_ref=reference_rhs,
        mms=mms,
        y0_free=np.array([1.0, 0.0]),
        t_end=1.0,
        ns=(10, 20, 40, 80, 160),
        order=2.0,
        patch=(np.array([0.5, -0.3]), np.array([0.8, 1.1])),
        integrate_trajectory=lambda s, y0, t, n: solver.integrate(s, y0, t, n, trajectory=True),
    )
