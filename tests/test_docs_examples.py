"""The documentation shows each example's output from docs/examples/output; check it is still what the example prints."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs" / "examples"
# 1e-13 and below, and exact zeros, differ between platforms (1.1e-16 on one, 0.0e+00 on another)
ROUNDOFF = re.compile(r"-?\d+(?:\.\d+)?e-(?:1[3-9]|[2-9]\d)|-?0\.0+e[+-]00")


def normalise(text):
    return [ROUNDOFF.sub("~0", line) for line in text.strip().splitlines()]


@pytest.mark.parametrize("script", sorted(p.name for p in EXAMPLES.glob("*.py")))
def test_example_output_matches_the_docs(script):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONIOENCODING": "utf-8"}
    out = subprocess.run([sys.executable, str(EXAMPLES / script)], capture_output=True, text=True, encoding="utf-8",
                         env=env, timeout=120)
    assert out.returncode == 0, out.stderr
    expected = (EXAMPLES / "output" / script.replace(".py", ".txt")).read_text(encoding="utf-8")
    assert normalise(out.stdout) == normalise(expected)
