"""pytest plugin: every check in a `verify_*.py` file becomes a test.

A `verify_*.py` file defines `checks()`, returning a list of physverify.Check
(the same spec format as `physverify run`). With physverify installed, plain
`pytest` collects them; without installing, use `pytest -p physverify.pytest_plugin`.
Files named verify_*.py that do not define checks() are skipped. Turn the
plugin off with `-p no:physverify`.
"""

from __future__ import annotations

import pytest

from .checks import OrderResult, run_check


def pytest_collect_file(file_path, parent):
    if file_path.suffix == ".py" and file_path.name.startswith("verify_"):
        return VerifyFile.from_parent(parent, path=file_path)
    return None


class CheckFailed(Exception):
    pass


class VerifyFile(pytest.File):
    def collect(self):
        from .report import load_spec

        try:
            checks = load_spec(self.path)
        except AttributeError as exc:
            if "does not define checks()" in str(exc):
                return
            raise
        seen = {}
        for check in checks:
            name = f"{check.family}: {check.label}"
            seen[name] = seen.get(name, 0) + 1
            if seen[name] > 1:
                name = f"{name} [{seen[name]}]"
            yield CheckItem.from_parent(self, name=name, check=check)


class CheckItem(pytest.Item):
    def __init__(self, *, check, **kwargs):
        super().__init__(**kwargs)
        self.check = check
        self.add_marker(pytest.mark.physverify)

    def runtest(self):
        result = run_check(self.check)
        self.user_properties.append(("status", result.status))
        if not result.ok:
            raise CheckFailed(result)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, CheckFailed):
            result = excinfo.value.args[0]
            lines = [f"{result.status}: {result.message}"]
            if isinstance(result, OrderResult) and result.hs:
                lines.append(f"{'h':>12s} {'error':>12s}")
                lines += [f"{h:12.4g} {e:12.4g}" for h, e in zip(result.hs, result.errors)]
            return "\n".join(lines)
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, None, f"{self.check.family}: {self.check.label}"


def pytest_configure(config):
    config.addinivalue_line("markers", "physverify: a check collected from a verify_*.py file")
