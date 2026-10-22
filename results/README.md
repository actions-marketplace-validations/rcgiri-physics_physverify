# Results

Everything here can be regenerated from a clean checkout:

```bash
pip install -e .[dev]
python scripts/reproduce_all.py          # seeded-bug matrix, catalogue, comparison, run times
python scripts/reproduce_all.py --slow   # also the Monte Carlo (Ising) matrix, several minutes
```

| File | What it is | Deterministic? |
|---|---|---|
| [detection_matrix.md](detection_matrix.md) | Which check family flags which of the 37 seeded bugs, with the breakdown into FAIL and INCONCLUSIVE/ERROR. | Yes; `tests/test_seeded_bugs.py` requires a fresh run to match it. |
| [bug_catalogue.md](bug_catalogue.md) | Each seeded bug: the change, the expected symptom, the predicted and observed families, and links to the exact lines that switch it on. | Yes; tested the same way. |
| [detection_matrix_details.md](detection_matrix_details.md) | The message of every check on every bug. | Yes. |
| [detection_matrix.json](detection_matrix.json) | One record per (problem, bug, check): full status, message, prediction, run time, and `provenance` (physverify version, git commit, Python, NumPy, platform, date). | The statuses are; run times and provenance are not. |
| [run_time.md](run_time.md) | Run time per check family and problem. | No. |
| [comparison.md](comparison.md) | The check families against plain "compare with one answer" tests. | The counts are; run times are not. |
| [heat1d_by_check.md](heat1d_by_check.md) | The heat-equation bugs, one column per individual check. | Yes. |
| [method_bugs.md](method_bugs.md) | Bugs in numerical methods themselves, modelled on bugs found in public code; regenerate with the command at its top. | Yes; `tests/test_method_bugs.py`. |
| [ising_matrix.md](ising_matrix.md), [ising_scorecard.md](ising_scorecard.md), [ising_details.md](ising_details.md), [ising_calibration.md](ising_calibration.md) | The Monte Carlo checks on seeded Ising bugs (`--slow`). | Yes for fixed seeds. |
| [corpus/](corpus/) | Runs on public repositories, listed by ID until their authors are told. | No: needs the repositories and the sandbox. |
| [own_work/](own_work/) | Runs on the author's own projects. | No. |

The bugs and the checks were written by the same person, so the detection counts show the tool works as designed; they are not a promise about bugs in other people's code.
