"""Exact reference solutions that testing public codes needed again and again.

Each one was written by hand in several adapters before it moved here (repository IDs as in
results/corpus/SUMMARY.md). All are numpy-only and vectorised where that is natural.
"""

from __future__ import annotations

import math

import numpy as np

# --- statistical mechanics ---------------------------------------------------------------------------


def ising2d_exact(L: int, T: float, J: float = 1.0, h: float = 0.0) -> dict:
    """Exact thermal averages of the periodic L x L Ising model by enumerating all 2^(L*L) states.

    H = -J sum_<ij> s_i s_j - h sum_i s_i, k_B = 1. Returns per-site <e>, <|m|>, <m^2>, <m^4>, the
    specific heat per site and Z. Practical up to L = 4 (65536 states); used for D04, H06, H55.
    """
    n = L * L
    if n > 20:
        raise ValueError("enumeration is limited to L*L <= 20 sites (L <= 4)")
    states = ((np.arange(2**n)[:, None] >> np.arange(n)) & 1) * 2 - 1
    s = states.reshape(-1, L, L)
    bonds = np.sum(s * np.roll(s, 1, axis=1), axis=(1, 2)) + np.sum(s * np.roll(s, 1, axis=2), axis=(1, 2))
    M = s.sum(axis=(1, 2))
    E = -J * bonds - h * M
    w = np.exp(-(E - E.min()) / T)
    Z = w.sum()
    avg = lambda q: float(np.sum(w * q) / Z)  # noqa: E731
    e, e2 = avg(E) / n, avg(E**2) / n**2
    return {"e": e, "m_abs": avg(np.abs(M)) / n, "m2": avg(M**2) / n**2, "m4": avg(M**4) / n**4,
            "c": n * (e2 - e * e) / T**2, "Z": float(Z * np.exp(-E.min() / T))}


def langevin(x):
    """L(x) = coth x - 1/x, with the series near 0."""
    x = np.asarray(x, dtype=float)
    small = np.abs(x) < 1e-3
    safe = np.where(small, 1.0, x)
    return np.where(small, x / 3 - x**3 / 45, 1 / np.tanh(safe) - 1 / safe)


def heisenberg_open_chain(N: int, J: float, T: float) -> dict:
    """Classical unit-vector Heisenberg chain with open ends, H = -J sum S_i.S_{i+1}: exact per-site
    energy and specific heat (each bond is independent). Used for H64."""
    b = J / T
    e = -(N - 1) * J * float(langevin(b)) / N
    c = (N - 1) / N * (1 - b * b / math.sinh(b) ** 2)
    return {"e": e, "c": c}


# --- diffusion and transport -------------------------------------------------------------------------


def heat_sine_mode(x, t, L: float = 1.0, kappa: float = 1.0, mode: int = 1):
    """u_t = kappa u_xx on [0, L], u = 0 at both ends, u(x, 0) = sin(mode pi x / L)."""
    k = mode * np.pi / L
    return np.exp(-kappa * k * k * t) * np.sin(k * np.asarray(x, dtype=float))


def advection_diffusion_gaussian(x, t, x0: float, sigma0: float, v: float = 0.0, D: float = 0.0):
    """Gaussian of peak 1 and width sigma0 at x0, carried at speed v and spread by D on the whole line:
    sigma^2 = sigma0^2 + 2 D t, peak sigma0/sigma. Used for H25."""
    s = math.sqrt(sigma0**2 + 2 * D * t)
    return sigma0 / s * np.exp(-((np.asarray(x, dtype=float) - x0 - v * t) ** 2) / (2 * s * s))


def semi_infinite_step(x, t, alpha: float, T0: float, Ts: float):
    """Semi-infinite solid at T0, surface held at Ts from t = 0: T = Ts + (T0 - Ts) erf(x / 2 sqrt(alpha t))."""
    x = np.asarray(x, dtype=float)
    return Ts + (T0 - Ts) * np.vectorize(math.erf)(x / (2 * math.sqrt(alpha * t)))


# --- mechanics ---------------------------------------------------------------------------------------


def double_pendulum_acc(th1, w1, th2, w2, m1, m2, l1, l2, g=9.81):
    """Angular accelerations of a double pendulum (point masses, massless rods, angles from the downward
    vertical), from the Lagrangian mass matrix. Used for D01, E01, H03, H27."""
    d = th1 - th2
    M = np.array([[(m1 + m2) * l1**2, m2 * l1 * l2 * np.cos(d)], [m2 * l1 * l2 * np.cos(d), m2 * l2**2]])
    r = np.array([-m2 * l1 * l2 * w2**2 * np.sin(d) - (m1 + m2) * g * l1 * np.sin(th1),
                  m2 * l1 * l2 * w1**2 * np.sin(d) - m2 * g * l2 * np.sin(th2)])
    return np.linalg.solve(M, r)


def double_pendulum_energy(th1, w1, th2, w2, m1, m2, l1, l2, g=9.81):
    v1sq = (l1 * w1) ** 2
    v2sq = v1sq + (l2 * w2) ** 2 + 2 * l1 * l2 * w1 * w2 * np.cos(th1 - th2)
    return 0.5 * m1 * v1sq + 0.5 * m2 * v2sq - (m1 + m2) * g * l1 * np.cos(th1) - m2 * g * l2 * np.cos(th2)


def cantilever_tip(P: float, L: float, E: float, I: float) -> tuple[float, float]:
    """Euler-Bernoulli cantilever with an end load: tip deflection P L^3/(3EI) and rotation P L^2/(2EI)."""
    return P * L**3 / (3 * E * I), P * L**2 / (2 * E * I)


# --- quantum mechanics -------------------------------------------------------------------------------


def infinite_well_energy(n, W: float, hbar: float = 1.0, m: float = 1.0):
    """E_n = n^2 pi^2 hbar^2 / (2 m W^2), n = 1, 2, ... Used for H19."""
    n = np.asarray(n, dtype=float)
    return n * n * np.pi**2 * hbar**2 / (2 * m * W * W)


def barrier_transmission(E, V: float, a: float, hbar: float = 1.0, m: float = 1.0):
    """Transmission probability through a square barrier of height V and width a (E != V). Used for H40."""
    E = np.asarray(E, dtype=float)
    k = np.sqrt(2 * m * np.abs(V - E)) / hbar * a
    s2 = np.where(E < V, np.sinh(k) ** 2, np.sin(k) ** 2)
    return 1 / (1 + V * V * s2 / (4 * E * np.abs(V - E)))


def tfim_open_ground_energy(N: int, J: float, h: float) -> float:
    """Ground energy of the open transverse-field Ising chain H = J sum Z_i Z_{i+1} + h sum X_i, from the
    free-fermion (Jordan-Wigner, Bogoliubov-de Gennes) solution; the sign of J does not matter. Used for H22."""
    A = np.zeros((N, N))
    B = np.zeros((N, N))
    np.fill_diagonal(A, 2 * h)
    for i in range(N - 1):
        A[i, i + 1] = A[i + 1, i] = J
        B[i, i + 1], B[i + 1, i] = J, -J
    eps = np.linalg.eigvalsh(np.block([[A, B], [-B, -A]]))
    return float(-0.5 * np.sum(eps[eps > 0]))
