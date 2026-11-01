# Operator invariants

Four properties every correct discretisation has, whatever its order of accuracy. None of them needs an exact solution, and each takes a few lines to set up.

| Check | Property | Typical bug it catches |
|---|---|---|
| `check_nullspace` | A discrete Laplacian, gradient or divergence maps a constant field to zero at every interior point. | Stencil weights stacked in the wrong order, a missing metric factor in one direction, an off-by-one neighbour index. |
| `check_uniform_state` | A uniform state with no flow and no source is unchanged by time stepping. | A scheme that returns an updated value where the caller expects a rate (or the reverse), a source that is never zero, a wrong-signed boundary term. |
| `check_advection_direction` | A feature carried by velocity u moves by u t. | A solver that integrates U_t - F_x = 0: densities and pressures from a state at rest look right, but anything with an initial velocity runs mirrored. |
| `check_force_gradient` | A conservative force equals minus the derivative of its potential. | A wrong factor in one term of a hand-written derivative. |

```python
import numpy as np
from physverify.operators import (check_nullspace, check_uniform_state,
                                  check_advection_direction, check_force_gradient)

check_nullspace(A, (nx, ny))                     # A: the code's matrix (dense or sparse), or a function field -> field
check_uniform_state(solver.step, np.full(n, 300.0))
check_advection_direction(lambda f, t: run_solver(f, t), x, u=1.0, t=0.2)
check_force_gradient(lambda r: pot(r)[0], lambda r: pot(r)[1], np.linspace(0.9, 3, 20))
```

Notes:

- `check_nullspace` ignores one cell at every edge by default (boundary rows hold boundary conditions). Pass `interior=` to change that, and `field=` for other null-space fields (a linear field for a second-derivative operator on a uniform grid).
- `check_advection_direction` needs a uniform periodic grid and u t below half the domain. On a solver without periodic boundaries, run it for a short time on a domain large enough that nothing reaches the boundary.
- `check_force_gradient` uses the radial convention: positive F pushes the particles apart.

## Where these came from

In the corpus sessions of 2026-11-01 these four found four bugs: a scrambled polar-grid diffusion matrix (interior row sums 22 and 44 instead of 0), a Lax-Wendroff option that heated still water by 0.909 K in 5 s, an Euler solver that moved fluid at -u while its shock-tube magnitudes were right, and a screened-Coulomb force at 36-59 % of -dU/dr. They passed on the correct codes they were tried on (pylj, magnelio, Glimy, tdyno and five other pair potentials). These are counts within that sample only.
