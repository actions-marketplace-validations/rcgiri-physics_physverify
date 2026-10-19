| Problem | Bug | mms | reference | invariant | limit | patch | Predicted by design |
|---|---|---|---|---|---|---|---|
| projectile | (none) | ok | ok | ok | ok | ok | baseline (all should pass) |
| projectile | gravity_sign | FLAGGED | FLAGGED | FLAGGED | FLAGGED | FLAGGED | invariant, limit, mms, patch, reference |
| projectile | linear_drag_missing_mass | FLAGGED | FLAGGED | no | no | FLAGGED | mms, patch, reference |
| projectile | quad_drag_factor_half | FLAGGED | FLAGGED | no | no | FLAGGED | mms, patch, reference |
| projectile | quad_drag_speed_from_vx | FLAGGED | FLAGGED | no | no | FLAGGED | mms, patch, reference |
| projectile | quad_drag_abs_vx | FLAGGED | no | no | no | FLAGGED | mms, patch |
| projectile | landing_no_interp | no | no | no | FLAGGED | no | limit |
| projectile | angle_not_converted | no | no | no | FLAGGED | no | limit |
| projectile | euler_extra_step | no | no | no | no | FLAGGED | patch |
| projectile | euler_instead_of_rk4 | FLAGGED | FLAGGED | FLAGGED | FLAGGED | no | invariant, mms, reference |
| projectile | rk4_weights | FLAGGED | FLAGGED | FLAGGED | FLAGGED | FLAGGED | invariant, mms, patch, reference |
| projectile | rk4_full_step_stage2 | FLAGGED | FLAGGED | FLAGGED | FLAGGED | FLAGGED | mms, patch, reference |
| pendulum | (none) | ok | ok | ok | ok | ok | baseline (all should pass) |
| pendulum | coupling_sign | FLAGGED | FLAGGED | FLAGGED | no | FLAGGED | invariant, mms, patch, reference |
| pendulum | mass_matrix_missing_cos | FLAGGED | FLAGGED | FLAGGED | no | FLAGGED | invariant, mms, patch, reference |
| pendulum | gravity_mass_missing | FLAGGED | FLAGGED | FLAGGED | FLAGGED | FLAGGED | invariant, limit, mms, patch, reference |
| pendulum | rk4_stage4_time | FLAGGED | no | no | no | FLAGGED | mms, patch |
| pendulum | swapped_lengths | FLAGGED | FLAGGED | FLAGGED | no | FLAGGED | invariant, mms, patch, reference |
| pendulum | small_angle_gravity | FLAGGED | FLAGGED | FLAGGED | no | FLAGGED | invariant, mms, patch, reference |
| pendulum | euler_instead_of_rk4 | FLAGGED | FLAGGED | FLAGGED | no | no | invariant, mms, reference |
| pendulum | rk4_weights | FLAGGED | FLAGGED | FLAGGED | no | FLAGGED | invariant, mms, patch, reference |
| pendulum | rk4_full_step_stage2 | FLAGGED | FLAGGED | FLAGGED | no | FLAGGED | mms, patch, reference |
| heat1d | (none) | ok | ok | n/a | n/a | ok | baseline (all should pass) |
| heat1d | dx_off_by_one | FLAGGED | FLAGGED | n/a | n/a | FLAGGED | mms, patch, reference |
| heat1d | alpha_ignored | FLAGGED | FLAGGED | n/a | n/a | FLAGGED | mms, patch, reference |
| heat1d | extra_time_step | no | no | n/a | n/a | FLAGGED | patch |
| heat1d | unstable_dt | FLAGGED | FLAGGED | n/a | n/a | FLAGGED | mms, patch, reference |
| heat1d | source_time_shift | no | no | n/a | n/a | FLAGGED | patch |

Bugs seeded: 25. Flagged by at least one check: 25. Missed by all: 0.
Bug-free baselines with a false alarm: 0 of 3.
Bugs flagged per family: mms 20, reference 18, invariant 12, limit 7, patch 21.
Bugs flagged by that family alone: mms 0, reference 0, invariant 0, limit 2, patch 3.
