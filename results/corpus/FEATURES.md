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

## `physverify scan` stages

From the full rescan with 0.5.0's rules (tested commits). "Applies to" counts repositories that contain what the stage looks at, by a text search; for constants and names it is every repository with Python files. A WARN is a statement the scan is confident about; a NOTE is a prompt to look.

| Stage | Applies to | WARN (repositories) | NOTE (repositories) | Known defects found | Checked by hand |
|---|---|---|---|---|---|
| tables | 27 with a table | 13 (3) | 73 (27) | 10 | every WARN: all real |
| grid | 348 using `linspace` | 9 (6) | 13 (7) | 2 (+ 3 new, confirmed by runs) | every WARN: 8 real, 1 benign |
| constants | 622 | 0 | 983 (75) | 2 (as NOTEs) | not checked one by one |
| pairs | 338 with `x_to_y`-style names | 0 | 795 (79) | 0 (round trips need Phase 2) | not checked |
| names | 622 | 307 (72), of which 59 files that do not parse | 3 (2) | 3 | a random sample of 30: about 28 real |
| api | 497 importing NumPy or SciPy | 158 (27) | 59 (21) | 2 | spot checks: removed features, all real |
| literals | 622 | 3 (2) | 0 | 1 | every WARN: 2 real (2 deliberate NaN tests, since excluded) |
| units | 43 mentioning physical types | 1 (1) | 0 | 1 | every WARN: real |

## Features that run code

`check_order` on steppers found in the code, conservation checks, `physverify.identities` and the statistical checks need to run the repositories' code in the sandbox. Their sweeps come with Phase 2 of the scan plan (`physverify scan --run`, see [ROADMAP.md](../../ROADMAP.md)), which builds the probes that find where they apply.
