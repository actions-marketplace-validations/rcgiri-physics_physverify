# Roadmap

What may come after 0.4.2. The unreleased changes (identity checks, `extract_functions`, `load_repaired`, `residual_check`, `decay_rate`, an accuracy option for `check_order`, and sandbox version stubs, latest-stack image and conflict hint) are in the changelog. Nothing here is promised or scheduled; the order is a rough guess at what would help users most. Suggestions are welcome as GitHub issues.


## Principles

- **Evidence before features.** Independent trial reports (see CONTRIBUTING.md) come before new check families.
- **Independence of the reference is the first concern.** Every recipe and template asks for equations written from the physics, and for a second, independent check.
- **A PASS is a bounded claim.** Every output says what was tested; [What a PASS means](docs/assumptions.md) says what was not.
- **Deepen before widening.** Numerical-method coverage grows only when it adds value for ODE/PDE time integration, convergence or conservation. Statistical (Monte Carlo) checks grow carefully: each new one with its false-alarm rate and power measured over repeated seeds.
- **Every published number is regenerable** with `python scripts/reproduce_all.py`, or says why not.

## Done for 0.5.0: the installed package holds only the checks

The benchmark and the single-repository adapters moved to `benchmark/pvbench/` (not installed). The AI-assistant parts (`physverify hook`, `physverify mcp`) stay in the package: they use only the standard library, so an extra would not make the install any smaller.

## Now: improve the tool, not the number of repositories tested

From 2026-10-23 no new corpus batches are planned. Of the 74 defects reported to authors, 14 were found by a physverify check as such and most of the rest by the test script written for each repository ([FINDINGS_BY_METHOD.md](results/corpus/FINDINGS_BY_METHOD.md)). Writing those scripts is the bottleneck, so the work now goes into checks that need no script, then into rescanning the repositories already tested: what is recovered, and what is a false alarm, within that sample only.

### Done: `physverify scan PATH` (static, runs nothing)

Near-miss constants, Runge-Kutta tables written as literals (order, row sums, error and embedded weights, claimed order from names), grid spacing against `linspace`, inverse-pair suggestions. See `docs/running/cli.md`.

### Next for `scan`

- **Done: tables written as code.** Stages such as `k2 = h*f(t + h/2, y + k1/2)` are read back into `A`, `b`, `c` and checked like literal tables and against a table in the docstring. Next: split systems (`x` and `v` advanced side by side) and implicit stages.
- **Stages that run code, in the sandbox only:** a smoke run, inverse pairs as round trips, `min_*` / `max_*` and 2D / 3D siblings called with the same arguments, and self-convergence (Richardson) where a solver with a step-count argument is found.
- **Call-pattern discovery.** Find functions that look like a right-hand side `f(t, y)`, a stepper `step(y, dt)` or a solver `solve(..., n)` and suggest a spec. The user confirms; nothing is assumed silently.
- **A declarative spec instead of Python.** A `[tool.physverify]` table in `pyproject.toml` naming the solver, its call pattern, the claimed order and the equations as text (turned into a reference with SymPy).
- **Measure false alarms.** Every new stage is run over the whole cloned corpus at the tested and the latest commits, and each WARN is checked by hand before the stage is released.

## Must-have improvements

- **2D and 3D heat equation.** Manufactured solutions, an independent reference operator, order studies in space and time, and checks for Dirichlet, Neumann and periodic boundaries, including the corners and edges where 2D/3D codes most often go wrong. Then the same for the wave and advection-diffusion equations.
- **Whole PDE order studies from SymPy.** `physverify.symbolic` already derives source terms; the next step is to run the full study from an equation written as text.
- **IMEX / additive Runge-Kutta coupling conditions.** Check the conditions that link the explicit and implicit tables of an IMEX pair (bi-coloured trees), not only each table on its own. Also the order of embedded error estimators.
- **Stochastic checks that stop early.** Stop sampling as soon as the result is decisive, so slow Monte Carlo codes fit inside a time budget.
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
