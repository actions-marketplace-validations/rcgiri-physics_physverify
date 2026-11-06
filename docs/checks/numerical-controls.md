# Numerical controls, paths and Itô integrals

These checks ask whether a result responds to its numerical controls as it should, and whether the inputs a solver builds for itself are right. They run the code, so use them on trusted code or in the sandbox.

| Check | Property | Typical bug it catches |
|---|---|---|
| `steps.check_step_independence` | A quantity at a fixed physical time settles as dt shrinks. | A velocity or rate used without its factor of dt. |
| `steps.check_tolerance_response` | An adaptive solver's error falls as its tolerance is tightened. | A boundary value frozen during the Runge-Kutta stages, which the error estimate cannot see. |
| `stochastic.ito.check_ito_integrals` | Generated iterated integrals satisfy exact Itô identities. | A wrong term in the formula for I_ijk. |
| `operators.check_path` | A built wire or path has the expected segment lengths and closes if it should. | A helper that continues from the wrong vertex. |

```python
from physverify.steps import check_step_independence, check_tolerance_response
from physverify.stochastic.ito import check_ito_integrals
from physverify.operators import check_path

check_step_independence(lambda dt: msd_at_T(dt), [0.1, 0.05, 0.02])     # or return (value, standard_error)
check_tolerance_response(lambda tol: max_error(tol), [1e-6, 1e-8, 1e-10, 1e-11], floor=1e-13)
check_ito_integrals(lambda p: generate(p), (10, 40))                    # generate returns (W, I2, I3)
check_path(vertices, segment_lengths=1.0, closed=True)
```

## Notes

- **`check_step_independence`** passes a code that is still converging, as long as the changes between steps shrink. It reports value ~ dt^k when they do not. With few Monte Carlo samples the margin is wide, so a small dependence on dt can pass; it is meant for errors of scale.
- **`check_tolerance_response`** needs an error from time stepping alone. Use a problem the spatial scheme solves exactly: u = x sin t solves u_t = u_xx + x cos t with u(0, t) = 0 and u(1, t) = sin t, and it is linear in x, so a central stencil has no spatial error. Tighten `atol` along with `tol`, or `atol` sets the error instead. The required slope, 0.5, is below the p/(p+1) expected of an order p method.
- **`check_ito_integrals`** cannot tell a formula error from slow truncation at a single series length, so give two lengths a factor of 4 or more apart. An identity still above `rtol` that has not fallen by 25 % is reported. The isometry test has low power on small samples: with 2000 samples, scaling one I_ijk by 0.8 was not detected by this test, while scaling it by 0.6 was. Use more samples when one index family is in doubt.

## Measured false alarms

On correct code simulated for the purpose, with new random numbers each time:

| Check | Correct code | False alarms |
|---|---|---|
| `check_ito_integrals` | left-point sums on 100 and 400 substeps, two noises, 2000 samples | 2 of 300 |
| `check_step_independence` | active Ornstein-Uhlenbeck particle, 1000 samples, dt = 0.1, 0.05, 0.02 | 0 of 300 |

These figures apply to these settings only.

## Where these came from

In the corpus session of 2026-11-06 the first four reproduced findings first made by hand: a mean squared displacement behaving as dt^-2.06, an RKF error following tol^0.18 on a moving boundary (tol^0.92 with fixed boundaries in the same solver), a multi-noise I_iii residual of about 0.08 that did not fall from series length 10 to 20, and a square coil with a segment of length 1.414. On the same repositories they passed Brownian motion, active Brownian particles, the one-noise and Milstein integrals, and a circular loop.
