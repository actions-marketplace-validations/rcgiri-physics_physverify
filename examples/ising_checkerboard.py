"""A small 2D Ising sampler to be checked: checkerboard Metropolis, many chains at once.

Written independently of physverify's own samplers, in the style of a short
research code. It provides the interface physverify.stochastic expects
(sample, error_bar, init, sweep, measure; see docs/ising.md). Introduce a bug,
for example drop the factor 2 in `dE`, and `physverify run` reports it.
"""

import numpy as np

J = 1.0


class State:
    def __init__(self, spins, E, M):
        self.spins, self.E, self.M = spins, E, M


class CheckerboardIsing:
    algorithm = "checkerboard"

    def __init__(self, burn_in=100):
        self.burn_in = burn_in

    def measure(self, state, h=0.0):
        s = state.spins
        bonds = (s * (np.roll(s, -1, axis=1) + np.roll(s, -1, axis=2))).sum(axis=(1, 2))
        M = s.sum(axis=(1, 2))
        return -J * bonds - h * M, M

    def init(self, L, n_chains, start, rng, h=0.0):
        if start == "cold":
            spins = np.ones((n_chains, L, L))
        else:
            spins = rng.choice([-1.0, 1.0], size=(n_chains, L, L))
        state = State(spins, None, None)
        state.E, state.M = self.measure(state, h)
        return state

    def sweep(self, state, T, h, rng):
        n_chains, L, _ = state.spins.shape
        parity = np.add.outer(np.arange(L), np.arange(L)) % 2
        for colour in (0, 1):
            s = state.spins
            field = J * (np.roll(s, 1, 1) + np.roll(s, -1, 1) + np.roll(s, 1, 2) + np.roll(s, -1, 2)) + h
            dE = 2.0 * s * field
            flip = (parity == colour) & (rng.random(s.shape) < np.exp(-np.maximum(dE, 0.0) / T))
            state.E = state.E + (dE * flip).sum(axis=(1, 2))
            state.M = state.M - (2.0 * s * flip).sum(axis=(1, 2))
            state.spins = np.where(flip, -s, s)

    def sample(self, L, T, h, n_sweeps, seed, n_chains=1, start="hot"):
        rng = np.random.default_rng(seed)
        state = self.init(L, n_chains, start, rng, h)
        for _ in range(self.burn_in):
            self.sweep(state, T, h, rng)
        e = np.empty((n_chains, n_sweeps))
        m = np.empty((n_chains, n_sweeps))
        for t in range(n_sweeps):
            self.sweep(state, T, h, rng)
            E, M = self.measure(state, h)
            e[:, t], m[:, t] = E / L**2, M / L**2
        return e, m

    def error_bar(self, series):
        """Error of the mean by blocking: halve the series into blocks until the estimate levels off."""
        x = np.asarray(series, dtype=float)
        best = x.std() / np.sqrt(len(x))
        while len(x) >= 32:
            x = 0.5 * (x[: len(x) // 2 * 2 : 2] + x[1 : len(x) // 2 * 2 : 2])
            best = max(best, x.std(ddof=1) / np.sqrt(len(x)))
        return best
