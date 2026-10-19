"""A small solver to be checked: midpoint method for a damped oscillator.

x'' = -omega^2 x - 2 gamma x', written as y = [x, v]. The solver accepts an
additive source term, which is the hook physverify needs. Change `damping` in
`rhs` (for example to 2.0 * GAMMA * 1.1) and `physverify run` reports it.
"""

import numpy as np

OMEGA, GAMMA = 3.0, 0.4


def rhs(t, y):
    damping = 2.0 * GAMMA
    return np.array([y[1], -(OMEGA**2) * y[0] - damping * y[1]])


def integrate(source, y0, t_end, n_steps, trajectory=False):
    h = t_end / n_steps
    y = np.array(y0, dtype=float)
    states = [y]
    for i in range(n_steps):
        t = i * h
        k1 = rhs(t, y) + source(t)
        mid = y + 0.5 * h * k1
        y = y + h * (rhs(t + 0.5 * h, mid) + source(t + 0.5 * h))
        states.append(y)
    return np.array(states) if trajectory else y
