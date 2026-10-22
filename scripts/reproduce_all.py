"""Regenerate every benchmark table in results/ from a clean checkout.

    python scripts/reproduce_all.py          # seeded-bug matrix, catalogue, comparison (deterministic)
    python scripts/reproduce_all.py --slow   # also the Monte Carlo (Ising) matrix, several minutes

The Markdown tables are deterministic and must match the committed ones
(tests/test_seeded_bugs.py checks this); detection_matrix.json and run_time.md
also record the machine and the run times, which differ between runs.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ["-m", "physverify.matrix", "results/detection_matrix.md"],
    ["-m", "physverify.compare", "results/comparison.md"],
    ["scripts/make_figures.py"],
]
SLOW = [["-m", "physverify.stochastic.matrix", "results/ising_matrix.md"]]


def main() -> int:
    steps = STEPS + (SLOW if "--slow" in sys.argv[1:] else [])
    for step in steps:
        print("python", " ".join(step), flush=True)
        subprocess.run([sys.executable, *step], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    print("done; `git diff results/` shows what changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
