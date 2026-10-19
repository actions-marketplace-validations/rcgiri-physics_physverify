"""The Ising sampler interface, and a vectorised sampler with switchable seeded bugs.

Interface a code under test provides (see docs/ising.md):

black box
    sample(L, T, h, n_sweeps, seed, n_chains=1, start="hot") -> (e, m)
        per-spin energy H / N and magnetization M / N after every sweep, arrays of
        shape (n_chains, n_sweeps), after the code's own burn-in
    error_bar(series) -> float
        the code's error bar for the mean of one chain's series (optional)

white box (optional; checks that need a method the code lacks are skipped)
    init(L, n_chains, start, rng) -> state      state.spins (n_chains, L, L), state.E, state.M
    sweep(state, T, h, rng)                      one sweep, updating state.E and state.M incrementally
    step(state, sites, u, T, h)                  one single-site update per chain at the given
                                                 sites (flat index) with the given uniforms
    measure(state, h) -> (E, M)                  totals computed from the lattice

`rng` follows numpy's Generator: the code may call only rng.integers(low, high,
size) and rng.random(size). For single-site algorithms the expected order is one
site array, then one uniform array, per attempt (physverify.stochastic.reference).

Many chains are run at once (arrays over the first axis), which makes the
statistical checks affordable in plain NumPy. The chains are independent.
"""

from __future__ import annotations

import numpy as np

from .stats import blocked_error

ALGORITHMS = ("metropolis", "heatbath", "checkerboard", "wolff")


class State:
    def __init__(self, spins, E, M):
        self.spins, self.E, self.M = spins, E, M


class IsingSampler:
    """Metropolis (random site), heat bath (random site), checkerboard Metropolis or Wolff.

    `bugs` switches on seeded bugs by name (see physverify.stochastic.ising.BUGS).
    With no bugs this sampler reproduces physverify.stochastic.reference exactly.
    """

    def __init__(self, algorithm="metropolis", bugs=frozenset(), burn_in=100):
        if algorithm not in ALGORITHMS:
            raise ValueError(algorithm)
        self.algorithm = algorithm
        self.bugs = frozenset(bugs)
        self.burn_in = 0 if "no_burn_in" in self.bugs else burn_in
        self.J = -1.0 if "j_sign_flipped" in self.bugs else 1.0
        self.zero_one = "spins_zero_one" in self.bugs

    # --- representation ---

    def _up(self):
        return 1.0

    def _down(self):
        return 0.0 if self.zero_one else -1.0

    def _flipped(self, s):
        return 1.0 - s if self.zero_one else -s

    # --- lattice sums ---

    def _tables(self, L):
        """Neighbour indices (N, 4) and weights (N, 4) of every site, with the code's bugs applied."""
        key = ("tables", L)
        if key not in self.__dict__:
            idx = np.empty((L * L, 4), dtype=np.intp)
            w = np.ones((L * L, 4))
            for i in range(L):
                for j in range(L):
                    k = i * L + j
                    down, up = ((i + 1) % L) * L + j, ((i - 1) % L) * L + j
                    right, left = i * L + (j + 1) % L, i * L + (j - 1) % L
                    if "same_neighbour_twice" in self.bugs:
                        up = down
                    idx[k] = (down, up, right, left)
                    if "missing_wrap_x" in self.bugs:
                        w[k, 2] = 1.0 if j + 1 < L else 0.0
                        w[k, 3] = 1.0 if j - 1 >= 0 else 0.0
            self.__dict__[key] = (idx, w)
        return self.__dict__[key]

    def _neighbour_sum(self, flat, sites, L):
        """Sum of the four neighbours of the given site in every chain (flat: (n_chains, N))."""
        idx, w = self._tables(L)
        n_chains = flat.shape[0]
        base = np.arange(n_chains) * (L * L)
        values = flat.ravel()
        total = 0.0
        for d in range(4):
            v = values[base + idx[sites, d]]
            total = total + (v if "missing_wrap_x" not in self.bugs else v * w[sites, d])
        return total

    def _neighbour_sum_all(self, spins):
        s = spins
        down, up = np.roll(s, -1, axis=1), np.roll(s, 1, axis=1)
        right, left = np.roll(s, -1, axis=2), np.roll(s, 1, axis=2)
        return down + up + right + left

    def measure(self, state, h=0.0):
        s = state.spins
        if "energy_double_counted" in self.bugs:
            bonds = (s * self._neighbour_sum_all(s)).sum(axis=(1, 2))
        else:
            right = np.roll(s, -1, axis=2)
            if "missing_wrap_x" in self.bugs:
                right = right.copy()
                right[:, :, -1] = 0.0
            bonds = (s * (right + np.roll(s, -1, axis=1))).sum(axis=(1, 2))
        M = s.sum(axis=(1, 2))
        return -self.J * bonds - h * M, M

    # --- set-up ---

    def init(self, L, n_chains, start, rng, h=0.0):
        if start == "cold":
            spins = np.full((n_chains, L, L), self._up())
        else:
            spins = np.where(rng.random((n_chains, L, L)) < 0.5, self._up(), self._down())
        state = State(spins, None, None)
        state.E, state.M = self.measure(state, h)
        return state

    # --- single-site updates ---

    def step(self, state, sites, u, T, h):
        spins = state.spins
        n_chains, L, _ = spins.shape
        flat = spins.reshape(n_chains, L * L)  # a view: writes go to state.spins
        rows = np.arange(n_chains)
        sites = np.asarray(sites, dtype=np.intp)
        s = flat[rows, sites]
        h_dyn = -h if "field_sign_wrong" in self.bugs else h
        phi = self.J * self._neighbour_sum(flat, sites, L) + h_dyn
        if self.algorithm == "heatbath":
            factor = 1.0 if "heatbath_missing_2" in self.bugs else 2.0
            p_up = 1.0 / (1.0 + np.exp(-factor * phi / T))
            new = np.where(u < p_up, self._up(), self._down())
            dE_track = -(new - s) * phi
        else:
            dE = (1.0 if "delta_e_missing_factor_2" in self.bugs else 2.0) * s * phi
            with np.errstate(over="ignore"):
                if "exp_de_times_t" in self.bugs:
                    p = np.exp(-dE * T)
                elif "acceptance_table_off_by_one" in self.bugs:
                    p = np.exp(-(dE + 4.0) / T)  # table entry for the next energy class
                else:
                    p = np.exp(-dE / T)
            accept = u < np.minimum(1.0, p)
            if "reject_zero_de" in self.bugs:
                accept &= dE != 0.0
            new = np.where(accept, self._flipped(s), s)
            dE_track = dE  # the code tracks the energy with its own local energy change
        changed = new != s
        if "incremental_energy_not_updated" not in self.bugs:
            state.E = state.E + np.where(changed, dE_track, 0.0)
        state.M = state.M + (new - s)
        flat[rows, sites] = new

    # --- sweeps ---

    def sweep(self, state, T, h, rng):
        if self.algorithm in ("metropolis", "heatbath"):
            n_chains, L, _ = state.spins.shape
            N = L * L
            for _ in range(N):
                if "same_random_number" in self.bugs:
                    u = rng.random(n_chains)
                    sites = np.minimum((u * N).astype(int), N - 1)
                else:
                    high = N - L if "sweep_skips_last_row" in self.bugs else N
                    sites = rng.integers(0, high, size=n_chains)
                    u = rng.random(n_chains)
                self.step(state, sites, u, T, h)
        elif self.algorithm == "checkerboard":
            self._checkerboard_sweep(state, T, h, rng)
        else:
            self._wolff_update(state, T, h, rng)

    def _checkerboard_sweep(self, state, T, h, rng):
        s = state.spins
        n_chains, L, _ = s.shape
        ii, jj = np.meshgrid(np.arange(L), np.arange(L), indexing="ij")
        if "synchronous_update" in self.bugs:
            masks = [np.ones((L, L), dtype=bool)]
        elif "checkerboard_wrong_parity" in self.bugs:
            masks = [(ii + jj) % 2 == 0, (ii + jj) % 2 == 0]
        else:
            masks = [(ii + jj) % 2 == 0, (ii + jj) % 2 == 1]
        for mask in masks:
            phi = self.J * self._neighbour_sum_all(s) + h
            dE = 2.0 * s * phi
            u = rng.random((n_chains, L, L))
            accept = mask & (u < np.minimum(1.0, np.exp(-dE / T)))
            state.E = state.E + np.where(accept, dE, 0.0).sum(axis=(1, 2))
            state.M = state.M + np.where(accept, -2.0 * s, 0.0).sum(axis=(1, 2))
            s = np.where(accept, -s, s)
        state.spins[...] = s

    def _wolff_update(self, state, T, h, rng):
        """One Wolff cluster flip per chain (h must be 0). A 'sweep' here is one cluster update."""
        if h != 0.0:
            raise ValueError("the Wolff update is implemented for h = 0 only")
        n_chains, L, _ = state.spins.shape
        k = 1.0 if "wolff_probability" in self.bugs else 2.0
        p_add = 1.0 - np.exp(-k * self.J / T)
        for c in range(n_chains):
            s = state.spins[c]
            seed = int(rng.integers(0, L * L))
            i0, j0 = divmod(seed, L)
            sign = s[i0, j0]
            cluster = {(i0, j0)}
            stack = [(i0, j0)]
            while stack:
                i, j = stack.pop()
                for a, b in (((i + 1) % L, j), ((i - 1) % L, j), (i, (j + 1) % L), (i, (j - 1) % L)):
                    if (a, b) not in cluster and s[a, b] == sign and rng.random() < p_add:
                        cluster.add((a, b))
                        stack.append((a, b))
            for a, b in cluster:
                s[a, b] = -s[a, b]
        state.E, state.M = self.measure(state, h)

    # --- black box ---

    def sample(self, L, T, h, n_sweeps, seed, n_chains=1, start="hot"):
        rng = np.random.default_rng(12345 if "seed_ignored" in self.bugs else seed)
        state = self.init(L, n_chains, start, rng, h)
        for _ in range(self.burn_in):
            self.sweep(state, T, h, rng)
        e = np.empty((n_chains, n_sweeps))
        m = np.empty((n_chains, n_sweeps))
        N = L * L
        for t in range(n_sweeps):
            self.sweep(state, T, h, rng)
            E, M = self.measure(state, h)
            e[:, t] = E / N
            m[:, t] = M / (L if "m_normalised_by_L" in self.bugs else N)
        return e, m

    def error_bar(self, series):
        x = np.asarray(series, dtype=float)
        if "naive_error_bars" in self.bugs:
            return float(x.std() / np.sqrt(len(x)))
        return blocked_error(x)
