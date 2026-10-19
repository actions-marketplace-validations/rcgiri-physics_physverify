# physverify

Checks that a physics simulation solves the right equations at the right accuracy, not only that it runs.

Status: version 0.0.1, an early prototype. It handles ODE systems and one PDE example. It has not been used by anyone else yet.

## What it does

You describe the physics once, independently of the code under test (a reference right-hand side). physverify then runs five kinds of check:

| Family | What it does | What it can see |
|---|---|---|
| `mms` | Method of Manufactured Solutions. Picks a smooth function, derives the forcing that makes it an exact solution of the reference equations, runs your code with that forcing, and checks the error shrinks at the design order. | A wrong right-hand side anywhere in the state space you sample, and a stepper that is not the order it claims. |
| `reference` | Compares your code with a solution of the reference equations computed independently. | The same bugs, but only along the one trajectory you run. |
| `invariant` | Drift of a conserved quantity (energy, say) as the step shrinks. | Inconsistency between the equations of motion and the conserved quantity. |
| `limit` | A known limiting case: closed-form range, normal-mode frequencies. | Bugs in post-processing or in limits the other checks do not reach. |
| `patch` | A manufactured solution that lies inside the scheme's discrete solution space (for example cubic in x and linear in t for a three-point stencil with forward Euler), so a correct code reproduces it to round-off for any grid and step. | An error that is as small as the scheme's own truncation error and shrinks at the same rate, which every order-of-convergence check accepts. Available for every explicit Runge-Kutta ODE code (a solution linear in t) and for the heat solver; see [docs/patch.md](docs/patch.md). |

Pass/fail rests on the observed order of convergence (`physverify.order.check_order`), which reports PASS, FAIL, EXACT (error at round-off, order not measurable) or INCONCLUSIVE.

## Try it

Only NumPy is needed (pytest to run the tests). Install from the folder, or run from source with `PYTHONPATH=src`:

```bash
pip install -e .
```

Write a spec file that defines `checks()`; [examples/verify_damped_oscillator.py](examples/verify_damped_oscillator.py) checks the solver in [examples/damped_oscillator.py](examples/damped_oscillator.py). You provide an independent reference right-hand side and an `integrate(source, y0, t_end, n_steps)` function that advances your code with an additive source term `source(t)`. Codes with no source hook can still be wrapped; see `src/physverify/adapters/projectile_v2.py` for one that has no time argument either.

Then any of:

```bash
physverify run examples/verify_damped_oscillator.py                 # text; exit code 1 if any check fails
physverify run examples/verify_damped_oscillator.py --json -        # JSON on stdout
physverify run examples/verify_damped_oscillator.py --html report.html   # self-contained page with convergence plots
pytest examples/verify_damped_oscillator.py                         # each check is a pytest test (plugin installed with the package)
```

Without installing, use `python -m physverify` for `physverify` and `pytest -p physverify.pytest_plugin`. Change the damping in `examples/damped_oscillator.py` by 10% and every family flags it.

The benchmark and the test suite:

```bash
physverify matrix results/detection_matrix.md   # the seeded-bug tables below
physverify compare results/comparison.md        # the same bugs against plain unit tests
python -m pytest -q                             # about 1.5 minutes
```

## Seeded-bug benchmark

25 bugs are injected one at a time into three small solvers: a projectile with drag, a double pendulum and the 1D heat equation. Every check is run on each bug. The results are in four files:

- [results/detection_matrix.md](results/detection_matrix.md): the full table.
- [results/bug_catalogue.md](results/bug_catalogue.md): for each bug, the change, the expected symptom, the predicted checks and the observed checks.
- [results/detection_matrix_details.md](results/detection_matrix_details.md): the message from every check.
- [results/heat1d_by_check.md](results/heat1d_by_check.md): a separate table for the heat solver, whose checks refine the step and the grid in different ways.

| | Count |
|---|---|
| Bugs seeded | 25 |
| Flagged by at least one check | 25 |
| Missed by every check | 0 |
| False alarms on the 3 bug-free baselines | 0 |
| Flagged by `mms` / `reference` / `invariant` / `limit` / `patch` | 20 / 18 / 12 / 7 / 21 |
| Flagged by one family alone | `limit` 2, `patch` 3, all others 0 |

**Reproducing it.** The checks are deterministic. `tests/test_seeded_bugs.py` reruns every check and requires that `detection_matrix.md` and `bug_catalogue.md` match the committed files exactly. Two commands regenerate the tables:

```bash
PYTHONPATH=src python -m physverify.matrix results/detection_matrix.md
PYTHONPATH=src python -m physverify.compare results/comparison.md
```

**Against ordinary tests.** [results/comparison.md](results/comparison.md) runs the same 25 bugs through four strategies. "Plain tests" means one run per case, compared with a reference or a known value within 0.1% (1% for the heat solver).

| Strategy | Bugs caught | False alarms | Runtime on the author's laptop |
|---|---|---|---|
| plain tests | 20 of 25 | 0 of 3 | 18 s |
| `reference` only | 18 of 25 | 0 of 3 | 24 s |
| `mms` only | 20 of 25 | 0 of 3 | 17 s |
| all five families | 25 of 25 | 0 of 3 | 45 s |

The plain tests missed five bugs:
- `quad_drag_abs_vx` and `rk4_stage4_time`, which only show on forced or backward-moving runs.
- `landing_no_interp`, a 0.1% range error.
- `extra_time_step` and `source_time_shift` in the heat solver.

A tighter tolerance would catch more of them. The difficulty is choosing it: the order studies need no tolerance on the error itself, only on the order.

How to read this:

- **Same author.** The bugs and the checks were written by the same person (the author). The predicted detections and symptoms come from reasoning, not from tuning. This measures these 25 bugs. It is not an estimate of how many real-world bugs would be caught.
- **`mms` and `reference` overlap heavily.** `mms` sees two bugs that `reference` does not:
  - `quad_drag_abs_vx` is wrong only when the projectile moves backwards, and a single forward trajectory never reaches it.
  - `rk4_stage4_time` is visible only when the right-hand side depends on time, and the free pendulum does not.
- **`limit` catches two bugs nothing else does.** These are the landing point not being interpolated and the launch angle not being converted to radians. Both live in the code around the integrator, not in it.
- **`patch` catches three bugs alone.** Each one adds an error of the same order as the scheme's own, so every order-of-convergence check accepts it:
  - `heat1d/extra_time_step`
  - `heat1d/source_time_shift`
  - `projectile/euler_extra_step`
- **Not independent evidence.** The heat patch test was added after `extra_time_step` was the one miss in the first version of the table. The ODE patch test and the other two order-preserving bugs were added together, after the heat result. So these three detections are not independent evidence. They show that the mechanism works as designed. [docs/patch.md](docs/patch.md) states exactly what the patch check assumes and proves.
- **A built-in blind spot, shown on purpose.** A manufactured solution built from the code's own right-hand side hides a wrong right-hand side. `tests/test_mms.py` demonstrates this.

## Results on two real projects

Run read-only against `projectile-simulation` and `double-pendulum-simulation` (siblings of this folder; nothing is written into them, and `git status` is clean in both afterwards).

- `projectile_sim_v2.py` (`ProjectileV2`): in vacuum, linear and quadratic drag modes, for both RK4 and Euler, the code agrees with an independent reference at the claimed order (4 and 1). Vacuum energy drift also has the right order, the error over the whole trajectory converges at the same order, and every mode reproduces the linear `patch` solution to round-off. **One finding, now fixed:** the range read from the end of `simulate()` was only first order in dt, because the landing interpolation branch tested `int(fraction) != 0` and `fraction` was between -0.08 and 0 in the three cases run (dt = 0.1, 0.01, 0.001), so it never ran. With `dt=0.01`, `v0=30`, 45 degrees, the reported vacuum range was 91.641 m against an exact 91.743 m, an error of 0.10 m. The interior trajectory points were not affected. The fix (a few lines in `simulate()`, applied and committed in that repo on 2026-10-19) interpolates the landing point linearly; the observed order of the range is now 2.00 and the error at `dt=0.01` is 1.2e-4 m. `benchmark_scipy.py` could not be re-run here (it needs SciPy and matplotlib). Separately, the README gives the linear drag coefficient as 6*pi*eta*r while the code uses a fixed 0.01 N s/m; which one is intended is not for physverify to say.
- `mechanics.py` (double pendulum): `get_derivatives` matches an independent closed-form reference, `calculate_energy` is consistent with it, the linear `patch` solution is reproduced to round-off, and the small-oscillation frequencies match the closed form. `solvers.py` was not tested because it needs SciPy, which is not installed here.

## Known limits

- ODE systems get the full treatment. The one PDE example (`heat1d`) uses hand-derived forcing; a symbolic or automatic route for PDEs is not written yet.
- The `patch` test needs a manufactured solution the scheme reproduces exactly. Finding one is easy for a three-point stencil with forward Euler and can be hard or impossible for other schemes. The "time-only" and "grid-only" studies isolate one kind of error only to leading order: the time-stepping error is itself smoothed by the discrete Laplacian, a cross term of order dt * dx^2 (visible as about 0.1% differences between grids in `tests/test_reference_problems.py`).
- The error floor in `check_order` is 1e-12, or 1e-13 times the solution's size if that is larger (`physverify.order.effective_floor`). Round-off grows with the number of steps too, so very long runs may need a larger floor.
- MMS needs a way to add a source term. Codes without one need a small adapter, and an adapter can itself be wrong.
- No claim is made that this finds bugs outside the cases shown here.

## Related work

Each part of physverify has earlier work behind it. Searched on 2026-10-19; I did not find a package that combines all five check families with a seeded-bug benchmark, but that is a search result, not proof that none exists.

- Salari and Knupp, [Code Verification by the Method of Manufactured Solutions](https://www.osti.gov/biblio/759450) (Sandia report SAND2000-1444, 2000). Describes MMS and a blind-test protocol for finding which coding mistakes it can and cannot expose. The seeded-bug benchmark here follows the same idea on a much smaller scale.
- Wu and Mitchell, [Mutant Accuracy Testing for Assessing the Implementation of Numerical Algorithms](https://www.cs.toronto.edu/~rwu/papers/wu2019mutation.pdf) (NSV at CAV, 2019). Tests numerical implementations, correct and with artificially introduced bugs, in MATLAB, by comparing a code's error with that of mutated versions of itself. Its oracle differs from the ones here, and it notes that convergence-rate checks depend on heuristic thresholds, which is the weakness `patch` is meant to address.
- [MASA](https://github.com/manufactured-solutions/MASA). A C++ library of manufactured solutions for PDE codes. It supplies solutions; it does not run a user's solver and report PASS/FAIL.
- [ExactPack](https://github.com/lanl/ExactPack) (Los Alamos). A Python package for code verification built on exact solutions of benchmark problems. It complements MMS, and its problems could serve as `reference` cases.
- [materials-simulation-skills](https://github.com/HeshamFS/materials-simulation-skills). Agent skills for simulation work, including a `benchmark-and-mms-planner` skill. From its skill description it is a planning aid, not a runner of checks on user code (only the description was read). It is the nearest thing found to the planned assistant hook.

For `patch`, no prior work was found. The name comes from finite-element patch tests, which also require a scheme to reproduce a simple field exactly, but I found no published test that uses a manufactured solution inside the scheme's discrete solution space to catch errors of the same order as the truncation error. I did not read the finite-element patch-test or "nearby problems" literature, so similar ideas may exist under other names.

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
tests/            86 tests, including the seeded-bug regression
```

## Next steps (not done)

PDE manufactured solutions with symbolic derivatives, a pytest plugin, an HTML report, an MCP or Claude Code hook so an AI assistant can run the checks after writing simulation code, and more benchmark problems (Kepler, Sod shock tube, 2D Ising).

## Licence

MIT. Copyright (c) 2026 Ram Chandra Giri.
