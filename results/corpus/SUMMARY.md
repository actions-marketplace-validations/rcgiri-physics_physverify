# physverify on other people's code: first six batches

Status: development batches (October 2026), run before freezing the tool. They show what physverify finds on public code and what it cannot test yet; they are not the final study described in the plan (100 or more tested repositories, analysis plan written down first).

Repositories are identified here by an ID and the kind of code, not by name: the authors are told about a finding before it is published with their name. Per-repository records (URL, commit, adapter, every check result) are kept and can be shared on request.

The testing and the write-ups were done with help from an AI assistant (Claude Code). Every finding below was reproduced by running the code, and checked by hand against the code and, where relevant, the literature before being called a bug.

## How the repositories were chosen

Public GitHub repositories of Python physics code, drawn at random with a recorded seed, one or two per physics topic so that no single kind of code dominates. Batch 1 is a plain random sample; later batches favour recently active repositories, whose authors are more likely to answer, and are kept separate from batch 1 in any rate. The exact search rules are in the per-repository records.

Batch 5 used a different, fixed rule: the 60 newest small repositories (created 2026-09-09 to 2026-10-19, under 3 MB) whose README says the work is complete and does not say it is in progress, from 60 physics topic searches, with machine-learning and dashboard projects left out. It is not random. Its counts describe those 60 repositories only and are not a rate for public physics code in general; nor is any other batch's.

Batch 6 was chosen to be quick to test, to try new helpers in the package: the 20 newest small repositories (created 2026-10-17 to 2026-10-20) from 40 physics topic searches with at most 8 Python files that import nothing beyond NumPy, SciPy, Matplotlib and the standard library. It had no README filter. Small, new and single-purpose code is not a fair sample of anything, so its counts say nothing about a bug rate either.

## How each repository was tested

1. Cloned on the host at a fixed commit, with Git hooks, symlinks and LFS downloads turned off. No code from the repository ran on the host.
2. Run inside a locked-down container (`sandbox/`): no network, the repository mounted read-only, an unprivileged user, 2 CPUs, 2 GB of memory, a time limit. Extra packages were installed as pre-built wheels only, in a separate step.
3. A short adapter per repository, written from the physics (the equations, the paper, the README's claims), not from the code: manufactured solutions and convergence orders, exact cases, conserved quantities, Butcher order conditions, statistical checks for Monte Carlo codes.
4. Every FAIL was adjudicated before being counted, with one label: confirmed bug, ambiguous specification, adapter error, documented limitation, or inconclusive.

## Funnel

| | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Batch 5 | Batch 6 | Total |
|---|---|---|---|---|---|---|---|
| Drawn and cloned | 9 | 11 | 10 | 10 | 60 | 20 | 120 |
| Out of scope (neural networks, apps, analysis-only, games, toys, data structures, finance, statistics, unfinished) | 2 | 5 | 3 | 5 | 27 | 4 | 46 |
| Needs hardware the author does not have (NVIDIA CUDA 12+) | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| Testable but not tested (heavy set-up, dependencies, or input files not in the repository) | 0 | 1 | 2 | 1 | 1 | 0 | 5 |
| Tested | 7 | 4 | 5 | 4 | 32 | 16 | 68 |
| Repositories with a confirmed bug | 3 | 1 | 1 | 1 | 5 | 1 | 12 |
| Confirmed bugs | 4 | 1 | 3 | 1 | 6 | 1 | 16 |

In batches 1 to 4, half of the drawn repositories (20 of 40) could be tested; in batch 5, 32 of 60. How often real code cannot be tested is itself a result: most of the rest are not numerical solvers. In batch 5 two of the 32 tested repositories hold the same student project (H47, H48), so the 6 bugs are in 4 distinct codes; one tested repository (H29) was tested only in part, because compiling its JAX solver on finer grids was too slow for the sandbox.

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
| H01 | Heat equation, FTCS / backward Euler / Crank-Nicolson | 12 | **3 bugs**: one time step too many; the source is not multiplied by dt; with CN and BE the Dirichlet values are written after the solve instead of inside the linear system (27 times the textbook CN error, no convergence) |
| H03 | Double pendulum (SciPy) | 3 | Clean: matches an independent Lagrangian to 4e-15 |
| H05 | Quantum harmonic oscillator, finite differences | 6 | Clean: eigenvalues at order 2.00 |
| H06 | 2D Ising model, Metropolis | 3 | Clean: 4x4 exact enumeration within 0.4 standard errors |
| H08 | Q4 plane-elasticity finite elements | 3 | Clean: patch test exact on a distorted mesh |
| H11 | Ising model, VQE and adiabatic evolution (Qiskit) | 5 | Clean: Hamiltonians exact, Trotter path order 2, variational bound kept |
| H13 | 3D frame solver for bridge animation | 3 | Clean: beam theory exact; frequencies converge |
| H14 | Quantum-group spin-chain memory bound | 2 | Clean: recurrence equals the direct algebra projection to 2e-16 |
| H15 | Bound-state return on a lattice | 4 | Clean: matches a direct real-space simulation to 1e-10 |
| H16 | Numerical-methods coursework | 5 | Clean (one exercise blows up before its first output point: inconclusive) |
| H17 | Sine-Gordon wave equation, explicit | 4 | Clean: order 2.02 as documented; 1 note: the energy diagnostic is first order |
| H19 | Infinite square well, finite differences | 5 | **1 bug**: grid spacing W/(N-1) for N-1 interior points; energies 2% low and first order |
| H20 | Balance control with delayed feedback | 2 | Clean: first order as expected for its Euler scheme |
| H21 | Lattice random walk with exclusion | 3 | Clean: diffusion constant and event statistics exact within noise |
| H22 | Transverse-field Ising chain, entanglement | 4 | Clean: ground energy equals the free-fermion solution to 1e-14 |
| H23 | Shallow water on the sphere | 2 | Clean: the README's own error table reproduced exactly |
| H25 | Groundwater transport (FiPy notebook) | 2 | No bug; 1 note: the first-order scheme puts the peak 7.5% low, and the notebook's refinement estimate (3.4%) is about half the true error |
| H27 | N-link pendulum (web app) | 2 | Clean: energy kept to 3e-11 |
| H29 | Meshfree RBF-FD PDE solvers (JAX) | 1 | Partly tested: the README's Poisson example is reproduced to 3e-13 |
| H40 | Wave packet at a square barrier | 5 | Clean: transmission exact, CN order 2 |
| H41 | Forest-fire percolation | 2 | Clean |
| H43 | HHL quantum linear solver (Qiskit) | 2 | Clean: recovers the matrix inverse to 3e-15 |
| H44 | Billiards physics (game) | 4 | Clean: friction integrator order 2, collisions exact |
| H47, H48 | Stepped-domain 2D heat conduction (same code in two repositories) | 2 | **1 bug**: boundary nodes are given full cells and full faces, so 7% too much heat enters at dx = 0.125 and convergence is slower than first order |
| H52 | 1D heat conduction with ablation | 4 | Clean: order 2 in space and time, exact energy balance (the ablation front was not tested) |
| H54 | 2D heat diffusion library | 4 | **1 bug**: the insulated boundary loses 8.5% of the heat and is first order; the repository's own test checks one step |
| H55 | Benchmark scripts (percolation, Ising, three bodies) | 5 | Clean |
| H56 | Plasma lensing of radio bursts | 4 | Clean: images, caustics and Fermat's principle exact |
| H60 | Tight-binding bands and Chern numbers | 4 | Clean: Haldane gaps and Chern numbers exact |
| H62 | Fisher information of a lossy chain | 5 | Clean: photon flux conserved to 4e-16 |
| H64 | Classical Heisenberg Monte Carlo (C) | 5 | Clean: exact spin-chain results within 0.3% |

| I01 | Two-body orbit, velocity Verlet | 4 | Clean: order 2, angular momentum to 1e-14 |
| I02 | Simple pendulum, RK4 and exact period | 3 | Clean |
| I03 | Projectile with quadratic drag | 3 | Clean: first order as expected for its Euler scheme |
| I04 | 2D Euler equations, four schemes | 5 | Clean; 1 documentation note: the README calls Lax-Friedrichs unconditionally stable, and it blows up at CFL 1.3 |
| I05 | 2D N-body, velocity Verlet | 2 | Clean: momentum to 8e-16, energy order 2 |
| I06 | Double pendulum with joint friction | 3 | Clean: matches the Lagrangian reference to 7e-15, friction power balance exact |
| I09 | 2D lattice random walk (animated) | 3 | Clean: unit steps, mean squared displacement n (z = 0.4) |
| I11 | PN junction, depletion model and Poisson solver | 3 | Clean: numerical potential order 2 |
| I12 | Two-body orbit toolkit | 6 | **1 bug** (minor): the Kepler solver does not converge for some negative mean anomalies at high eccentricity |
| I13 | Orbit propagation with J2 and a Kalman filter | 3 | Clean: the filter's Jacobian matches finite differences to 2e-9 |
| I14 | 2D heat equation, explicit | 3 | Clean: linear fields and discrete modes exact |
| I15 | Three-body problem, Forest-Ruth integrator | 4 | Clean: order 4, energy error order 4 |
| I16 | Laplace equation, Jacobi relaxation | 2 | No bug; 1 note: stopping at a change of 1e-6 per sweep leaves an error of 2e-3 at N = 100 |
| I17 | Orbit propagator, mission planner, GNSS positioning | 6 | Clean |
| I18 | 1D heat conduction, 5-node example | 1 | Clean |
| I20 | Solar-system N-body, Beeman | 4 | Clean: Beeman order 2, Euler and Euler-Cromer order 1 |

261 checks were run in the final versions of the adapters of batches 1 to 4, 117 in batch 5 and 55 in batch 6.

## Mistakes on our side

The adapters made mistakes too, and they are counted, not hidden. Before adjudication, about 15 FAILs came from the adapters, not from the code, for example: a reference that used 4π² where the code used the Gaussian G; an integrator check with atoms placed so that a pair crossed the potential cutoff; a newer CODATA proton mass than the one the code states; reading past the end of a padded array; a fixed-point solver that diverged; steps too coarse to show the asymptotic order. Each was found by checking the FAIL before reporting it. No false alarm reached an issue draft.

Batch 5 added 7 adapter mistakes, also caught before reporting: a sign convention of the course a Thomas solver was written for; a convergence point placed at a re-entrant corner, where the solution is singular; a projection onto the commutant of a symmetry instead of the symmetry algebra; a percolation test that assumed top-to-bottom spanning where the code documents all four edges; two expected orders that were too low (the codes converged faster); and an unweighted error norm where the README's numbers use an area-weighted one. Batch 6 added 6 more, all found before reporting: two tolerances or orders set without a reason (a Verlet energy band, Euler-Cromer measured after a whole orbit, where its error cancels), two order studies on steps too coarse (the pre-asymptotic hint said so), a probe placed so close to a junction that the field looked like a jump, and an issue draft whose first command-line example did not fail; the failing inputs were measured and the draft corrected before posting. A borrowed example helper in H29 also placed ghost nodes a fixed distance outside the boundary, which made finer grids singular; that is a property of the example, not of the solver, and is not counted as a bug.

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
- From batch 5: `studies.balance_check`, an exact budget at every resolution (total heat with insulated walls, heat from a known source), which says when a mismatch shrinks with resolution: a scheme can converge and still not conserve (H54, H01, H47).
- Four more seeded method bugs from batch 5, each with a control: Dirichlet values written after the solve (H01), an insulated wall made by copying the neighbour (H54), a source without dt (H01), a grid spacing off by one interval (H19). The table now has 9 bugs, all caught, and 9 controls that pass.
- Before batch 6: `physverify.references` (exact solutions written by hand in several adapters, each tested against an independent computation), `loaders.stub_modules` (stand-ins for unused imports, including names and decorators) and `loaders.run_script` (run a whole script with plotting off). In batch 6 they replaced hand-written references and stubs in 6 of the 16 adapters.
- Sandbox fixes from batch 5: a step stopped by the time limit no longer leaves its container running to race the next install; installs have their own time limit (`PHYSVERIFY_DEPS_TIME_LIMIT`, default 40 min); wheels that bundle their own OpenMP runtime (qiskit-aer) are preloaded automatically.

## What could not be tested, and why

Neural-network and physics-informed-network solvers (no deterministic method to check), code that needs input files kept outside the repository (one Colab script read a ZIP and a spreadsheet from the author's Google Drive), apps and games where the physics sits inside a drawing loop, analysis-only toolkits, GPU-only code (CUDA), and packages whose dependencies are not published as wheels. Testing more of these would need new kinds of checks, not just more adapters.
