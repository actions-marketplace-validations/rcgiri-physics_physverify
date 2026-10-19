# Contributing

Thanks for your interest. physverify is a small, early project, so every report helps.

- **Found a wrong result or a bug?** Open an issue with a minimal example and the output.
- **Tried it on your own solver?** Please open an issue and say how it went, even if everything passed. Knowing what works is useful too.
- **Code changes:** fork, make a branch, and open a pull request. Run the tests first:

```bash
pip install -e ".[dev]"
python -m pytest -q
```

`tests/test_seeded_bugs.py` requires the committed tables in `results/` to match a fresh run. If your change alters them on purpose, regenerate them with the commands in [docs/technical.md](docs/technical.md) and commit the new tables.
