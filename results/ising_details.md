### metropolis / (baseline)
- bookkeeping [L = 4, h = 0.25] EXACT (0.3 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] EXACT (0.1 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] PASS (2.5 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (5.6 s): all 18 comparisons agree; largest: P(e = -1) = 0.12301 +- 0.0012, exact 0.12107 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] PASS (43.4 s): all 19 comparisons agree; largest: <|m|> L=4 T=1.8 = 0.95774 +- 0.00057, exact 0.95633 (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (9.9 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (2.9 s): all 48 comparisons agree; largest: <s s_right> at (3,2) = 0.52063 +- 0.0057, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (2.9 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.014453 +- 0.013, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (12.3 s): observed spread of chain means 0.0333, rms reported error bar 0.036. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.076984 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### heatbath / (baseline)
- bookkeeping [L = 4, h = 0.25] EXACT (0.3 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [heatbath replay, L = 4, h = 0 and 0.25] EXACT (0.1 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] PASS (2.7 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (6.0 s): all 18 comparisons agree; largest: P(|m| = 0.375) = 0.048516 +- 0.00092, exact 0.04725 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] PASS (24.3 s): all 19 comparisons agree; largest: <e> L=4 T=3 h=0.5 = -1.7181 +- 0.0048, exact -1.73 (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [heatbath, L = 4, h = 0 and 0.25] PASS (4.7 s): all 10 comparisons agree; largest: P(up | local field = -4, h = 0) = 0.036951 +- 0.00099, exact 0.039166 (Bonferroni over 10, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (2.9 s): all 48 comparisons agree; largest: <s s_down> at (0,0) = 0.48927 +- 0.006, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (2.9 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.010986 +- 0.015, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (12.3 s): observed spread of chain means 0.0404, rms reported error bar 0.0389. all 1 comparisons agree; largest: log(observed spread / reported error bar) = 0.038218 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### checkerboard / (baseline)
- bookkeeping [L = 4, h = 0.25] EXACT (0.1 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- reproducibility [seeds] PASS (0.5 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (2.3 s): all 18 comparisons agree; largest: P(e any other value) = 0.010273 +- 0.00033, exact 0.011174 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] PASS (14.7 s): all 19 comparisons agree; largest: <e> L=8 T=3 (Kaufman) = -0.84414 +- 0.0014, exact -0.84132 (Bonferroni over 19, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (0.9 s): all 48 comparisons agree; largest: <s s_right> at (0,2) = 0.52052 +- 0.0045, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.1 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = -0.00068359 +- 0.011, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (3.5 s): observed spread of chain means 0.0209, rms reported error bar 0.025. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.17899 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### wolff / (baseline)
- bookkeeping [L = 4, h = 0.25] EXACT (0.1 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- reproducibility [seeds] PASS (0.5 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (23.2 s): all 18 comparisons agree; largest: P(e = -1.5) = 0.22171 +- 0.0015, exact 0.22417 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, L = 8] PASS (111.7 s): all 14 comparisons agree; largest: <m^2> L=4 T=1.8 = 0.92511 +- 0.0007, exact 0.92622 (Bonferroni over 14, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (5.3 s): all 48 comparisons agree; largest: <s s_down> at (0,0) = 0.53052 +- 0.0085, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (13.7 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.009082 +- 0.014, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (13.9 s): observed spread of chain means 0.0271, rms reported error bar 0.0304. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.11469 +- 0.089, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / j_sign_flipped
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=-24.5, M=2; measured by the code E=-24.5, M=2; recomputed independently E=23.5, M=2
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 0: lattice differs from the reference replay at 5 sites
- reproducibility [seeds] PASS (5.7 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (3.4 s): P(|m| = 0) = 0.53796 +- 0.0021, exact 0.017406: off by 244.0 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (27.3 s): <m^2> L=4 T=1.8 = 0.0030691 +- 3e-05, exact 0.92622: off by 30905.8 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] FAIL (4.5 s): P(accept | dE = -8, h = 0) should be 1 but 77834 of 81021 attempts were rejected
- symmetry [bonds and sites, L = 4, T = 3] FAIL (2.8 s): <s s_down> at (3,3) = -0.50391 +- 0.0052, exact 0.50853: off by 193.4 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (2.0 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.014453 +- 0.013, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (8.7 s): observed spread of chain means 0.0333, rms reported error bar 0.036. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.076984 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / delta_e_missing_factor_2
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=2.75, M=-2; measured by the code E=4.5, M=-2; recomputed independently E=4.5, M=-2
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 0: lattice differs from the reference replay at 5 sites
- reproducibility [seeds] PASS (2.5 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (6.0 s): P(e = -2) = 0.0094727 +- 0.0015, exact 0.34371: off by 225.2 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (24.4 s): <e^2> L=8 T=3 (Kaufman) = 0.15841 +- 0.00061, exact 0.77587: off by 1006.2 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] FAIL (2.8 s): P(accept | dE = 4, h = 0) = 0.44989 +- 0.0014, exact 0.2019: off by 181.5 standard errors (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (1.7 s): <s s_down> at (1,0) = 0.17958 +- 0.0047, exact 0.50853: off by 70.3 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (3.5 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.020166 +- 0.015, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (7.5 s): observed spread of chain means 0.022, rms reported error bar 0.0205. all 1 comparisons agree; largest: log(observed spread / reported error bar) = 0.068812 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / exp_de_times_t
- bookkeeping [L = 4, h = 0.25] EXACT (0.2 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 1: lattice differs from the reference replay at 4 sites
- reproducibility [seeds] PASS (2.6 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (5.5 s): P(e = -1.5) = 0 +- 0.0013, exact 0.22417: off by 172.0 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (28.8 s): <e> L=8 T=3 (Kaufman) = -1.8672 +- 0.0098, exact -0.84132: off by 105.0 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] FAIL (3.1 s): P(accept | dE = 0.5, h = 0.25) = 0.29141 +- 0.0028, exact 0.81873: off by 191.6 standard errors (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (2.6 s): <s s_down> at (1,0) = 0.98438 +- 0.011, exact 0.50853: off by 43.2 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] FAIL (3.4 s): <e> over the first 10 sweeps, hot minus cold start = 0.064014 +- 0.011, exact 0: off by 5.9 standard errors (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] FAIL (8.4 s): observed spread of chain means 0.105, rms reported error bar 0.0309. log(observed spread / reported error bar) = 1.2277 +- 0.063, exact 0: off by 19.6 standard errors (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / missing_wrap_x
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=-8.5, M=-6; measured by the code E=-8.5, M=-6; recomputed independently E=-6.5, M=-6
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 0: lattice differs from the reference replay at 1 sites
- reproducibility [seeds] PASS (5.1 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (7.7 s): P(e any other value) = 0.58743 +- 0.0019, exact 0.011174: off by 310.2 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (40.1 s): <e^2> L=4 T=1.8 = 2.265 +- 0.0059, exact 3.5413: off by 216.5 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] FAIL (3.4 s): P(accept | dE = -0, h = 0) should be 1 but 13239 of 69120 attempts were rejected
- symmetry [bonds and sites, L = 4, T = 3] FAIL (2.0 s): <s s_right> at (2,3) = 0.099062 +- 0.0066, exact 0.50853: off by 62.5 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] INCONCLUSIVE (2.0 s): no significant deviation, but the error bars cannot resolve a deviation of the stated size for 1 of 1 comparisons (first: <e> over the first 10 sweeps, hot minus cold start) (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (7.8 s): observed spread of chain means 0.0311, rms reported error bar 0.0333. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.068323 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / same_neighbour_twice
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=-10.5, M=-6; measured by the code E=-6.5, M=-6; recomputed independently E=-6.5, M=-6
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 0: lattice differs from the reference replay at 4 sites
- reproducibility [seeds] PASS (4.4 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (4.1 s): P(e = -1.5) = 0.13041 +- 0.0013, exact 0.22417: off by 70.5 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (30.6 s): <e^2> L=8 T=3 (Kaufman) = 0.45551 +- 0.0022, exact 0.77587: off by 148.9 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] FAIL (3.5 s): P(accept | dE = -0, h = 0) should be 1 but 19193 of 72065 attempts were rejected
- symmetry [bonds and sites, L = 4, T = 3] FAIL (1.9 s): <s s_right> at (1,3) = 0.34557 +- 0.0057, exact 0.50853: off by 28.5 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] INCONCLUSIVE (2.0 s): no significant deviation, but the error bars cannot resolve a deviation of the stated size for 1 of 1 comparisons (first: <e> over the first 10 sweeps, hot minus cold start) (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (11.6 s): observed spread of chain means 0.0486, rms reported error bar 0.0531. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.088468 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / energy_double_counted
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=-6.5, M=-6; measured by the code E=-14.5, M=-6; recomputed independently E=-6.5, M=-6
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] EXACT (0.6 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] PASS (7.0 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (7.1 s): P(e any other value) = 0.66717 +- 0.0031, exact 0.011174: off by 211.9 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (31.3 s): <e> L=4 T=1.8 = -3.7243 +- 0.0029, exact -1.8587: off by 640.5 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (5.9 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (1.9 s): all 48 comparisons agree; largest: <s s_right> at (3,2) = 0.52063 +- 0.0057, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] INCONCLUSIVE (2.7 s): no significant deviation, but the error bars cannot resolve a deviation of the stated size for 1 of 1 comparisons (first: <e> over the first 10 sweeps, hot minus cold start) (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (9.2 s): observed spread of chain means 0.0667, rms reported error bar 0.072. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.076984 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / m_normalised_by_L
- bookkeeping [L = 4, h = 0.25] EXACT (0.2 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] EXACT (0.3 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] PASS (3.6 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (4.2 s): P(|m| any other value) = 0.90813 +- 0.0017, exact 0: off by 539.5 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (25.5 s): <|m|> L=4 T=1.8 = 3.831 +- 0.0023, exact 0.95633: off by 1270.3 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (3.4 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (1.9 s): all 48 comparisons agree; largest: <s s_right> at (3,2) = 0.52063 +- 0.0057, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.6 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.014453 +- 0.013, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (7.5 s): observed spread of chain means 0.0333, rms reported error bar 0.036. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.076984 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / sweep_skips_last_row
- bookkeeping [L = 4, h = 0.25] EXACT (0.4 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] EXACT (0.2 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] PASS (3.4 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (4.2 s): P(e = -2) = 0.075049 +- 0.0079, exact 0.34371: off by 33.8 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (20.9 s): <e^2> L=4 T=1.8 = 1.6595 +- 0.038, exact 3.5413: off by 49.2 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (2.8 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (2.4 s): <s s_down> at (3,1) = 0.31219 +- 0.016, exact 0.50853: off by 12.2 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] FAIL (2.4 s): <e> over the first 10 sweeps, hot minus cold start = 0.70308 +- 0.018, exact 0: off by 38.1 standard errors (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] FAIL (6.3 s): observed spread of chain means 0.325, rms reported error bar 0.025. log(observed spread / reported error bar) = 2.5628 +- 0.063, exact 0: off by 40.8 standard errors (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / same_random_number
- bookkeeping [L = 4, h = 0.25] EXACT (0.2 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1 drew random numbers as ['random', 'random', 'random', 'random']... (16 calls); expected 16 pairs of (site, uniform) as in physverify.stochastic.reference
- reproducibility [seeds] PASS (2.1 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (3.6 s): P(e = -0.75) = 0 +- 0.00094, exact 0.099622: off by 106.4 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (21.5 s): <|m|> L=4 T=3 = 0.77651 +- 0.00075, exact 0.60129: off by 234.1 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (3.5 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (1.7 s): <s s_right> at (2,0) = 1 +- 0, exact 0.50853: off by inf standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.7 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.0055176 +- 0.0096, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (6.9 s): observed spread of chain means 0.0205, rms reported error bar 0.019. all 1 comparisons agree; largest: log(observed spread / reported error bar) = 0.075156 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / seed_ignored
- bookkeeping [L = 4, h = 0.25] EXACT (0.3 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] EXACT (0.1 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] FAIL (2.6 s): different seeds gave identical runs: the seed is ignored
- exact_distribution [L = 4, T = 2.5] PASS (5.1 s): all 18 comparisons agree; largest: P(|m| = 0.375) = 0.04916 +- 0.00082, exact 0.04725 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] PASS (24.0 s): all 19 comparisons agree; largest: <|m|> L=4 T=1.8 = 0.95581 +- 0.00062, exact 0.95633 (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (3.0 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (1.8 s): all 48 comparisons agree; largest: <s s_right> at (3,2) = 0.52063 +- 0.0057, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.9 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.020068 +- 0.014, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (6.8 s): observed spread of chain means 0.0354, rms reported error bar 0.036. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.016965 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / acceptance_table_off_by_one
- bookkeeping [L = 4, h = 0.25] EXACT (0.2 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 0: lattice differs from the reference replay at 3 sites
- reproducibility [seeds] PASS (2.6 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (5.0 s): P(e = -2) = 0.87141 +- 0.0016, exact 0.34371: off by 340.4 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (20.8 s): <e> L=8 T=3 (Kaufman) = -1.8245 +- 0.001, exact -0.84132: off by 980.3 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] FAIL (2.6 s): P(accept | dE = -0, h = 0) should be 1 but 40118 of 50339 attempts were rejected
- symmetry [bonds and sites, L = 4, T = 3] FAIL (1.6 s): <s s_right> at (0,2) = 0.91813 +- 0.003, exact 0.50853: off by 137.4 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.6 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = -0.00063477 +- 0.0028, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (8.9 s): observed spread of chain means 0.00724, rms reported error bar 0.00735. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.015888 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / incremental_energy_not_updated
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=1, M=-6; measured by the code E=-6.5, M=-6; recomputed independently E=-6.5, M=-6
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] EXACT (0.4 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] PASS (2.9 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (2.5 s): all 18 comparisons agree; largest: P(e = -1) = 0.12301 +- 0.0012, exact 0.12107 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] PASS (27.7 s): all 19 comparisons agree; largest: <|m|> L=4 T=1.8 = 0.95774 +- 0.00057, exact 0.95633 (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (2.5 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (1.0 s): all 48 comparisons agree; largest: <s s_right> at (3,2) = 0.52063 +- 0.0057, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.1 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.014453 +- 0.013, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (4.4 s): observed spread of chain means 0.0333, rms reported error bar 0.036. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.076984 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / no_burn_in
- bookkeeping [L = 4, h = 0.25] EXACT (0.1 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] EXACT (0.1 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] PASS (0.2 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (1.6 s): all 18 comparisons agree; largest: P(e = -0.5) = 0.081445 +- 0.0013, exact 0.077846 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (12.3 s): <|m|> L=4 T=1.8 = 0.95041 +- 0.00068, exact 0.95633: off by 8.7 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (2.7 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (1.0 s): all 48 comparisons agree; largest: <s s_right> at (3,2) = 0.52063 +- 0.0057, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] FAIL (0.1 s): <e> over the first 10 sweeps, hot minus cold start = 0.42749 +- 0.017, exact 0: off by 24.8 standard errors (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (3.9 s): observed spread of chain means 0.0335, rms reported error bar 0.0361. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.074694 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / naive_error_bars
- bookkeeping [L = 4, h = 0.25] EXACT (0.1 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] EXACT (0.1 s): 10 sweeps of 4 chains at h = 0 and h = 0.25 match the reference replay exactly
- reproducibility [seeds] PASS (1.5 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (2.7 s): all 18 comparisons agree; largest: P(e = -1) = 0.12301 +- 0.0012, exact 0.12107 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] PASS (15.3 s): all 19 comparisons agree; largest: <|m|> L=4 T=1.8 = 0.95774 +- 0.00057, exact 0.95633 (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] PASS (1.9 s): all 7 comparisons agree; largest: P(accept | dE = 8, h = 0) = 0.03974 +- 0.0007, exact 0.040762 (Bonferroni over 7, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] PASS (1.2 s): all 48 comparisons agree; largest: <s s_right> at (3,2) = 0.52063 +- 0.0057, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.1 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.014453 +- 0.013, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] FAIL (4.2 s): observed spread of chain means 0.0333, rms reported error bar 0.0158. log(observed spread / reported error bar) = 0.74784 +- 0.063, exact 0: off by 11.9 standard errors (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / field_sign_wrong
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=-8, M=-8; measured by the code E=-6, M=-8; recomputed independently E=-6, M=-8
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0.25, sweep 1, chain 0: lattice differs from the reference replay at 2 sites
- reproducibility [seeds] PASS (1.7 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (2.0 s): all 18 comparisons agree; largest: P(e = -1) = 0.12301 +- 0.0012, exact 0.12107 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (15.8 s): <m> L=4 T=3 h=0.5 = -0.7452 +- 0.0024, exact 0.74321: off by 627.3 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] FAIL (1.9 s): P(accept | dE = -0.5, h = 0.25) should be 1 but 5436 of 30765 attempts were rejected
- symmetry [bonds and sites, L = 4, T = 3] PASS (1.0 s): all 48 comparisons agree; largest: <s s_right> at (3,2) = 0.52063 +- 0.0057, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.1 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.014453 +- 0.013, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (4.2 s): observed spread of chain means 0.0333, rms reported error bar 0.036. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.076984 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / spins_zero_one
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=-3, M=11; measured by the code E=-15.75, M=11; recomputed independently E=-15.75, M=11
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 0: lattice differs from the reference replay at 7 sites
- reproducibility [seeds] PASS (1.3 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (2.3 s): P(e any other value) = 0.42531 +- 0.0019, exact 0.011174: off by 220.9 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (15.0 s): <e> L=8 T=3 (Kaufman) = -1.6838 +- 0.00082, exact -0.84132: off by 1032.4 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] INCONCLUSIVE (1.9 s): no significant deviation, but the error bars cannot resolve a deviation of the stated size for 3 of 9 comparisons (first: P(accept | dE = 2, h = 0)) (Bonferroni over 9, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (1.7 s): <s> at (2,0) = 0.915 +- 0.0018, exact 0: off by 497.8 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.6 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.0012939 +- 0.0041, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (5.7 s): observed spread of chain means 0.00751, rms reported error bar 0.00901. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.18127 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### metropolis / reject_zero_de
- bookkeeping [L = 4, h = 0.25] EXACT (0.2 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [metropolis replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 0: lattice differs from the reference replay at 3 sites
- reproducibility [seeds] PASS (1.9 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] PASS (2.5 s): all 18 comparisons agree; largest: P(e = -1.5) = 0.2212 +- 0.0019, exact 0.22417 (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] INCONCLUSIVE (15.8 s): no significant deviation, but the error bars cannot resolve a deviation of the stated size for 1 of 19 comparisons (first: <e> L=4 T=2.27) (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [metropolis, L = 4, h = 0 and 0.25] FAIL (2.0 s): P(accept | dE = -0, h = 0) should be 1 but 70031 of 70031 attempts were rejected
- symmetry [bonds and sites, L = 4, T = 3] PASS (1.1 s): all 48 comparisons agree; largest: <s s_down> at (1,1) = 0.52656 +- 0.0075, exact 0.50853 (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] PASS (1.2 s): all 1 comparisons agree; largest: <e> over the first 10 sweeps, hot minus cold start = 0.012061 +- 0.014, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (4.4 s): observed spread of chain means 0.0479, rms reported error bar 0.0525. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.091936 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### heatbath / heatbath_missing_2
- bookkeeping [L = 4, h = 0.25] EXACT (0.1 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- scripted_rng [heatbath replay, L = 4, h = 0 and 0.25] FAIL (0.0 s): h = 0, sweep 1, chain 0: lattice differs from the reference replay at 4 sites
- reproducibility [seeds] PASS (1.4 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (1.9 s): P(e = -2) = 0.0094141 +- 0.0015, exact 0.34371: off by 225.2 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (17.5 s): <e^2> L=8 T=3 (Kaufman) = 0.15707 +- 0.00069, exact 0.77587: off by 894.6 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- acceptance [heatbath, L = 4, h = 0 and 0.25] FAIL (2.4 s): P(up | local field = 4.25, h = 0.25) = 0.84608 +- 0.0011, exact 0.9677: off by 115.3 standard errors (Bonferroni over 10, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (1.4 s): <s s_down> at (1,3) = 0.17688 +- 0.0055, exact 0.50853: off by 60.8 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] INCONCLUSIVE (1.2 s): no significant deviation, but the error bars cannot resolve a deviation of the stated size for 1 of 1 comparisons (first: <e> over the first 10 sweeps, hot minus cold start) (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (4.0 s): observed spread of chain means 0.0231, rms reported error bar 0.0234. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.011953 +- 0.063, exact 0 (Bonferroni over 1, false-alarm rate 0.001)

### checkerboard / synchronous_update
- bookkeeping [L = 4, h = 0.25] FAIL (0.0 s): after sweep 1, chain 0: tracked E=-26.5, M=-6; measured by the code E=5.5, M=-6; recomputed independently E=5.5, M=-6
- reproducibility [seeds] PASS (0.2 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (0.4 s): P(e any other value) = 1 +- 0.00033, exact 0.011174: off by 3010.3 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (4.2 s): <|m|> L=4 T=3 h=0.5 = 0 +- 0, exact 0.77255: off by inf standard errors (Bonferroni over 19, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (1.1 s): <s s_down> at (1,2) = -0.78125 +- 0.039, exact 0.50853: off by 33.0 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] FAIL (0.8 s): <e> over the first 10 sweeps, hot minus cold start = -0.49482 +- 0.032, exact 0: off by 15.6 standard errors (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] FAIL (1.9 s): reported error bars are not positive and finite (rms 0.0)

### checkerboard / checkerboard_wrong_parity
- bookkeeping [L = 4, h = 0.25] EXACT (0.1 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- reproducibility [seeds] PASS (0.2 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (1.0 s): P(e = -2) = 0.0070703 +- 0.0032, exact 0.34371: off by 106.9 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, in a field, L = 8] FAIL (9.1 s): <e^2> L=4 T=1.8 = 0.5313 +- 0.025, exact 3.5413: off by 121.6 standard errors (Bonferroni over 19, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (0.4 s): <s s_right> at (1,2) = 0.21672 +- 0.048, exact 0.50853: off by 6.1 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] FAIL (0.5 s): <e> over the first 10 sweeps, hot minus cold start = 1.3285 +- 0.013, exact 0: off by 99.6 standard errors (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] FAIL (1.4 s): observed spread of chain means 0.256, rms reported error bar 0.00636. log(observed spread / reported error bar) = 3.6965 +- 0.063, exact 0: off by 58.9 standard errors (Bonferroni over 1, false-alarm rate 0.001)

### wolff / wolff_probability
- bookkeeping [L = 4, h = 0.25] EXACT (0.0 s): tracked, measured and recomputed E and M agree exactly over 40 sweeps of 8 chains
- reproducibility [seeds] PASS (0.1 s): same seed reproduces the run; a different seed changes it
- exact_distribution [L = 4, T = 2.5] FAIL (4.9 s): P(e = -2) = 0.0091667 +- 0.0017, exact 0.34371: off by 195.2 standard errors (Bonferroni over 18, false-alarm rate 0.001)
- moments [L = 4 at three temperatures, L = 8] FAIL (18.8 s): <e^2> L=4 T=2.27 = 0.47578 +- 0.0034, exact 2.7033: off by 664.0 standard errors (Bonferroni over 14, false-alarm rate 0.001)
- symmetry [bonds and sites, L = 4, T = 3] FAIL (1.1 s): <s s_down> at (0,1) = 0.18604 +- 0.013, exact 0.50853: off by 25.6 standard errors (Bonferroni over 48, false-alarm rate 0.001)
- equilibration [hot and cold starts, L = 4, T = 2] INCONCLUSIVE (2.6 s): no significant deviation, but the error bars cannot resolve a deviation of the stated size for 1 of 1 comparisons (first: <e> over the first 10 sweeps, hot minus cold start) (Bonferroni over 1, false-alarm rate 0.001)
- error_bars [L = 4, T = 2.269] PASS (2.1 s): observed spread of chain means 0.029, rms reported error bar 0.0313. all 1 comparisons agree; largest: log(observed spread / reported error bar) = -0.074855 +- 0.089, exact 0 (Bonferroni over 1, false-alarm rate 0.001)
