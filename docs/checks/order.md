# Order of convergence

**Question:** does the error shrink as fast as the method promises?

Every study on this site ends in `check_order(hs, errors, expected)`. If you already run your own convergence study, you can call it directly.

```python
--8<-- "docs/examples/check_order_direct.py"
```

Output:

```text
--8<-- "docs/examples/output/check_order_direct.txt"
```

## How the verdict is decided

- The observed order is fitted on the finest resolutions (`fit_points`, default 4) whose errors are above the round-off floor.
- **PASS** when it lies within `tol_low` below and `tol_high` above the expected order (defaults 0.3 and 1.0; `tol=` sets both). Higher than expected is allowed, because some problems superconverge.
- **EXACT** when every error is below the floor (default 1e-12, scaled by the solution's size): the code reproduced the solution, so the order cannot be measured.
- **INCONCLUSIVE** when fewer than two errors are above the floor. The message says so, and that coarser resolutions are needed.

## Choosing step sizes

- Use at least four resolutions, each twice the previous.
- Keep the finest error well above round-off (about 1e-11). For a 4th-order method that often means *coarser* steps than you would use in production.
- Count steps, do not test times: run exactly `n` steps of size `t_end / n`. See [Convergence-study pitfalls](../pitfalls.md).
