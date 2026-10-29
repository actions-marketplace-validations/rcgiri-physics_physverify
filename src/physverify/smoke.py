"""Does it even run? A first stage before any physics check.

In the corpus study, three repositories did not parse at all and several crashed or waited for input before
any physics could be tested (J147-J149, J156, J159). `smoke(path)` compiles each script and runs it in a
separate process with a time limit, stdin closed and plotting off, and reports one line per script.
It runs the code, so use it only on code you trust or inside the sandbox (sandbox/).
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PARSES = "parse error"
CRASH = "crash"
TIMEOUT = "timeout"
INPUT = "waits for input"
OK = "ok"


@dataclass
class SmokeResult:
    path: str
    outcome: str
    detail: str = ""
    nan_warnings: int = 0


def _scripts(path: Path) -> list[Path]:
    from .scan import python_files  # skips virtual environments and build output below `path` (not above it)

    if path.is_file():
        return [path]
    return [p for p in python_files(path) if not p.name.startswith("test_")]


def smoke_script(script: Path, *, timeout: float = 60.0) -> SmokeResult:
    src = script.read_text(encoding="utf-8", errors="replace")
    try:
        compile(src, str(script), "exec")
    except SyntaxError as exc:
        return SmokeResult(str(script), PARSES, f"line {exc.lineno}: {exc.msg}")
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONWARNINGS="default")
    try:
        p = subprocess.run([sys.executable, script.name], cwd=script.parent, stdin=subprocess.DEVNULL,
                           capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return SmokeResult(str(script), TIMEOUT, f"still running after {timeout:g} s")
    err = p.stderr or ""
    nan = sum(err.count(w) for w in ("invalid value encountered", "overflow encountered", "divide by zero"))
    if p.returncode != 0:
        last = [line for line in err.strip().splitlines() if line.strip()][-1:] or [f"exit code {p.returncode}"]
        outcome = INPUT if "EOFError" in last[0] else CRASH
        return SmokeResult(str(script), outcome, last[0][:300], nan)
    return SmokeResult(str(script), OK, "ran to the end", nan)


def smoke(path, *, timeout: float = 60.0) -> list[SmokeResult]:
    """Compile and run every script under `path` (or the one file) and report what happened."""
    return [smoke_script(s, timeout=timeout) for s in _scripts(Path(path))]
