# Checking a 2D Ising Monte Carlo code

`physverify.stochastic` checks samplers of the 2D Ising model. It implements the plan in [plan_ising.md](plan_ising.md), apart from the optional scaling check.

A Monte Carlo code has no step size, and its output is random. Correct means the chain samples the Boltzmann distribution. So the order-of-convergence machinery of the rest of physverify does not apply. The checks below fall into two groups:
- **exact:** a correct code gives exactly the expected answer;
- **statistical:** each comes with a stated false-alarm rate.

## Convention

The Hamiltonian is H = -J Σ s_i s_j - h Σ s_i, with:
- spins s = ±1;
- J = 1;
- k_B = 1;
- periodic boundaries;
- the bond sum over the right and the down neighbour of every site.

The reported quantities are per spin: e = H / N and m = M / N. A code using another convention, such as spins in {0, 1}, is a different model, and the checks will say so.

## Exact references

All in [src/physverify/stochastic/exact.py](../src/physverify/stochastic/exact.py):

| Route | Use |
|---|---|
| Enumeration of all states, L ≤ 5 | Exact distributions and moments at any T and h |
| Kaufman's closed form for a finite torus at h = 0 | Moments for larger L (used at L = 8) |
| Onsager and Yang | Infinite-lattice energy, T_c and spontaneous magnetization |

The three routes were cross-checked before anything relied on them (milestone M0):
- **Enumeration and Kaufman:** log Z agrees to about 1e-15 for L = 2 to 5.
- **Kaufman and Onsager:** at L = 64 and 256, Kaufman's energy agrees with Onsager's to 1e-11 away from T_c.
- **At T_c:** Kaufman's energy approaches -√2, with an error of about 1/L.

These cross-checks are in `tests/test_ising.py`. The L = 5 one takes about 2.5 minutes and runs only with `PHYSVERIFY_SLOW=1`.

## Interface for the code under test

A sampler is an object with some of these methods. Arrays have one row per independent chain.

| Method | Kind | Purpose |
|---|---|---|
| `sample(L, T, h, n_sweeps, seed, n_chains=1, start="hot") -> (e, m)` | black box | Per-spin energy and magnetization after every sweep, after the code's own burn-in, shape (n_chains, n_sweeps) |
| `error_bar(series) -> float` | optional | The code's error bar for the mean of one chain |
| `init(L, n_chains, start, rng, h) -> state` | white box | `state.spins` (n_chains, L, L), and tracked totals `state.E` and `state.M` |
| `sweep(state, T, h, rng)` | white box | One sweep; updates `state.E` and `state.M` incrementally |
| `step(state, sites, u, T, h)` | white box | One single-site update per chain, at the given flat site indices with the given uniforms |
| `measure(state, h) -> (E, M)` | white box | Totals computed from the lattice by the code |
| `algorithm` | attribute | "metropolis", "heatbath", "checkerboard" or "wolff" |

`rng` behaves like a NumPy `Generator`, and the code may call only `rng.integers(low, high, size)` and `rng.random(size)`. A single-site sweep is expected to draw, for each attempt, one array of sites and then one array of uniforms. This is the order the reference replay uses, as in [reference.py](../src/physverify/stochastic/reference.py).

`physverify.stochastic.checks.ising_checks(sampler)` returns the checks that apply to the sampler. [examples/verify_ising.py](../examples/verify_ising.py) is a complete spec for the independently written checkerboard sampler in [examples/ising_checkerboard.py](../examples/ising_checkerboard.py). It runs with `physverify run`, the pytest plugin or the agent hook, like any other spec.

## Checks

Each check has a fixed seed, so a run is deterministic.

| Check | Kind | What it compares |
|---|---|---|
| `bookkeeping` | exact | Tracked E and M, the code's own measurement, and an independent recomputation, after every sweep |
| `scripted_rng` | exact | The code's sweeps fed recorded random numbers, against the trusted reference replaying the same numbers, lattice by lattice, at h = 0 and h = 0.25. This is the stochastic counterpart of `patch` |
| `reproducibility` | exact | The same seed gives the same run; another seed gives a different run |
| `exact_distribution` | statistical | Fraction of time at each energy level and each \|m\| level, L = 4, T = 2.5, against enumeration. Levels with probability below 0.01 are pooled into one bin |
| `moments` | statistical | <e>, <e²>, <\|m\|>, <m²> at L = 4 for T = 1.8, T_c and 3; <m> in a field; <e> and <e²> at L = 8 against Kaufman |
| `acceptance` | statistical | Single updates at controlled sites: the acceptance frequency for each energy change against min(1, e^(-dE/T)), or the heat-bath probability. Any rejection of a move that must be accepted is a FAIL |
| `symmetry` | statistical | Every bond's mean correlation and every site's mean spin, against the exact values (translation and spin-flip symmetry) |
| `equilibration` | statistical | Hot and cold starts agree over the first 10 reported sweeps |
| `error_bars` | statistical | The code's reported error bars against the actual spread of independent chains |

## Verdicts and error bars

Every statistical estimate is a mean over independent chains. Each chain is burned in by the code and then averaged. Because the chains are independent, the standard error is the spread of the chain means over √(number of chains), and no autocorrelation model is needed.

For a code's own single-chain error bars, `stats.tau_int` (Sokal's windowing) and `stats.blocked_error` give the correct reference.

A check compares m estimates with exact values. Each comparison is a two-sided Student-t test at level α/m (Bonferroni), with α = 0.001 per check. The verdict is:
- **FAIL:** some comparison is significant.
- **INCONCLUSIVE:** none is significant, but the error bars are too wide to resolve a deviation of the stated size (0.02 per spin for most averages).
- **PASS:** otherwise.

For event frequencies the standard error has a binomial floor, so a rare level that never occurs does not count as a certain deviation.

With 6 statistical checks per sampler, the false-alarm rate per sampler is at most 0.006.

The calibration in [results/ising_calibration.md](../results/ising_calibration.md) tests these error bars. It uses 1000 independent replicate runs of the bug-free sampler, analysed exactly as the checks analyse them, at nominal levels 0.05 and 0.01.

## Seeded bugs

The benchmark has the 20 bugs of the plan plus the equivalent mutant, with predictions committed before any bug was run, and one bug added later (`field_counted_twice`, found in a real code; its prediction was written before its run). The outcomes are in:
- [results/ising_matrix.md](../results/ising_matrix.md): the table;
- [results/ising_scorecard.md](../results/ising_scorecard.md): predicted against flagged, bug by bug;
- [results/ising_details.md](../results/ising_details.md): every message.

[results/ising_calibration.md](../results/ising_calibration.md) gives power curves: the detection probability against run length.

The suite does not force predictions to come true. Wrong predictions stay in the scorecard. One check was changed after a result was seen, and the scorecard says which one and why.

```bash
PYTHONPATH=src:benchmark python -m pvbench.ising_matrix results/ising_matrix.md        # about 20 to 30 minutes
python -m physverify.stochastic.calibrate results/ising_calibration.md
```

## Limits

- **Evidence, not proof.** A passing statistical suite is evidence, not proof. A bias smaller than the error bars, here about 0.02 per spin, is invisible.
- **Small lattices.** All statistical checks use L = 4 (and L = 8 for one comparison), where exact answers are cheap. A bug that shows only on large lattices or near the critical point at large L is not covered.
- **Narrow single-site checks.** `scripted_rng` and `acceptance` need single-site updates and a specific order of random-number draws. Codes that do not allow generator injection get the statistical checks only.
- **Not built:** the optional scaling check (Binder-cumulant crossing). The Wolff variant is checked only statistically.
- **Slow.** Plain NumPy and Python. The Wolff sampler loops in Python over chains and is the slowest part of the matrix.
