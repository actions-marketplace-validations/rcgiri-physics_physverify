# Related work and credits

physverify does not introduce a new verification method. Its checks are standard ideas from the code-verification literature, put together in one small Python package. This page lists the work they come from, and the tools that do similar things, some of them better.

## Methods

- **Manufactured solutions and observed order of accuracy.** K. Salari and P. Knupp, *Code Verification by the Method of Manufactured Solutions*, Sandia report SAND2000-1444 (2000), [OSTI 759450](https://www.osti.gov/biblio/759450). Their study of which coding mistakes an order study can and cannot expose also shaped the seeded-bug benchmark.
- P. J. Roache, *Code Verification by the Method of Manufactured Solutions*, J. Fluids Eng. 124 (2002) 4-10, [doi:10.1115/1.1436090](https://doi.org/10.1115/1.1436090).
- W. L. Oberkampf and C. J. Roy, *Verification and Validation in Scientific Computing*, Cambridge University Press (2010), [doi:10.1017/CBO9780511760396](https://doi.org/10.1017/CBO9780511760396).
- I. B. Celik et al., *Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications*, J. Fluids Eng. 130 (2008) 078001, [doi:10.1115/1.2960953](https://doi.org/10.1115/1.2960953): the grid convergence index, planned for the order checks ([ROADMAP.md](roadmap.md)).
- **Runge-Kutta order conditions.** J. C. Butcher, and E. Hairer, S. P. Nørsett and G. Wanner, *Solving Ordinary Differential Equations I*, Springer (2nd ed. 1993). `physverify.butcher` checks the conditions on rooted trees as given there.
- **Patch tests.** The exact patch tests come from the finite-element patch test (B. M. Irons and A. Razzaque, 1972; see also F. Stummel, *The generalized patch test*, SIAM J. Numer. Anal. 16 (1979) 449-471, [doi:10.1137/0716037](https://doi.org/10.1137/0716037)). physverify applies the idea to time integrators and finite-difference stencils: a solution the discrete scheme should reproduce exactly, with the source term worked out by hand rather than by the code under test.
- **Seeded bugs.** R. Wu and D. Mitchell, *Mutant Accuracy Testing* (NSV 2019), applied mutation testing to numerical code before the benchmark here did.

## Tools that overlap

- **[NodePy](https://github.com/ketch/nodepy)** (D. I. Ketcheson and contributors; [JOSS paper](https://doi.org/10.21105/joss.02515)) analyses Runge-Kutta and other ODE methods: order conditions, stage order, stability functions and regions, and convergence tests. It covers most of what `check_tableau` does, and more; use it for deeper analysis of a method. physverify's addition is reading tables out of a project's source and comparing them with the order the code claims.
- **[MASA](https://github.com/manufactured-solutions/MASA)** (C++ with C, Python and Fortran interfaces; Malaya et al. 2012): a library of manufactured solutions for heat, Euler, Navier-Stokes and other equations, with automatic differentiation. Its PDE coverage is far wider than physverify's.
- **[DiffEqDevTools.jl](https://github.com/SciML/DiffEqDevTools.jl)** (Julia, SciML; now part of OrdinaryDiffEq.jl): convergence-order tests, errors against reference solutions and solver comparisons. It is the closest existing tool to physverify's order and reference checks.
- **A PETSc agent benchmark** (GitHub, 2026): AI agents generate, compile and run PETSc programs, which are graded for accuracy and coarse/fine convergence through MCP. It also shows why an upper bound on the error alone is not enough: an agent can print a small number without solving anything.
- **Mutation testing tools** such as [mutmut](https://github.com/boxed/mutmut) and [Cosmic Ray](https://github.com/sixty-north/cosmic-ray) generate mutants automatically. They do not know which mutants are physically meaningful, but they could enlarge the seeded-bug set.
- **Regression and property testing.** [pytest-regressions](https://github.com/ESSS/pytest-regressions) compares outputs with stored baselines (a baseline can keep a bug) and [Hypothesis](https://github.com/HypothesisWorks/hypothesis) generates test inputs. physverify uses Hypothesis in its own tests.
- **[ExactPack](https://github.com/lanl/ExactPack)** (Los Alamos): exact solutions for hydrodynamics benchmarks such as Sod and Sedov.
- **The [MOOSE](https://mooseframework.inl.gov/) `mms` Python module**: SymPy source terms and convergence plots for MOOSE applications.
- **[physics-lint](https://tyy0811.github.io/physics-lint/)** checks trained neural PDE surrogates for residual, conservation, boundary-condition, positivity and symmetry violations, with rule IDs and SARIF output for CI. It targets learned models; physverify targets numerical solvers.
- **[noether-guard](https://github.com/SuperInstance/noether-guard)** (Rust) monitors the conserved quantities that follow from declared symmetries (energy, momentum, angular momentum) during a run and reports when and at what time scale they start to drift.
- **[fineness](https://github.com/nicoseijas/fineness)** (Python, on PyPI) certifies numerical and stochastic software with mutation-gated checks (a check counts only after it has been shown that it can fail), mandatory error bars and trust levels that cannot exceed those of their inputs. The mutation idea is the one physverify plans in `physverify mutate` (issue #28).
- **[foam-verify](https://github.com/Cskar10/foam-verify)** checks OpenFOAM results without running them: grid convergence index, iterative convergence of the reported quantities, settings consistency across grid levels and comparison with reference data, with a read-only MCP server and a committed evaluation of AI agents judging grid studies. It is specific to OpenFOAM; physverify works on the solver's code.
- **[NuclearMC-Verifier](https://github.com/SHARK20031010/NuclearMC-Verifier)** statically checks LLM-written Geant4 (C++) Monte Carlo transport code for physics errors that compile and run cleanly, on a benchmark of 190 tasks. It targets one framework and does not run the code.
- **[convergence](https://pypi.org/project/convergence/)** (PyPI) computes the observed order and the grid convergence index from a grid study, a port of the NASA verification tutorial code; `physverify.studies.gci` does the same calculation.
- **Floating-point tools** such as [Verificarlo](https://github.com/verificarlo/verificarlo), [Verrou](https://github.com/edf-hpc/verrou) and [Herbie](https://github.com/herbie-fp/herbie) find rounding and precision errors, a different class of bug from the wrong equations physverify looks for. The two approaches complement each other.

## AI code review

LLM-written unit tests have been compared with human ones on general Python bugs (arXiv 2606.08588), and generic review prompts have been criticised for simulation code (arXiv 2605.09360). Neither uses physics codes with known defects. Closer to physverify's aim are FEM-Bench (arXiv 2025, LLM-written finite-element code and tests), a 2026 study of LLM-written LAMMPS scripts with an agentic verification skill, and a 2026 preprint that rebuilds the PDE encoded in a MOOSE input and compares it with the intended equations, a check physverify does not make. physverify's [pilot comparison](results.md) did, on 20 repositories; see [Checking an AI code review](ai-review.md) for how the two are used together.

## Exact references

Each function in `physverify.references` names its source in its docstring (`help(physverify.references.<name>)`), for example Kaufman's and Onsager's results for the 2D Ising model ([Ising checks](ising.md)).

## People and projects

- The maintainers of the projects in the corpus study, who answered reports, reproduced them and fixed them. Questions from the [qmat](https://github.com/Parallel-in-Time/qmat) maintainers led to the linear-order and stage-order checks in `physverify.butcher`.
- Much of the code, the documentation and the corpus study were written with AI coding assistants (Claude Code), directed and checked by the author. Every reported defect was confirmed by running the code before it was reported.

If your work should be listed here and is not, please open an issue.
