"""Run physverify work in a fresh Python process with a time limit.

A new interpreter imports the code under test as it is on disk now, so an edit between two runs is always
seen (a long-running process such as the MCP server keeps its first import), and a run that hangs can be
killed. Used by `physverify confirm` and by the MCP tools. The child sends everything the code under test
prints to stderr and writes its result as JSON after a marker line on stdout.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

MARKER = "@@physverify-result@@"
TAIL = 2000  # characters of the child's stderr kept for a report
_CHILD = "import sys; from physverify.isolate import child_main; sys.exit(child_main(sys.argv[1:]))"


def _text(data) -> str:
    if data is None:
        return ""
    return data.decode("utf-8", "replace") if isinstance(data, bytes) else data


def _tail(data) -> str:
    return _text(data)[-TAIL:]


def run_isolated(mode: str, args, timeout: float | None, cwd=None) -> dict:
    """Run `mode` ("claim" or "specs") on `args` in a new Python process, killed after `timeout` seconds.

    Returns {"status": "done", "result": ..., "stderr_tail": ...}, {"status": "timeout", "stderr_tail": ...}
    or {"status": "error", "error": ..., "stderr_tail": ...} when the child ended without a result.
    """
    src = str(Path(__file__).resolve().parents[1])  # the physverify the parent uses, also for the child
    # no .pyc written: a same-size edit within a second could otherwise load stale bytecode in the next run
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    env["PYTHONPATH"] = src + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src
    cmd = [sys.executable, "-c", _CHILD, mode, *[str(a) for a in args]]
    try:
        proc = subprocess.run(cmd, capture_output=True, env=env, cwd=cwd, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as exc:
        return {"status": "timeout", "stderr_tail": _tail(exc.stderr)}
    out = _text(proc.stdout)
    i = out.rfind(MARKER)
    if i < 0:
        return {"status": "error", "error": f"the child process exited with code {proc.returncode} without a result",
                "stderr_tail": _tail(proc.stderr)}
    try:
        result = json.loads(out[i + len(MARKER):])
    except json.JSONDecodeError as exc:
        return {"status": "error", "error": f"the child's result is not valid JSON ({exc})", "stderr_tail": _tail(proc.stderr)}
    return {"status": "done", "result": result, "stderr_tail": _tail(proc.stderr)}


def child_main(argv) -> int:
    """Entry point of the child process: run one mode and write its JSON result after MARKER on stdout."""
    mode, rest = argv[0], list(argv[1:])
    real_stdout = sys.stdout
    with contextlib.redirect_stdout(sys.stderr):  # the code under test must not corrupt the result
        if mode == "claim":
            from .confirm import evaluate_claim

            result = evaluate_claim(rest[0])
        elif mode == "specs":
            from .agent import run_specs

            result = run_specs([Path(s) for s in rest])
        else:
            print(f"physverify.isolate: unknown mode {mode!r}", file=sys.stderr)
            return 2
    real_stdout.write("\n" + MARKER + json.dumps(result) + "\n")
    real_stdout.flush()
    return 0
