# Seeded bugs in methods (pvbench.method_bugs)

Each bug is a pattern found in a public repository (IDs as in [corpus/SUMMARY.md](corpus/SUMMARY.md)), with a bug-free control. Regenerate with `PYTHONPATH=src:benchmark python -c "from pvbench.method_bugs import run_all, to_markdown; print(to_markdown(run_all()))"`.

| Case | Seeded bug | From | Check | Result | Missed by |
|---|---|---|---|---|---|
| tableau_ok | no (control) | - | `butcher.check_tableau` | PASS |  |
| tableau_label_too_high | yes | F09 | `butcher.check_tableau` | FAIL |  |
| embedded_ok | no (control) | - | `butcher.check_tableau` | PASS |  |
| error_weights_as_embedded | yes | E09 | `butcher.check_tableau` | FAIL |  |
| backward_ok | no (control) | - | `studies.backward_mms_study` | PASS |  |
| backward_stage_times_forward | yes | D08 | `studies.backward_mms_study` | FAIL | any forward-in-time check, and backward runs of autonomous equations |
| time_loop_ok | no (control) | - | `studies.time_grid_check` | PASS |  |
| while_loop_overshoot | yes | D08 | `studies.time_grid_check` | FAIL | order studies that read the state nearest t_end |
| spectral_ok | no (control) | - | `studies.size_sweep_check` | PASS |  |
| spectral_even_only | yes | G10 | `studies.size_sweep_check` | FAIL | any study on power-of-two grids |
| dirichlet_ok | no (control) | - | `order.check_order` | PASS |  |
| dirichlet_after_solve | yes | H01 | `order.check_order` | FAIL | a single run compared with a loose tolerance (the error is small but does not shrink) |
| neumann_ok | no (control) | - | `studies.balance_check` | PASS |  |
| neumann_by_copy | yes | H54 | `studies.balance_check` | FAIL | a one-step test with the heat away from the walls |
| source_ok | no (control) | - | `studies.balance_check` | PASS |  |
| source_without_dt | yes | H01 | `studies.balance_check` | FAIL | any test with zero source |
| spacing_ok | no (control) | - | `order.check_order` | PASS |  |
| spacing_off_by_one | yes | H19 | `order.check_order` | FAIL | a single comparison at n = 100 with a 5% tolerance |
