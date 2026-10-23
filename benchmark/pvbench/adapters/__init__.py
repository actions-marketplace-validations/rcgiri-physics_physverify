"""Adapters that connect physverify to existing simulation code (read-only)."""

from __future__ import annotations

import os
from pathlib import Path


def sibling_project(env_var: str, folder: str) -> Path:
    """Folder of another project: $env_var if set, else a sibling of this repository."""
    if os.environ.get(env_var):
        return Path(os.environ[env_var])
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root.parent / folder
