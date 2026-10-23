# Command line

```text
physverify run SPEC [SPEC ...]   run the checks in spec files (glob patterns are expanded)
physverify init [SPEC]           write a starter spec for a fixed-step ODE solver
physverify smoke PATH            compile and run each script; report crashes, hangs and NaNs
physverify references            list the exact references
physverify hook | mcp            for AI coding assistants (see that page)
```

## `physverify run`

```bash
physverify run "tests/**/verify_*.py"
physverify run my_spec.py --html report.html      # a page with convergence plots
physverify run my_spec.py --json results.json     # or --json - for stdout
physverify run my_spec.py --markdown summary.md   # appends a table (for $GITHUB_STEP_SUMMARY)
physverify run my_spec.py --quiet
```

Exit codes: 0 when no check fails (PASS, EXACT or SKIP), 1 when any check fails, is INCONCLUSIVE or raises, 2 when a spec cannot be loaded or a pattern matches nothing.

## SKIP and time budget

```python
--8<-- "docs/examples/skip_and_budget.py"
```

Output:

```text
--8<-- "docs/examples/output/skip_and_budget.txt"
```

### SKIP

Call `requires("package")` at the start of a check (or `raise SkipCheck(reason)`) when it needs an optional package. Without it, a check that quietly returned PASS when the package was missing would be counted as a pass.

### Time budget

`--budget SECONDS` on the command line, or `Check(..., budget_s=...)` for one check.

- Order studies stop adding finer resolutions when the next one would not finish inside the budget, fit what they have, and add "time budget: ran 3 of 5 resolutions" to the message.
- A check still running at twice its budget is reported INCONCLUSIVE, and the remaining checks run.
- Python cannot stop a running thread, so such a check keeps running in the background until the program exits; its result is discarded.

## `physverify scan`

!!! note "Planned for 0.5.0"
    `physverify scan` is planned for the next release, 0.5.0. Until then it is only in the development version: `pip install git+https://github.com/rcgiri-physics/physverify`.

```bash
physverify scan path/to/project
physverify scan path/to/project --only tables,grid --json scan.json
```

Reads every `.py` file with Python's `ast` module and **runs nothing**, so it is safe on code you have not read. Four stages, each from a kind of bug found in public code:

| Stage | Looks for | Level |
|---|---|---|
| `constants` | literals close to, but not equal to, a physical constant: within 10% for constants with units (`6.6e-11`), within 0.2% for pure numbers (`3.14`, `2.27`), and `g` only when assigned to a gravity name (`g = 9.7`); one line per constant and file | NOTE |
| `tables` | Runge-Kutta tables written as literals: the order the coefficients really have, row sums against `c`, error weights that must sum to 0, and the order a name, docstring or `order` attribute claims (`rk4`, `heun3`, `3rd order`, `def order(self): return 3`). Tables are read from assignments, from constructor keywords and dicts (`ButcherTableau(a=..., b=..., b_error=..., order=5)`), from classes that inherit them, and from `A = np.zeros((s, s))` filled by `A[i, :k] = [...]`. Also **stages written as code** (`k2 = h*f(t + h/2, y + k1/2)`): the table is read back from the calls, then checked the same way, against the stage times, and against a Butcher table drawn in the docstring | WARN when a claim, `c` or the docstring does not match, when a stage leaves out `h`, or when a combination of the stages sums to neither 1 nor 0; else NOTE |
| `grid` | a spacing `(b - a)/D` next to `linspace(a, b, M)` with `D` not equal to `M - 1`; compared by substituting random values, so `W/(N-1)` with `linspace(0, W, N+1)` is caught too. `D` must differ from `M - 1` by a constant, so an element length `L/n` next to a plotting grid of `100*n` points is not flagged | WARN in the same function, NOTE across functions or files |
| `pairs` | functions whose names say they undo each other (`x_to_y` / `y_to_x`, `s2z` / `z2s`), to check with `identities.check_roundtrip` | NOTE |

Exit code 1 if there is any WARN, 0 otherwise, 2 for a bad path or stage name. Files that do not parse are listed, not skipped silently. A clean scan means only that these patterns were not found. Stages are read only for explicit methods on one state variable: implicit methods and systems split into parts (`x` and `v` advanced side by side) are skipped, and no check of the physics is made.

## `physverify smoke`

```bash
physverify smoke path/to/project --timeout 60
```

Each script is compiled, then run in its own process with a time limit, stdin closed and plotting off. It reports scripts that do not parse, crash, wait for input or emit NaN/overflow warnings. It runs the code, so use it on trusted code or in the sandbox.

## pytest

With physverify installed, `pytest my_spec.py` turns each check into a pytest test (SKIP becomes a pytest skip). See [Continuous integration](../ci.md).
