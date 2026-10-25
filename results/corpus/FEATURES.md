# Each feature on every repository where it applies

Status: 2026-10-24, physverify 0.5.0. Corpus: the 626 repositories cloned for batches 1 to 8, at the commit that was tested (625 also at their latest commit). Repositories are named by ID. The counts describe this sample only; they are not rates for physics code in general.

The point of these tables is to say how often each check is useful, not only that it found a bug once: how many repositories it applies to, how many defects it finds there, and how many of its warnings are wrong.

## `check_tableau` (Runge-Kutta order conditions)

Applied to every Runge-Kutta table `physverify scan` extracts: tables written as literals, as constructor arguments or class attributes, and steppers whose stages are written as code. `check_tableau` was then run on the extracted coefficients with the order the code claims (nothing from the repositories ran). About 21 s for the whole corpus.

| | Tested commits | Latest commits |
|---|---|---|
| Repositories with at least one table | 27 of 626 (4%) | 25 of 625 |
| Tables | 86 (43 distinct sets of coefficients) | 84 |
| ... written as stages in code / literals / constructor or dict | 47 / 26 / 13 | |
| ... explicit / implicit | 74 / 12 | |
| ... with a stated order (name, docstring, `order` attribute) | 78 | |
| PASS | 75 | 76 |
| FAIL | 11 | 8 |
| ... real defects | 10, in 3 repositories (E09: 3, F09: 3, J042: 4 functions in 3 files) | 7 (F09 fixed its three) |
| ... not a defect | 1: J042's fourth-order Ralston typed with 7 digits; its order conditions hold to 5e-7, and the FAIL message says that this looks like rounded coefficients | 1 (the same) |
| False alarms | 0 | 0 |

All ten defects had already been reported to the authors. Two tables (F09 RK32 and ARK343ERK) have a linear order one higher than their true order: a convergence test on y' = λy alone would show the claimed order, which is how those labels went unnoticed.

### Stability and embedded-order claims

The 12 implicit tables and every table with an embedded pair were also checked against what their names and docstrings state: S-stable, L-stable or A-stable methods (R(inf), the A-stability margin, stiff accuracy), and embedded orders written as 5(4), 4(5) or 3(2). Every claim holds, apart from E09's Tsit5 error weights already counted above: no new defects and no false alarms. Gauss-Legendre is A-stable but not L-stable, and its documentation does not claim more.

## `physverify scan` stages

From the full rescan with the rules as of 2026-10-24 (tested commits; about 28 minutes for the corpus). "Applies to" counts repositories that contain what the stage looks at, by a text search; for constants and names it is every repository with Python files. A WARN is a statement the scan is confident about; a NOTE is a prompt to look.

| Stage | Applies to | WARN (repositories) | NOTE (repositories) | Known defects found | Checked by hand |
|---|---|---|---|---|---|
| tables | 27 with a table | 13 (3) | 73 (27) | 10 | every WARN: all real |
| grid | 348 using `linspace` | 9 (6) | 12 (6) | 2 (+ 3 new, confirmed by runs) | every WARN: 8 real, 1 benign; every NOTE (13 before the last change): 2 known defects, 5 plausible but unconfirmed, 6 different grids sharing a name (1 of them, a correct periodic grid, is no longer reported) |
| constants | 622 | 0 | 411 (61) | 2 | a random sample of 50 (of 983, before the last change): about 10 worth a look (constants from old CODATA editions, rounded values), 9 deliberate approximations in tests, about 30 coincidences, 1 a mistake in physverify's own value of R. The rules were then tightened (1% for constants with units, long numeric tables and data files summarised, the atomic mass unit and neutron mass added), leaving 411 |
| pairs | 338 with `x_to_y`-style names | 0 | 424 (75) | 0 (round trips need Phase 2) | a random sample of 30 (of 795): 18 plausible inverse pairs, 12 pairs of test functions, which are no longer reported |
| names | 622 | 265 (70), of which 59 files that do not parse (29 Python 2) | 6 (5) | 3 | a random sample of 100 (of 248 undefined names, before the last change): about 82 real (43 missing imports of names defined elsewhere in the repository, Python 2 builtins, typos such as `AttributError`, functions removed but still called), 18 names a host program or a library injects at run time, in 2 repositories; files with many such names are now one NOTE |
| api | 497 importing NumPy or SciPy | 131 (20) | 86 (29) | 2 | all 27 repositories with a WARN before the last change: only 1 pins an old NumPy or SciPy, so for the others a fresh install hits the removal. `distutils` (28 warnings, mostly in build scripts) is now a NOTE, because setuptools still provides it |
| literals | 622 | 1 (1) | 0 | 1 | every WARN: real (2 deliberate NaN comparisons in tests are no longer flagged) |
| units | 43 mentioning physical types | 1 (1) | 0 | 1 | every WARN: real |

Sampling was done by the author with an AI assistant, with a fixed random seed; the samples and scripts are in the private study folder. Most name and API warnings are in scripts, examples and tests rather than in the physics: they say whether code still runs, not whether it is right.

## Features that run code

`check_order` on steppers found in the code, conservation checks, `physverify.identities` and the statistical checks need to run the repositories' code in the sandbox. Their sweeps come with Phase 2 of the scan plan (`physverify scan --run`, see [ROADMAP.md](../../ROADMAP.md)), which builds the probes that find where they apply.
