"""Every seeded method bug is caught by the check named for it, and every control passes."""

from physverify.checks import FAIL
from physverify.method_bugs import run_all


def test_every_method_bug_is_caught_and_every_control_passes():
    for case, result in run_all():
        if case.buggy:
            assert result.status == FAIL, (case.name, result.message)
        else:
            assert result.status in ("PASS", "EXACT"), (case.name, result.message)


def test_committed_method_bug_table_matches_a_fresh_run():
    from pathlib import Path

    from physverify.method_bugs import to_markdown

    committed = (Path(__file__).resolve().parents[1] / "results" / "method_bugs.md").read_text(encoding="utf-8")
    assert to_markdown(run_all()) in committed
