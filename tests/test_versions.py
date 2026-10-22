"""The version is the same everywhere it is written, so a release cannot ship with a stale one."""

import re
from pathlib import Path

import physverify

ROOT = Path(__file__).resolve().parents[1]


def _read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_versions_agree():
    v = physverify.__version__
    assert re.search(r'^version = "([^"]+)"', _read("pyproject.toml"), re.M).group(1) == v
    assert re.search(r"^version: (\S+)", _read("CITATION.cff"), re.M).group(1) == v
    readme = _read("README.md")
    assert f"(v{v})" in readme and f"physverify@v{v}" in readme, "update the version in README.md"
    assert f"physverify@v{v}" in _read("docs/index.md"), "update the action version in docs/index.md"
