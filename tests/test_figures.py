"""The committed figures are what scripts/make_figures.py draws now, so they cannot go stale."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_convergence_figure_is_up_to_date():
    spec = importlib.util.spec_from_file_location("make_figures", ROOT / "scripts" / "make_figures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    committed = (ROOT / "docs" / "images" / "convergence.svg").read_text(encoding="utf-8")
    assert module.svg() == committed, "run python scripts/make_figures.py and commit the figure"
