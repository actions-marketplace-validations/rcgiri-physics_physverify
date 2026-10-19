# double-pendulum-simulation

Commit `405870b`. Adapter: `src/physverify/adapters/double_pendulum.py` (from Phase 1). Date 2026-10-19. physverify `0297ffe` + Stage A adapters.

## What it claims

README: energy drift 3.29e-13 with DOP853 at rtol = 1e-12; maximum Lyapunov exponent about 0.26 for theta1 = theta2 = 90 deg, m = L = 1.

## Results

| Family | Check | Result |
|---|---|---|
| mms | mechanics.py RHS + RK4 | PASS, order 3.98 |
| reference | mechanics.py RHS + RK4 | PASS, order 3.95 |
| mms | whole trajectory | PASS, order 4.05 |
| invariant | energy | PASS, order 5.30 |
| patch | linear manufactured solution | EXACT (8.1e-15) |
| limit | small-oscillation frequencies | PASS (5.8e-13) |

Scripted study, `solvers.run_simulation` (DOP853, rtol 1e-12), now testable with SciPy, from (2.0, 2.5, 0, 0): at t = 2 it matches the reference to 8e-12 with relative energy drift 6e-13 (consistent with the README's 3.29e-13 claim). At t = 20 the two differ by 1.8 rad although energy drift stays at 2e-11: this is chaos (row 1 of the audit plan), not an error, and shows why final-state comparison is meaningless beyond a few Lyapunov times.

Scripted study, `scripts/lyapunov.py` run unchanged in a scratch copy (it writes plots): 0.2556, reproducing the README's 0.26.

Independent estimate (two trajectories, renormalised every 0.2 s, DOP853 at rtol 1e-12, same initial state and parameters): 0.902 at T = 100 s, 0.896 at T = 400 s.

## Findings

### DP-1 (label 1, confirmed): README's Lyapunov exponent is a short-window estimate, about 3.5 times too small

`scripts/lyapunov.py`: one perturbed trajectory, no renormalisation, slope of ln|delta| fitted only over 1 s < t < 8 s. Over 7 s the local stretching rate along this particular trajectory is far from its long-time average, so 0.26 is a finite-time exponent, not the maximal Lyapunov exponent, which is about 0.90 s^-1 by the renormalised method (stable between T = 100 and 400 s). The conclusion lambda > 0 (chaos) still holds.

Suggested fix: Benettin-style renormalisation over a long time, and report the value with its spread over T. Applied later the same day; see the Fix section below.

## Not tested

`poincare_section.py`, `visualize_chaos.py`, `animate_pendulum.py`: plots without a known value to compare with.

## Fix (2026-10-19)

DP-1 fixed in `314fa08`: lyapunov.py also computes the Benettin long-time exponent, 0.867 over 400 s from the project's own get_derivatives (the independent run above gave 0.896, so the second digit is uncertain); README now quotes about 0.87 and explains the 0.26.
