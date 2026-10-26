# Related work and credits

physverify does not introduce a new verification method. Its checks are standard ideas from the code-verification literature, put together in one small Python package. This page lists the work they come from, and the tools that do similar things, some of them better.

## Methods

- **Manufactured solutions and observed order of accuracy.** K. Salari and P. Knupp, *Code Verification by the Method of Manufactured Solutions*, Sandia report SAND2000-1444 (2000), [OSTI 759450](https://www.osti.gov/biblio/759450). Their study of which coding mistakes an order study can and cannot expose also shaped the seeded-bug benchmark.
- P. J. Roache, *Code Verification by the Method of Manufactured Solutions*, J. Fluids Eng. 124 (2002) 4-10, [doi:10.1115/1.1436090](https://doi.org/10.1115/1.1436090).
- W. L. Oberkampf and C. J. Roy, *Verification and Validation in Scientific Computing*, Cambridge University Press (2010), [doi:10.1017/CBO9780511760396](https://doi.org/10.1017/CBO9780511760396).
- I. B. Celik et al., *Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications*, J. Fluids Eng. 130 (2008) 078001, [doi:10.1115/1.2960953](https://doi.org/10.1115/1.2960953): the grid convergence index, planned for the order checks ([ROADMAP.md](roadmap.md)).
- **Runge-Kutta order conditions.** J. C. Butcher, and E. Hairer, S. P. Nørsett and G. Wanner, *Solving Ordinary Differential Equations I*, Springer (2nd ed. 1993). `physverify.butcher` checks the conditions on rooted trees as given there.
- **Seeded bugs.** R. Wu and D. Mitchell, *Mutant Accuracy Testing* (NSV 2019), applied mutation testing to numerical code before the benchmark here did.

## Tools that overlap

- **[NodePy](https://github.com/ketch/nodepy)** (D. I. Ketcheson and contributors; [JOSS paper](https://doi.org/10.21105/joss.02515)) analyses Runge-Kutta and other ODE methods: order conditions, stage order, stability functions and regions, and convergence tests. It covers most of what `check_tableau` does, and more; use it for deeper analysis of a method. physverify's addition is reading tables out of a project's source and comparing them with the order the code claims.
- **[MASA](https://github.com/manufactured-solutions/MASA)** (C++): a library of manufactured solutions.
- **[ExactPack](https://github.com/lanl/ExactPack)** (Los Alamos): exact solutions for hydrodynamics benchmarks such as Sod and Sedov.
- **The [MOOSE](https://mooseframework.inl.gov/) `mms` Python module**: SymPy source terms and convergence plots for MOOSE applications.
- **Floating-point tools** such as [Verificarlo](https://github.com/verificarlo/verificarlo), [Verrou](https://github.com/edf-hpc/verrou) and [Herbie](https://github.com/herbie-fp/herbie) find rounding and precision errors, a different class of bug from the wrong equations physverify looks for. The two approaches complement each other.

## Exact references

Each function in `physverify.references` names its source in its docstring (`help(physverify.references.<name>)`), for example Kaufman's and Onsager's results for the 2D Ising model ([Ising checks](ising.md)).

## People and projects

- The maintainers of the projects in the corpus study, who answered reports, reproduced them and fixed them. Questions from the [qmat](https://github.com/Parallel-in-Time/qmat) maintainers led to the linear-order and stage-order checks in `physverify.butcher`.
- Much of the code, the documentation and the corpus study were written with AI coding assistants (Claude Code), directed and checked by the author. Every reported defect was confirmed by running the code before it was reported.

If your work should be listed here and is not, please open an issue.
