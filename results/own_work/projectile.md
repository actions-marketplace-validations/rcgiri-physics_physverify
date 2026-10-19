# projectile-simulation

Commit `66e3251` (includes the landing-point fix; the plan's note that the fix was uncommitted is now out of date). Adapters: `projectile_v2.py` (Phase 1), `projectile_v1.py` (new). Date 2026-10-19. physverify `0297ffe` + Stage A adapters.

## What it claims

README: v1 forward Euler, O(dt); v2 RK4, global error O(dt^4); closed-form vacuum and linear-drag solutions; C_d = 0.47.

## Results

v2 (ProjectileV2): all 27 checks pass (mms, reference, whole trajectory, patch, invariant for vacuum, linear, quadratic drag with RK4 and Euler at their design orders; vacuum range at order 2.00 after the fix).

v1 (Projectile, forward Euler; positions only, no source hook, so no MMS or patch):

| Family | Check | Result |
|---|---|---|
| reference | vacuum position at t = 2 vs closed form | PASS, order 1.00 |
| reference | linear-drag position at t = 2 vs closed form | PASS, order 1.00 |
| reference | quadratic-drag position at t = 2 vs RK4 reference | PASS, order 1.00 |
| limit | vacuum range vs v0^2 sin(2 angle) / g | FAIL: errors 0.32, 0.11, 0.0040, 0.0040 m for dt = 0.02 to 0.0025 |

## Findings

### P-v2 (label 1, confirmed bug, already fixed): v2 landing range was first order

Found on 2026-10-19 in Phase 1, fixed in this repo in commit `66e3251`, regression test in `tests/test_real_projects.py`. Counted once.

### P-v1 (label 4, limitation of a first-order baseline): v1 range has a sawtooth error

v1 keeps the last point with y >= 0 and does not interpolate the landing, so the range error is the distance from that grid point to the true landing, between 0 and about vx * dt, and its size jumps with the phase of the step grid (two step sizes gave identical errors). The bound is first order, consistent with Euler, but the error is not a smooth function of dt. Not worth fixing in a historical baseline; worth a sentence in the README if v1 figures are used (Figure 2 of the manuscript is from v1).

### P-README (label 2, ambiguous specification): drag coefficient

An earlier check found a drag-coefficient mismatch in the README, found in Phase 1. Not re-examined here: README and both code versions now show C_d = 0.47. Counted once, from Phase 1.

## Not tested

`benchmark_scipy.py` writes a plot; its numbers were reproduced in a scratch script.
