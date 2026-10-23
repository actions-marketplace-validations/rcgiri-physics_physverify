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


class Placeholder:
    """Stand-in for a name from a module that is not installed.

    Calling it returns another placeholder, except that calling it with a single
    function returns that function, so stubbed decorators (``@app.route(...)``,
    ``@jit``) leave the decorated code usable. Attribute access also returns a
    placeholder. A tested code path that really uses the stub gets a placeholder
    back instead of a result, which the checks then report.
    """

    def __init__(self, name: str = "stub"):
        self._name = name

    def __call__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and callable(args[0]) and not isinstance(args[0], Placeholder):
            return args[0]
        return Placeholder(f"{self._name}()")

    def __getattr__(self, attr):
        if attr.startswith("__"):
            raise AttributeError(attr)
        return Placeholder(f"{self._name}.{attr}")

    def __repr__(self):
        return f"<stub {self._name}>"


def _stub_module(name: str, attrs=()) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__dict__["__stub__"] = True
    for a in attrs:
        setattr(mod, a, Placeholder(f"{name}.{a}"))
    return mod


def stub_modules(spec, *, force: bool = False) -> list[str]:
    """Install stub modules for imports a tested code path does not use.

    `spec` is an iterable of module names, or a mapping from a module name to the
    names it must provide (``{"sklearn.metrics": ["accuracy_score"]}``), so that
    ``from sklearn.metrics import accuracy_score`` succeeds. Parent packages are
    created as needed. A module that imports for real is left alone unless
    `force` is true. Returns the names installed.
    """
    items = spec.items() if hasattr(spec, "items") else ((s, ()) for s in spec)
    installed = []
    for name, attrs in items:
        if not force:
            try:
                importlib.import_module(name)
                continue
            except ImportError:
                pass
        parts = name.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            if parent not in sys.modules:
                sys.modules[parent] = _stub_module(parent)
                installed.append(parent)
        sys.modules[name] = _stub_module(name, attrs)
        installed.append(name)
        parent, _, child = name.rpartition(".")
        if parent:
            setattr(sys.modules[parent], child, sys.modules[name])
    return installed


def run_script(path, *, argv=(), stubs=None, inputs=None) -> tuple[dict, str]:
    """Run a whole script as __main__ and return (its globals, what it printed).

    For scripts whose results are only module-level variables (coursework,
    notebooks exported to .py, demos). Matplotlib is switched to a non-interactive
    backend and plt.show() does nothing, so the run never waits for a window.

    `inputs` answers the script's input() prompts in order (interactive scripts);
    a prompt with no answer left raises EOFError instead of waiting.
    """
    import builtins
    import contextlib
    import io
    import runpy

    if stubs:
        stub_modules(stubs)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.show = lambda *a, **k: None
    except ImportError:
        pass
    old_argv, old_input = sys.argv, builtins.input
    sys.argv = [str(path), *argv]
    if inputs is not None:
        answers = iter([str(a) for a in inputs])

        def _input(prompt=""):
            try:
                return next(answers)
            except StopIteration:
                raise EOFError(f"the script asked for more input than given: {prompt!r}") from None

        builtins.input = _input
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            globs = runpy.run_path(str(path), run_name="__main__")
    finally:
        sys.argv, builtins.input = old_argv, old_input
    return globs, out.getvalue()


def load_module_from_path(name: str, path, stubs=()):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    added = stub_modules(stubs)

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


def load_definitions_from_path(name: str, path, *, keep=(), inner=(), namespace=None, stubs=()):
    """Load only the definitions of a script whose top level runs a simulation.

    Many research scripts parse argv, open a window or run a long simulation at
    import. This executes only the top-level imports, functions and classes, and
    the top-level assignments to the names in `keep` (constants the functions
    use). `inner` names functions defined inside other functions (for example
    marimo or Jupyter-exported cells); they are lifted to module level, and
    their imports must then come from `namespace`.

    Nothing else in the file runs, so a function that relies on a global set by
    the skipped code fails with NameError; set it on the returned module.

    `stubs` names modules (or maps module names to the names they must provide, see
    `stub_modules`) to replace with stubs when they are not installed
    (pygame, IPython, orbax, ...), for imports the tested functions do not use.
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
    stub_modules(stubs)
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__dict__.update(namespace or {})
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), module.__dict__)
    return module


def _top_level_names(node) -> list[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def _used_names(node) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def extract_functions(path, names, *, namespace=None, stubs=()) -> types.ModuleType:
    """Load the named top-level functions or classes of one file, plus the same-file definitions they use.

    For a package that cannot be installed or imported as a whole (a compiled extension, a dependency
    that needs a newer NumPy, an import of a GUI toolkit), when the function under test is plain Python.
    The named definitions are taken with every top-level function, class or simple assignment they
    refer to, followed transitively (a `curvature` that calls `centered_diff` brings it along). Each
    top-level import is run on its own; one that fails is skipped and listed in the returned module's
    `__skipped_imports__`, so a NameError later points at it. Names the code needs from other files of
    the package can be passed in `namespace` (for example a stub `gf` object with the one function used).

    Nothing else in the file runs. The returned module records what was loaded in `__extracted__`.
    """
    path = Path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    defs: dict[str, list] = {}
    for node in tree.body:
        for n in _top_level_names(node):
            defs.setdefault(n, []).append(node)
    missing = [n for n in names if n not in defs]
    if missing:
        raise KeyError(f"not defined at the top level of {path.name}: {', '.join(missing)}")
    wanted: set = set()
    todo = list(names)
    while todo:
        n = todo.pop()
        if n in wanted:
            continue
        wanted.add(n)
        for node in defs.get(n, ()):
            todo += [m for m in _used_names(node) if m in defs and m not in wanted]
    future = [node for node in tree.body if isinstance(node, ast.ImportFrom) and node.module == "__future__"]
    chosen = future + [node for node in tree.body if set(_top_level_names(node)) & wanted]
    stub_modules(stubs)
    module = types.ModuleType(path.stem)
    module.__file__ = str(path)
    module.__dict__.update(namespace or {})
    skipped = []
    old_flag = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)) and node not in future:
                if isinstance(node, ast.ImportFrom) and node.level:
                    skipped.append(ast.unparse(node) + "  (relative import)")
                    continue
                try:
                    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), module.__dict__)
                except Exception as exc:  # noqa: BLE001 - any failing import is skipped and reported
                    skipped.append(f"{ast.unparse(node)}  ({type(exc).__name__}: {exc})")
        exec(compile(ast.Module(body=chosen, type_ignores=[]), str(path), "exec"), module.__dict__)
    finally:
        sys.dont_write_bytecode = old_flag
    module.__skipped_imports__ = skipped
    module.__extracted__ = sorted(wanted)
    return module
