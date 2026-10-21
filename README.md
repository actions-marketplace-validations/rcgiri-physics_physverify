# physverify

[![PyPI](https://img.shields.io/pypi/v/physverify)](https://pypi.org/project/physverify/) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23534512.svg)](https://doi.org/10.5281/zenodo.23534512) [![Docs](https://img.shields.io/badge/docs-site-blue)](https://rcgiri-physics.github.io/physverify/)

**A tool that checks whether a physics simulation is solving the right equations correctly, not just running without errors.**

Status: early version (0.4.1). Documentation with many examples: https://rcgiri-physics.github.io/physverify/. It has been tried on 250 public physics repositories (see below), but nobody besides the author has used it yet, so feedback is very welcome.

## Who it is for

- Students and researchers who wrote their own solver (orbits, pendulums, heat flow, shock tubes, Monte Carlo) and want more confidence than "the plot looks right".
- Maintainers of numerical libraries who want their methods checked on every push, for example that each Runge-Kutta table really has the order its name says.
- Anyone reviewing someone else's simulation code.

You do not need to know numerical analysis to read the results: each check says in plain words what it measured and what it expected.

## The problem it addresses

A simulation can run, produce nice plots and still be wrong: a minus sign in the wrong place, a factor of 2 missing, a time step that is off by one. Ordinary tests often miss these, because nobody knows the "right answer" for a real simulation to compare against.

## How it works, in plain words

physverify uses a few standard ideas from numerical analysis:

1. **Make up an answer, then check the code finds it.** Pick a smooth function, work out what extra push (a "source term") would make it an exact solution, give that push to your code, and see if your code reproduces the function. This is called the *Method of Manufactured Solutions*.
2. **Check the error shrinks at the right speed.** If your method is supposed to be 4th order, halving the time step should make the error about 16 times smaller. If it only gets 2 times smaller, something is wrong, even if the error looked small.
3. **Check conserved quantities and budgets.** Energy, mass or momentum should stay constant (or drift in a predictable way), and heat added through a wall or a source should match what went in, exactly, on every grid.
4. **Check known special cases.** For example, a projectile with no air resistance has a range you can write down by hand.
5. **Exact "patch" tests.** Some solutions should be reproduced to computer precision. This catches small bugs that the other checks let through.
6. **Algebraic checks on the method itself.** For a Runge-Kutta method, whether the coefficients really have the order they claim can be settled exactly, with no test problem (the "order conditions").

Each check reports **PASS**, **FAIL**, **EXACT** or **INCONCLUSIVE** (or **SKIP** when an optional dependency is missing).

There is also a separate set of checks for random (Monte Carlo) simulations, using the 2D Ising model as the example.

### What a result looks like

```text
mms        PASS   midpoint damped oscillator: observed order 2.04 (expected 2)
reference  PASS   midpoint damped oscillator: observed order 2.01 (expected 2)
mms        PASS   midpoint damped oscillator (whole trajectory): observed order 2.02 (expected 2)
patch      EXACT  midpoint damped oscillator: reproduced to round-off (largest error 2.7e-15), as designed
4 of 4 checks passed
```

And for a Runge-Kutta table that claims order 3 (a real case from a public library):

```python
from physverify.butcher import check_tableau
check_tableau(A, b, c, claimed=3)
# FAIL: claims order 3 but satisfies the order conditions only up to 2 ...;
#       linear order 3 is higher than the order 2: a convergence test on y' = lambda*y alone would overstate the order
```

The second line explains why the library's own tests had not noticed: its test problem was the one kind of equation on which this method happens to look third order.

## Does it actually catch bugs?

To test it, 37 bugs were added one at a time to five small solvers (projectile, double pendulum, planet orbit, heat equation, shock tube):

- **35 of 37** bugs were caught. Plain "compare with one answer" tests caught 27.
- **0 false alarms** on the bug-free versions.
- The 2 missed bugs are explained in the [technical details](https://github.com/rcgiri-physics/physverify/blob/main/docs/technical.md).

For the Monte Carlo checks, all 21 seeded bugs were caught with no false alarms.

The bugs and the checks were written by the same person, so these numbers show the tool works as designed. They are not a promise about bugs in other people's code.

## Trying it on other people's code

To see what it does on code it was not written for, public Python physics repositories from GitHub were run in a locked-down container (October 2026): no network, the repository read-only, nothing from it run on the author's computer. 40 were drawn at random from topic searches (batches 1 to 4); another 60 were the newest small repositories whose README says the work is complete (batch 5), and 20 more were picked because they are quick to test (batch 6); batches 5 and 6 are not random. Batch 7 was a larger queue of 450 recently active small repositories from 61 topic searches, ordered by stars (not random either).

- **68 of the 120 could be tested.** Most of the others were not numerical solvers (neural networks, apps and games, analysis tools, finance), one needed a recent NVIDIA GPU, and a few need more set-up.
- **16 confirmed bugs in 12 of the 68.** For example: a measured energy that counts the magnetic-field term twice; backward time-stepping that is only first-order accurate; Runge-Kutta coefficient tables labelled with a higher order than they have; a spectral derivative that crashes for an odd number of grid points; boundary values applied after the linear solve instead of inside it; an insulated wall that leaks heat; a grid spacing off by one interval; a Kepler solver that fails for negative angles.
- **Batch 7: 182 of 450 tested, at least one confirmed defect in 41.** For example: a "Regge-Wheeler" ringdown code that uses the scalar-field potential; MHD shock jump ratios that break the Rankine-Hugoniot conditions; a reactor period for negative reactivity off by a factor of several thousand; a pressure solver that stops after one sweep; gravitational accelerations with the wrong sign; three files that do not parse. Some of the 41 are minor (a label, an optional viewer that crashes).
- **The rest had no confirmed bug.** Most passed every check that applied, often to 1e-13 or better.
- **Our own adapters were wrong about 28 times** before checking (a wrong constant, too-coarse steps, a wrong sign convention, and so on). Every FAIL was checked by hand before being called a bug, and these mistakes are recorded, not hidden.

These counts describe the repositories that were drawn; they are not a bug rate for physics code in general.

Each lesson became a new check or a clearer message in physverify. The testing and write-ups were done with help from an AI assistant; every number comes from running the code. Authors are told about a finding before their project is named, so the repositories are listed by ID: [results/corpus/SUMMARY.md](https://github.com/rcgiri-physics/physverify/blob/main/results/corpus/SUMMARY.md) (batches 1 to 6) and [results/corpus/BATCH7.md](https://github.com/rcgiri-physics/physverify/blob/main/results/corpus/BATCH7.md).

## Try it

You need Python 3.10 or newer.

```bash
pip install physverify
```

The example below lives in the repository, so clone it to follow along:

```bash
git clone https://github.com/rcgiri-physics/physverify.git
cd physverify
physverify run examples/verify_damped_oscillator.py
```

You should see a list of checks, all passing. Now open `examples/damped_oscillator.py`, change the damping by 10%, and run the same command again: the checks fail.

To check your own code you write a short "spec" file. It tells physverify two things: the equations your code is meant to solve (written independently of your code), and how to run your code. [examples/verify_damped_oscillator.py](https://github.com/rcgiri-physics/physverify/blob/main/examples/verify_damped_oscillator.py) is a complete example to copy.

To start a spec for your own ODE solver, let physverify write one:

```bash
physverify init verify_solver.py --solver mysolver --order 4
```

Then fill in the two places marked TODO: the equations, written from the physics, and a starting state.

Other ways to run it:

```bash
physverify run my_spec.py --html report.html   # a web page with convergence plots
physverify run my_spec.py --json -             # machine-readable output
pytest my_spec.py                              # each check becomes a pytest test
```

## Run it on every push

Add physverify to your GitHub Actions workflow. The job fails when a check fails, just like a broken unit test:

```yaml
      - uses: actions/checkout@v4
      - uses: rcgiri-physics/physverify@v0.4.1
        with:
          specs: tests/verify_*.py
          install: -e .
```

The results table appears on the run's summary page. [docs/ci.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/ci.md) covers the options, pre-commit and pytest.

## What's new in 0.4.0

- **Runge-Kutta tables:** besides the order, it now checks the "linear" order (what a test on y' = lambda*y measures), the stage order, A- and L-stability and stiff accuracy, and fails when the nodes `c` do not match the table.
- **Honest counts:** a check that cannot run because an optional package is missing now says SKIP instead of passing.
- **Time budget:** `physverify run --budget 60` stops a slow check from using up the whole run.
- **New helpers** for convergence studies that compare at the wrong time, for the coverage of error bars, and for ringdown frequencies; more exact reference solutions (`physverify references`).
- **`physverify smoke`:** a quick first pass that finds scripts that crash, hang on `input()` or produce NaNs.
- **Continuous integration:** a GitHub Action, `physverify init` to write a starter spec, and a pre-commit hook.

The full list is in [CHANGELOG.md](https://github.com/rcgiri-physics/physverify/blob/main/CHANGELOG.md).

## What it can and cannot do

- Works best for ordinary differential equations (orbits, pendulums, projectiles).
- Partial differential equations: only 1D examples so far (heat equation, shock tube).
- Your code needs a way to accept an extra source term, or a small wrapper ("adapter") around it. The wrapper can itself contain mistakes.
- Passing all checks does not prove the code is correct, only that these tests found nothing wrong.

## Questions

**Do I have to change my code?** Usually not. Most codes can be checked through a short spec file that calls them. Codes with no way to add a source term need a small wrapper; [ROADMAP.md](https://github.com/rcgiri-physics/physverify/blob/main/ROADMAP.md) describes plans to need fewer of them.

**How long does it take?** The checks run your code several times at different resolutions, so the time is mostly your own code's run time. The example above takes about two seconds.

**What does INCONCLUSIVE mean?** The errors were too small or too noisy to measure an order (often they are already at round-off). The message says which, and what to try.

**Can it run untrusted code safely?** physverify itself runs code on your computer like any Python program. For other people's code, use the locked-down container in [sandbox/](https://github.com/rcgiri-physics/physverify/blob/main/sandbox/README.md).

## What's next

[ROADMAP.md](https://github.com/rcgiri-physics/physverify/blob/main/ROADMAP.md): checking code without writing a wrapper, 2D and 3D heat-equation checks, IMEX Runge-Kutta pairs and a documentation website with many examples.

## More

- [results/corpus/SUMMARY.md](https://github.com/rcgiri-physics/physverify/blob/main/results/corpus/SUMMARY.md): the first 120 public repositories, what was tested and what was found; [BATCH7.md](https://github.com/rcgiri-physics/physverify/blob/main/results/corpus/BATCH7.md) for the next 450.
- [sandbox/README.md](https://github.com/rcgiri-physics/physverify/blob/main/sandbox/README.md): the locked-down container used to run other people's code.
- [results/own_work/SUMMARY.md](https://github.com/rcgiri-physics/physverify/blob/main/results/own_work/SUMMARY.md): results on four of the author's own public physics projects (two real bugs found and fixed).
- [docs/technical.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/technical.md): full details, benchmark tables, limits and related work.
- [docs/patch.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/patch.md): what the exact "patch" checks assume.
- [docs/ising.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/ising.md): checks for Monte Carlo codes.
- [docs/ci.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/ci.md): `physverify init`, the GitHub Action, pre-commit and pytest.
- [docs/agent.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/agent.md): using it with an AI coding assistant.
- [CHANGELOG.md](https://github.com/rcgiri-physics/physverify/blob/main/CHANGELOG.md)

Run the project's own tests with `pip install -e .[dev]` then `python -m pytest -q` (about 3 minutes).

## Citing

If physverify helps your work, please cite it. The DOI [10.5281/zenodo.23534512](https://doi.org/10.5281/zenodo.23534512) always points to the newest version, and each release has its own DOI on Zenodo. GitHub's "Cite this repository" button gives the same information from [CITATION.cff](https://github.com/rcgiri-physics/physverify/blob/main/CITATION.cff).

## Licence

MIT. Copyright (c) 2026 Ram Chandra Giri.
