# Ising seeded bugs: predictions against outcomes

Predictions and symptoms were committed (src/physverify/stochastic/ising.py, commit 0297ffe) before any
bug was run, and have not been changed since.

One check was changed after a result was seen. `scripted_rng` and `acceptance` first ran only in a field
(h = 0.25), where no single flip has dE = 0, so the equivalent mutant `reject_zero_de` was invisible to
both: a unit test showed this before the first full matrix run. Both checks now also run at h = 0. Their
detection of `reject_zero_de` below is therefore not a blind result.

## j_sign_flipped (metropolis)

- Change: coupling J = -1 (antiferromagnet) in the dynamics and the measurement
- Expected symptom: on an even lattice the energy distribution is unchanged (sublattice flip maps AF to FM), but |m| collapses and bond correlations change sign
- Predicted: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Flagged: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: -

## delta_e_missing_factor_2 (metropolis)

- Change: energy change of a flip computed as s * phi instead of 2 s * phi
- Expected symptom: samples at twice the temperature; the tracked energy drifts from the lattice
- Predicted: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Flagged: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: -

## exp_de_times_t (metropolis)

- Change: acceptance exp(-dE * T) instead of exp(-dE / T)
- Expected symptom: samples at temperature 1 / T^2
- Predicted: acceptance, exact_distribution, moments, scripted_rng, symmetry
- Flagged: acceptance, equilibration, error_bars, exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: equilibration, error_bars

## missing_wrap_x (metropolis)

- Change: no periodic wrap in the x direction, in the dynamics and the measurement
- Expected symptom: a cylinder instead of a torus: wrap bonds uncorrelated, energies shifted
- Predicted: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Flagged: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: -

## same_neighbour_twice (metropolis)

- Change: the neighbour below is used twice and the one above not at all (dynamics only)
- Expected symptom: wrong local fields: wrong distribution, tracked energy drifts
- Predicted: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Flagged: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: -

## energy_double_counted (metropolis)

- Change: energy measurement counts every bond twice (dynamics right)
- Expected symptom: reported energies doubled; the lattice evolution is correct
- Predicted: bookkeeping, exact_distribution, moments
- Flagged: bookkeeping, exact_distribution, moments
- Predicted but not flagged: -
- Flagged but not predicted: -

## m_normalised_by_L (metropolis)

- Change: magnetization per spin divides by L instead of L^2 (reporting only)
- Expected symptom: reported m is L times too large; nothing else changes
- Predicted: exact_distribution, moments
- Flagged: exact_distribution, moments
- Predicted but not flagged: -
- Flagged but not predicted: -

## sweep_skips_last_row (metropolis)

- Change: random sites drawn from the first L - 1 rows only
- Expected symptom: the last row never changes; replay with the same site draws agrees
- Predicted: exact_distribution, moments, symmetry
- Flagged: equilibration, error_bars, exact_distribution, moments, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: equilibration, error_bars

## same_random_number (metropolis)

- Change: one uniform used both to choose the site (int(u N)) and to accept
- Expected symptom: site-dependent acceptance: sites with high index rarely flip uphill; detailed balance broken
- Predicted: exact_distribution, moments, scripted_rng, symmetry
- Flagged: exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: -

## seed_ignored (metropolis)

- Change: the generator is always seeded with the same constant
- Expected symptom: every seed gives the same run; each run is still a correct sample
- Predicted: reproducibility
- Flagged: reproducibility
- Predicted but not flagged: -
- Flagged but not predicted: -

## acceptance_table_off_by_one (metropolis)

- Change: acceptance looked up one energy class too high (exp(-(dE + 4) / T))
- Expected symptom: uphill moves accepted too rarely; the lattice is too ordered
- Predicted: acceptance, exact_distribution, moments, scripted_rng, symmetry
- Flagged: acceptance, exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: -

## incremental_energy_not_updated (metropolis)

- Change: the tracked energy is not updated after a flip
- Expected symptom: only the tracked energy is wrong; reported (measured) values are right
- Predicted: bookkeeping
- Flagged: bookkeeping
- Predicted but not flagged: -
- Flagged but not predicted: -

## no_burn_in (metropolis)

- Change: no burn-in: measurement starts from the initial lattice
- Expected symptom: hot and cold starts disagree over the first sweeps; long averages are barely biased
- Predicted: equilibration
- Flagged: equilibration, moments
- Predicted but not flagged: -
- Flagged but not predicted: moments

## naive_error_bars (metropolis)

- Change: error bar of the mean computed as std / sqrt(n), ignoring autocorrelation
- Expected symptom: reported error bars too small by about sqrt(2 tau)
- Predicted: error_bars
- Flagged: error_bars
- Predicted but not flagged: -
- Flagged but not predicted: -

## field_sign_wrong (metropolis)

- Change: the field enters the dynamics with the wrong sign (measurement right)
- Expected symptom: invisible at h = 0; in a field m has the wrong sign
- Predicted: acceptance, bookkeeping, moments, scripted_rng
- Flagged: acceptance, bookkeeping, moments, scripted_rng
- Predicted but not flagged: -
- Flagged but not predicted: -

## field_counted_twice (metropolis)

- Change: measured energy uses -h * (sum of the 4 neighbours) / 2 per site, i.e. -2 h M (dynamics right)
- Expected symptom: invisible at h = 0; in a field <e> and <e^2> are wrong while m is right (found in a real thesis code)
- Predicted: bookkeeping, moments
- Flagged: bookkeeping, moments
- Predicted but not flagged: -
- Flagged but not predicted: -

## spins_zero_one (metropolis)

- Change: spins stored as {0, 1} and used in the +-1 formulas
- Expected symptom: a different model: energies and magnetizations off the allowed levels
- Predicted: acceptance, bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Flagged: bookkeeping, exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: acceptance
- Flagged but not predicted: -

## reject_zero_de (metropolis) — negative control

- Change: moves with dE = 0 are rejected instead of accepted (equivalent mutant)
- Expected symptom: same stationary distribution, different dynamics: only the dynamics checks should see it
- Predicted: acceptance, scripted_rng
- Flagged: acceptance, scripted_rng
- Predicted but not flagged: -
- Flagged but not predicted: -

## heatbath_missing_2 (heatbath)

- Change: heat-bath probability 1 / (1 + exp(-phi / T)) instead of exp(-2 phi / T)
- Expected symptom: samples at twice the temperature
- Predicted: acceptance, exact_distribution, moments, scripted_rng, symmetry
- Flagged: acceptance, exact_distribution, moments, scripted_rng, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: -

## synchronous_update (checkerboard)

- Change: all sites updated at once from the old lattice instead of two sublattices
- Expected symptom: neighbours flip together; wrong distribution, tracked energy wrong
- Predicted: bookkeeping, exact_distribution, moments
- Flagged: bookkeeping, equilibration, error_bars, exact_distribution, moments, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: equilibration, error_bars, symmetry

## checkerboard_wrong_parity (checkerboard)

- Change: both half-sweeps update the even sublattice
- Expected symptom: the odd sublattice never changes
- Predicted: exact_distribution, moments, symmetry
- Flagged: equilibration, error_bars, exact_distribution, moments, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: equilibration, error_bars

## wolff_probability (wolff)

- Change: cluster bond probability 1 - exp(-J / T) instead of 1 - exp(-2 J / T)
- Expected symptom: clusters too small; samples a different distribution
- Predicted: exact_distribution, moments
- Flagged: exact_distribution, moments, symmetry
- Predicted but not flagged: -
- Flagged but not predicted: symmetry
