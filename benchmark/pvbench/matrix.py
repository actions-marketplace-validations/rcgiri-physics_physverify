"""Run every check on every seeded bug and tabulate which checks notice which bug.

    python -m pvbench.matrix results/detection_matrix.md

This also writes detection_matrix.json (every check's full status, message and
run time, with how and where it was made) and run_time.md next to it.

The bugs were written by the author of this package, so the catch rate below is
a measure of these bugs, not of bugs in general.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from physverify.checks import FAIL, FAMILIES, Check, Result, run_check
from .problems import heat1d, kepler, pendulum, projectile, sod

PROBLEMS = {m.NAME: m for m in (projectile, pendulum, kepler, heat1d, sod)}


@dataclass
class Row:
    problem: str
    bug: str | None  # None is the bug-free baseline
    results: list = field(default_factory=list)  # list of (Check, Result)
    seconds: list = field(default_factory=list)  # run time of each check, when measured

    def flagged(self) -> dict:
        """family -> labels of the checks that did not pass"""
        out: dict = {}
        for check, result in self.results:
            if not result.ok:
                out.setdefault(check.family, []).append(check.label)
        return out

    def flagged_by_fail(self) -> bool:
        """At least one check gave FAIL, a clean detection (not only INCONCLUSIVE or ERROR)."""
        return any(result.status == FAIL for _, result in self.results)

    def families_present(self) -> set:
        return {check.family for check, _ in self.results}


def evaluate(module, bugs=frozenset()) -> list:
    return [(check, run_check(check)) for check in module.checks(bugs)]


def evaluate_timed(problem, bug) -> Row:
    row = Row(problem, bug)
    for check in PROBLEMS[problem].checks(frozenset([bug]) if bug else frozenset()):
        start = time.perf_counter()
        row.results.append((check, run_check(check)))
        row.seconds.append(time.perf_counter() - start)
    return row


def build_rows(problems=None) -> list:
    rows = []
    for name, module in PROBLEMS.items():
        if problems and name not in problems:
            continue
        rows.append(evaluate_timed(name, None))
        for bug in module.BUGS:
            rows.append(evaluate_timed(name, bug))
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
    by_fail = [r for r in caught if r.flagged_by_fail()]
    by_family = {f: sum(1 for r in bug_rows if f in r.flagged()) for f in FAMILIES}
    only_one = {f: sum(1 for r in bug_rows if set(r.flagged()) == {f}) for f in FAMILIES}
    summary = [
        "",
        f"Bugs seeded: {len(bug_rows)}. Flagged by at least one check: {len(caught)}. Missed by all: {len(missed)}"
        + (" (" + ", ".join(f"{r.problem}/{r.bug}" for r in missed) + ")" if missed else "")
        + ".",
        f"Of the {len(caught)} flagged: {len(by_fail)} by at least one FAIL, {len(caught) - len(by_fail)} only by"
        " INCONCLUSIVE or ERROR"
        + (" (" + ", ".join(f"{r.problem}/{r.bug}" for r in caught if not r.flagged_by_fail()) + ")"
           if len(by_fail) < len(caught) else "")
        + ".",
        f"Bug-free baselines with a false alarm: {len(false_alarms)} of {len(rows) - len(bug_rows)}.",
        "Bugs flagged per family: " + ", ".join(f"{f} {n}" for f, n in by_family.items()) + ".",
        "Bugs flagged by that family alone: " + ", ".join(f"{f} {n}" for f, n in only_one.items()) + ".",
    ]
    return head + "\n".join(lines) + "\n" + "\n".join(summary) + "\n"


def provenance() -> dict:
    """How and where a result file was made; kept out of the Markdown so the committed tables stay comparable."""
    import datetime
    import platform
    import subprocess

    import numpy

    from physverify import __version__

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10,
                                cwd=Path(__file__).resolve().parent).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        commit = None
    return {
        "physverify": __version__,
        "git_commit": commit,
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "platform": platform.platform(),
        "date": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }


def to_json(rows) -> str:
    """One record per (problem, bug, check) with the full status, message, prediction and run time."""
    records = []
    for row in rows:
        predicted = sorted(PROBLEMS[row.problem].BUGS[row.bug].expected) if row.bug else []
        seconds = row.seconds or [None] * len(row.results)
        for (check, result), sec in zip(row.results, seconds):
            records.append({
                "problem": row.problem,
                "bug": row.bug,
                "family": check.family,
                "check": check.label,
                "status": result.status,
                "message": result.message,
                "predicted_to_flag": check.family in predicted,
                "seconds": None if sec is None else round(sec, 4),
            })
    return json.dumps({"provenance": provenance(), "records": records}, indent=1) + "\n"


def run_time(rows) -> str:
    """Total run time per check family and problem, over the baseline and every bug (not deterministic)."""
    totals: dict = {}
    for row in rows:
        for (check, _), sec in zip(row.results, row.seconds):
            totals.setdefault(row.problem, {}).setdefault(check.family, 0.0)
            totals[row.problem][check.family] += sec
    lines = [
        "# Run time per check family",
        "",
        "Seconds, summed over the baseline and every seeded bug of each problem, on the machine recorded in",
        "detection_matrix.json (`provenance`). Generated by `python scripts/reproduce_all.py`; it varies between runs.",
        "",
        "| Problem | " + " | ".join(FAMILIES) + " | Total |",
        "|---|" + "---|" * (len(FAMILIES) + 1),
    ]
    for problem, fam in totals.items():
        cells = " | ".join(f"{fam[f]:.2f}" if f in fam else "n/a" for f in FAMILIES)
        lines.append(f"| {problem} | {cells} | {sum(fam.values()):.2f} |")
    return "\n".join(lines) + "\n"


def details(rows) -> str:
    """Per-check messages, for reading why a cell is what it is."""
    out = []
    for row in rows:
        out.append(f"### {row.problem} / {row.bug or '(baseline)'}")
        for check, result in row.results:
            out.append(f"- {check.family} [{check.label}] {result.status}: {result.message}")
        out.append("")
    return "\n".join(out)


REPO = "https://github.com/rcgiri-physics/physverify/blob/main/"


def bug_switches(problem: str, bug: str) -> list:
    """(path, line number, code) of every line that switches the bug on: `"bug" in bugs`."""
    root = Path(__file__).resolve().parents[2]
    files = [Path(PROBLEMS[problem].__file__), Path(__file__).resolve().parent / "problems" / "_common.py"]
    out = []
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if f'"{bug}" in bugs' in line:
                out.append((f.resolve().relative_to(root).as_posix(), n, line.strip()))
    return out


def catalogue(rows) -> str:
    """One entry per seeded bug: what is changed, the expected symptom, predicted and observed families."""
    out = [
        "# Seeded-bug catalogue",
        "",
        "Generated by `python -m pvbench.matrix results/detection_matrix.md`. Each bug is switched on by",
        "name in the problem's solver; the lines that switch it on are linked under each bug.",
        "Predictions and symptoms were written from reasoning before the checks were run.",
        "",
    ]
    for row in rows:
        if row.bug is None:
            continue
        info = PROBLEMS[row.problem].BUGS[row.bug]
        flagged = sorted(row.flagged())
        out += [
            f"## {row.problem} / {row.bug}",
            "",
            f"- Change: {info.description}",
            f"- Expected symptom: {info.symptom or '(not recorded)'}",
            f"- Predicted to be flagged by: {', '.join(sorted(info.expected)) or 'nothing (blind spot)'}",
            f"- Flagged by: {', '.join(flagged) or 'nothing'}",
            "- Outcome of its " + str(len(row.results)) + " checks: " + ", ".join(
                f"{n} {s}" for s, n in sorted(Counter(r.status for _, r in row.results).items())),
        ]
        switches = bug_switches(row.problem, row.bug)
        if switches:
            out.append("- Where it is switched on:")
            out += [f"    - [{path}:{n}]({REPO}{path}#L{n}): `{code}`" for path, n, code in switches]
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
        path.with_name("bug_catalogue.md").write_text(catalogue(rows), encoding="utf-8")
        path.with_suffix(".json").write_text(to_json(rows), encoding="utf-8")
        path.with_name("run_time.md").write_text(run_time(rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
