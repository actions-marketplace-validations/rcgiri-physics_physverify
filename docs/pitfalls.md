# Convergence-study pitfalls

A convergence study can go wrong in ways that make a correct code look broken, or a broken one look fine. These came up again and again when testing public code, both in the codes' own studies and in the studies written to check them.

## Comparing at the wrong time

**`int(t_end / h)` can come out one short.** In floating point, `2*pi / (2*pi/200)` is 199.99999999999997, and `int` makes it 199. The run stops one step before `t_end`, its error is then O(h) instead of O(h^4), and an order-4 method looks first order.

**Comparing arrays index by index**, or taking the maximum over "the last N samples", moves the comparison time with h.

`trajectory_order_study` takes the whole trajectories and compares every run at one fixed time, failing loudly when a run has no sample there:

```python
--8<-- "docs/examples/trajectory_pitfall.py"
```

Output:

```text
--8<-- "docs/examples/output/trajectory_pitfall.txt"
```

## Comparing at a whole number of periods

At a whole period, phase errors of an oscillator can cancel, and a method can look more accurate than it is: a symplectic Euler method showed order 2 there in a real study. The last line above is a note, not a failure: compare at a time that is not a multiple of the period too.

## Loops that test the time instead of counting steps

`while t < t_end: t += h` takes one step too many whenever rounding leaves `t` just below `t_end`, and the right number otherwise. `time_grid_check` runs the code with several step sizes and checks the number of steps and the final time:

```python
--8<-- "docs/examples/time_grid.py"
```

Output:

```text
--8<-- "docs/examples/output/time_grid.txt"
```

The fix is to count: `for k in range(n): t = (k + 1) * h`.

## Errors already at round-off

If the coarsest step already gives an error of 1e-13, the error cannot shrink any more and the study reports INCONCLUSIVE or EXACT, not a failure. Use *coarser* steps. The message says when this happened.

## Absolute tolerances

A check that requires "error below 1e-6 at the finest step" depends on the problem's scale and on how fine the finest step is. The observed order does not. Prefer the order; if an absolute tolerance fails while the observed order is right, the code is most likely fine.

## Start-up transients

When fitting a decay or relaxation rate from a run that starts from equilibrium, skip the start-up transient. In one real code, fitting from t = 0 gave a viscosity 2% off; skipping the transient gave 0.01%.
