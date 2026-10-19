# Plan: verifying 2D Ising (stochastic) codes

Status: plan only, nothing built. Another session is building the deterministic phases (benchmark, `patch` write-up, CLI, pytest plugin, agent hook), so this plan should be started only after those land, to avoid editing the same files. Suggested home for the code: a new `src/physverify/stochastic/` package, so the existing modules are not touched.

## 1. Why Ising needs its own plan

Everything in physverify today assumes a deterministic code whose error shrinks with a step size `dt` or `dx`. An Ising Metropolis code has neither:

- The output is random. Two correct runs give different numbers.
- There is no `dt`. "Correct" means the chain samples the Boltzmann distribution, not that an error shrinks.
- The error is statistical, so a verdict needs an error bar, and the error bar must account for autocorrelation (neighbouring samples are not independent).
- Any statistical test has a false-alarm rate. On a correct code, some tests will fail by chance unless the rate is controlled and measured.

So `check_order` (PASS / FAIL / EXACT / INCONCLUSIVE from an order estimate) cannot be reused. The verdict names can stay; the logic underneath is new.

## 2. What "correct" means: reference facts

Convention to fix before writing anything: H = -J sum over nearest-neighbour pairs of s_i s_j - h sum s_i, s = +1 or -1, periodic boundaries, k_B = 1. Every reference number below depends on this convention; a code using spins {0,1} or another J is a different model (and that mismatch is itself a realistic student bug).

| Reference | Use | Note |
|---|---|---|
| Exact enumeration, L = 2, 3, 4 (2^4, 2^9, 2^16 states), L = 5 (2^25, about 3.4e7 states) | Exact distribution of energy and magnetization at any temperature; exact averages | L = 6 is 2^36 states, too many for brute force |
| Kaufman's closed form for the partition function of a finite L x M torus | Exact averages for larger L | Implement it, then check it against enumeration at L = 4 and 5 before trusting it (it is from memory of the literature, not read in this session) |
| Onsager critical temperature T_c = 2J / ln(1 + sqrt 2), about 2.2692 J | `limit` check, scaling check | Infinite lattice only |
| Energy per spin at T_c = -sqrt 2 J | Same | Infinite lattice |
| Yang's spontaneous magnetization, m = (1 - sinh^-4(2J/T))^(1/8) for T < T_c | Low-temperature check at large L | Finite L deviates near T_c |
| Ground state energy per spin = -2J; infinite-temperature energy per spin = 0 | Trivial limits | |
| Single-flip energy change takes five values: -8J, -4J, 0, +4J, +8J | Acceptance-rule check | 2D square lattice only |
| Exponents beta = 1/8, gamma = 7/4, nu = 1; Binder cumulant at T_c about 0.61 | Optional scaling check | Check the literature value and the boundary conditions before using the cumulant number |

## 3. New check families

| Check | What it does | Needs from the code | Bugs it can see |
|---|---|---|---|
| `bookkeeping` | After K updates, the tracked energy and magnetization equal the ones recomputed from the lattice (integers, so exact) | Access to lattice and tracked values | Wrong energy change, stale incremental update, double-counted bonds |
| `scripted_rng` (proposal) | Replace the random number generator with a scripted sequence, then compare the whole lattice evolution with a hand-written reference step by step. Zero error expected | A way to inject the generator | Almost any logic bug in the update, without statistics. This is the stochastic analogue of `patch`. I found no prior work for it, but I have not looked for it specifically |
| `exact_distribution` | On L = 2 to 4, run long, compare the histogram of energies (or states) with the exact Boltzmann distribution (chi-square with an effective sample size) | Only a sampler | Wrong acceptance rule, wrong temperature scaling, broken periodic wrap, wrong neighbours |
| `moments` | Compare mean energy, mean absolute magnetization, magnetization squared, specific heat and susceptibility with exact values at temperatures below, at and above T_c | A sampler giving energy and magnetization series | Most statistical-distribution bugs |
| `acceptance` (white-box) | For each of the five energy-change classes, the acceptance frequency equals min(1, exp(-dE/T)) | Ability to run single updates | Wrong inequality, wrong beta, lookup-table index errors |
| `symmetry` | Spin-flip symmetry at h = 0, equal averages on both sublattices | Sampler | Checkerboard and indexing bugs |
| `equilibration` | Cold and hot starts agree after burn-in; two independent seeds agree | Sampler with a seed | No thermalization, stuck states |
| `error_bars` | If the code reports an error bar, replicate many times and compare it with the observed spread | Reported error bar | Naive error bars that ignore autocorrelation (common in student code) |
| `reproducibility` | Same seed gives the same run; different seeds give independent runs | Seed parameter | Reused or reset seeds |
| `scaling` (optional, expensive) | Binder-cumulant crossing and rough T_c estimate for L = 8 to 64 | Sampler | Gross errors only; too coarse for subtle bugs |

Deterministic checks (`bookkeeping`, `scripted_rng`, `reproducibility`) are plain PASS / FAIL. The rest are statistical.

## 4. Verdict design for statistical checks

- Verdicts: PASS, FAIL, INCONCLUSIVE. INCONCLUSIVE means the error bar is too large to tell the code from a wrong one. This must be common at first and must not be hidden.
- Error bars from blocking (batch means) with an estimate of the integrated autocorrelation time. Near T_c the chain is slow, so many runs there will be INCONCLUSIVE unless run longer; say so.
- One significance level per test (for example 1e-4) with a correction across the whole suite, stated in the report.
- Calibration experiment (this is a result worth reporting): run the full suite on the trusted reference sampler with at least 1000 different seeds and count FAILs. The count must match the stated false-alarm rate. If it does not, the error bars are wrong.
- Power curves instead of one yes / no: for each seeded bug, record detection probability against run length.
- Runtime tiers: fast (bookkeeping, scripted RNG, tiny exact; seconds), standard (minutes), full (scaling).

## 5. Seeded-bug set for Ising (about 20, fixed before looking at results)

As with the heat solver, write a prediction table (which check should flag which bug) before running anything, and say afterwards which predictions were wrong.

1. J sign flipped (antiferromagnet).
2. Energy change missing its factor of 2.
3. exp(-dE * T) instead of exp(-dE / T).
4. Missing periodic wrap in one direction.
5. Wrong neighbour index (right and down only, or the same neighbour twice).
6. Bonds double counted in the energy measurement only (dynamics right).
7. Magnetization normalised by L instead of L squared (measurement only).
8. Sweep skips the last row or column (sites not sampled uniformly).
9. Synchronous update (all spins updated from the old state).
10. Checkerboard update with wrong parity.
11. Same random number used for choosing the site and for acceptance.
12. Reseeding every sweep, or seed ignored.
13. Acceptance lookup table indexed off by one.
14. Incremental energy not updated after a flip.
15. No burn-in discarded.
16. Naive error bars on correlated data.
17. Field h with the wrong sign.
18. Heat-bath probability written incorrectly.
19. Wolff cluster probability 1 - exp(-beta J) instead of 1 - exp(-2 beta J).
20. Spins stored as {0, 1} instead of {-1, +1}.

Equivalent mutant (negative control): reject moves with dE = 0 instead of accepting them. This still preserves the Boltzmann distribution, so distribution checks should NOT flag it, but `acceptance` should, because the dynamics differ. It shows the difference between checking the stationary distribution and checking the dynamics. Report it honestly rather than counting it as a miss or a catch.

## 6. Interface for code under test

Minimum (black box): `sample(L, T, h, n_sweeps, seed) -> arrays of energy and magnetization per sweep`. Optional (white box): lattice access, a single-update function, a replaceable random number generator. Many student codes are scripts with global variables. A trusted reference sampler (small, slow, clearly written) ships with physverify and is the object the calibration runs on.

## 7. Milestones and done criteria

| Milestone | Done when |
|---|---|
| M0 Reference facts | Enumeration, Kaufman and the Onsager limit agree to the stated tolerance |
| M1 Reference sampler + deterministic checks | `bookkeeping`, `scripted_rng`, `exact_distribution` on L <= 4 pass on the reference and fail on bugs 2, 5, 6, 14 |
| M2 Statistical machinery | Calibration over 1000 or more seeds gives the stated false-alarm rate |
| M3 Seeded-bug matrix | All 20 bugs plus the equivalent mutant run, prediction table written first, power curves plotted |
| M4 White-box checks | `acceptance`, `symmetry`, `equilibration`, Wolff variant |
| M5 Optional scaling and docs | Adapter spec and one worked example |

## 8. Risks and honest limits

- A passing statistical suite is evidence, not proof; subtle bias smaller than the error bar is invisible.
- Critical slowing down near T_c makes the most interesting region the most expensive.
- Reference formulas can be wrong; that is why M0 cross-checks three routes.
- `scripted_rng` needs generator injection, which many codes do not allow; those codes fall back to statistical checks only.
- Pure Python is slow; keep sizes small and consider an optional accelerated path without making it a core dependency.
