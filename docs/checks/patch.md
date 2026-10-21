# Exact patch tests

**Question:** does the code reproduce, to round-off, a solution it should get exactly?

For an explicit Runge-Kutta method, a solution linear in t is reproduced exactly for every step size, provided the right-hand side is right, the stage times match the table and the weights sum to one. The expected error is zero, not small, so bugs that are as small as the method's own error still show.

## Example: a stage evaluated at the wrong time

```python
--8<-- "docs/examples/patch_exact.py"
```

Output:

```text
--8<-- "docs/examples/output/patch_exact.txt"
```

The bug shifts the midpoint stage from t + h/2 to t + 0.4 h. On a smooth problem this costs a little accuracy and might go unnoticed; on the patch solution it is a clear error.

## Using it

`patch_study(integrate, rhs_ref, y0, slope, t_end, ns)` builds the source term for u(t) = y0 + slope * t and expects round-off error at every `n`. `ode_checks(..., patch=(y0, slope))` adds it to the standard bundle.

The exact conditions, the proof and the heat-equation version are on [Patch test theory](../patch.md).
