| Problem | Bug | mms | reference | invariant | limit | Predicted by design |
|---|---|---|---|---|---|---|
| projectile | (none) | ok | ok | ok | ok | baseline (all should pass) |
| projectile | gravity_sign | FLAGGED | FLAGGED | FLAGGED | FLAGGED | invariant, limit, mms, reference |
| projectile | linear_drag_missing_mass | FLAGGED | FLAGGED | no | no | mms, reference |
| projectile | quad_drag_factor_half | FLAGGED | FLAGGED | no | no | mms, reference |
| projectile | quad_drag_speed_from_vx | FLAGGED | FLAGGED | no | no | mms, reference |
| projectile | quad_drag_abs_vx | FLAGGED | no | no | no | mms |
| projectile | landing_no_interp | no | no | no | FLAGGED | limit |
| projectile | angle_not_converted | no | no | no | FLAGGED | limit |
| projectile | euler_instead_of_rk4 | FLAGGED | FLAGGED | FLAGGED | FLAGGED | invariant, mms, reference |
| projectile | rk4_weights | FLAGGED | FLAGGED | FLAGGED | FLAGGED | invariant, mms, reference |
| projectile | rk4_full_step_stage2 | FLAGGED | FLAGGED | FLAGGED | FLAGGED | mms, reference |
| pendulum | (none) | ok | ok | ok | ok | baseline (all should pass) |
| pendulum | coupling_sign | FLAGGED | FLAGGED | FLAGGED | no | invariant, mms, reference |
| pendulum | mass_matrix_missing_cos | FLAGGED | FLAGGED | FLAGGED | no | invariant, mms, reference |
| pendulum | gravity_mass_missing | FLAGGED | FLAGGED | FLAGGED | FLAGGED | invariant, limit, mms, reference |
| pendulum | swapped_lengths | FLAGGED | FLAGGED | FLAGGED | no | invariant, mms, reference |
| pendulum | small_angle_gravity | FLAGGED | FLAGGED | FLAGGED | no | invariant, mms, reference |
| pendulum | euler_instead_of_rk4 | FLAGGED | FLAGGED | FLAGGED | no | invariant, mms, reference |
| pendulum | rk4_weights | FLAGGED | FLAGGED | FLAGGED | no | invariant, mms, reference |
| pendulum | rk4_full_step_stage2 | FLAGGED | FLAGGED | FLAGGED | no | mms, reference |
| heat1d | (none) | ok | ok | n/a | n/a | baseline (all should pass) |
| heat1d | dx_off_by_one | FLAGGED | FLAGGED | n/a | n/a | mms, reference |
| heat1d | alpha_ignored | FLAGGED | FLAGGED | n/a | n/a | mms, reference |
| heat1d | extra_time_step | no | no | n/a | n/a | none (blind spot) |
| heat1d | unstable_dt | FLAGGED | FLAGGED | n/a | n/a | mms, reference |

Bugs seeded: 22. Flagged by at least one check: 21. Missed by all: 1 (heat1d/extra_time_step).
Bug-free baselines with a false alarm: 0 of 3.
Bugs flagged per family: mms 19, reference 18, invariant 12, limit 7.
Bugs flagged by that family alone: mms 1, reference 0, invariant 0, limit 2.
