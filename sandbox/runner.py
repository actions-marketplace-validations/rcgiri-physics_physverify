"""Start-up inside the sandbox container: copy the repository to a writable place, optionally apply the
Python 3.14 shim, run the adapter, then report files the code wrote into its own directory.

    python /pv/runner.py <adapter.py> [args ...]

Environment: PHYSVERIFY_REPO_SRC (read-only clone, default /repo-src), PHYSVERIFY_REPO (the writable copy,
default /tmp/repo), PHYSVERIFY_PY314_SHIM=1 to apply the shim. Standard library only.

Some repositories write next to their own source (a cache in the package folder, an output folder
that must already exist), which fails from a read-only install. Running from a copy lets the checks
go ahead, and the note at the end records it as a portability issue rather than hiding it.
"""

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

FUTURE = "from __future__ import annotations\n"


def snapshot(root: Path) -> dict:
    out = {}
    for p in root.rglob("*"):
        if p.is_file() and not p.is_symlink():
            st = p.stat()
            out[p.relative_to(root).as_posix()] = (st.st_size, st.st_mtime_ns)
    return out


def written(before: dict, after: dict) -> list:
    """Files created or changed between two snapshots."""
    return sorted(k for k, v in after.items() if before.get(k) != v)


def py314_shim(source: str) -> str | None:
    """Source with `from __future__ import annotations` as its first statement, or None when not needed
    or not possible (already there, or the file does not parse on this Python).

    Python 3.14 evaluates annotations lazily, so code written for it may annotate with names defined
    later in the file; on 3.10-3.13 that fails at import unless annotations are postponed.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__" and any(a.name == "annotations" for a in node.names):
            return None
    lines = source.splitlines(keepends=True)
    body = tree.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        at = body[0].end_lineno  # after the module docstring
    else:
        at = 0
        while at < min(2, len(lines)) and lines[at].startswith("#"):  # shebang and coding lines stay first
            at += 1
    if at and at <= len(lines) and not lines[at - 1].endswith("\n"):
        lines[at - 1] += "\n"
    return "".join(lines[:at]) + FUTURE + "".join(lines[at:])


def apply_shim(root: Path) -> int:
    n = 0
    for p in root.rglob("*.py"):
        try:
            new = py314_shim(p.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
        if new is not None:
            p.write_text(new, encoding="utf-8")
            n += 1
    return n


def main(argv) -> int:
    src = Path(os.environ.get("PHYSVERIFY_REPO_SRC", "/repo-src"))
    dst = Path(os.environ.get("PHYSVERIFY_REPO", "/tmp/repo"))
    shutil.copytree(src, dst, symlinks=True, ignore=shutil.ignore_patterns(".git"), dirs_exist_ok=True)
    if os.environ.get("PHYSVERIFY_PY314_SHIM") == "1":
        print(f"physverify sandbox: Python 3.14 shim added postponed annotations to {apply_shim(dst)} files", file=sys.stderr)
    before = snapshot(dst)
    rc = subprocess.call([sys.executable, *argv], env={**os.environ, "PHYSVERIFY_REPO": str(dst)})
    changed = written(before, snapshot(dst))
    if changed:
        shown = ", ".join(changed[:5]) + (f" and {len(changed) - 5} more" if len(changed) > 5 else "")
        print(f"physverify sandbox: portability note: the code wrote {len(changed)} file{'s' if len(changed) != 1 else ''} into its own directory "
              f"({shown}); it would fail from a read-only install", file=sys.stderr)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
