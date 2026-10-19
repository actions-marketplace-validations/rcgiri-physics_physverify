# Stage A: audit of my own physics projects

Date: 2026-10-19. physverify at commit `0297ffe` plus the uncommitted adapters `lorenz.py`, `three_body.py`, `projectile_v1.py` (to be committed with this report). SciPy 1.18.1, NumPy 2.5.4, Python 3.14, in a separate virtual environment; SciPy is not a physverify dependency.

Reproduce: `PYTHONPATH=src python scripts/audit_projects.py --jsonl results/own_work/results.jsonl`. Machine-readable results, one line per check: [results.jsonl](results.jsonl). All four project repos had a clean `git status` after the run; nothing was written into them.

Scope: 4 Python physics projects. This is not "all my computational physics work"; see the out-of-scope list below.

| Project (commit) | Testable | Checks run | Results | Findings by label | Detail |
|---|---|---|---|---|---|
| [projectile-simulation](https://github.com/rcgiri-physics/projectile-simulation) (`66e3251`) | yes: v2 fully, v1 positions only | 27 (v2) + 4 (v1) | v2: all pass. v1: positions order 1 as designed; range error does not converge smoothly | 1 confirmed bug (v2 range, already fixed and committed); 1 limitation (v1 range); 1 ambiguous spec (drag coefficient in README) | [projectile.md](projectile.md) |
| [double-pendulum-simulation](https://github.com/rcgiri-physics/double-pendulum-simulation) (`405870b`) | yes | 6 + 2 scripted studies | all pass | 1 confirmed (README Lyapunov value is a short-window estimate) | [double_pendulum.md](double_pendulum.md) |
| [lorenz-attractor-simulation](https://github.com/rcgiri-physics/lorenz-attractor-simulation) (`93ac915`) | yes | 7 + 1 scripted study | all pass | 1 confirmed, minor (Lyapunov script uses SciPy's default rtol = 1e-3) | [lorenz.md](lorenz.md) |
| [three-body-simulation](https://github.com/rcgiri-physics/three-body-simulation) (`2262a15`) | yes | 14 | 12 pass, 2 fail | 1 confirmed bug (Verlet driver stops one step early); 1 ambiguous spec (energy not softened) | [three_body.md](three_body.md) |
| discharge_tube | no | 0 | not testable: physics is inside two HTML/JS pages, tied to the animation loop, uses `Math.random` (12 calls) | none | - |

Labels: 1 confirmed bug, 2 ambiguous specification, 3 adapter or tool error, 4 documented limitation, 5 inconclusive.

Totals over the four code projects: 58 checks; 55 passed or exact, 3 failed: TB-1 (confirmed bug), TB-2 (ambiguous specification) and P-v1 (limitation of a first-order baseline). The v2 range bug (confirmed, found and fixed earlier in Phase 1) passes now and is counted once as a finding. No failure was an adapter or tool error. Two further confirmed findings (L-1, DP-1) came from re-running the projects' own Lyapunov scripts, not from a physverify check.

## Adapter or tool errors met during the audit

None were left in the results, but one was caught while writing an adapter: the first three-body reference used unsoftened gravity, which would have flagged the code for following its own documented softening (eps = 1e-4). The reference now uses the softening that docs/theory.md describes. This is the kind of adapter mistake the plan warns about; it is recorded so the minutes-per-flag count is honest.

## Not done in Stage A

- TB-1, TB-2, L-1 and DP-1 were fixed later on 2026-10-19 as separate commits in each project's repo (three-body `73faf33`, `b83d173`; lorenz `5d676ff`; double pendulum `314fa08`); not pushed. results.jsonl was regenerated after the fixes. Manuscript claims M-2 and M-3 are not edited.
- Figure-eight period (about 6.3259) was not used as a reference because the literature value was not checked here.
- double-pendulum `poincare_section.py` and `visualize_chaos.py`, three-body `run_sensitivity_sweep.py` and the animation scripts were read but not run: they produce plots, not numbers that can be checked against a known value.
