# physverify

**A tool that checks whether a physics simulation is solving the right equations correctly, not just running without errors.**

Status: early version (0.1.0). Nobody besides the author has used it yet, so feedback is very welcome.

## The problem it addresses

A simulation can run, produce nice plots and still be wrong: a minus sign in the wrong place, a factor of 2 missing, a time step that is off by one. Ordinary tests often miss these, because nobody knows the "right answer" for a real simulation to compare against.

## How it works, in plain words

physverify uses a few standard ideas from numerical analysis:

1. **Make up an answer, then check the code finds it.** Pick a smooth function, work out what extra push (a "source term") would make it an exact solution, give that push to your code, and see if your code reproduces the function. This is called the *Method of Manufactured Solutions*.
2. **Check the error shrinks at the right speed.** If your method is supposed to be 4th order, halving the time step should make the error about 16 times smaller. If it only gets 2 times smaller, something is wrong, even if the error looked small.
3. **Check conserved quantities.** Energy, mass or momentum should stay constant (or drift in a predictable way).
4. **Check known special cases.** For example, a projectile with no air resistance has a range you can write down by hand.
5. **Exact "patch" tests.** Some solutions should be reproduced to computer precision. This catches small bugs that the other checks let through.

Each check reports **PASS**, **FAIL**, **EXACT** or **INCONCLUSIVE**.

There is also a separate set of checks for random (Monte Carlo) simulations, using the 2D Ising model as the example.

## Does it actually catch bugs?

To test it, 37 bugs were added one at a time to five small solvers (projectile, double pendulum, planet orbit, heat equation, shock tube):

- **35 of 37** bugs were caught. Plain "compare with one answer" tests caught 27.
- **0 false alarms** on the bug-free versions.
- The 2 missed bugs are explained in the [technical details](https://github.com/rcgiri-physics/physverify/blob/main/docs/technical.md).

For the Monte Carlo checks, all 21 seeded bugs were caught with no false alarms.

The bugs and the checks were written by the same person, so these numbers show the tool works as designed. They are not a promise about bugs in other people's code.

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

Other ways to run it:

```bash
physverify run my_spec.py --html report.html   # a web page with convergence plots
physverify run my_spec.py --json -             # machine-readable output
pytest my_spec.py                              # each check becomes a pytest test
```

## What it can and cannot do

- Works best for ordinary differential equations (orbits, pendulums, projectiles).
- Partial differential equations: only 1D examples so far (heat equation, shock tube).
- Your code needs a way to accept an extra source term, or a small wrapper ("adapter") around it. The wrapper can itself contain mistakes.
- Passing all checks does not prove the code is correct, only that these tests found nothing wrong.

## More

- [results/own_work/SUMMARY.md](https://github.com/rcgiri-physics/physverify/blob/main/results/own_work/SUMMARY.md): results on four of the author's own public physics projects (two real bugs found and fixed).
- [docs/technical.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/technical.md): full details, benchmark tables, limits and related work.
- [docs/patch.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/patch.md): what the exact "patch" checks assume.
- [docs/ising.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/ising.md): checks for Monte Carlo codes.
- [docs/agent.md](https://github.com/rcgiri-physics/physverify/blob/main/docs/agent.md): using it with an AI coding assistant.
- [CHANGELOG.md](https://github.com/rcgiri-physics/physverify/blob/main/CHANGELOG.md)

Run the project's own tests with `pip install -e .[dev]` then `python -m pytest -q` (about 1.5 minutes).

## Licence

MIT. Copyright (c) 2026 Ram Chandra Giri.
