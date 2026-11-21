# Runge–Kutta table census

Runge–Kutta coefficients are copied by hand from papers into code. One wrong digit can lower a method's order without any visible sign: adaptive step control shrinks the step until the error looks fine, and a test on y′ = λy, where f does not depend on t, often cannot see a wrong node. In November 2026 the checks in `physverify.butcher` were run (`check_rosenbrock`, `check_additive` and `check_dense_output` were added for it in 0.9.0) on the coefficient tables of open-source ODE libraries to see how many tables have the order their names claim.

## What was checked

- **847 Runge–Kutta tables** (explicit, implicit, IMEX and low-storage) **from 34 libraries**, each read at a pinned commit. Each table was checked against the order conditions to its claimed order (`check_tableau`), with the stage times compared to the row sums of A, embedded pairs, error weights and stability claims. Residuals were also computed to 50 digits.
- **A second opinion:** NodePy recomputed the order of the 680 tables that passed by 2026-11-16 and agreed on all 680. It was not run on tables added later, on embedded weights or on Rosenbrock tables (NodePy has no Rosenbrock order code).
- **Rosenbrock and W-method tables** (`check_rosenbrock`): 77 tables from 8 libraries first, then the Rosenbrock code of every repository a GitHub code search found with its own Rosenbrock implementation.
- **More than the coefficients** in selected cases: dense output (`check_dense_output`), low-storage forms converted back to Butcher form, IMEX coupling conditions (`check_additive`), symplectic splitting coefficients and linear multistep methods. Some findings were also confirmed by convergence runs in the library's own language (Julia, Fortran, Java, C).
- **First sources:** 344 tables were compared with their first published source (papers, books, the authors' coefficient files), which also turned up three errors in the sources themselves.

## Results (counts for these libraries only)

- 791 of the 847 tables pass, 39 fail, 16 state no order and 1 was truncated in the code.
- Each failure was reviewed by hand against its source, with an exact recheck and a convergence run. More than half are defects: coefficient typos, stage times that do not match the row sums, wrong embedded weights, documentation and code that disagree, and order labels that are too high. The others are by design (for example, methods built on purpose for linear problems), harmless or still open.
- Most defects show only when f depends on t, or only in the error estimate. A convergence test on y′ = λy passes them. **If you test an integrator, include a problem with an explicit time dependence**, such as y′ = y cos t.

## Reports and outcomes (as of 2026-11-21)

23 defect reports were sent to the libraries:

| Outcome | Reports |
|---|---|
| Confirmed by the maintainers | 5: [OrdinaryDiffEq.jl #5001](https://github.com/SciML/OrdinaryDiffEq.jl/issues/5001) (fixed), [SUNDIALS #1083](https://github.com/LLNL/sundials/issues/1083) (reproduced, fix proposed), [Hipparchus #507](https://github.com/Hipparchus-Math/hipparchus/issues/507) (documentation fix and regression test planned for 5.0), [qmat #25](https://github.com/Parallel-in-Time/qmat/issues/25) (fixed), [jaxfun #71](https://github.com/spectralDNS/jaxfun/issues/71) (fix in progress) |
| Fix in review | 2 |
| Waiting for a reply | 16 |

A library is named here only after its maintainers confirm; the list is updated as replies arrive. Questions about a table's source and reports that turned out to be duplicates or already fixed are not counted. Earlier, [qmat #23](https://github.com/Parallel-in-Time/qmat/issues/23) led qmat to run `physverify.butcher` in its own CI.

## Not covered

- Only the tables and, in the cases above, the code that applies them. A correct table can still be used by a step function with a bug.
- The libraries were chosen by availability, not at random, so the counts are not an error rate for numerical software.
- A few tables could not be compared with a first source because the paper was not available.

The per-table results are published as a dataset: [runge-kutta-catalog](https://github.com/rcgiri-physics/runge-kutta-catalog), archived on Zenodo as [doi:10.5281/zenodo.24412889](https://doi.org/10.5281/zenodo.24412889). It has one row per table (library, pinned version, file, coefficients as printed, the library's claim, the verdict and the review), cards comparing 40 Runge-Kutta methods and 3 Rosenbrock methods with their first published sources, 88 Rosenbrock and W-method tables from 10 libraries, and scripts that re-check every table with physverify, so the counts on this page can be checked table by table. Tables with a reported but unconfirmed defect are held back there too, and only counted.

To check a table yourself, see [Runge–Kutta tables](checks/runge-kutta.md).
