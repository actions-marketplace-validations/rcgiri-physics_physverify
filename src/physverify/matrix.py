"""Run every check on every seeded bug and tabulate which checks notice which bug.

    python -m physverify.matrix results/detection_matrix.md

The bugs were written by the author of this package, so the catch rate below is
a measure of these bugs, not of bugs in general.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from .checks import FAMILIES, Check, Result, run_check
from .problems import heat1d, pendulum, projectile

PROBLEMS = {m.NAME: m for m in (projectile, pendulum, heat1d)}


@dataclass
class Row:
    problem: str
    bug: str | None  # None is the bug-free baseline
    results: list = field(default_factory=list)  # list of (Check, Result)

    def flagged(self) -> dict:
        """family -> labels of the checks that did not pass"""
        out: dict = {}
        for check, result in self.results:
            if not result.ok:
                out.setdefault(check.family, []).append(check.label)
        return out

    def families_present(self) -> set:
        return {check.family for check, _ in self.results}


def evaluate(module, bugs=frozenset()) -> list:
    return [(check, run_check(check)) for check in module.checks(bugs)]


def build_rows(problems=None) -> list:
    rows = []
    for name, module in PROBLEMS.items():
        if problems and name not in problems:
            continue
        rows.append(Row(name, None, evaluate(module)))
        for bug in module.BUGS:
            rows.append(Row(name, bug, evaluate(module, frozenset([bug]))))
    return rows


def _cell(row: Row, family: str) -> str:
    if family not in row.families_present():
        return "n/a"
    flagged = row.flagged().get(family)
    if not flagged:
        return "no" if row.bug else "ok"
    return "FLAGGED" if row.bug else "FALSE ALARM"


def to_markdown(rows) -> str:
    head = "| Problem | Bug | " + " | ".join(FAMILIES) + " | Predicted by design |\n"
    head += "|---|---|" + "---|" * (len(FAMILIES) + 1) + "\n"
    lines = []
    for row in rows:
        predicted = "baseline (all should pass)" if row.bug is None else ", ".join(
            sorted(PROBLEMS[row.problem].BUGS[row.bug].expected)
        ) or "none (blind spot)"
        cells = " | ".join(_cell(row, f) for f in FAMILIES)
        lines.append(f"| {row.problem} | {row.bug or '(none)'} | {cells} | {predicted} |")
    bug_rows = [r for r in rows if r.bug]
    caught = [r for r in bug_rows if r.flagged()]
    missed = [r for r in bug_rows if not r.flagged()]
    false_alarms = [r for r in rows if r.bug is None and r.flagged()]
    by_family = {f: sum(1 for r in bug_rows if f in r.flagged()) for f in FAMILIES}
    only_one = {f: sum(1 for r in bug_rows if set(r.flagged()) == {f}) for f in FAMILIES}
    summary = [
        "",
        f"Bugs seeded: {len(bug_rows)}. Flagged by at least one check: {len(caught)}. Missed by all: {len(missed)}"
        + (" (" + ", ".join(f"{r.problem}/{r.bug}" for r in missed) + ")" if missed else "")
        + ".",
        f"Bug-free baselines with a false alarm: {len(false_alarms)} of {len(rows) - len(bug_rows)}.",
        "Bugs flagged per family: " + ", ".join(f"{f} {n}" for f, n in by_family.items()) + ".",
        "Bugs flagged by that family alone: " + ", ".join(f"{f} {n}" for f, n in only_one.items()) + ".",
    ]
    return head + "\n".join(lines) + "\n" + "\n".join(summary) + "\n"


def details(rows) -> str:
    """Per-check messages, for reading why a cell is what it is."""
    out = []
    for row in rows:
        out.append(f"### {row.problem} / {row.bug or '(baseline)'}")
        for check, result in row.results:
            out.append(f"- {check.family} [{check.label}] {result.status}: {result.message}")
        out.append("")
    return "\n".join(out)


def by_check_markdown(rows, problem: str) -> str:
    """One column per individual check, for a problem whose checks differ in how they refine."""
    rows = [r for r in rows if r.problem == problem]
    labels = [(c.family, c.label) for c, _ in rows[0].results]
    head = "| Bug | " + " | ".join(f"{fam}: {label}" for fam, label in labels) + " |\n"
    head += "|---|" + "---|" * len(labels) + "\n"
    lines = []
    for row in rows:
        cells = []
        for _, result in row.results:
            cells.append(("ok" if row.bug is None else "no") if result.ok else ("FALSE ALARM" if row.bug is None else "FLAGGED"))
        lines.append(f"| {row.bug or '(none)'} | " + " | ".join(cells) + " |")
    return head + "\n".join(lines) + "\n"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    rows = build_rows()
    text = to_markdown(rows)
    print(text)
    if argv:
        path = Path(argv[0])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        path.with_name(path.stem + "_details.md").write_text(details(rows), encoding="utf-8")
        path.with_name("heat1d_by_check.md").write_text(by_check_markdown(rows, "heat1d"), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
