# Exact references

**Question:** does the code match a result known in closed form, or computable exactly?

physverify ships a collection of exact results that people kept writing by hand. Each one is tested in physverify's own test suite against an independent computation (finite differences, enumeration, orbit integration).

```bash
physverify references
```

lists them; `help(physverify.references.<name>)` gives the formula and its source.

## Example: a Schroedinger solver against the Morse levels

```python
--8<-- "docs/examples/references_morse.py"
```

Output:

```text
--8<-- "docs/examples/output/references_morse.txt"
```

The differences are small and shrink as the grid is refined, as they should for a second-order finite-difference Hamiltonian.

## What is available

| Area | References |
|---|---|
| Statistical physics | 2D Ising model by exact enumeration (up to 4x4), classical Heisenberg chain, open transverse-field Ising chain ground energy |
| Heat and transport | heat-equation sine modes, a moving and spreading Gaussian, the semi-infinite solid with a temperature step |
| Mechanics | double-pendulum accelerations and energy, cantilever tip deflection and slope |
| Quantum mechanics | infinite square well, square-barrier transmission, Morse levels and turning points |
| Gravitation | Schwarzschild quasinormal frequencies, Kerr innermost stable orbit, exact light deflection |
| Reactor physics | asymptotic period from the inhour equation, for either sign of reactivity |

A real code used the positive-reactivity formula for a negative reactivity and was off by a factor of about 7000; the reference handles both signs.
