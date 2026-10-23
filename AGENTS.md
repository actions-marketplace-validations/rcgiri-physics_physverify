# Notes for AI coding assistants

This file is for an AI assistant (Claude Code, Codex, Cursor, Copilot and others) that is asked either to **check a project with physverify** or to **change physverify itself**. People are welcome to read it too.

## Checking someone's project with physverify

1. Install into a virtual environment: `python -m venv .pv && . .pv/bin/activate && pip install physverify` (on Windows `.pv\Scripts\Activate.ps1`).
2. Start with `physverify scan PATH` (physverify 0.5.0 or newer). It reads the source and runs nothing, so it is safe on untrusted code. Exit code 1 means at least one WARN.
3. `physverify run`, `physverify smoke`, the hook and the MCP server **run** the code. Use them only on code the user trusts, or inside the container in `sandbox/` (see `sandbox/README.md`).
4. Write the reference in a spec from the physics: the README, the paper, a textbook. Never derive it from the solver under test, or a bug in the solver is copied into the reference and the check passes. Say where each equation came from.
5. When a check fails, suspect the spec first: units, sign conventions, time origin, the step counts, CODATA edition. `docs/troubleshooting.md` and `docs/pitfalls.md` list the mistakes that were made most often. In the corpus study, adapters written with an AI assistant were wrong about 28 times before they were right.
6. Report what was tested and what was not. A PASS is a bounded claim (`docs/assumptions.md`).
7. Do not post issues, comments or pull requests on other people's projects without the user's explicit approval of the exact text.

Useful entry points: `physverify init` (a starter spec), `physverify references` (exact solutions), `docs/recipes.md`, `examples/verify_damped_oscillator.py`.

## Working on physverify itself

- Install with `pip install -e ".[dev]"` and run `python -m pytest -q` before and after a change. Slow tests are marked `slow`.
- `tests/test_seeded_bugs.py` and `tests/test_figures.py` compare with committed files in `results/`; if a change alters them on purpose, run `python scripts/reproduce_all.py` and commit the new files.
- `tests/test_docs_examples.py` re-runs `docs/examples/` and compares with `docs/examples/output/`.
- The installed package (`src/physverify/`) holds only the checks and uses only NumPy at import time; the benchmark lives in `benchmark/pvbench/` and is not installed.
- Keep the scope in `ROADMAP.md`: deepen ODE/PDE time integration, convergence and conservation before adding new families. Statistical checks need a measured false-alarm rate.
- Every message a check prints should say what was tested, in plain words. Match the style of the surrounding code: short docstrings that say where a rule came from.
- Never state a general bug rate for physics code from the corpus results; give counts within the stated sample only.
- Plain commit messages; follow `CONTRIBUTING.md`.
