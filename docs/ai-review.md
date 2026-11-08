# Checking an AI code review

An AI reviewer asked to "look for bugs in the physics or numerics" of a simulation will usually return a list of suspicions. Some are real, some are not, and reading the code again rarely settles which. In a pilot on 20 public repositories (2026-11-08), a reviewer found 8 of 10 known defects, but also raised alarms on 6 or 7 of 10 repositories that had been tested clean, and none of those alarms was a physics defect. On the repositories with defects, some further claims were real and some were wrong; two that looked convincing on reading were wrong when the code was run. These counts describe that sample only.

physverify is the step after the review: each claim becomes a check that runs the code against a reference written from the physics.

## From claim to verdict

1. **Write the claim down precisely.** File, line, and what should happen instead, e.g. "`compute_power_spectrum` divides by W(k); the bias on P(k) is W(k)²".
2. **Choose a reference that does not come from the code.** An exact solution, a textbook identity, a paper's formula, or a second independent calculation. `physverify references` lists exact solutions. Say where it came from.
3. **Write the smallest test that can tell the two answers apart.** Pick inputs where the claim predicts a clearly different number (a factor, a sign, an order of convergence), and compute both. If no input separates them, the claim is not decidable this way: say so.
4. **Run it.** On code you do not trust, inside the [sandbox](https://github.com/rcgiri-physics/physverify/tree/main/sandbox). If only one function is needed, `physverify.loaders.extract_functions` loads it without importing the whole package.
5. **Record the verdict:** confirmed (with the numbers), rejected (with the numbers), or open. A fix that removes the difference is good supporting evidence.

## Examples from the pilot

| claim | reference | result |
|---|---|---|
| FFTLog period taken as (N−1)Δ instead of NΔ | exact Hankel pair x e^{−x²/2} ↔ y e^{−y²/2} | error 3.8e-3 at N = 256, falling as 1/N; 2.5e-8 with NΔ: confirmed |
| `kx + ky % 2` meant `(kx + ky) % 2` in a spherical-to-cartesian table | the m = 0 column must reproduce the Legendre polynomial P_l(z) | exact for l ≤ 3, off by 0.12–0.66 for l = 4–6: confirmed |
| a dataclass field order makes import crash | run the import | it imports: rejected |

## Notes

- A claim confirmed by reading only is still a suspicion. Report it as such.
- Expect some confident claims to be wrong: in the pilot one rated "high" (an import crash) did not happen when run.
- Before telling a maintainer, follow the usual rules: show the numbers, say what was not tested, and keep it to what the run supports.
