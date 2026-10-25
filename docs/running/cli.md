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

New in 0.5.0.

```bash
physverify scan path/to/project
physverify scan path/to/project --only tables,grid --json scan.json
```

Reads every `.py` file with Python's `ast` module and **runs nothing**, so it is safe on code you have not read. Four stages, each from a kind of bug found in public code:

| Stage | Looks for | Level |
|---|---|---|
| `constants` | literals close to, but not equal to, a physical constant: within 1% for constants with units (`6.67e-11`; a long numeric table, or a file with more than 20 near-constants, is summarised in one NOTE), within 0.2% for pure numbers (`3.14`, `2.27`), within 0.1% for values fixed by definition (the astronomical unit, the torr, the nautical mile, the SI 2019 constants and their CGS values, so an old `h_CGS = 6.626196e-27` is noted), and `g` only when assigned to a gravity name (`g = 9.7`); one line per constant and file | NOTE |
| `tables` | Runge-Kutta tables written as literals: the order the coefficients really have, row sums against `c`, error weights that must sum to 0, and the order a name, docstring or `order` attribute claims (`rk4`, `heun3`, `3rd order`, `def order(self): return 3`). Tables are read from assignments, from constructor keywords and dicts (`ButcherTableau(a=..., b=..., b_error=..., order=5)`), from classes that inherit them, and from `A = np.zeros((s, s))` filled by `A[i, :k] = [...]`. Also **stages written as code** (`k2 = h*f(t + h/2, y + k1/2)`): the table is read back from the calls, then checked the same way, against the stage times, and against a Butcher table drawn in the docstring | WARN when a claim, `c` or the docstring does not match, when a stage leaves out `h`, or when a combination of the stages sums to neither 1 nor 0; else NOTE |
| `grid` | a spacing `(b - a)/D` next to `linspace(a, b, M)` with `D` not equal to `M - 1`; compared by substituting random values, so `W/(N-1)` with `linspace(0, W, N+1)` is caught too. `D` must differ from `M - 1` by a constant, so an element length `L/n` next to a plotting grid of `100*n` points is not flagged | WARN in the same function, NOTE across functions or files |
| `names` | a name used but never defined or imported in the file (a misspelt parameter, `np` without `import numpy`, with a "did you mean" for one-letter slips), and a file that does not parse. Names inside `try ... except NameError/ImportError` and in branches for another Python version are skipped; files with `from x import *` or `exec` are not checked | WARN |
| `api` | features removed from NumPy (`np.NaN`, `np.float`, `np.product`, `np.array(x, copy=False)`), SciPy (`scipy.integrate.simps`, `scipy.misc`) and Python (`imp`, `distutils`) | WARN; deprecated ones (`np.trapz`) NOTE |
| `literals` | `1e0 - 5` (meant `1e-5`?), `x ^ 2` (exclusive or, not a power), `x == np.nan` (never true) | WARN |
| `units` | a table of (unit expression, "physical type") whose dimension does not match the name, such as `(si.W * si.m**2 / si.Hz, "surface tension")` | WARN |
| `pairs` | functions whose names say they undo each other (`x_to_y` / `y_to_x`, `s2z` / `z2s`), to check with `identities.check_roundtrip` | NOTE |

From Python, `physverify.scan.extract_tables(path)` returns every table the scan found (A, b, c, the claimed order and its source), to pass on to `check_tableau` for stage order or stability claims.

Exit code 1 if there is any WARN, 0 otherwise, 2 for a bad path or stage name. Files that do not parse are listed, not skipped silently. A clean scan means only that these patterns were not found. Stages are read only for explicit methods on one state variable: implicit methods and systems split into parts (`x` and `v` advanced side by side) are skipped, and no check of the physics is made.

## `physverify smoke`

```bash
physverify smoke path/to/project --timeout 60
```

Each script is compiled, then run in its own process with a time limit, stdin closed and plotting off. It reports scripts that do not parse, crash, wait for input or emit NaN/overflow warnings. It runs the code, so use it on trusted code or in the sandbox.

## pytest

With physverify installed, `pytest my_spec.py` turns each check into a pytest test (SKIP becomes a pytest skip). See [Continuous integration](../ci.md).
