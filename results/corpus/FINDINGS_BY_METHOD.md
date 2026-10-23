# What found each bug: physverify's checks, or the script written for the repository

Status: 2026-10-23, covering every finding reported to authors from batches 1 to 8 (67 reports of defects with 74 defects in all, and 2 questions). Repositories are named by ID, as in [SUMMARY.md](SUMMARY.md) and [BATCH7.md](BATCH7.md).

The counts are for the repositories tested in these batches only. They are not a bug rate for physics code in general, and they are not a measure of how often physverify finds bugs in code it is pointed at: most of the finding was done by the person (with an AI assistant) who wrote each repository's script.

## Why this matters

Every repository was tested with a short script (an "adapter") that calls its code. physverify gave the scripts their building blocks (a sandbox, an order study, conservation and statistical checks, Butcher order conditions, a comparison with a stated tolerance), but in many cases the bug was found because the script compared the code with an independent answer someone worked out by hand. That is useful, but it is not physverify finding the bug. This page separates the two, so that what the tool itself can do is not overstated.

## The four ways a defect was found

| How it was found | Defects | Reports | What it means |
|---|---|---|---|
| **A physverify check** (`check_order`, `check_tableau`, a conservation check) failed on a problem that needs no answer written for that code | 14 | 9 | The tool's own method found it. The script only had to call the solver. |
| **The code does not run** (crash, missing import, removed NumPy function, missing folder) | 11 | 11 | Found by running it at all (`physverify smoke`, or the first call in a script). |
| **The script's own reference** (an exact formula, a published value, a hand-derived limit, an edge input) disagreed with the code | 37 | 37 | Found by the script's author. physverify ran the comparison and the sandbox, but a plain `assert` would have found the same thing. |
| **Reading the code first**, then confirming with a run in the sandbox | 12 | 12 | Found by reading (batch 8 libraries K15-K28). The run proved it; it did not find it. |
| Total | 74 | 67 | D08 and H01 count in two rows; plus 2 questions to authors (G07, K19) |

So **14 of the 74 defects (19%) were found by a physverify check as such**, 11 more by simply running the code, and 49 by the person writing or reading the test. Within this sample, the checks that need no knowledge of the answer found mostly one kind of bug: a numerical method that does not reach its stated order, or a quantity that should be conserved and is not.

## Per report

Some entries are judgement calls, marked *; where a report has two defects found in different ways, they are counted separately.

**physverify check** (14 defects)

| ID | Defect | Check |
|---|---|---|
| D08 | backward integration first order | `check_order` |
| E09 | Tsit5 error weights sum to 0.97 | `check_tableau` (error weights) |
| F09 | three order labels one too high | `check_tableau` |
| H01 | source not scaled by dt; CN/BE Dirichlet values outside the solve (2 defects) | `check_order` |
| H19 | grid spacing W/(N-1) for N-1 interior points | `check_order` (first order) |
| H47 | boundary cells too large: heat input too high | conservation |
| H54 | Neumann boundary leaks energy | conservation |
| J042 | heun, rk38, bs below their stated order (3 defects) | `check_order` |
| J155 | convergence study compares solutions one step apart | `check_order` (measured 2, the repository's study says 1.76) |

**The code does not run** (11): D03, G10, J005, J012, J147, J157, J253, J264, J265, J290, J420.

**The script's reference** (37): D04, D08 (step past the end time), H01 (one step too many), I12, J019, J077, J130, J133*, J156, J159, J192, J216, J220, J222, J224, J277*, J288, J294, J298, J318, J348, J383, J384, J385, J386*, J400, J408, J409, J416, J427*, J439, J442*, K09, K12, K51, K55, K60. Marked entries had a physverify check in the script (energy conservation, an order study or a manufactured solution) that also failed, but the defect was first seen and explained by the script's own comparison.

**Reading, then a run** (12): K15, K16 (2), K17 (2), K18, K20, K21, K22, K26, K27, K28.

## What the new `physverify scan` recovers without any script

`physverify scan` (added 2026-10-23) reads a repository's source and runs nothing. On the tested commits it recovers 18 of the 74 defects with no adapter (the Phase 1 additions are listed in [RESCAN_2026-10.md](RESCAN_2026-10.md)):

| ID | Found by `scan` | Stage |
|---|---|---|
| F09 | the three order labels: RK32 and ARK343ERK below their stated order, and the ARK548 embedded weights below their stated `orderEmbedded` (tables inherited from base classes and built element by element) | tables (3 defects) |
| E09 | Tsit5 error weights summing to 0.97, read from the keywords of a `ButcherTableau(...)` call | tables |
| J042 | `heun` (stage time), `rk38` (a stage missing), `bs` (weights): read from the stages written as code and compared with the docstring tables | tables (3 defects) |
| H19 | `dx = W/(N-1)` next to `linspace(0, W, N+1)` | grid |
| K26 | `dx = extent/N` next to `linspace(-extent/2, extent/2, N)` in another file | grid (a NOTE, because the files differ) |

It also finds the RK53 typo reported to F09 in a follow-up (row 2 of A sums to 3/13 but c[2] = 3/16). It cannot recover anything in the "script's reference" group by design. The rescan of all cloned repositories, at the tested and at the latest commit, is in [RESCAN_2026-10.md](RESCAN_2026-10.md): it found 7 new defects, each confirmed by a run (three stepper bugs in E09, a weight order in J042's n-body examples, and grid spacings in J029, J298 and J415).

## How this was classified

From each report's text and the script that produced it (`physverify_private/corpus/adapters/`, not published): which line of the script first showed the failure, and whether that line was a physverify check that needs no answer, or a comparison with an answer someone wrote. Done by the author with an AI assistant on 2026-10-23, not by an independent reader.
