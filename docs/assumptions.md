# What a PASS means

A PASS means the checks found nothing wrong. It does not prove the simulation correct. Each check family rests on assumptions; when one is false, a check can pass on wrong code.

| Family | Assumes | Independent of the code? |
|---|---|---|
| Manufactured solutions | The reference equations are right; the solution is smooth; the steps are in the asymptotic range; the adapter adds the source where the solver evaluates the right-hand side. | Only if the reference equations were written from the physics, not copied from the code. |
| Reference solutions | The same, plus a trustworthy reference integrator (RK4 at fine steps). | Same as above. |
| Conserved quantities | The quantity really is conserved (or its budget is known) for this problem. | Yes, if it comes from the physics. A good second check. |
| Known limits | The limit is exact and the code can reach it. | Yes. |
| Patch tests | The scheme represents the chosen solution exactly (see [patch test theory](patch.md)). | Yes, but only for the parts of the scheme the patch touches. |
| Runge-Kutta tables | The table you pass is the one the code uses. | Yes: pure algebra on the coefficients. |

## A check that shares the code's mistake

The solver below should solve a spring, x'' = -omega² x, but has the sign of the force wrong. The reference right-hand side was written by looking at the solver, so it has the same wrong sign:

```python
--8<-- "docs/examples/shared_sign_error.py"
```

```text
--8<-- "docs/examples/output/shared_sign_error.txt"
```

Both order checks pass, because the code converges at second order, to the wrong equations. The energy check fails, because energy conservation comes from the physics and not from the code. **Always include at least one check that is independent of how the equations were typed in:** a conserved quantity, a known limit or an exact solution.

## Checklist before trusting a PASS

- Are the reference equations written from the physics (paper, textbook, notes), not copied from the code?
- Are units and signs stated, and do they match the code's conventions?
- Are initial and boundary conditions checked separately (they are easy to get wrong and a convergence study may not reach them)?
- Does the test reach the part of the state space where bugs hide (large amplitudes, boundaries, odd grid sizes)?
- Is there a second, independent check, such as a conserved quantity or a limiting case?
