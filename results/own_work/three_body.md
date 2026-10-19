# three-body-simulation

Commit `2262a15`. Adapter: `src/physverify/adapters/three_body.py`. Date 2026-10-19. physverify `0297ffe` + Stage A adapters.

## What it claims

docs/theory.md: planar three-body problem, G = 1, a_i = sum_j G m_j (r_j - r_i) / |r_j - r_i|^3, with an optional softening (r^2 + eps^2)^1.5. README: a symplectic velocity-Verlet engine that conserves energy over long runs, compared with SciPy RK45.

## Reference used

Pairwise accelerations written from theory.md with eps = 1e-4 (the value in physics.py), stepped with physverify's RK4 at 16 times the finest step. Softened energy, total momentum and angular momentum written independently. Test orbit: the figure-eight initial condition (smooth and bounded; its period was not used).

## Results

| Family | Check | Result |
|---|---|---|
| mms | get_derivatives + RK4 | PASS, order 4.00 |
| reference | get_derivatives + RK4 | PASS, order 4.00 |
| mms | whole trajectory | PASS, order 4.00 |
| invariant | softened energy, RK4 | PASS, order 4.98 |
| patch | linear manufactured solution | EXACT (5.6e-14) |
| invariant | calculate_energy is the conserved quantity | FAIL: differs by 1.1e-8 (relative 8e-9) |
| reference | verlet_step | PASS, order 2.00 |
| invariant | verlet_step energy | PASS, order 2.00 |
| invariant | verlet_step total momentum | EXACT (6.6e-15) |
| invariant | verlet_step angular momentum | EXACT (2.7e-15) |
| patch | verlet_step time reversal | EXACT (1.6e-15) |
| limit | two-body circular orbit closes after one period | PASS, order 2.00 |
| reference | run_verlet_simulation final state at t_end | FAIL: order 1.00, last time 0.995 for t_end = 1 |
| reference | run_simulation (solve_ivp) at default tolerances | PASS, 6.5e-10 at t = 2 |

Not applicable: MMS on verlet_step (no source-term hook; row 25), so reversibility and exact invariants were used instead.

## Findings

### TB-1 (label 1, confirmed bug): run_verlet_simulation stops one step before t_end

`src/integrators.py`, `times = np.arange(t_start, t_end, dt)` and the loop over `n_steps - 1`. `np.arange` excludes `t_end`, so the last state returned is at `t_end - dt`.

Minimal example: `run_verlet_simulation(y0, masses, (0, 1), 0.1)` returns 10 times, the last 0.9. With `(0, 0.3)` and `dt = 0.1` it returns 3 times, the last 0.2. Because `np.arange` with a float step can include or exclude the end point depending on rounding, the number of steps is also not reliable in general.

Effect: the "final state" error is first order in dt (0.0065 at dt = 0.005), not Verlet's second order, the same pattern as the projectile range bug. Plots over a long span are not visibly affected; anything that compares the final state with another solver at `t_end` is (compare_integrators.py, simulate_solar_system.py use this driver).

Suggested fix: `n_steps = int(round((t_end - t_start) / dt)) + 1` and `times = t_start + dt * np.arange(n_steps)`. Applied later the same day; see the Fix section below.

### TB-2 (label 2, ambiguous specification): calculate_energy does not soften the potential

The forces use (r^2 + eps^2)^-1.5 with eps = 1e-4; `calculate_energy` uses -G m_i m_j / r. The quantity the dynamics conserves is the softened energy -G m_i m_j / sqrt(r^2 + eps^2). The difference is about eps^2 / (2 r^3), 8e-9 relative here, far below Verlet's energy error at the step sizes used in the scripts, so no plot is affected. It matters only in close encounters (r comparable to eps) or when energy error near 1e-8 is claimed, and the README does claim a relative energy error of about 1e-9, so the mismatch is the same size as the quoted figure. Either soften the energy or state that it is the unsoftened energy.

## Status

At audit time neither fix was applied and the repo was untouched (`git status` clean after the run).

## Fixes (2026-10-19)

TB-1 fixed in `73faf33`, TB-2 in `b83d173` (three-body-simulation). After the fixes all 14 checks pass; the two former failures are now regression tests in `tests/test_real_projects.py`.
