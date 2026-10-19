"""Checks for an Ising sampler (see physverify.stochastic.sampler for the interface).

Deterministic (plain PASS / FAIL, no statistics):

bookkeeping      tracked E and M, the code's own measurement, and an independent
                 recomputation from the lattice all agree exactly after every sweep
scripted_rng     the code's sweeps, fed recorded random numbers, give exactly the
                 lattices of the trusted reference replaying the same numbers
reproducibility  the same seed gives the same run; different seeds do not

Statistical (PASS / FAIL / INCONCLUSIVE, false-alarm rate per check stated in the message):

exact_distribution  fractions of time at each energy level and each |m| level, L = 4,
                    against exact enumeration
moments             <e>, <e^2>, <|m|>, <m^2> at temperatures below, at and above T_c
                    (L = 4, enumeration), <m> in a field, and <e>, <e^2> at L = 8
                    (Kaufman's closed form)
acceptance          single updates at controlled sites: acceptance frequency for each
                    energy change against min(1, exp(-dE / T)) (Metropolis) or the
                    heat-bath probability
symmetry            translation and spin-flip symmetry: every bond's mean correlation
                    and every site's mean spin against the exact values
equilibration       hot and cold starts agree from the first reported sweep
error_bars          the code's reported error bars against the actual spread of
                    independent chains

Each check uses its own fixed seed, so the whole suite is deterministic.
"""

from __future__ import annotations

import math

import numpy as np

from ..checks import EXACT, FAIL, INCONCLUSIVE, PASS, Check, Result
from . import exact as X
from . import reference as R
from .stats import ALPHA_CHECK, Comparison, compare_chain_means, t_critical, verdict

RESOLUTION = 0.02  # smallest deviation in a per-spin average (or a probability) that a statistical check must resolve
T_LOW, T_HIGH = 1.8, 3.0
T_DIST = 2.5


def _missing(sampler, *names):
    return [n for n in names if not callable(getattr(sampler, n, None))]


def _skip(names) -> Result:
    return Result(INCONCLUSIVE, f"not available: the sampler does not provide {', '.join(names)}")


# --- deterministic ---


def bookkeeping(sampler, *, L=4, h=0.25, n_chains=8, n_sweeps=40, seed=101) -> Check:
    def run():
        if _missing(sampler, "init", "sweep", "measure"):
            return _skip(_missing(sampler, "init", "sweep", "measure"))
        field = 0.0 if getattr(sampler, "algorithm", "") == "wolff" else h
        rng = np.random.default_rng(seed)
        state = sampler.init(L, n_chains, "hot", rng, field)
        for sweep in range(1, n_sweeps + 1):
            sampler.sweep(state, 2.5, field, rng)
            E_code, M_code = sampler.measure(state, field)
            for c in range(n_chains):
                spins = state.spins[c].tolist()
                E_ref, M_ref = R.energy(spins, field), R.magnetization(spins)
                values = {
                    "tracked": (float(state.E[c]), float(state.M[c])),
                    "measured by the code": (float(E_code[c]), float(M_code[c])),
                    "recomputed independently": (E_ref, M_ref),
                }
                if len({v for v in values.values()}) > 1:
                    listing = "; ".join(f"{k} E={v[0]:g}, M={v[1]:g}" for k, v in values.items())
                    return Result(FAIL, f"after sweep {sweep}, chain {c}: {listing}")
        return Result(EXACT, f"tracked, measured and recomputed E and M agree exactly over {n_sweeps} sweeps of {n_chains} chains")

    return Check("bookkeeping", f"L = {L}, h = {h:g}", run)


class RecordingRNG:
    """A numpy Generator that records every integers() and random() call, in order."""

    def __init__(self, seed):
        self._g = np.random.default_rng(seed)
        self.log = []

    def integers(self, low, high=None, size=None):
        out = self._g.integers(low, high, size=size)
        self.log.append(("integers", np.array(out, copy=True)))
        return out

    def random(self, size=None):
        out = self._g.random(size)
        self.log.append(("random", np.array(out, copy=True)))
        return out


def scripted_rng(sampler, *, L=4, T=2.5, h=0.25, n_chains=4, n_sweeps=10, seed=202) -> Check:
    algorithm = getattr(sampler, "algorithm", "metropolis")

    def run():
        if algorithm not in ("metropolis", "heatbath"):
            return Result(INCONCLUSIVE, f"no reference replay for the {algorithm} algorithm")
        if _missing(sampler, "init", "sweep"):
            return _skip(_missing(sampler, "init", "sweep"))
        for field in (0.0, h):  # h = 0 has moves with dE = 0, a field has none: both are needed
            result = _replay_once(field)
            if result is not None:
                return result
        return Result(EXACT, f"{n_sweeps} sweeps of {n_chains} chains at h = 0 and h = {h:g} match the reference replay exactly")

    def _replay_once(h):
        state = sampler.init(L, n_chains, "hot", np.random.default_rng(seed), h)
        lattices = [state.spins[c].tolist() for c in range(n_chains)]
        for sweep in range(1, n_sweeps + 1):
            rng = RecordingRNG(seed + sweep)
            sampler.sweep(state, T, h, rng)
            kinds = [k for k, _ in rng.log]
            if kinds != ["integers", "random"] * (len(kinds) // 2) or len(kinds) != 2 * L * L:
                return Result(
                    FAIL,
                    f"h = {h:g}, sweep {sweep} drew random numbers as {kinds[:4]}... ({len(kinds)} calls); expected "
                    f"{L * L} pairs of (site, uniform) as in physverify.stochastic.reference",
                )
            for c in range(n_chains):
                draws = [(int(rng.log[2 * a][1][c]), float(rng.log[2 * a + 1][1][c])) for a in range(L * L)]
                lattices[c] = R.replay(lattices[c], draws, T, h, algorithm)
                if state.spins[c].tolist() != lattices[c]:
                    diff = int(np.sum(np.array(lattices[c]) != state.spins[c]))
                    return Result(FAIL, f"h = {h:g}, sweep {sweep}, chain {c}: lattice differs from the reference replay at {diff} sites")
        return None

    return Check("scripted_rng", f"{algorithm} replay, L = {L}, h = 0 and {h:g}", run)


def reproducibility(sampler, *, L=4, T=2.5, n_sweeps=20) -> Check:
    def run():
        a = sampler.sample(L, T, 0.0, n_sweeps, seed=1, n_chains=2)
        b = sampler.sample(L, T, 0.0, n_sweeps, seed=1, n_chains=2)
        c = sampler.sample(L, T, 0.0, n_sweeps, seed=2, n_chains=2)
        if not all(np.array_equal(x, y) for x, y in zip(a, b)):
            return Result(FAIL, "the same seed gave different runs")
        if all(np.array_equal(x, y) for x, y in zip(a, c)):
            return Result(FAIL, "different seeds gave identical runs: the seed is ignored")
        return Result(PASS, "same seed reproduces the run; a different seed changes it")

    return Check("reproducibility", "seeds", run)


# --- statistical ---


def _binned(series, levels, probs, min_p):
    """Per chain fractions for the levels with probability >= min_p, plus one bin for the rest.

    Returns (names, exact probabilities, per-chain fractions). Values that are on no
    allowed level at all (a wrong normalisation, {0, 1} spins) fall in the rest bin.
    """
    keep = probs >= min_p
    fractions = [(np.abs(series - lev) < 1e-9).mean(axis=1) for lev in levels[keep]]
    rest = 1.0 - np.sum(fractions, axis=0)
    names = [f"{lev:g}" for lev in levels[keep]] + ["any other value"]
    return names, list(probs[keep]) + [float(1.0 - probs[keep].sum())], fractions + [rest]


def distribution_comparisons(e, m, L, T, min_p=0.01) -> list:
    n_samples = e.size
    comps = []
    for symbol, series, (levels, probs) in (
        ("e", e, X.energy_distribution(L, T)),
        ("|m|", np.abs(m), X.abs_magnetization_distribution(L, T)),
    ):
        for name, p, f in zip(*_binned(series, levels, probs, min_p)):
            floor = math.sqrt(max(p, 1.0 / n_samples) * (1 - min(p, 0.5)) / n_samples)  # binomial lower bound
            comps.append(compare_chain_means(f"P({symbol} = {name})" if name[0].isdigit() or name[0] == "-" else f"P({symbol} {name})", f, p, RESOLUTION, floor))
    return comps


def exact_distribution(sampler, *, L=4, T=T_DIST, n_chains=512, n_sweeps=200, seed=303, alpha=ALPHA_CHECK) -> Check:
    def run():
        e, m = sampler.sample(L, T, 0.0, n_sweeps, seed=seed, n_chains=n_chains)
        return verdict(distribution_comparisons(e, m, L, T), alpha)

    return Check("exact_distribution", f"L = {L}, T = {T:g}", run)


def moment_comparisons(e, m, exact: dict, label: str, signed=False) -> list:
    comps = [
        compare_chain_means(f"<e> {label}", e.mean(axis=1), exact["e"], RESOLUTION),
        compare_chain_means(f"<e^2> {label}", (e * e).mean(axis=1), exact["e2"], RESOLUTION * 4),  # e^2 is of size 1 to 4
    ]
    if m is not None:
        comps += [
            compare_chain_means(f"<|m|> {label}", np.abs(m).mean(axis=1), exact["abs_m"], RESOLUTION),
            compare_chain_means(f"<m^2> {label}", (m * m).mean(axis=1), exact["m2"], RESOLUTION),
        ]
        if signed:
            comps.append(compare_chain_means(f"<m> {label}", m.mean(axis=1), exact["m"], RESOLUTION))
    return comps


def moments(sampler, *, n_chains=512, n_sweeps=300, seed=404, alpha=ALPHA_CHECK) -> Check:
    with_field = getattr(sampler, "algorithm", "") != "wolff"

    def run():
        comps = []
        for k, T in enumerate((T_LOW, X.T_C, T_HIGH)):
            e, m = sampler.sample(4, T, 0.0, n_sweeps, seed=seed + k, n_chains=n_chains)
            comps += moment_comparisons(e, m, X.exact_moments(4, T), f"L=4 T={T:.3g}")
        if with_field:
            e, m = sampler.sample(4, T_HIGH, 0.5, n_sweeps, seed=seed + 10, n_chains=n_chains)
            comps += moment_comparisons(e, m, X.exact_moments(4, T_HIGH, 0.5), "L=4 T=3 h=0.5", signed=True)
        e, _ = sampler.sample(8, T_HIGH, 0.0, n_sweeps // 2, seed=seed + 20, n_chains=n_chains)
        comps += moment_comparisons(e, None, X.kaufman_moments(8, T_HIGH), "L=8 T=3 (Kaufman)")
        return verdict(comps, alpha)

    label = "L = 4 at three temperatures" + (", in a field" if with_field else "") + ", L = 8"
    return Check("moments", label, run)


def acceptance(sampler, *, L=4, T=2.5, h=0.25, n_chains=4096, rounds=4, seed=505, alpha=ALPHA_CHECK) -> Check:
    algorithm = getattr(sampler, "algorithm", "metropolis")

    def run():
        if algorithm not in ("metropolis", "heatbath"):
            return Result(INCONCLUSIVE, f"single-site acceptance does not apply to the {algorithm} algorithm")
        if _missing(sampler, "init", "step"):
            return _skip(_missing(sampler, "init", "step"))
        rng = np.random.default_rng(seed)
        stats = {}  # (field, class) -> (expected probability, list of outcomes)
        for field in (0.0, h):  # h = 0 has the dE = 0 class, a field does not: both are needed
            failure = _attempts(field, rng, stats)
            if failure is not None:
                return failure
        comps = []
        what = "accept" if algorithm == "metropolis" else "up"
        for (field, key) in sorted(stats):
            p, outs = stats[(field, key)]
            if len(outs) < 50:
                continue
            outs = np.array(outs)
            name = f"P({what} | {'dE' if algorithm == 'metropolis' else 'local field'} = {key:g}, h = {field:g})"
            if p >= 1.0:
                if outs.min() < 1.0:
                    return Result(FAIL, f"{name} should be 1 but {int((outs < 1).sum())} of {len(outs)} attempts were rejected")
                continue
            se = math.sqrt(p * (1 - p) / len(outs))  # binomial, independent attempts
            comps.append(Comparison(name, float(outs.mean()), se, p, 0.02, 1e7))
        if not comps:
            return Result(INCONCLUSIVE, "no energy class was sampled often enough")
        return verdict(comps, alpha)

    def _attempts(h, rng, stats):
        state = sampler.init(L, n_chains, "hot", rng, h)
        for _ in range(rounds * L * L):
            sites = rng.integers(0, L * L, size=n_chains)
            u = rng.random(n_chains)
            before = state.spins.reshape(n_chains, -1)[np.arange(n_chains), sites].copy()
            flat = state.spins.reshape(n_chains, -1)
            sp = state.spins  # periodic neighbour sum, computed here independently of the sampler
            nn_all = np.roll(sp, 1, 1) + np.roll(sp, -1, 1) + np.roll(sp, 1, 2) + np.roll(sp, -1, 2)
            nn = nn_all.reshape(n_chains, -1)[np.arange(n_chains), sites]
            phi = R.J * nn + h
            sampler.step(state, sites, u, T, h)
            after = flat[np.arange(n_chains), sites]
            if algorithm == "metropolis":
                dE = 2.0 * before * phi
                keys = np.round(dE, 6)
                outcome = after != before
                expected = np.minimum(1.0, np.exp(-dE / T))
            else:
                keys = np.round(phi, 6)
                outcome = after > 0
                expected = 1.0 / (1.0 + np.exp(-2.0 * phi / T))
            for key, o, p in zip(keys, outcome, expected):
                stats.setdefault((h, float(key)), [float(p), []])[1].append(float(o))
        return None

    return Check("acceptance", f"{algorithm}, L = {L}, h = 0 and {h:g}", run)


def symmetry(sampler, *, L=4, T=T_HIGH, n_chains=256, n_sweeps=150, burn_in=100, seed=606, alpha=ALPHA_CHECK) -> Check:
    def run():
        if _missing(sampler, "init", "sweep"):
            return _skip(_missing(sampler, "init", "sweep"))
        rng = np.random.default_rng(seed)
        state = sampler.init(L, n_chains, "hot", rng, 0.0)
        for _ in range(burn_in):
            sampler.sweep(state, T, 0.0, rng)
        n = L * L
        bond_sum = np.zeros((n_chains, 2, L, L))
        site_sum = np.zeros((n_chains, L, L))
        for _ in range(n_sweeps):
            sampler.sweep(state, T, 0.0, rng)
            s = state.spins
            bond_sum[:, 0] += s * np.roll(s, -1, axis=2)
            bond_sum[:, 1] += s * np.roll(s, -1, axis=1)
            site_sum += s
        ex = X.exact_moments(L, T)
        bond_exact = -ex["e"] / 2.0  # 2N bonds, H = -sum of bond correlations
        comps = []
        for d, name in ((0, "right"), (1, "down")):
            for i in range(L):
                for j in range(L):
                    comps.append(compare_chain_means(f"<s s_{name}> at ({i},{j})", bond_sum[:, d, i, j] / n_sweeps, bond_exact, 0.05))
        for i in range(L):
            for j in range(L):
                comps.append(compare_chain_means(f"<s> at ({i},{j})", site_sum[:, i, j] / n_sweeps, 0.0, 0.15))
        return verdict(comps, alpha)

    return Check("symmetry", f"bonds and sites, L = {L}, T = {T:g}", run)


def equilibration(sampler, *, L=4, T=2.0, n_chains=512, window=10, seed=707, alpha=ALPHA_CHECK) -> Check:
    def run():
        e_hot, _ = sampler.sample(L, T, 0.0, window, seed=seed, n_chains=n_chains, start="hot")
        e_cold, _ = sampler.sample(L, T, 0.0, window, seed=seed + 1, n_chains=n_chains, start="cold")
        a, b = e_hot.mean(axis=1), e_cold.mean(axis=1)
        se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        comp = Comparison(f"<e> over the first {window} sweeps, hot minus cold start", float(a.mean() - b.mean()), se, 0.0, 2.5 * RESOLUTION, len(a) + len(b) - 2)
        return verdict([comp], alpha)

    return Check("equilibration", f"hot and cold starts, L = {L}, T = {T:g}", run)


def error_bars(sampler, *, L=4, T=None, n_chains=128, n_sweeps=1000, seed=808, alpha=ALPHA_CHECK) -> Check:
    T = X.T_C if T is None else T

    def run():
        if _missing(sampler, "error_bar"):
            return _skip(["error_bar"])
        e, _ = sampler.sample(L, T, 0.0, n_sweeps, seed=seed, n_chains=n_chains)
        reported = np.array([sampler.error_bar(e[c]) for c in range(n_chains)])
        observed = float(e.mean(axis=1).std(ddof=1))
        rms = float(np.sqrt(np.mean(reported**2)))
        if not (np.isfinite(rms) and rms > 0):
            return Result(FAIL, f"reported error bars are not positive and finite (rms {rms})")
        # log of a sample standard deviation has standard error about 1 / sqrt(2 (n - 1))
        comp = Comparison("log(observed spread / reported error bar)", math.log(observed / rms), 1.0 / math.sqrt(2 * (n_chains - 1)), 0.0, 0.3, 1e7)
        result = verdict([comp], alpha)
        result.message = f"observed spread of chain means {observed:.3g}, rms reported error bar {rms:.3g}. " + result.message
        return result

    return Check("error_bars", f"L = {L}, T = {T:.4g}", run)


ALL = (bookkeeping, scripted_rng, reproducibility, exact_distribution, moments, acceptance, symmetry, equilibration, error_bars)
FAMILIES = tuple(f.__name__ for f in ALL)


SINGLE_SITE = ("metropolis", "heatbath")
NEEDS = {
    "bookkeeping": ("init", "sweep", "measure"),
    "scripted_rng": ("init", "sweep"),
    "acceptance": ("init", "step"),
    "symmetry": ("init", "sweep"),
    "error_bars": ("error_bar",),
}


def applicable(sampler, family: str) -> bool:
    """False for a check the sampler cannot support: missing methods, or not a single-site algorithm."""
    if family in ("scripted_rng", "acceptance") and getattr(sampler, "algorithm", "") not in SINGLE_SITE:
        return False
    return not _missing(sampler, *NEEDS.get(family, ()))


def ising_checks(sampler, **overrides) -> list[Check]:
    """The checks that apply to this sampler (see `applicable`).

    `overrides` maps a check name to keyword arguments for it, for example
    {"moments": {"n_chains": 128}} for a slow sampler. Called directly, a check
    that does not apply reports INCONCLUSIVE instead.
    """
    return [f(sampler, **overrides.get(f.__name__, {})) for f in ALL if applicable(sampler, f.__name__)]
