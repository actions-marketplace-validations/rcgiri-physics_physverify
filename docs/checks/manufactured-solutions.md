# Manufactured solutions

**Question:** does the code solve *these* equations, at the order it claims?

You choose a smooth function u(t), and physverify adds the source term that makes u an exact solution of the reference equations. A correct code then reproduces u, and its error shrinks at the method's order. A code that solves slightly different equations, or takes a wrong step, does not.

## Example: a half-step typo in the midpoint method

The midpoint method takes half a step to a midpoint, then a full step using the slope there. Writing `h` instead of `h / 2` still gives a method that runs, stays stable and looks plausible on a plot.

```python
--8<-- "docs/examples/order_bug.py"
```

Output:

```text
--8<-- "docs/examples/output/order_bug.txt"
```

The buggy version is still close to the right answer at these step sizes, so a comparison with one answer at a loose tolerance can pass it. The order study does not: the error halves when it should quarter.

## What you provide

- `ManufacturedODE(u, reference_rhs)`: the manufactured solution `u(t)` (returning an array) and the reference right-hand side, written from the physics. The source term is computed by complex-step differentiation, so `u` must accept complex `t` (use `np.sin`, not `math.sin`).
- `integrate(source, y0, t_end, n)`: runs your code for exactly `n` steps from t = 0 with `source(t)` added to the right-hand side, and returns the final state.

!!! tip "Write the reference independently"
    If the reference right-hand side is copied from the code under test, a wrong sign in the code is copied too and the check passes. Write it again from the equations.

## Variants

- `mms_trajectory_study`: the largest error over the whole run, not only at the end (catches errors that cancel by the final time).
- `backward_mms_study`: integrate from `t_end` back to 0. A code that evaluates its stages at `t + h/2` while stepping backwards passes forwards but drops to first order here.
- `ode_checks(...)`: bundles the standard checks for an ODE solver; see [Getting started](../getting-started.md).
