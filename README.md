# physverify

Checks that a physics simulation solves the right equations at the right accuracy, not only that it runs.

Status: version 0.0.1, an early prototype. It handles ODE systems and one PDE example. It has not been used by anyone else yet.

## What it does

You describe the physics once, independently of the code under test (a reference right-hand side). physverify then runs four kinds of check:

| Family | What it does | What it can see |
|---|---|---|
| `mms` | Method of Manufactured Solutions. Picks a smooth function, derives the forcing that makes it an exact solution of the reference equations, runs your code with that forcing, and checks the error shrinks at the design order. | A wrong right-hand side anywhere in the state space you sample, and a stepper that is not the order it claims. |
| `reference` | Compares your code with a solution of the reference equations computed independently. | The same bugs, but only along the one trajectory you run. |
| `invariant` | Drift of a conserved quantity (energy, say) as the step shrinks. | Inconsistency between the equations of motion and the conserved quantity. |
| `limit` | A known limiting case: closed-form range, normal-mode frequencies. | Bugs in post-processing or in limits the other checks do not reach. |

Pass/fail rests on the observed order of convergence (`physverify.order.check_order`), which reports PASS, FAIL, EXACT (error at round-off, order not measurable) or INCONCLUSIVE.

## Try it

Only NumPy is needed (pytest to run the tests). No install step:

```bash
PYTHONPATH=src python examples/check_my_solver.py   # check a small solver, then try the 10% bug described inside
PYTHONPATH=src python -m physverify.matrix results/detection_matrix.md   # the seeded-bug table below
python -m pytest -q                                  # 70 tests, about 30 s
```

To check your own ODE code you provide two things: an independent reference right-hand side, and an `integrate(source, y0, t_end, n_steps)` function that advances your code with an additive source term `source(t)`. `examples/check_my_solver.py` is the shortest working example. Codes with no source hook can still be wrapped; see `src/physverify/adapters/projectile_v2.py` for one that has no time argument either.

## Seeded-bug benchmark

22 bugs are injected one at a time into three small solvers (projectile with drag, double pendulum, 1D heat equation), and every check is run on each. Full table: [results/detection_matrix.md](results/detection_matrix.md), per-check messages: [results/detection_matrix_details.md](results/detection_matrix_details.md).

| | Count |
|---|---|
| Bugs seeded | 22 |
| Flagged by at least one check | 21 |
| Missed by every check | 1 (`heat1d/extra_time_step`) |
| False alarms on the 3 bug-free baselines | 0 |
| Flagged by `mms` / `reference` / `invariant` / `limit` | 19 / 18 / 12 / 7 |
| Flagged by one family alone | `mms` 1, `limit` 2, `reference` 0, `invariant` 0 |

How to read this:

- The bugs and the checks were written by the same person (the author), and the predicted detections come from reasoning, not from tuning. This measures these 22 bugs. It is not an estimate of how many real-world bugs would be caught.
- `mms` and `reference` overlap heavily. The one bug only `mms` caught is `quad_drag_abs_vx`, which is wrong only when the projectile moves backwards. A single forward trajectory never reaches it.
- `limit` caught two bugs nothing else did (landing point not interpolated, launch angle not converted to radians). Both live in the code around the integrator, not in it.
- The one blind spot is real and understood: an extra time step is an O(dt) shift, and with dt tied to dx^2 it is the same order as the scheme's own error, so no convergence-order test sees it.
- A manufactured solution built from the code's own right-hand side hides a wrong right-hand side. `tests/test_mms.py` demonstrates this on purpose.

## Results on two real projects

Run read-only against `projectile-simulation` and `double-pendulum-simulation` (siblings of this folder; nothing is written into them, and `git status` is clean in both afterwards).

- `projectile_sim_v2.py` (`ProjectileV2`): in vacuum, linear and quadratic drag modes, for both RK4 and Euler, the code agrees with an independent reference at the claimed order (4 and 1). Vacuum energy drift also has the right order. **One finding, now fixed:** the range read from the end of `simulate()` was only first order in dt, because the landing interpolation branch tested `int(fraction) != 0` and `fraction` was between -0.08 and 0 in the three cases run (dt = 0.1, 0.01, 0.001), so it never ran. With `dt=0.01`, `v0=30`, 45 degrees, the reported vacuum range was 91.641 m against an exact 91.743 m, an error of 0.10 m. The interior trajectory points were not affected. The fix (a few lines in `simulate()`, applied on 2026-10-19 and not yet committed in that repo) interpolates the landing point linearly; the observed order of the range is now 2.00 and the error at `dt=0.01` is 1.2e-4 m. `benchmark_scipy.py` could not be re-run here (it needs SciPy and matplotlib). Separately, the README gives the linear drag coefficient as 6*pi*eta*r while the code uses a fixed 0.01 N s/m; which one is intended is not for physverify to say.
- `mechanics.py` (double pendulum): `get_derivatives` matches an independent closed-form reference, `calculate_energy` is consistent with it, and the small-oscillation frequencies match the closed form. `solvers.py` was not tested because it needs SciPy, which is not installed here.

## Known limits

- ODE systems get the full treatment. The one PDE example (`heat1d`) uses hand-derived forcing; a symbolic or automatic route for PDEs is not written yet.
- The error floor in `check_order` is an absolute 1e-12, which suits solutions of size 1 to 10. Rescale it for other magnitudes.
- Checks measure the state at one final time, not the whole trajectory.
- MMS needs a way to add a source term. Codes without one need a small adapter, and an adapter can itself be wrong.
- No claim is made that this finds bugs outside the cases shown here.

## Layout

```
src/physverify/
  order.py        observed order and PASS/FAIL logic
  mms.py          manufactured solutions (complex-step derivative, no SymPy needed)
  studies.py      reference, invariant and bundled ODE checks
  steppers.py     Euler, midpoint, RK4
  problems/       seeded-bug solvers: projectile, pendulum, heat1d
  adapters/       read-only adapters for the two real projects
  matrix.py       builds the detection table
tests/            70 tests, including the seeded-bug regression
```

## Next steps (not done)

PDE manufactured solutions with symbolic derivatives, a pytest plugin, an HTML report, an MCP or Claude Code hook so an AI assistant can run the checks after writing simulation code, and more benchmark problems (Kepler, Sod shock tube, 2D Ising).

## Licence

MIT. Copyright (c) 2026 Ram Chandra Giri.
