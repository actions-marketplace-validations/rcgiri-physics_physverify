"""Check your own ODE code in four steps.

    PYTHONPATH=src python examples/check_my_solver.py

The code under test here is a small midpoint-method solver for a damped
oscillator. It declares second order. Change `damping` inside `my_rhs` to see
the checks flag it.
"""

import numpy as np

from physverify import ManufacturedODE, ode_checks
from physverify.checks import run_check

OMEGA, GAMMA = 3.0, 0.4


# 1. An independent statement of the physics: x'' = -omega^2 x - 2 gamma x'.
def reference_rhs(t, y):
    return np.array([y[1], -(OMEGA**2) * y[0] - 2.0 * GAMMA * y[1]])


# 2. The code under test. It must accept an additive source term; this is the hook.
def my_rhs(t, y):
    damping = 2.0 * GAMMA  # try 2.0 * GAMMA * 1.1
    return np.array([y[1], -(OMEGA**2) * y[0] - damping * y[1]])


def my_integrate(source, y0, t_end, n_steps):
    h = t_end / n_steps
    y = np.array(y0, dtype=float)
    for i in range(n_steps):
        t = i * h
        k1 = my_rhs(t, y) + source(t)
        mid = y + 0.5 * h * k1
        y = y + h * (my_rhs(t + 0.5 * h, mid) + source(t + 0.5 * h))
    return y


# 3. A smooth manufactured solution (any smooth function of t, written with NumPy).
mms = ManufacturedODE(lambda t: np.array([np.sin(1.3 * t) + 0.2, 1.3 * np.cos(1.3 * t) * 0.8]), reference_rhs)

# 4. Run the checks.
for check in ode_checks(
    "midpoint solver",
    my_integrate,
    rhs_ref=reference_rhs,
    mms=mms,
    y0_free=np.array([1.0, 0.0]),
    t_end=1.0,
    ns=(10, 20, 40, 80, 160),
    order=2.0,
    # quantity=...  pass a conserved quantity here if your system has one (damping means this one has none)
):
    result = run_check(check)
    print(f"{check.family:10s} {result.status:12s} {result.message}")
