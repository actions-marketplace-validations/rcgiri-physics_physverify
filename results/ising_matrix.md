| Algorithm | Bug | bookkeeping | scripted_rng | reproducibility | exact_distribution | moments | acceptance | symmetry | equilibration | error_bars |
|---|---|---|---|---|---|---|---|---|---|---|
| metropolis | (none) | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| heatbath | (none) | ok | ok | ok | ok | ok | ok | ok | ok | ok |
| checkerboard | (none) | ok | n/a | ok | ok | ok | n/a | ok | ok | ok |
| wolff | (none) | ok | n/a | ok | ok | ok | n/a | ok | ok | ok |
| metropolis | j_sign_flipped | FAIL (p) | FAIL (p) | ok | FAIL (p) | FAIL (p) | FAIL (p) | FAIL (p) | ok | ok |
| metropolis | delta_e_missing_factor_2 | FAIL (p) | FAIL (p) | ok | FAIL (p) | FAIL (p) | FAIL (p) | FAIL (p) | ok | ok |
| metropolis | exp_de_times_t | ok | FAIL (p) | ok | FAIL (p) | FAIL (p) | FAIL (p) | FAIL (p) | FAIL | FAIL |
| metropolis | missing_wrap_x | FAIL (p) | FAIL (p) | ok | FAIL (p) | FAIL (p) | FAIL (p) | FAIL (p) | inconcl. | ok |
| metropolis | same_neighbour_twice | FAIL (p) | FAIL (p) | ok | FAIL (p) | FAIL (p) | FAIL (p) | FAIL (p) | inconcl. | ok |
| metropolis | energy_double_counted | FAIL (p) | ok | ok | FAIL (p) | FAIL (p) | ok | ok | inconcl. | ok |
| metropolis | m_normalised_by_L | ok | ok | ok | FAIL (p) | FAIL (p) | ok | ok | ok | ok |
| metropolis | sweep_skips_last_row | ok | ok | ok | FAIL (p) | FAIL (p) | ok | FAIL (p) | FAIL | FAIL |
| metropolis | same_random_number | ok | FAIL (p) | ok | FAIL (p) | FAIL (p) | ok | FAIL (p) | ok | ok |
| metropolis | seed_ignored | ok | ok | FAIL (p) | ok | ok | ok | ok | ok | ok |
| metropolis | acceptance_table_off_by_one | ok | FAIL (p) | ok | FAIL (p) | FAIL (p) | FAIL (p) | FAIL (p) | ok | ok |
| metropolis | incremental_energy_not_updated | FAIL (p) | ok | ok | ok | ok | ok | ok | ok | ok |
| metropolis | no_burn_in | ok | ok | ok | ok | FAIL | ok | ok | FAIL (p) | ok |
| metropolis | naive_error_bars | ok | ok | ok | ok | ok | ok | ok | ok | FAIL (p) |
| metropolis | field_sign_wrong | FAIL (p) | FAIL (p) | ok | ok | FAIL (p) | FAIL (p) | ok | ok | ok |
| metropolis | field_counted_twice | FAIL (p) | ok | ok | ok | FAIL (p) | ok | ok | ok | ok |
| metropolis | spins_zero_one | FAIL (p) | FAIL (p) | ok | FAIL (p) | FAIL (p) | inconcl. (p) | FAIL (p) | ok | ok |
| metropolis | reject_zero_de | ok | FAIL (p) | ok | ok | inconcl. | FAIL (p) | ok | ok | ok |
| heatbath | heatbath_missing_2 | ok | FAIL (p) | ok | FAIL (p) | FAIL (p) | FAIL (p) | FAIL (p) | inconcl. | ok |
| checkerboard | synchronous_update | FAIL (p) | n/a | ok | FAIL (p) | FAIL (p) | n/a | FAIL | FAIL | FAIL |
| checkerboard | checkerboard_wrong_parity | ok | n/a | ok | FAIL (p) | FAIL (p) | n/a | FAIL (p) | FAIL | FAIL |
| wolff | wolff_probability | ok | n/a | ok | FAIL (p) | FAIL (p) | n/a | FAIL | inconcl. | ok |

(p) marks a check predicted, before running, to flag the bug. ok = PASS or EXACT; inconcl. = INCONCLUSIVE; n/a = the check does not apply to the algorithm (scripted_rng and acceptance need single-site updates).

Seeded bugs: 21, plus 1 equivalent mutant (negative control). Flagged by at least one check: 21 of 21.
Bug-free baselines with a FAIL: 0 of 4; statistical INCONCLUSIVE on baselines: 0.
Predictions: 76 predicted detections happened, 1 predicted detections did not, 11 detections were not predicted (details in the scorecard).
Each statistical check has a false-alarm rate of at most 0.001 (Bonferroni within the check); with 6 statistical checks per sampler the rate per sampler is at most 0.006.
