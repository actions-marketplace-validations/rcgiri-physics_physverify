# Changelog

## 0.1.0 (2026-10-19)

First release on PyPI.

- **Stochastic codes.** Checks for 2D Ising Monte Carlo samplers with exact references, 20 seeded bugs and a calibration study ([docs/ising.md](docs/ising.md)).
- **Audit of the author's public physics projects** ([results/own_work/SUMMARY.md](results/own_work/SUMMARY.md)).

- **Exactness (`patch`) checks for ODE codes.** Every consistent explicit Runge-Kutta method reproduces a solution linear in t exactly, so any error at all is a bug. [docs/patch.md](docs/patch.md) states the assumptions and proofs for this and for the heat-equation patch.
- **Larger benchmark.** It now has 37 seeded bugs over 5 problems. The new problems are Kepler (energy and angular-momentum invariants, orbit closure) and Sod's shock tube (exact Riemann solution, exact discrete conservation). New bugs include several that keep the scheme's order of convergence.
- **Benchmark records.** Each bug records its expected symptom, written before the run. `results/bug_catalogue.md` lists, for each bug, what is changed, the prediction and the outcome, including two predictions that turned out wrong and two bugs no check catches.
- **Comparison with plain tests.** `results/comparison.md` compares the families with plain single-run tests.
- **Reproducible tables.** The tests require the committed tables to match a fresh run.
- **Whole-trajectory MMS study.** The error is measured over the whole run, not only at the final time.
- **Scale-aware noise floor.**
- **Command line.** `physverify run` gives text, JSON (`--json`) and a self-contained HTML report (`--html`). The command also has `matrix` and `compare`.
- **pytest plugin.** Checks in `verify_*.py` files become tests.
- **Claude Code hook (`physverify hook`) and a minimal MCP server (`physverify mcp`).** The server answers both the older `initialize` handshake and the 2026-07-28 per-request protocol (`server/discover`). See [docs/agent.md](docs/agent.md).
- **SymPy-derived manufactured sources** (`physverify.symbolic`, optional extra `symbolic`).
- **Hypothesis property tests.**

## 0.0.1

- First prototype: four check families plus the heat-equation patch test, and a 22-bug benchmark over three solvers.
