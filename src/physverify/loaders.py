"""Import a module from a path without touching its folder.

Used by the adapters that test other people's code. Nothing is written next to
the module (no __pycache__), and optional plotting imports can be stubbed so a
simulation file can be imported on a machine without matplotlib.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import sys
import types
from pathlib import Path


def _stub_module(name: str) -> types.ModuleType:
    return types.ModuleType(name)


def load_module_from_path(name: str, path, stubs=()):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    added = []
    for stub in stubs:
        try:
            importlib.import_module(stub)
        except ImportError:
            sys.modules[stub] = _stub_module(stub)
            added.append(stub)

    old_flag = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(name, None)  # do not leave a half-initialised module behind
            raise
    finally:
        sys.dont_write_bytecode = old_flag
        for stub in added:
            sys.modules.pop(stub, None)
    return module


def load_definitions_from_path(name: str, path, *, keep=(), inner=(), namespace=None):
    """Load only the definitions of a script whose top level runs a simulation.

    Many research scripts parse argv, open a window or run a long simulation at
    import. This executes only the top-level imports, functions and classes, and
    the top-level assignments to the names in `keep` (constants the functions
    use). `inner` names functions defined inside other functions (for example
    marimo or Jupyter-exported cells); they are lifted to module level, and
    their imports must then come from `namespace`.

    Nothing else in the file runs, so a function that relies on a global set by
    the skipped code fails with NameError; set it on the returned module.
    """
    path = Path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    body = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body.append(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id in keep for t in targets):
                body.append(node)
    if inner:
        wanted = set(inner)
        body += [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in wanted and n not in tree.body]
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__dict__.update(namespace or {})
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), module.__dict__)
    return module
