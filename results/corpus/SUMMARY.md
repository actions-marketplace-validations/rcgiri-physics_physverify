# physverify on other people's code: first four batches

Status: development batches (October 2026), run before freezing the tool. They show what physverify finds on public code and what it cannot test yet; they are not the final study described in the plan (100 or more tested repositories, analysis plan written down first).

Repositories are identified here by an ID and the kind of code, not by name: the authors are told about a finding before it is published with their name. Per-repository records (URL, commit, adapter, every check result) are kept and can be shared on request.

The testing and the write-ups were done with help from an AI assistant (Claude Code). Every finding below was reproduced by running the code, and checked by hand against the code and, where relevant, the literature before being called a bug.

## How the repositories were chosen

Public GitHub repositories of Python physics code, drawn at random with a recorded seed, one or two per physics topic so that no single kind of code dominates. Batch 1 is a plain random sample; later batches favour recently active repositories, whose authors are more likely to answer, and are kept separate from batch 1 in any rate. The exact search rules are in the per-repository records.

## How each repository was tested

1. Cloned on the host at a fixed commit, with Git hooks, symlinks and LFS downloads turned off. No code from the repository ran on the host.
2. Run inside a locked-down container (`sandbox/`): no network, the repository mounted read-only, an unprivileged user, 2 CPUs, 2 GB of memory, a time limit. Extra packages were installed as pre-built wheels only, in a separate step.
3. A short adapter per repository, written from the physics (the equations, the paper, the README's claims), not from the code: manufactured solutions and convergence orders, exact cases, conserved quantities, Butcher order conditions, statistical checks for Monte Carlo codes.
4. Every FAIL was adjudicated before being counted, with one label: confirmed bug, ambiguous specification, adapter error, documented limitation, or inconclusive.

## Funnel

| | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Total |
|---|---|---|---|---|---|
| Drawn and cloned | 9 | 11 | 10 | 10 | 40 |
| Out of scope (neural networks, apps, analysis-only, games, toys, data structures) | 2 | 5 | 3 | 5 | 15 |
| Needs hardware the author does not have (NVIDIA CUDA 12+) | 0 | 1 | 0 | 0 | 1 |
| Testable but not tested yet (heavy set-up or dependencies) | 0 | 1 | 2 | 1 | 4 |
| Tested | 7 | 4 | 5 | 4 | 20 |
| Repositories with a confirmed bug | 3 | 1 | 1 | 1 | 6 |
| Confirmed bugs | 4 | 1 | 3 | 1 | 9 |

About half of the drawn repositories (20 of 40) could be tested. How often real code cannot be tested is itself a result: most of the rest are not numerical solvers.

## Results per tested repository

| ID | Kind of code | Checks | Result |
|---|---|---|---|
| D01 | Double pendulum on a cart (optimal control) | 2 | Clean: matches an independent Lagrangian to 1e-15 |
| D02 | Exact discretisation of the harmonic oscillator | 3 | Clean: exact to 3e-12, as claimed |
| D03 | Fourier-series solution of the heat equation (notebook) | 5 | **1 bug**: crashes on NumPy 2 (`np.NaN` removed); the mathematics is right (1e-7 against finite differences) |
| D04 | 2D Ising model, thesis code | 8 | **1 bug**: the measured energy counts the magnetic-field term twice; sampling is right; thesis results unaffected (all runs at h = 0) |
| D05 | Lorenz system (SciPy) | 5 | Clean |
| D06 | Sun-Earth Lagrange points (game) | 5 | Clean; 2 notes (fixed-Sun model; Gaussian G next to a 2π orbital speed) |
| D08 | Small RK4 library | 4 | **2 bugs**: backward integration is first order for time-dependent equations; the loop can take one step past the end time |
| E01 | Double pendulum (game) | 3 | Clean |
| E05 | Molecular dynamics engine (Taichi) | 3 | Clean: forces to 1e-14, energy error order 2.00, momentum to 6e-15 |
| E09 | Runge-Kutta tables in a research solver | 47 | **1 bug**: the Tsit5 error-estimate weights sum to 0.97 instead of 0 (reported to the authors) |
| E10 | Schrödinger time evolution (C++ extension) | 4 | Clean: first order as documented, exact for commuting Hamiltonians, unitary to 3e-13 |
| F01 | Thin-film flow, finite volume | 4 | Clean: exact for a uniform gap, order 2 otherwise |
| F02 | Finite-volume operators for ocean models (JAX) | 7 | Clean where testable: six time steppers at their stated order; the elliptic solver needs a package that has no wheel |
| F04 | Lattice Boltzmann permeability | 4 | Clean: plane Poiseuille at order 2; the README's claim that TRT is independent of τ holds to 1e-10 |
| F08 | Schrödinger-Poisson (JAX) | 3 | No bug; 1 note: the time per step comes from a fixed 1000-point sum, accurate to 3e-6 |
| F09 | Runge-Kutta and collocation coefficients library | 93 | **3 bugs**: three order labels one higher than the coefficients satisfy |
| G04 | Flux-reconstruction operators | 20 | Clean |
| G07 | Particle-in-cell plasma code (JAX) | 5 | No bug called; 1 question for the authors: the implicit scheme does not keep Gauss's law (33% after 60 steps), and the README claims charge conservation only for the explicit scheme |
| G08 | Quantum oscillator and cyclotron (CLI) | 11 | Clean |
| G10 | 2D wave propagation, pseudo-spectral | 14 | **1 bug** (minor): the Fourier derivative crashes for an odd number of grid points; exact for even ones |

261 checks were run in the final versions of the adapters.

## Mistakes on our side

The adapters made mistakes too, and they are counted, not hidden. Before adjudication, about 15 FAILs came from the adapters, not from the code, for example: a reference that used 4π² where the code used the Gaussian G; an integrator check with atoms placed so that a pair crossed the potential cutoff; a newer CODATA proton mass than the one the code states; reading past the end of a padded array; a fixed-point solver that diverged; steps too coarse to show the asymptotic order. Each was found by checking the FAIL before reporting it. No false alarm reached an issue draft.

## What physverify gained from this

Each lesson is a test in `tests/test_corpus_lessons.py`:

- `physverify.butcher`: the order of a Runge-Kutta table from the rooted-tree order conditions. Exact, and needs no test problem (E09, F09).
- `studies.time_grid_check` (a run must end at `t_end` after exactly n steps) and `studies.backward_mms_study` (D08).
- `studies.size_sweep_check`: run at odd and even sizes (G10).
- Hints in `check_order`: steps too coarse, errors not monotone, an error that does not change with the step (D01, F09, E05).
- `physverify.constants`: literals close to, but not equal to, a physical constant, with both CODATA 2018 and 2022 values (D06, G08).
- `loaders.load_definitions_from_path`: load only the functions of a script that runs a simulation at import, including notebook cells, with stubs for missing imports (D03, D04, F08).
- A new seeded Ising bug from D04 (`field_counted_twice`); the benchmark now has 21, all caught.
- A small benchmark of seeded method bugs from D08, E09, F09 and G10, each with a bug-free control ([../method_bugs.md](../method_bugs.md)): all 5 caught, 5 controls pass.
- Sandbox fixes: package versions pinned against the image, LFS files left as pointers, a shared wheel cache, path checks.

## What could not be tested, and why

Neural-network and physics-informed-network solvers (no deterministic method to check), apps and games where the physics sits inside a drawing loop, analysis-only toolkits, GPU-only code (CUDA), and packages whose dependencies are not published as wheels. Testing more of these would need new kinds of checks, not just more adapters.
