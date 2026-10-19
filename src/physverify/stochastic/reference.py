"""A trusted reference: one Ising chain in plain Python, written for clarity, not speed.

Used to replay a recorded random-number stream (the `scripted_rng` check) and as
the independent energy and magnetization functions for `bookkeeping`. The
vectorised sampler in `physverify.stochastic.sampler` must reproduce it exactly
when given the same random numbers; a test checks that.

Random-number protocol for single-site updates (Metropolis and heat bath): per
attempt, one integer site index k in [0, L*L) (row-major: i = k // L, j = k % L),
then one uniform u in [0, 1).
"""

from __future__ import annotations

import math

J = 1.0


def neighbour_sum(spins, i, j):
    L = len(spins)
    return spins[(i + 1) % L][j] + spins[(i - 1) % L][j] + spins[i][(j + 1) % L] + spins[i][(j - 1) % L]


def energy(spins, h=0.0):
    """H = -J sum over right and down bonds of s_i s_j - h sum s_i."""
    L = len(spins)
    bonds = 0.0
    for i in range(L):
        for j in range(L):
            bonds += spins[i][j] * (spins[i][(j + 1) % L] + spins[(i + 1) % L][j])
    return -J * bonds - h * magnetization(spins)


def magnetization(spins):
    return float(sum(sum(row) for row in spins))


def metropolis_attempt(spins, k, u, T, h=0.0):
    """One Metropolis attempt at site k with uniform u; flips in place. Returns True if accepted."""
    L = len(spins)
    i, j = divmod(int(k), L)
    s = spins[i][j]
    dE = 2.0 * s * (J * neighbour_sum(spins, i, j) + h)
    if dE <= 0.0 or u < math.exp(-dE / T):
        spins[i][j] = -s
        return True
    return False


def heat_bath_attempt(spins, k, u, T, h=0.0):
    """One heat-bath update at site k: the spin is set up with probability 1 / (1 + exp(-2 phi / T))."""
    L = len(spins)
    i, j = divmod(int(k), L)
    phi = J * neighbour_sum(spins, i, j) + h
    p_up = 1.0 / (1.0 + math.exp(-2.0 * phi / T))
    spins[i][j] = 1 if u < p_up else -1
    return True


def replay(spins, draws, T, h, algorithm="metropolis"):
    """Apply a list of (site, u) draws in order; returns the final lattice (a copy)."""
    spins = [list(row) for row in spins]
    attempt = metropolis_attempt if algorithm == "metropolis" else heat_bath_attempt
    for k, u in draws:
        attempt(spins, k, u, T, h)
    return spins
