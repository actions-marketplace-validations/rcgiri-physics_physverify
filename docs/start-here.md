# Start here

This page is for someone who has a physics simulation (their own, a student's, or one from GitHub) and wants to know whether it is right, but who does not use Python tools every day. It takes about ten minutes. If you would rather let an AI coding assistant do the steps, skip to [With an AI assistant](#with-an-ai-assistant).

## What physverify does, in one paragraph

A simulation can run, make a nice plot, and still be wrong: a sign flipped, a factor of 2 missing, a time step that makes it first order instead of fourth. physverify checks the things that must be true if the code solves the equations it claims to: that the error shrinks at the promised rate when the step is made smaller, that energy is kept when it should be, that a Runge-Kutta table really has its stated order. It cannot prove code is correct; a PASS says only that the tested properties hold ([What a PASS means](assumptions.md)).

## 1. Install Python and physverify

You need Python 3.10 or newer. Check with:

```bash
python --version
```

If that fails, install Python from [python.org](https://www.python.org/downloads/) (on Windows, tick "Add python.exe to PATH" in the installer), then open a new terminal.

Make a separate environment, so physverify does not change anything else on your computer:

=== "Windows (PowerShell)"

    ```bash
    python -m venv pv-env
    pv-env\Scripts\Activate.ps1
    pip install physverify
    ```

=== "macOS / Linux"

    ```bash
    python3 -m venv pv-env
    source pv-env/bin/activate
    pip install physverify
    ```

Each time you open a new terminal, run the `Activate` / `source` line again.

## 2. See it work (no files needed)

```bash
physverify demo
```

It checks a correct solver (every check passes) and a copy with one wrong number (every check fails). If you see both, the installation works.

## 3. Scan a project without writing anything

!!! note "Planned for 0.5.0"
    `physverify scan` is planned for the next release, 0.5.0. Until then it is only in the development version: `pip install git+https://github.com/rcgiri-physics/physverify`.

```bash
physverify scan path/to/the/project
```

`scan` only **reads** the code; it never runs it, so it is safe on code you downloaded. It looks for four things that were real bugs in public code:

| What | Example |
|---|---|
| **constants** close to, but not equal to, a physical constant | `g = 9.7`, `pi = 3.14` |
| **tables**: Runge-Kutta methods that do not have the order their name says, whether written as a table or as stages in code (`k2 = h*f(t + h/2, y + k1/2)`), or whose stages disagree with the table in their own docstring | a method called "order 3" that is only order 2 |
| **grid**: a spacing that does not match its grid | `x = linspace(0, L, N)` with `dx = L/N` (it is `L/(N-1)`) |
| **pairs**: functions that should undo each other | `cart_to_polar` and `polar_to_cart` |

Each line is a `WARN` (very likely a mistake) or a `NOTE` (worth one look). Nothing found does not mean the code is right; most bugs need step 4.

## 4. Check your own solver

For a solver that steps an ODE forward in time (pendulum, orbit, oscillator):

```bash
physverify init verify_solver.py --solver mysolver --order 4
```

This writes a file `verify_solver.py` with two places marked `TODO`:

1. **the equations**, written again from the physics (not copied from your code: if you copy, a mistake is copied too);
2. **a starting state**.

Then:

```bash
physverify run verify_solver.py
```

[Getting started](getting-started.md) explains the file line by line, and [Recipes](recipes.md) has ready-made versions for the heat equation, a Monte Carlo sampler and other kinds of code.

## 5. Running code you did not write

`physverify run` and `physverify smoke` **run** the code they check. For code from the internet, use the locked-down container in [`sandbox/`](https://github.com/rcgiri-physics/physverify/tree/main/sandbox) (needs Docker): no network, the code read-only, a time limit. `physverify scan` needs no container.

## With an AI assistant

If you use Claude Code, Cursor, Copilot or another assistant that can run commands, you can paste this prompt into it, in the folder of the project:

```text
Install physverify in a virtual environment and check this project with it. Until 0.5.0 is released, install
the development version, which has `physverify scan`: pip install git+https://github.com/rcgiri-physics/physverify
1. Run `physverify scan .` and explain each WARN and NOTE in plain words; say which you think are real.
2. Find the main solver. Write a spec with `physverify init`, filling in the equations from the physics
   (the README, the paper or the textbook), NOT from the solver's code. Tell me where you took them from.
3. Run `physverify run` on the spec and explain the result. If a check fails, first check the spec
   (units, sign conventions, the step counts) before blaming the solver, as docs/troubleshooting.md says.
4. Do not change the solver. Do not run code from the internet outside the sandbox.
Report what was tested and what was not.
```

[Using physverify with an AI assistant](agent.md) shows how to make the assistant re-run the checks after every edit, and the repository's [AGENTS.md](https://github.com/rcgiri-physics/physverify/blob/main/AGENTS.md) gives an assistant the rules it needs to work on physverify itself.

## Stuck?

[Troubleshooting](troubleshooting.md), or open a [question](https://github.com/rcgiri-physics/physverify/issues/new?template=question.md). No question is too basic.
