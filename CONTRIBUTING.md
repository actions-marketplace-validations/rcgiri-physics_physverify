# Contributing

Thanks for your interest. physverify is actively evolving, and contributions and test cases from the computational physics community are what make its results trustworthy. You do not need to be an expert programmer: several of the most useful contributions below need no change to physverify's code at all.

## Help wanted

1. **A trial report on your own solver (most wanted).** Install physverify from PyPI, write a spec for a solver you know well, and tell us how it went: what was flagged, what was missed, and where you got stuck. Even "everything passed in 20 minutes" is useful. Use the [trial report template](https://github.com/rcgiri-physics/physverify/issues/new?template=trial_report.md).
2. **A blind test.** Make a few copies of your solver with bugs you choose (and keep one correct copy), without telling us which is which. Run physverify on all of them and report, for each: detected, missed, false alarm, or could not be set up. Results from someone other than the author are the evidence the project needs most; they will be published in `results/independent/` (anonymously if you prefer), misses first.
3. **New seeded bugs.** The benchmark's 37 bugs were written by the author, who also wrote the checks. A bug written by someone else, added to one of the problems in `benchmark/pvbench/problems/` with its expected symptom, tests the checks more fairly.
4. **Adapters for common solver styles,** for example a SciPy `solve_ivp`-style function, or a solver that writes its output to files.
5. **Documentation:** a step that confused you, a missing example, a typo. Small pull requests are welcome.
6. **Exact reference solutions** from your field (with a citation), for `physverify.references`.

## Reporting a problem

- **A check that fails when it should pass, or passes when it should fail:** use the [bug report template](https://github.com/rcgiri-physics/physverify/issues/new?template=bug_report.md) with a minimal example and the output. First read [Troubleshooting](https://rcgiri-physics.github.io/physverify/troubleshooting/): many failures come from the spec or the adapter, not the solver.

## Changing the code

Fork, make a branch, and open a pull request. Run the tests first:

```bash
pip install -e ".[dev]"
python -m pytest -q
```

- `tests/test_seeded_bugs.py` requires the committed tables in `results/` to match a fresh run, and `tests/test_figures.py` does the same for the figures. If your change alters them on purpose, run `python scripts/reproduce_all.py` and commit the new files (see [results/README.md](results/README.md)).
- `tests/test_docs_examples.py` re-runs every example in `docs/examples/` and compares its output with `docs/examples/output/`.
- Before adding a new kind of check, open an issue first. New checks should deepen what exists (ODE and PDE time integration, convergence, conservation) rather than widen the scope; see the principles in [ROADMAP.md](ROADMAP.md).
