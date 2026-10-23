"""Ising (stochastic) checks: exact references, statistics, the samplers, and the fast deterministic checks.

The full seeded-bug matrix takes several minutes; set PHYSVERIFY_SLOW=1 to run
the test that regenerates it and compares with results/ising_matrix.md.
"""

import math
import os
from pathlib import Path

import numpy as np
import pytest

from physverify.checks import EXACT, FAIL, INCONCLUSIVE, PASS
from physverify.stochastic import checks as K
from physverify.stochastic import exact as X
from physverify.stochastic import reference as R
from physverify.stochastic.sampler import IsingSampler
from physverify.stochastic.stats import Comparison, compare_chain_means, t_critical, tau_int, verdict

slow = pytest.mark.skipif(not os.environ.get("PHYSVERIFY_SLOW"), reason="set PHYSVERIFY_SLOW=1 for the slow Ising tests")


# --- M0: three routes to the exact answer agree ---


@pytest.mark.parametrize("L", [2, 3, 4])
@pytest.mark.parametrize("T", [1.5, X.T_C, 3.0, 10.0])
def test_kaufman_matches_enumeration(L, T):
    g = X.density_of_states(L)
    energies, _ = X._levels(L)
    log_z = math.log(float((g.sum(axis=1) * np.exp(-energies / T)).sum()))
    assert X.kaufman_log_z(L, T) == pytest.approx(log_z, abs=1e-11)


def test_enumeration_counts_and_ground_state():
    g = X.density_of_states(4)
    assert g.sum() == 2**16
    assert g[0, 0] == 1 and g[0, -1] == 1  # the two ground states, E = -2N, M = -N and +N
    m = X.exact_moments(4, 0.01)
    assert m["e"] == pytest.approx(-2.0) and m["abs_m"] == pytest.approx(1.0)
    hot = X.exact_moments(4, 1e6)
    assert abs(hot["e"]) < 1e-4 and hot["m2"] == pytest.approx(1 / 16, rel=1e-3)


@pytest.mark.parametrize("T", [1.8, 3.0])
def test_kaufman_large_lattice_matches_onsager_away_from_tc(T):
    assert X.kaufman_moments(64, T)["e"] == pytest.approx(X.onsager_energy(T), abs=1e-8)


def test_kaufman_at_tc_approaches_minus_root_2():
    errs = [abs(X.kaufman_moments(L, X.T_C)["e"] + math.sqrt(2)) for L in (32, 64, 128)]
    assert errs[0] > errs[1] > errs[2] and errs[2] < 0.01
    assert errs[1] / errs[2] == pytest.approx(2.0, rel=0.1)  # finite-size error about 1/L


def test_onsager_and_yang_known_values():
    assert X.T_C == pytest.approx(2.269185, abs=1e-6)
    assert X.onsager_energy(X.T_C) == pytest.approx(-math.sqrt(2))
    assert X.onsager_energy(X.T_C - 1e-7) == pytest.approx(-math.sqrt(2), abs=1e-4)
    assert X.yang_magnetization(1.0) == pytest.approx(0.99927, abs=1e-5)
    assert X.yang_magnetization(3.0) == 0.0


@slow
def test_l5_enumeration_matches_kaufman():
    g = X.density_of_states(5)
    energies, _ = X._levels(5)
    for T in (2.0, 2.5):
        log_z = math.log(float((g.sum(axis=1) * np.exp(-energies / T)).sum()))
        assert X.kaufman_log_z(5, T) == pytest.approx(log_z, abs=1e-10)


# --- statistics ---


def test_t_critical_known_values():
    assert t_critical(0.05, 10.0) == pytest.approx(2.2281, abs=1e-3)
    assert t_critical(0.05, 1e7) == pytest.approx(1.95996, abs=1e-4)


def test_tau_int_of_an_ar1_process():
    rng = np.random.default_rng(0)
    x = np.zeros(100000)
    noise = rng.normal(size=x.size)
    for i in range(1, x.size):
        x[i] = 0.8 * x[i - 1] + noise[i]
    assert tau_int(x) == pytest.approx((1 + 0.8) / (2 * (1 - 0.8)), rel=0.1)  # 4.5


def test_verdicts():
    good = Comparison("a", 1.001, 0.001, 1.0, 0.02, 100)
    bad = Comparison("b", 1.1, 0.001, 1.0, 0.02, 100)
    vague = Comparison("c", 1.0, 0.5, 1.0, 0.02, 100)
    assert verdict([good]).status == PASS
    assert verdict([good, bad]).status == FAIL
    assert verdict([good, vague]).status == INCONCLUSIVE


def test_rare_event_with_no_occurrences_is_not_a_certain_failure():
    c = compare_chain_means("rare", np.zeros(64), 1e-4, 0.02, min_se=math.sqrt(1e-4 / 6400))
    assert verdict([c]).status == PASS


# --- M1: the vectorised sampler equals the reference, deterministic checks see the predicted bugs ---


@pytest.mark.parametrize("algorithm", ["metropolis", "heatbath"])
def test_sampler_reproduces_the_reference_replay_exactly(algorithm):
    assert K.scripted_rng(IsingSampler(algorithm)).run().status == EXACT


@pytest.mark.parametrize("algorithm", ["metropolis", "heatbath", "checkerboard", "wolff"])
def test_bookkeeping_is_exact_on_every_bug_free_algorithm(algorithm):
    assert K.bookkeeping(IsingSampler(algorithm)).run().status == EXACT


@pytest.mark.parametrize(
    "bug",
    ["delta_e_missing_factor_2", "same_neighbour_twice", "energy_double_counted", "incremental_energy_not_updated"],
)
def test_deterministic_checks_flag_plan_milestone_m1_bugs(bug):
    """docs/plan_ising.md, M1: bookkeeping fails on bugs 2, 5, 6 and 14."""
    assert K.bookkeeping(IsingSampler("metropolis", {bug})).run().status == FAIL


def test_scripted_rng_flags_reused_random_numbers_and_the_equivalent_mutant():
    assert K.scripted_rng(IsingSampler("metropolis", {"same_random_number"})).run().status == FAIL
    assert K.scripted_rng(IsingSampler("metropolis", {"reject_zero_de"})).run().status == FAIL


def test_reproducibility_flags_an_ignored_seed():
    assert K.reproducibility(IsingSampler("metropolis")).run().status == PASS
    assert K.reproducibility(IsingSampler("metropolis", {"seed_ignored"})).run().status == FAIL


def test_acceptance_passes_on_metropolis_and_flags_the_equivalent_mutant():
    assert K.acceptance(IsingSampler("metropolis")).run().ok
    result = K.acceptance(IsingSampler("metropolis", {"reject_zero_de"})).run()
    assert result.status == FAIL and "should be 1" in result.message


def test_reference_energy_convention():
    spins = [[1, 1], [1, 1]]
    assert R.energy(spins) == -8.0  # L = 2: 2N = 8 bonds, each pair counted twice, as in the exact module
    assert R.magnetization(spins) == 4.0


def test_checks_without_white_box_methods_are_inconclusive_not_errors():
    class BlackBox:
        def __init__(self):
            self._s = IsingSampler("metropolis")

        def sample(self, *args, **kwargs):
            return self._s.sample(*args, **kwargs)

    sampler = BlackBox()
    for make in (K.bookkeeping, K.scripted_rng, K.acceptance, K.symmetry, K.error_bars):
        result = make(sampler).run()
        assert result.status == INCONCLUSIVE and "not" in result.message


# --- the full matrix (slow) ---


@slow
def test_committed_ising_matrix_matches_a_fresh_run():
    from pvbench.ising_matrix import run_all, to_markdown

    committed = (Path(__file__).resolve().parents[1] / "results" / "ising_matrix.md").read_text(encoding="utf-8")
    assert to_markdown(run_all()) == committed
