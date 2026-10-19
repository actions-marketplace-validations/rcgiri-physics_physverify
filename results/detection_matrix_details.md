### projectile / (baseline)
- mms [vacuum/rk4] PASS: observed order 4.00 (expected 4)
- reference [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- invariant [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- mms [vacuum/euler] PASS: observed order 1.00 (expected 1)
- reference [vacuum/euler] PASS: observed order 1.00 (expected 1)
- invariant [vacuum/euler] PASS: observed order 1.00 (expected 1)
- mms [linear/rk4] PASS: observed order 4.00 (expected 4)
- reference [linear/rk4] PASS: observed order 4.00 (expected 4)
- mms [linear/euler] PASS: observed order 1.00 (expected 1)
- reference [linear/euler] PASS: observed order 1.00 (expected 1)
- mms [quadratic/rk4] PASS: observed order 4.00 (expected 4)
- reference [quadratic/rk4] PASS: observed order 4.01 (expected 4)
- mms [quadratic/euler] PASS: observed order 1.00 (expected 1)
- reference [quadratic/euler] PASS: observed order 1.00 (expected 1)
- limit [vacuum/rk4 range] PASS: observed order 2.00 (expected 2)

### projectile / gravity_sign
- mms [vacuum/rk4] FAIL: error does not decrease with resolution (about 19.6 at the finest level)
- reference [vacuum/rk4] FAIL: error does not decrease with resolution (about 19.6 at the finest level)
- invariant [vacuum/rk4] FAIL: error does not decrease with resolution (about 2.72 at the finest level)
- mms [vacuum/euler] FAIL: error does not decrease with resolution (about 19.6 at the finest level)
- reference [vacuum/euler] FAIL: error does not decrease with resolution (about 19.6 at the finest level)
- invariant [vacuum/euler] FAIL: error does not decrease with resolution (about 2.72 at the finest level)
- mms [linear/rk4] FAIL: error does not decrease with resolution (about 19.4 at the finest level)
- reference [linear/rk4] FAIL: error does not decrease with resolution (about 19.4 at the finest level)
- mms [linear/euler] FAIL: error does not decrease with resolution (about 19.4 at the finest level)
- reference [linear/euler] FAIL: error does not decrease with resolution (about 19.4 at the finest level)
- mms [quadratic/rk4] FAIL: error does not decrease with resolution (about 16.5 at the finest level)
- reference [quadratic/rk4] FAIL: error does not decrease with resolution (about 15.6 at the finest level)
- mms [quadratic/euler] FAIL: error does not decrease with resolution (about 16.5 at the finest level)
- reference [quadratic/euler] FAIL: error does not decrease with resolution (about 15.6 at the finest level)
- limit [vacuum/rk4 range] ERROR: RuntimeError: projectile never landed within 100 s

### projectile / linear_drag_missing_mass
- mms [vacuum/rk4] PASS: observed order 4.00 (expected 4)
- reference [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- invariant [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- mms [vacuum/euler] PASS: observed order 1.00 (expected 1)
- reference [vacuum/euler] PASS: observed order 1.00 (expected 1)
- invariant [vacuum/euler] PASS: observed order 1.00 (expected 1)
- mms [linear/rk4] FAIL: error does not decrease with resolution (about 0.0389 at the finest level)
- reference [linear/rk4] FAIL: error does not decrease with resolution (about 0.12 at the finest level)
- mms [linear/euler] FAIL: error does not decrease with resolution (about 0.0412 at the finest level)
- reference [linear/euler] FAIL: error does not decrease with resolution (about 0.12 at the finest level)
- mms [quadratic/rk4] PASS: observed order 4.00 (expected 4)
- reference [quadratic/rk4] PASS: observed order 4.01 (expected 4)
- mms [quadratic/euler] PASS: observed order 1.00 (expected 1)
- reference [quadratic/euler] PASS: observed order 1.00 (expected 1)
- limit [vacuum/rk4 range] PASS: observed order 2.00 (expected 2)

### projectile / quad_drag_factor_half
- mms [vacuum/rk4] PASS: observed order 4.00 (expected 4)
- reference [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- invariant [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- mms [vacuum/euler] PASS: observed order 1.00 (expected 1)
- reference [vacuum/euler] PASS: observed order 1.00 (expected 1)
- invariant [vacuum/euler] PASS: observed order 1.00 (expected 1)
- mms [linear/rk4] PASS: observed order 4.00 (expected 4)
- reference [linear/rk4] PASS: observed order 4.00 (expected 4)
- mms [linear/euler] PASS: observed order 1.00 (expected 1)
- reference [linear/euler] PASS: observed order 1.00 (expected 1)
- mms [quadratic/rk4] FAIL: error does not decrease with resolution (about 0.339 at the finest level)
- reference [quadratic/rk4] FAIL: error does not decrease with resolution (about 1.41 at the finest level)
- mms [quadratic/euler] FAIL: error does not decrease with resolution (about 0.338 at the finest level)
- reference [quadratic/euler] FAIL: error does not decrease with resolution (about 1.41 at the finest level)
- limit [vacuum/rk4 range] PASS: observed order 2.00 (expected 2)

### projectile / quad_drag_speed_from_vx
- mms [vacuum/rk4] PASS: observed order 4.00 (expected 4)
- reference [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- invariant [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- mms [vacuum/euler] PASS: observed order 1.00 (expected 1)
- reference [vacuum/euler] PASS: observed order 1.00 (expected 1)
- invariant [vacuum/euler] PASS: observed order 1.00 (expected 1)
- mms [linear/rk4] PASS: observed order 4.00 (expected 4)
- reference [linear/rk4] PASS: observed order 4.00 (expected 4)
- mms [linear/euler] PASS: observed order 1.00 (expected 1)
- reference [linear/euler] PASS: observed order 1.00 (expected 1)
- mms [quadratic/rk4] FAIL: error does not decrease with resolution (about 0.354 at the finest level)
- reference [quadratic/rk4] FAIL: error does not decrease with resolution (about 0.343 at the finest level)
- mms [quadratic/euler] FAIL: error does not decrease with resolution (about 0.357 at the finest level)
- reference [quadratic/euler] FAIL: error does not decrease with resolution (about 0.343 at the finest level)
- limit [vacuum/rk4 range] PASS: observed order 2.00 (expected 2)

### projectile / quad_drag_abs_vx
- mms [vacuum/rk4] PASS: observed order 4.00 (expected 4)
- reference [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- invariant [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- mms [vacuum/euler] PASS: observed order 1.00 (expected 1)
- reference [vacuum/euler] PASS: observed order 1.00 (expected 1)
- invariant [vacuum/euler] PASS: observed order 1.00 (expected 1)
- mms [linear/rk4] PASS: observed order 4.00 (expected 4)
- reference [linear/rk4] PASS: observed order 4.00 (expected 4)
- mms [linear/euler] PASS: observed order 1.00 (expected 1)
- reference [linear/euler] PASS: observed order 1.00 (expected 1)
- mms [quadratic/rk4] FAIL: error does not decrease with resolution (about 0.000503 at the finest level)
- reference [quadratic/rk4] PASS: observed order 4.01 (expected 4)
- mms [quadratic/euler] PASS: observed order 1.00 (expected 1)
- reference [quadratic/euler] PASS: observed order 1.00 (expected 1)
- limit [vacuum/rk4 range] PASS: observed order 2.00 (expected 2)

### projectile / landing_no_interp
- mms [vacuum/rk4] PASS: observed order 4.00 (expected 4)
- reference [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- invariant [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- mms [vacuum/euler] PASS: observed order 1.00 (expected 1)
- reference [vacuum/euler] PASS: observed order 1.00 (expected 1)
- invariant [vacuum/euler] PASS: observed order 1.00 (expected 1)
- mms [linear/rk4] PASS: observed order 4.00 (expected 4)
- reference [linear/rk4] PASS: observed order 4.00 (expected 4)
- mms [linear/euler] PASS: observed order 1.00 (expected 1)
- reference [linear/euler] PASS: observed order 1.00 (expected 1)
- mms [quadratic/rk4] PASS: observed order 4.00 (expected 4)
- reference [quadratic/rk4] PASS: observed order 4.01 (expected 4)
- mms [quadratic/euler] PASS: observed order 1.00 (expected 1)
- reference [quadratic/euler] PASS: observed order 1.00 (expected 1)
- limit [vacuum/rk4 range] FAIL: observed order 1.00 is below the expected 2

### projectile / angle_not_converted
- mms [vacuum/rk4] PASS: observed order 4.00 (expected 4)
- reference [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- invariant [vacuum/rk4] EXACT: error below 1e-12 at every resolution; order not measurable
- mms [vacuum/euler] PASS: observed order 1.00 (expected 1)
- reference [vacuum/euler] PASS: observed order 1.00 (expected 1)
- invariant [vacuum/euler] PASS: observed order 1.00 (expected 1)
- mms [linear/rk4] PASS: observed order 4.00 (expected 4)
- reference [linear/rk4] PASS: observed order 4.00 (expected 4)
- mms [linear/euler] PASS: observed order 1.00 (expected 1)
- reference [linear/euler] PASS: observed order 1.00 (expected 1)
- mms [quadratic/rk4] PASS: observed order 4.00 (expected 4)
- reference [quadratic/rk4] PASS: observed order 4.01 (expected 4)
- mms [quadratic/euler] PASS: observed order 1.00 (expected 1)
- reference [quadratic/euler] PASS: observed order 1.00 (expected 1)
- limit [vacuum/rk4 range] FAIL: error does not decrease with resolution (about 182 at the finest level)

### projectile / euler_instead_of_rk4
- mms [vacuum/rk4] FAIL: observed order 1.00 is below the expected 4
- reference [vacuum/rk4] FAIL: observed order 1.00 is below the expected 4
- invariant [vacuum/rk4] FAIL: observed order 1.00 is below the expected 4
- mms [linear/rk4] FAIL: observed order 1.00 is below the expected 4
- reference [linear/rk4] FAIL: observed order 1.00 is below the expected 4
- mms [quadratic/rk4] FAIL: observed order 1.00 is below the expected 4
- reference [quadratic/rk4] FAIL: observed order 1.00 is below the expected 4
- limit [vacuum/rk4 range] FAIL: observed order 1.00 is below the expected 2

### projectile / rk4_weights
- mms [vacuum/rk4] FAIL: error does not decrease with resolution (about 3.03 at the finest level)
- reference [vacuum/rk4] FAIL: error does not decrease with resolution (about 3.33 at the finest level)
- invariant [vacuum/rk4] FAIL: observed order 1.00 is below the expected 4
- mms [linear/rk4] FAIL: error does not decrease with resolution (about 3.01 at the finest level)
- reference [linear/rk4] FAIL: error does not decrease with resolution (about 3.3 at the finest level)
- mms [quadratic/rk4] FAIL: error does not decrease with resolution (about 2.91 at the finest level)
- reference [quadratic/rk4] FAIL: error does not decrease with resolution (about 3.42 at the finest level)
- limit [vacuum/rk4 range] FAIL: observed order 1.01 is below the expected 2

### projectile / rk4_full_step_stage2
- mms [vacuum/rk4] FAIL: observed order 1.00 is below the expected 4
- reference [vacuum/rk4] FAIL: observed order 1.00 is below the expected 4
- invariant [vacuum/rk4] FAIL: observed order 1.00 is below the expected 4
- mms [linear/rk4] FAIL: observed order 1.00 is below the expected 4
- reference [linear/rk4] FAIL: observed order 1.00 is below the expected 4
- mms [quadratic/rk4] FAIL: observed order 1.00 is below the expected 4
- reference [quadratic/rk4] FAIL: observed order 1.01 is below the expected 4
- limit [vacuum/rk4 range] FAIL: observed order 1.01 is below the expected 2

### pendulum / (baseline)
- mms [rk4] PASS: observed order 3.98 (expected 4)
- reference [rk4] PASS: observed order 3.95 (expected 4)
- invariant [rk4] PASS: observed order 5.30 (expected 4)
- limit [small-oscillation frequencies] PASS: frequencies match the closed form (relative error 5.8e-13)

### pendulum / coupling_sign
- mms [rk4] FAIL: error does not decrease with resolution (about 0.02 at the finest level)
- reference [rk4] FAIL: error does not decrease with resolution (about 0.247 at the finest level)
- invariant [rk4] FAIL: error does not decrease with resolution (about 0.00248 at the finest level)
- limit [small-oscillation frequencies] PASS: frequencies match the closed form (relative error 5.8e-13)

### pendulum / mass_matrix_missing_cos
- mms [rk4] FAIL: error does not decrease with resolution (about 0.46 at the finest level)
- reference [rk4] FAIL: error does not decrease with resolution (about 0.0603 at the finest level)
- invariant [rk4] FAIL: error does not decrease with resolution (about 0.00065 at the finest level)
- limit [small-oscillation frequencies] PASS: frequencies match the closed form (relative error 3.3e-13)

### pendulum / gravity_mass_missing
- mms [rk4] FAIL: error does not decrease with resolution (about 1.73 at the finest level)
- reference [rk4] FAIL: error does not decrease with resolution (about 0.422 at the finest level)
- invariant [rk4] FAIL: error does not decrease with resolution (about 0.0203 at the finest level)
- limit [small-oscillation frequencies] FAIL: frequencies [np.float64(2.1219488542025706), np.float64(5.525671664678316)] differ from [2.621396023017722, 6.0009996814048545] (relative error 0.19)

### pendulum / swapped_lengths
- mms [rk4] FAIL: error does not decrease with resolution (about 0.0884 at the finest level)
- reference [rk4] FAIL: error does not decrease with resolution (about 0.0381 at the finest level)
- invariant [rk4] FAIL: error does not decrease with resolution (about 0.000296 at the finest level)
- limit [small-oscillation frequencies] PASS: frequencies match the closed form (relative error 5.8e-13)

### pendulum / small_angle_gravity
- mms [rk4] FAIL: error does not decrease with resolution (about 0.0129 at the finest level)
- reference [rk4] FAIL: error does not decrease with resolution (about 0.074 at the finest level)
- invariant [rk4] FAIL: error does not decrease with resolution (about 0.000762 at the finest level)
- limit [small-oscillation frequencies] PASS: frequencies match the closed form (relative error 5.3e-13)

### pendulum / euler_instead_of_rk4
- mms [rk4] FAIL: observed order 1.01 is below the expected 4
- reference [rk4] FAIL: observed order 1.39 is below the expected 4
- invariant [rk4] FAIL: observed order 1.17 is below the expected 4
- limit [small-oscillation frequencies] PASS: frequencies match the closed form (relative error 5.8e-13)

### pendulum / rk4_weights
- mms [rk4] FAIL: error does not decrease with resolution (about 0.49 at the finest level)
- reference [rk4] FAIL: error does not decrease with resolution (about 1.1 at the finest level)
- invariant [rk4] FAIL: observed order 0.97 is below the expected 4
- limit [small-oscillation frequencies] PASS: frequencies match the closed form (relative error 5.8e-13)

### pendulum / rk4_full_step_stage2
- mms [rk4] FAIL: observed order 0.93 is below the expected 4
- reference [rk4] FAIL: observed order 1.06 is below the expected 4
- invariant [rk4] FAIL: observed order 0.95 is below the expected 4
- limit [small-oscillation frequencies] PASS: frequencies match the closed form (relative error 5.8e-13)

### heat1d / (baseline)
- mms [FTCS] PASS: observed order 2.00 (expected 2)
- reference [FTCS eigenmode decay] PASS: observed order 1.99 (expected 2)

### heat1d / dx_off_by_one
- mms [FTCS] FAIL: observed order 0.91 is below the expected 2
- reference [FTCS eigenmode decay] FAIL: observed order 1.00 is below the expected 2

### heat1d / alpha_ignored
- mms [FTCS] FAIL: error does not decrease with resolution (about 0.235 at the finest level)
- reference [FTCS eigenmode decay] FAIL: error does not decrease with resolution (about 0.128 at the finest level)

### heat1d / extra_time_step
- mms [FTCS] PASS: observed order 2.00 (expected 2)
- reference [FTCS eigenmode decay] PASS: observed order 2.00 (expected 2)

### heat1d / unstable_dt
- mms [FTCS] FAIL: error does not decrease with resolution (about 4.31e+261 at the finest level)
- reference [FTCS eigenmode decay] FAIL: error does not decrease with resolution (about 2.16e+261 at the finest level)
