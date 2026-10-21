# Conserved quantities and budgets

**Questions:** does the code keep what the physics keeps? And does it keep exact budgets exactly?

## Energy drift that shrinks at the right order

A 2nd-order integrator may let the energy of an oscillator drift, but only by O(h^2). `invariant_study` measures the drift at several step sizes and checks its order.

```python
--8<-- "docs/examples/invariant_energy.py"
```

Output:

```text
--8<-- "docs/examples/output/invariant_energy.txt"
```

The buggy velocity update uses only the old acceleration. The positions still look like an oscillator, but the energy drifts at about first order.

## Budgets kept exactly on every grid

Some schemes conserve a quantity *exactly*: a finite-volume heat solver with insulated walls keeps the total heat to round-off, on every grid and for every step. A convergence study is the wrong test there, because a leak that shrinks with the grid would pass it. `balance_check` asks for the exact budget at every resolution.

```python
--8<-- "docs/examples/heat_balance.py"
```

Output:

```text
--8<-- "docs/examples/output/heat_balance.txt"
```

The buggy wall copies the neighbour value after each update, a common way to write an "insulated" boundary. It converges (the mismatch shrinks) but does not conserve heat. A real code written this way lost 8.5% of its heat.

## Other budgets worth checking

- Heat gained through a wall with a known flux, or from a known source, over a run.
- Total mass in an advection code with periodic boundaries.
- Momentum in an N-body code (exact for pairwise forces that obey Newton's third law).
- Angular momentum in a central-force orbit.
