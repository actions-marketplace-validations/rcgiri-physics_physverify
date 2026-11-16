"""Is the reference independent? A static look at a spec file before it runs.

The mistake the docs warn about most (AGENTS.md, docs/pitfalls.md) is a reference computed with the code
under test: a bug in the solver is then copied into the reference and the check passes. Here a function whose
name says it is a reference (`exact`, `reference`, `analytic`, `expected`, `*_ref`) is flagged when it uses a
module the spec imports that is not a standard numerical library. A function can be a fair reference and
still use such a module (a constant table, a unit), so these are notes, not failures.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

_TRUSTED = {"numpy", "np", "scipy", "math", "cmath", "sympy", "mpmath", "physverify", "pytest", "functools",
            "itertools", "fractions", "decimal", "dataclasses", "typing", "pathlib", "os", "sys", "json", "time",
            "warnings", "statistics", "random", "collections", "importlib", "matplotlib", "pandas", "astropy", "pint"}
_REFERENCE = re.compile(r"exact|reference|analytic|expected|truth|^ref_|_ref$|_ref_|^ref$", re.I)
_LOADERS = {"load_module_from_path", "import_module", "extract_functions", "load_spec"}


def _solver_modules(tree) -> dict[str, str | None]:
    """Names bound to modules that are neither standard nor numerical libraries, with the top-level module each
    came from (None when it is certainly local: a relative import or a module loaded from a path)."""
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    out: dict[str, str | None] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                top = a.name.split(".")[0]
                if top not in _TRUSTED and top not in stdlib:
                    out[(a.asname or a.name).split(".")[0]] = top
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            top = n.module.split(".")[0]
            if top not in _TRUSTED and top not in stdlib:
                out.update({a.asname or a.name: top for a in n.names if a.name != "*"})
        elif isinstance(n, ast.ImportFrom) and n.level > 0:  # from . import solver
            out.update({a.asname or a.name: None for a in n.names if a.name != "*"})
        elif isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            fn = n.value.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name in _LOADERS:
                out.update({t.id: None for t in n.targets if isinstance(t, ast.Name)})
    return out


def _solver_names(tree) -> set[str]:
    """Names bound to modules that are neither standard nor numerical libraries (the code under test)."""
    return set(_solver_modules(tree))


_SKIP_DIRS = {".git", ".hg", ".venv", "venv", "env", "site-packages", "node_modules", "__pycache__", ".tox", "build",
              "dist"}


def _in_tree(top: str, roots, depth: int = 4) -> bool:
    """True when a module or package called `top` is a file or folder below one of the roots (the repository)."""
    def walk(folder: Path, level: int) -> bool:
        if (folder / f"{top}.py").is_file() or (folder / top).is_dir():
            return True
        if level >= depth:
            return False
        try:
            subs = [d for d in folder.iterdir() if d.is_dir() and d.name not in _SKIP_DIRS and not d.name.startswith(".")]
        except OSError:
            return False
        return any(walk(d, level + 1) for d in subs)
    return any(walk(Path(r), 0) for r in roots if r and Path(r).is_dir())


def reference_notes(path, roots=None) -> list[str]:
    """One note per reference-like function in the spec that uses the code under test.

    With `roots` (the repository and the claim's folder; `physverify confirm` passes them), a module that is not
    found below any root is taken to be an installed library, not the code under test, and is not noted: a claim
    that a repository calls healpy wrongly may use healpy's own routine as the reference (study re-test, J163).
    `library_names(path, roots)` lists the names this lets through.
    """
    path = Path(path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), str(path))
    except (OSError, SyntaxError, ValueError):
        return []
    solver = _local(_solver_modules(tree), roots)
    if not solver:
        return []
    notes = []
    for f in ast.walk(tree):
        if not (isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and _REFERENCE.search(getattr(f, "name", ""))):
            continue
        used = sorted({n.id for n in ast.walk(f) if isinstance(n, ast.Name) and n.id in solver})
        if used:
            notes.append(f"{path.name}:{f.lineno}: the reference {f.name}() uses {', '.join(used)}, which the spec imports"
                         " as the code under test; a reference computed with the solver passes even when the solver is"
                         " wrong (derive it from the physics instead, or say why this use is safe)")
    return notes


def _local(modules: dict, roots) -> set[str]:
    if roots is None:
        return set(modules)
    return {name for name, top in modules.items() if top is None or _in_tree(top, roots)}


def library_names(path, roots) -> list[str]:
    """Imported names that reference_notes(path, roots) treats as installed libraries (not found below the roots)."""
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"), str(path))
    except (OSError, SyntaxError, ValueError):
        return []
    modules = _solver_modules(tree)
    return sorted(f"{name} ({top})" if name != top else name for name, top in modules.items()
                  if top is not None and not _in_tree(top, roots))
