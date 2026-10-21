"""Convergence-study pitfalls: a run that stops one step short, and comparing at a whole period."""
import math

import numpy as np

from physverify.studies import trajectory_order_study


def rk4_run(n_steps, h):
    """RK4 on x'' = -x; returns the times and states of every step."""
    t, y = [0.0], [np.array([1.0, 0.0])]

    def f(y):
        return np.array([y[1], -y[0]])

    for k in range(n_steps):
        x = y[-1]
        k1 = f(x)
        k2 = f(x + h / 2 * k1)
        k3 = f(x + h / 2 * k2)
        k4 = f(x + h * k3)
        y.append(x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4))
        t.append((k + 1) * h)
    return np.array(t), np.array(y)


T = 2 * math.pi


def exact(t):
    return np.array([math.cos(t), -math.sin(t)])


ns = (40, 80, 160, 320)
good = [rk4_run(n, T / n) for n in ns]
print("at 3T/4:", trajectory_order_study(good, exact, 0.75 * T, 4).message)

# the classic mistake: n = int(t_end / h) can come out one short in floating point
short = [rk4_run(n - 1 if n == 80 else n, T / n) for n in ns]
r = trajectory_order_study(short, exact, T, 4)
print("one run short:", r.status, "-", r.message)

r = trajectory_order_study(good, exact, T, 4, period=T)
print("at a whole period:", r.status, "-", r.message)
