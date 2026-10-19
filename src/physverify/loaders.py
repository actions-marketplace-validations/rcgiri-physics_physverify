"""Import a module from a path without touching its folder.

Used by the adapters that test other people's code. Nothing is written next to
the module (no __pycache__), and optional plotting imports can be stubbed so a
simulation file can be imported on a machine without matplotlib.
"""

from __future__ import annotations

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
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old_flag
        for stub in added:
            sys.modules.pop(stub, None)
    return module
