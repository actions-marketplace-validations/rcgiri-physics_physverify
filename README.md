# physverify

[![tests](https://github.com/rcgiri-physics/physverify/actions/workflows/ci.yml/badge.svg)](https://github.com/rcgiri-physics/physverify/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/physverify)](https://pypi.org/project/physverify/) [![Python](https://img.shields.io/pypi/pyversions/physverify)](https://pypi.org/project/physverify/) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23534512.svg)](https://doi.org/10.5281/zenodo.23534512) [![Docs](https://img.shields.io/badge/docs-site-blue)](https://rcgiri-physics.github.io/physverify/)

**Checks that a simulation solves the equations it claims, at the order of accuracy it claims, not just that it runs.**

Scope: numerical solutions of ODEs and PDEs (time integration, convergence, conservation), plus a few Monte Carlo checks. It needs only NumPy. Early version: nobody besides the author has used it yet, so feedback is very welcome.

```bash
pip install physverify
physverify demo
```

The demo checks a correct solver (all checks pass), then the same solver with the damping 10% too large (all fail):

![Error against step size: the correct solver follows the slope-2 line, the broken one levels off](https://raw.githubusercontent.com/rcgiri-physics/physverify/main/docs/images/convergence.svg)

## Use it on your own code

- **An ODE solver:** `physverify init verify_solver.py --solver mysolver --order 4` writes a spec; fill in the equations (from the physics, not from your code) and run `physverify run verify_solver.py`.
- **A Runge-Kutta table:** `check_tableau(A, b, c, claimed=3)` from `physverify.butcher` checks its order, stage order and stability from the coefficients alone.
- **Errors you already have:** `check_order(hs, errors, expected=2)` gives PASS, FAIL or INCONCLUSIVE with a reason.
- **On every push:** `uses: rcgiri-physics/physverify@v0.4.1` in GitHub Actions, or `pytest my_spec.py`.

[Getting started](https://rcgiri-physics.github.io/physverify/getting-started/) · [Recipes](https://rcgiri-physics.github.io/physverify/recipes/) · [What a PASS means](https://rcgiri-physics.github.io/physverify/assumptions/) · [API](https://rcgiri-physics.github.io/physverify/api/)

## Does it catch bugs?

Of 37 bugs seeded into five small solvers, it flagged 35 (plain "compare with one answer" tests: 27), with no false alarms. The bugs and checks were written by the same person, so this shows the tool works as designed, not how it does on other people's code. On public physics repositories it found real bugs, for example Runge-Kutta tables with a wrong order label; the counts are not a bug rate. Details: [results](https://rcgiri-physics.github.io/physverify/results/), and [results/README.md](https://github.com/rcgiri-physics/physverify/blob/main/results/README.md) to regenerate every table.

## Limits

Works best for ODEs; PDEs only in 1D so far. Your code needs a way to add a source term, or a small wrapper that can itself be wrong. A PASS means these checks found nothing wrong; it does not prove the simulation correct.

## Contributing, citing, licence

Help is welcome, especially trying it on your own solver: see [CONTRIBUTING.md](https://github.com/rcgiri-physics/physverify/blob/main/CONTRIBUTING.md). To cite, use [doi:10.5281/zenodo.23534512](https://doi.org/10.5281/zenodo.23534512) or [CITATION.cff](https://github.com/rcgiri-physics/physverify/blob/main/CITATION.cff). Changes: [CHANGELOG.md](https://github.com/rcgiri-physics/physverify/blob/main/CHANGELOG.md); plans: [ROADMAP.md](https://github.com/rcgiri-physics/physverify/blob/main/ROADMAP.md). MIT licence, copyright (c) 2026 Ram Chandra Giri.
