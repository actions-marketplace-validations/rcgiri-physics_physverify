# L series: which repositories are deep-tested

Written 2026-11-05, before the remaining L repositories were labelled. The same rule is applied to every repository.
Repositories are excluded by label, never deleted from the queue, so the funnel (drawn, excluded by reason, tested)
can be reproduced. Labels follow batches 1 to 7.

| Label | Rule |
|---|---|
| Deep-testable | A numerical method that can be checked without the author's data: a stepper or solver with a stated order, a conserved quantity, an exact limit, or a Monte Carlo sampler with a small exact case. It must install from wheels in the sandbox and run within its time and memory limits. |
| Out of scope | Neural networks and physics-informed networks, apps, games, dashboards, visualisation-only code, analysis-only code, drivers for external programs, non-physics code. |
| Needs hardware | Runs only on a GPU (CUDA). |
| Testable but not tested | A checkable method, but it needs external data files, a package with no wheels or a compiled build, a set-up too heavy for the sandbox, or the repository is no longer available. |

How a label is decided:

- From the README, the file list and the dependency files only. No repository code is run to label it.
- When the label is unsure, the repository is labelled deep-testable and the doubt is written in the reason. The test
  session then settles it and records the outcome.
- A repository already tested keeps its recorded verdict (clean, N defects, out of scope, not deep-testable).

Counts are stated within this queue only. They are not a bug rate for physics code in general.
