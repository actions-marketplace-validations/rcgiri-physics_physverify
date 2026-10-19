"""Exact reference values for the 2D Ising model on an L x L torus.

Convention throughout: H = -J sum_<ij> s_i s_j - h sum_i s_i with s = +1 or -1,
periodic boundaries, k_B = 1. The bond sum runs over the right and the down
neighbour of every site, 2 L^2 bonds (for L = 2 each pair is counted twice,
which is what a code looping over right and down neighbours does).

Three independent routes, cross-checked in the tests (milestone M0 of
docs/plan_ising.md):

enumeration  every state for L <= 5: the exact joint density of states g(E, M)
kaufman      Kaufman's closed form for the zero-field partition function of a
             finite torus (as written by Beale, PRL 76, 78 (1996))
onsager      the infinite-lattice energy, critical temperature and Yang's
             spontaneous magnetization
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

J = 1.0
T_C = 2.0 / math.log(1.0 + math.sqrt(2.0))  # Onsager, about 2.2692


# --- enumeration ---


@lru_cache(maxsize=None)
def density_of_states(L: int):
    """Exact counts g[(E_bond + 2N) / 2, (M + N) / 2] for J = 1, as an integer array.

    E_bond = -sum over the 2N right/down bonds of s_a s_b; M = sum of spins.
    L = 5 has 2^25 states and takes several seconds.
    """
    if not 1 <= L <= 5:
        raise ValueError("enumeration is limited to L <= 5")
    n = L * L
    bonds = []
    for i in range(L):
        for j in range(L):
            k = i * L + j
            bonds.append((k, i * L + (j + 1) % L))
            bonds.append((k, ((i + 1) % L) * L + j))
    counts = np.zeros((2 * n + 1, n + 1), dtype=np.int64)
    chunk = 1 << min(n, 22)
    for start in range(0, 1 << n, chunk):
        x = np.arange(start, start + chunk, dtype=np.uint64)
        up = np.zeros(chunk, dtype=np.int64)
        for k in range(n):
            up += ((x >> np.uint64(k)) & np.uint64(1)).astype(np.int64)
        unlike = np.zeros(chunk, dtype=np.int64)
        for a, b in bonds:
            unlike += (((x >> np.uint64(a)) ^ (x >> np.uint64(b))) & np.uint64(1)).astype(np.int64)
        energy = -(2 * n - 2 * unlike)  # each like bond -1, each unlike bond +1
        magnet = 2 * up - n
        idx = ((energy + 2 * n) // 2) * (n + 1) + (magnet + n) // 2
        counts += np.bincount(idx, minlength=counts.size).reshape(counts.shape)
    return counts


def _levels(L):
    n = L * L
    energies = np.arange(-2 * n, 2 * n + 1, 2, dtype=float)
    magnets = np.arange(-n, n + 1, 2, dtype=float)
    return energies, magnets


def boltzmann_weights(L: int, T: float, h: float = 0.0):
    """Normalised probabilities P(E_bond, M) on the (energy, magnetization) grid."""
    g = density_of_states(L).astype(float)
    energies, magnets = _levels(L)
    H = J * energies[:, None] - h * magnets[None, :]
    with np.errstate(divide="ignore"):
        logw = np.where(g > 0, np.log(g) - H / T, -np.inf)
    logw -= logw.max()
    w = np.exp(logw)
    return w / w.sum()


def exact_moments(L: int, T: float, h: float = 0.0) -> dict:
    """Exact per-spin averages from enumeration. e is the total energy H / N (field term included)."""
    n = L * L
    P = boltzmann_weights(L, T, h)
    energies, magnets = _levels(L)
    e = (J * energies[:, None] - h * magnets[None, :]) / n
    m = np.broadcast_to(magnets[None, :] / n, P.shape)
    return {
        "e": float((P * e).sum()),
        "e2": float((P * e * e).sum()),
        "m": float((P * m).sum()),
        "abs_m": float((P * np.abs(m)).sum()),
        "m2": float((P * m * m).sum()),
        "m4": float((P * m**4).sum()),
    }


def energy_distribution(L: int, T: float, h: float = 0.0):
    """(levels of e = H / N at h = 0, probabilities). Only valid for h = 0, where H depends on E alone."""
    if h != 0.0:
        raise ValueError("the energy distribution is tabulated for h = 0 only")
    energies, _ = _levels(L)
    p = boltzmann_weights(L, T).sum(axis=1)
    keep = p > 0
    return J * energies[keep] / (L * L), p[keep]


def abs_magnetization_distribution(L: int, T: float, h: float = 0.0):
    """(levels of |m|, probabilities)."""
    _, magnets = _levels(L)
    p = boltzmann_weights(L, T, h).sum(axis=0)
    levels = np.abs(magnets) / (L * L)
    out = {}
    for lev, prob in zip(levels, p):
        out[round(float(lev), 12)] = out.get(round(float(lev), 12), 0.0) + float(prob)
    keys = sorted(out)
    return np.array(keys), np.array([out[k] for k in keys])


# --- Kaufman's finite-torus partition function (h = 0) ---


def _log_abs_and_sign(values):
    values = np.asarray(values, dtype=float)
    sign = float(np.prod(np.sign(values)))
    with np.errstate(divide="ignore"):
        return float(np.sum(np.log(np.abs(values)))), sign


def kaufman_log_z(L: int, T: float, M: int | None = None) -> float:
    """log Z of the zero-field Ising model on an L x M torus (M = L by default), J = 1.

    Z = 1/2 (2 sinh 2K)^{LM/2} [Z1 + Z2 + Z3 + Z4],
    Z1 = prod_{r<L} 2 cosh(M g_{2r+1} / 2),  Z2 = prod 2 sinh(M g_{2r+1} / 2),
    Z3 = prod_{r<L} 2 cosh(M g_{2r} / 2),    Z4 = prod 2 sinh(M g_{2r} / 2),
    cosh g_l = cosh 2K coth 2K - cos(pi l / L) for l >= 1, and g_0 = 2K + ln tanh K
    (negative below T_c, which makes Z4 negative).
    """
    M = L if M is None else M
    K = J / T
    c = math.cosh(2 * K) / math.tanh(2 * K)
    gam = np.empty(2 * L)
    gam[0] = 2 * K + math.log(math.tanh(K))
    for l in range(1, 2 * L):
        gam[l] = math.acosh(c - math.cos(math.pi * l / L))
    odd, even = gam[1::2], gam[0::2]
    terms = [
        _log_abs_and_sign(2 * np.cosh(M * odd / 2)),
        _log_abs_and_sign(2 * np.sinh(M * odd / 2)),
        _log_abs_and_sign(2 * np.cosh(M * even / 2)),
        _log_abs_and_sign(2 * np.sinh(M * even / 2)),
    ]
    top = max(t[0] for t in terms if t[1] != 0)
    total = sum(s * math.exp(lg - top) for lg, s in terms if s != 0)
    return math.log(0.5) + 0.5 * L * M * math.log(2 * math.sinh(2 * K)) + top + math.log(total)


def kaufman_moments(L: int, T: float) -> dict:
    """Per-spin energy e and e^2 at h = 0 from derivatives of log Z in beta (central differences)."""
    n = L * L
    beta = 1.0 / T
    d = 1e-4 * beta

    def logz(b):
        return kaufman_log_z(L, 1.0 / b)

    f0, fp, fm = logz(beta), logz(beta + d), logz(beta - d)
    fpp, fmm = logz(beta + 2 * d), logz(beta - 2 * d)
    d1 = (-fpp + 8 * fp - 8 * fm + fmm) / (12 * d)
    d2 = (-fpp + 16 * fp - 30 * f0 + 16 * fm - fmm) / (12 * d * d)
    mean_E = -d1
    var_E = d2
    return {"e": mean_E / n, "e2": (var_E + mean_E**2) / n**2}


# --- Onsager / Yang, infinite lattice ---


def _ellipk(k: float) -> float:
    """Complete elliptic integral of the first kind K(k), modulus k < 1, by the AGM."""
    a, b = 1.0, math.sqrt(1.0 - k * k)
    for _ in range(60):
        a, b = 0.5 * (a + b), math.sqrt(a * b)
        if abs(a - b) < 1e-16 * a:
            break
    return math.pi / (2.0 * a)


def onsager_energy(T: float) -> float:
    """Energy per spin of the infinite lattice at h = 0."""
    K = J / T
    if abs(T - T_C) < 1e-12:
        return -math.sqrt(2.0) * J
    k = 2.0 * math.sinh(2 * K) / math.cosh(2 * K) ** 2
    return -J / math.tanh(2 * K) * (1.0 + 2.0 / math.pi * (2.0 * math.tanh(2 * K) ** 2 - 1.0) * _ellipk(k))


def yang_magnetization(T: float) -> float:
    """Spontaneous magnetization per spin of the infinite lattice (0 above T_c)."""
    if T >= T_C:
        return 0.0
    return (1.0 - math.sinh(2 * J / T) ** -4) ** 0.125
