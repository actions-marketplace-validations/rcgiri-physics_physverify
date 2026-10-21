# Command line

```text
physverify run SPEC [SPEC ...]   run the checks in spec files (glob patterns are expanded)
physverify init [SPEC]           write a starter spec for a fixed-step ODE solver
physverify smoke PATH            compile and run each script; report crashes, hangs and NaNs
physverify references            list the exact references
physverify matrix | compare      the seeded-bug benchmarks
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

## `physverify smoke`

```bash
physverify smoke path/to/project --timeout 60
```

Each script is compiled, then run in its own process with a time limit, stdin closed and plotting off. It reports scripts that do not parse, crash, wait for input or emit NaN/overflow warnings. It runs the code, so use it on trusted code or in the sandbox.

## pytest

With physverify installed, `pytest my_spec.py` turns each check into a pytest test (SKIP becomes a pytest skip). See [Continuous integration](../ci.md).
