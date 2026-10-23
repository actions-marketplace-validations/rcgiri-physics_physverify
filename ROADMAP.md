# Roadmap

What may come after 0.4.2. The unreleased changes (identity checks, `extract_functions`, sandbox version stubs and latest-stack image) are in the changelog. Nothing here is promised or scheduled; the order is a rough guess at what would help users most. Suggestions are welcome as GitHub issues.


## Principles

- **Evidence before features.** Independent trial reports (see CONTRIBUTING.md) come before new check families.
- **Independence of the reference is the first concern.** Every recipe and template asks for equations written from the physics, and for a second, independent check.
- **A PASS is a bounded claim.** Every output says what was tested; [What a PASS means](docs/assumptions.md) says what was not.
- **Deepen before widening.** Numerical-method coverage grows only when it adds value for ODE/PDE time integration, convergence or conservation. Statistical (Monte Carlo) checks grow carefully: each new one with its false-alarm rate and power measured over repeated seeds.
- **Every published number is regenerable** with `python scripts/reproduce_all.py`, or says why not.

## First for 0.5.0: keep the installed package to the checks

The package installs only NumPy and is about 1 MB, so installing it for one feature (for example `check_tableau`) is cheap. But code that users never call ships with it and blurs what physverify is:

- Move the seeded-bug benchmark (`problems/`, `matrix.py`, `compare.py`, `method_bugs.py`) and the adapters written for single corpus repositories (for example `adapters/three_body.py`) out of `src/physverify/` into a folder that is in the repository but not installed. They stay reproducible with `python scripts/reproduce_all.py`.
- Make the AI-assistant parts (`physverify hook`, `physverify mcp`) an optional extra, `pip install physverify[agent]`.
- Then the installed package holds only the checks: order studies, manufactured solutions, references, conserved quantities, patch tests, Runge-Kutta tables, exact references and statistics.

Done when the wheel no longer contains the moved code, `physverify demo` still works from it, and the committed tables are unchanged.

## Next (0.5.0): checking code without writing a wrapper

Today every check needs a short spec file, and for most codes a small adapter that adds a source term. That is the biggest barrier to trying physverify. Several checks need no adapter at all, because they ask the code only to run, not to solve a different problem:

- **Find and check Runge-Kutta tables automatically.** Scan a project's source for Butcher tables (arrays named `A`/`b`/`c`, `butcher`, `tableau`, or the classic coefficient patterns) and run `check_tableau` on each, with the order taken from the name or the docstring. This found mislabelled tables in two real packages and needs no knowledge of the equations.
- **Self-convergence (Richardson) studies.** Run the code at three or more resolutions and measure the order from the differences between them, with no exact solution. It cannot prove the equations are right, but it catches a wrong order, an off-by-one step count or a time grid that ends at the wrong time.
- **A declarative spec instead of Python.** A `[tool.physverify]` table in `pyproject.toml` (or a small YAML file) that names the solver function, its call pattern (`solve(y0, t_end, n_steps)`), the claimed order and the equations as text (turned into a reference with SymPy). physverify would then build the checks itself.
- **Call-pattern discovery.** Inspect a module for functions that look like a right-hand side `f(t, y)`, a stepper `step(y, dt)` or a solver `solve(..., n)`, call each with small test inputs, and suggest a spec. The user confirms; nothing is assumed silently.
- **`physverify scan PATH`.** One command that runs the wrapper-free stages in order (smoke run, near-miss constants, Butcher tables, self-convergence where a solver is found) and writes one report.

## Must-have improvements

- **2D and 3D heat equation.** Manufactured solutions, an independent reference operator, order studies in space and time, and checks for Dirichlet, Neumann and periodic boundaries, including the corners and edges where 2D/3D codes most often go wrong. Then the same for the wave and advection-diffusion equations.
- **Whole PDE order studies from SymPy.** `physverify.symbolic` already derives source terms; the next step is to run the full study from an equation written as text.
- **IMEX / additive Runge-Kutta coupling conditions.** Check the conditions that link the explicit and implicit tables of an IMEX pair (bi-coloured trees), not only each table on its own. Also the order of embedded error estimators.
- **Loading code that needs repair.** A `load_repaired(path, fix)` helper for files that do not parse as published, recording the repair so that a pass on repaired code is never reported as a pass on the original.
- **"Was any work done?" probe.** Count iterations or call every public function once; two real bugs were functions that silently did almost nothing (one Jacobi sweep in a pressure solver).
- **Stochastic checks that stop early.** Stop sampling as soon as the result is decisive, so slow Monte Carlo codes fit inside a time budget.
- **Clearer messages** when only an absolute tolerance fails while the observed order is exact, and a helper that skips the start-up transient before fitting a decay rate.
- **Sandbox: pick the image automatically.** When `deps` fails because a dependency needs a newer NumPy or SciPy than the pinned image, say so and suggest the latest-stack image, instead of a bare pip resolution error. (The shared wheel cache and the latest-stack image are done.)
- **Identity probes in `physverify scan`.** Run the cheap identity checks that need no knowledge of the equations: pairs of functions whose names say they are inverses (`x_to_y` / `y_to_x`, `s2z` / `z2s`) as round trips, and `min_*` / `max_*` or 2D / 3D siblings called with the same arguments.
- **Units in comparisons.** Most adapter mistakes in batch 8 were units or coordinate origins. An optional units-aware comparison (via pint, when installed) that refuses to compare quantities of different dimension.

## Documentation website

Done: the site at https://rcgiri-physics.github.io/physverify/ has a page for each kind of check, each built around a small runnable example (most with a deliberate bug and the check that catches it), plus recipes, convergence-study pitfalls, the command line and an API overview. A test re-runs every example and fails if its output no longer matches the page.

Still to do:

- An API reference generated from the docstrings (mkdocstrings), in place of the hand-written overview.
- More recipes: a 1D heat code end to end, an inference code, a Monte Carlo sampler.
- Plots of convergence studies on the pages, made from the examples.

## Later

- A small C/C++ and Fortran bridge (run a compiled solver through a command line or `ctypes` and read its output), since much physics code is not Python.
- Julia support through the same command-line route.
- A gallery of real bugs found (with the authors' permission), each with the check that found it.
