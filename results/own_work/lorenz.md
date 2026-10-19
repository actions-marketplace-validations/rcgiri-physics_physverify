# lorenz-attractor-simulation

Commit `93ac915`. Adapter: `src/physverify/adapters/lorenz.py`. Date 2026-10-19. physverify `0297ffe` + Stage A adapters.

## What it claims

docs/theory.md and README: the Lorenz equations with sigma = 10, beta = 8/3; a fixed point at rho = 10; Hopf threshold rho about 24.74; Lyapunov spectrum [0.8885, 0.0031, -14.5549], sum -13.6633 "closely matches" the trace -13.6667.

## Reference used

The right-hand side written from theory.md in a different arrangement; fixed points (0, 0, 0) and (+-sqrt(beta(rho - 1)), +-sqrt(beta(rho - 1)), rho - 1); divergence -(sigma + 1 + beta). The flow is chaotic, so trajectories are compared only up to t = 1 (growth below exp(0.91) = 2.5).

## Results

| Family | Check | Result |
|---|---|---|
| mms | lorenz_derivatives + RK4 | PASS, order 3.99 |
| reference | lorenz_derivatives + RK4, t = 1 | PASS, order 4.28 |
| mms | whole trajectory | PASS, order 3.99 |
| patch | linear manufactured solution | EXACT (1.5e-12) |
| limit | three fixed points are zeros of the field | EXACT (1.4e-14) |
| invariant | divergence constant -(sigma + 1 + beta) at 4 points | EXACT |
| limit | hand-written Jacobian in calculate_lyapunov.py vs derivative of the field | EXACT (2.4e-11) |

Hopf threshold: sigma(sigma + beta + 3) / (sigma - beta - 1) = 24.7368 for these values, matching the README's 24.74 (computed by hand, not a code check).

Scripted study: `scripts/calculate_lyapunov.py` run unchanged (46 s): [0.8931, 0.0032, -14.5596], sum -13.6632. The README's 0.8885 was not reproduced to its four digits (SciPy version differs from the one used then).

Independent rerun with the project's own Jacobian, the same QR method, a 50-unit transient discarded, T = 1000, DOP853 at rtol = 1e-10: [0.9042, -0.0024, -14.5685], sum -13.66667 (matches the trace to 2e-7). Published value for lambda_1 at these parameters is about 0.9056 (general knowledge; check before citing).

## Findings

### L-1 (label 1, confirmed, minor): Lyapunov script uses SciPy's default tolerances

`scripts/calculate_lyapunov.py`, the `solve_ivp(extended_system, ...)` call sets no `rtol`/`atol`, so SciPy's defaults (rtol = 1e-3, atol = 1e-6) apply. With those, lambda_1 comes out 0.889 to 0.899 depending on SciPy version and interval, and the exponent sum misses the exact trace by 3e-3 to 0.25. With rtol = 1e-10 the sum matches to 2e-7. So the README's "sum closely matches the trace, verifying ..." is true only to about 3 digits, and the remaining gap is solver error rather than a property of the attractor. The qualitative conclusion (lambda_1 > 0, chaos) is unaffected.

Suggested fix: pass `rtol=1e-10, atol=1e-12` (or use DOP853), discard an initial transient, and quote lambda_1 to the digits that survive a tolerance change. Applied later the same day; see the Fix section below.

## Not tested

`plot_bifurcation.py`, `plot_butterfly.py`, `verify_fixed_point.py`: plotting scripts. The fixed-point claim they illustrate is covered by the exact fixed-point check.

## Fix (2026-10-19)

L-1 fixed in `5d676ff`: DOP853 at rtol 1e-10 after a 50-unit transient. The script now gives [0.8948, 0.0005, -14.5620], sum -13.6667, matching the trace; README updated.
