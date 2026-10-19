"""Seeded-bug benchmark for Ising samplers (docs/plan_ising.md, section 5).

Each bug lives in one algorithm of physverify.stochastic.sampler.IsingSampler.
The predicted checks and the expected symptom were written down before any
bug was run. Unlike the deterministic benchmark, the test suite does not force
the predictions to come true: results/ising_matrix.md records predicted and
observed side by side, and wrong predictions are reported as such.

The equivalent mutant `reject_zero_de` is a negative control: it changes the
dynamics but keeps the Boltzmann distribution, so the distribution checks
should not flag it and the dynamics checks should.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import checks as K
from .sampler import IsingSampler

NAME = "ising"
VARIANTS = ("metropolis", "heatbath", "checkerboard", "wolff")


@dataclass(frozen=True)
class IsingBug:
    algorithm: str
    description: str
    predicted: frozenset
    symptom: str
    negative_control: bool = False


def _f(*names):
    return frozenset(names)


BUGS = {
    "j_sign_flipped": IsingBug(
        "metropolis", "coupling J = -1 (antiferromagnet) in the dynamics and the measurement",
        _f("bookkeeping", "scripted_rng", "exact_distribution", "moments", "acceptance", "symmetry"),
        "on an even lattice the energy distribution is unchanged (sublattice flip maps AF to FM), "
        "but |m| collapses and bond correlations change sign",
    ),
    "delta_e_missing_factor_2": IsingBug(
        "metropolis", "energy change of a flip computed as s * phi instead of 2 s * phi",
        _f("bookkeeping", "scripted_rng", "exact_distribution", "moments", "acceptance", "symmetry"),
        "samples at twice the temperature; the tracked energy drifts from the lattice",
    ),
    "exp_de_times_t": IsingBug(
        "metropolis", "acceptance exp(-dE * T) instead of exp(-dE / T)",
        _f("scripted_rng", "exact_distribution", "moments", "acceptance", "symmetry"),
        "samples at temperature 1 / T^2",
    ),
    "missing_wrap_x": IsingBug(
        "metropolis", "no periodic wrap in the x direction, in the dynamics and the measurement",
        _f("bookkeeping", "scripted_rng", "exact_distribution", "moments", "acceptance", "symmetry"),
        "a cylinder instead of a torus: wrap bonds uncorrelated, energies shifted",
    ),
    "same_neighbour_twice": IsingBug(
        "metropolis", "the neighbour below is used twice and the one above not at all (dynamics only)",
        _f("bookkeeping", "scripted_rng", "exact_distribution", "moments", "acceptance", "symmetry"),
        "wrong local fields: wrong distribution, tracked energy drifts",
    ),
    "energy_double_counted": IsingBug(
        "metropolis", "energy measurement counts every bond twice (dynamics right)",
        _f("bookkeeping", "exact_distribution", "moments"),
        "reported energies doubled; the lattice evolution is correct",
    ),
    "m_normalised_by_L": IsingBug(
        "metropolis", "magnetization per spin divides by L instead of L^2 (reporting only)",
        _f("exact_distribution", "moments"),
        "reported m is L times too large; nothing else changes",
    ),
    "sweep_skips_last_row": IsingBug(
        "metropolis", "random sites drawn from the first L - 1 rows only",
        _f("exact_distribution", "moments", "symmetry"),
        "the last row never changes; replay with the same site draws agrees",
    ),
    "same_random_number": IsingBug(
        "metropolis", "one uniform used both to choose the site (int(u N)) and to accept",
        _f("scripted_rng", "exact_distribution", "moments", "symmetry"),
        "site-dependent acceptance: sites with high index rarely flip uphill; detailed balance broken",
    ),
    "seed_ignored": IsingBug(
        "metropolis", "the generator is always seeded with the same constant",
        _f("reproducibility"),
        "every seed gives the same run; each run is still a correct sample",
    ),
    "acceptance_table_off_by_one": IsingBug(
        "metropolis", "acceptance looked up one energy class too high (exp(-(dE + 4) / T))",
        _f("scripted_rng", "exact_distribution", "moments", "acceptance", "symmetry"),
        "uphill moves accepted too rarely; the lattice is too ordered",
    ),
    "incremental_energy_not_updated": IsingBug(
        "metropolis", "the tracked energy is not updated after a flip",
        _f("bookkeeping"),
        "only the tracked energy is wrong; reported (measured) values are right",
    ),
    "no_burn_in": IsingBug(
        "metropolis", "no burn-in: measurement starts from the initial lattice",
        _f("equilibration"),
        "hot and cold starts disagree over the first sweeps; long averages are barely biased",
    ),
    "naive_error_bars": IsingBug(
        "metropolis", "error bar of the mean computed as std / sqrt(n), ignoring autocorrelation",
        _f("error_bars"),
        "reported error bars too small by about sqrt(2 tau)",
    ),
    "field_sign_wrong": IsingBug(
        "metropolis", "the field enters the dynamics with the wrong sign (measurement right)",
        _f("bookkeeping", "scripted_rng", "moments", "acceptance"),
        "invisible at h = 0; in a field m has the wrong sign",
    ),
    "field_counted_twice": IsingBug(
        "metropolis", "measured energy uses -h * (sum of the 4 neighbours) / 2 per site, i.e. -2 h M (dynamics right)",
        _f("bookkeeping", "moments"),
        "invisible at h = 0; in a field <e> and <e^2> are wrong while m is right (found in a real thesis code)",
    ),
    "spins_zero_one": IsingBug(
        "metropolis", "spins stored as {0, 1} and used in the +-1 formulas",
        _f("bookkeeping", "scripted_rng", "exact_distribution", "moments", "acceptance", "symmetry"),
        "a different model: energies and magnetizations off the allowed levels",
    ),
    "reject_zero_de": IsingBug(
        "metropolis", "moves with dE = 0 are rejected instead of accepted (equivalent mutant)",
        _f("scripted_rng", "acceptance"),
        "same stationary distribution, different dynamics: only the dynamics checks should see it",
        negative_control=True,
    ),
    "heatbath_missing_2": IsingBug(
        "heatbath", "heat-bath probability 1 / (1 + exp(-phi / T)) instead of exp(-2 phi / T)",
        _f("scripted_rng", "exact_distribution", "moments", "acceptance", "symmetry"),
        "samples at twice the temperature",
    ),
    "synchronous_update": IsingBug(
        "checkerboard", "all sites updated at once from the old lattice instead of two sublattices",
        _f("bookkeeping", "exact_distribution", "moments"),
        "neighbours flip together; wrong distribution, tracked energy wrong",
    ),
    "checkerboard_wrong_parity": IsingBug(
        "checkerboard", "both half-sweeps update the even sublattice",
        _f("exact_distribution", "moments", "symmetry"),
        "the odd sublattice never changes",
    ),
    "wolff_probability": IsingBug(
        "wolff", "cluster bond probability 1 - exp(-J / T) instead of 1 - exp(-2 J / T)",
        _f("exact_distribution", "moments"),
        "clusters too small; samples a different distribution",
    ),
}


def variant_checks(sampler) -> list:
    """The checks that apply to one sampler, with run lengths suited to its speed."""
    if sampler.algorithm == "wolff":  # one cluster update per 'sweep', looped in Python per chain
        return K.ising_checks(
            sampler,
            exact_distribution={"n_chains": 128, "n_sweeps": 600},
            moments={"n_chains": 128, "n_sweeps": 800},
            symmetry={"n_chains": 128},
            equilibration={"n_chains": 256},
            error_bars={"n_chains": 64, "n_sweeps": 600},
        )
    return K.ising_checks(sampler)


def checks(bugs=frozenset(), algorithm=None):
    """Checks for the sampler with the given bugs (all in one algorithm), or a bug-free variant."""
    bugs = frozenset(bugs)
    algorithms = {BUGS[b].algorithm for b in bugs}
    if len(algorithms) > 1:
        raise ValueError("bugs from different algorithms")
    algorithm = algorithms.pop() if algorithms else (algorithm or "metropolis")
    return variant_checks(IsingSampler(algorithm, bugs))
