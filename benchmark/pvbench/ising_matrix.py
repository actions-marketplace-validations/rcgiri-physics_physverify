"""Run every Ising check on every seeded bug; write the table, the prediction scorecard and the messages.

    python -m pvbench.ising_matrix results/ising_matrix.md

A check "flags" a bug when it returns FAIL or ERROR. INCONCLUSIVE is shown as
such and is neither a catch nor a pass. Takes several minutes (plain NumPy).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from physverify.checks import ERROR, FAIL, INCONCLUSIVE, run_check
from physverify.stochastic import ising
from physverify.stochastic.checks import FAMILIES

SHORT = {"PASS": "ok", "EXACT": "ok", FAIL: "FAIL", ERROR: "ERROR", INCONCLUSIVE: "inconcl.", "SKIP": "skip"}


def run_row(bug=None, algorithm=None):
    bugs = frozenset([bug]) if bug else frozenset()
    out = []
    for check in ising.checks(bugs, algorithm):
        start = time.perf_counter()
        result = run_check(check)
        out.append((check, result, time.perf_counter() - start))
    return out


def run_all(progress=False):
    rows = []
    for alg in ising.VARIANTS:
        rows.append((alg, None, run_row(None, alg)))
        if progress:
            print(f"baseline {alg} done", file=sys.stderr)
    for bug, info in ising.BUGS.items():
        rows.append((info.algorithm, bug, run_row(bug)))
        if progress:
            print(f"{bug} done", file=sys.stderr)
    return rows


def flagged(results):
    return {c.family for c, r, _ in results if r.status in (FAIL, ERROR)}


def to_markdown(rows) -> str:
    head = "| Algorithm | Bug | " + " | ".join(FAMILIES) + " |\n|---|---|" + "---|" * len(FAMILIES) + "\n"
    lines = []
    for alg, bug, results in rows:
        by_family = {c.family: r for c, r, _ in results}
        predicted = ising.BUGS[bug].predicted if bug else frozenset()
        cells = []
        for fam in FAMILIES:
            r = by_family.get(fam)
            cell = SHORT.get(r.status, r.status) if r else "n/a"
            if bug and fam in predicted:
                cell += " (p)"
            cells.append(cell)
        lines.append(f"| {alg} | {bug or '(none)'} | " + " | ".join(cells) + " |")
    bug_rows = [r for r in rows if r[1]]
    controls = [r for r in bug_rows if ising.BUGS[r[1]].negative_control]
    real = [r for r in bug_rows if not ising.BUGS[r[1]].negative_control]
    caught = [r for r in real if flagged(r[2])]
    baseline_alarms = [r for r in rows if not r[1] and flagged(r[2])]
    baseline_inconclusive = sum(1 for r in rows if not r[1] for _, res, _ in r[2] if res.status == INCONCLUSIVE)
    hit = miss = surprise = 0
    for _, bug, results in bug_rows:
        p, f = ising.BUGS[bug].predicted, flagged(results)
        hit += len(p & f)
        miss += len(p - f)
        surprise += len(f - p)
    summary = [
        "",
        "(p) marks a check predicted, before running, to flag the bug. ok = PASS or EXACT; inconcl. = INCONCLUSIVE; "
        "n/a = the check does not apply to the algorithm (scripted_rng and acceptance need single-site updates).",
        "",
        f"Seeded bugs: {len(real)}, plus {len(controls)} equivalent mutant (negative control). "
        f"Flagged by at least one check: {len(caught)} of {len(real)}"
        + (" (missed: " + ", ".join(r[1] for r in real if not flagged(r[2])) + ")" if len(caught) < len(real) else "")
        + ".",
        f"Bug-free baselines with a FAIL: {len(baseline_alarms)} of {len(rows) - len(bug_rows)}; "
        f"statistical INCONCLUSIVE on baselines: {baseline_inconclusive}.",
        f"Predictions: {hit} predicted detections happened, {miss} predicted detections did not, "
        f"{surprise} detections were not predicted (details in the scorecard).",
        "Each statistical check has a false-alarm rate of at most 0.001 (Bonferroni within the check); "
        "with 6 statistical checks per sampler the rate per sampler is at most 0.006.",
    ]
    return head + "\n".join(lines) + "\n" + "\n".join(summary) + "\n"


def scorecard(rows) -> str:
    out = [
        "# Ising seeded bugs: predictions against outcomes",
        "",
        "Predictions and symptoms were committed (src/physverify/stochastic/ising.py, commit 0297ffe) before any",
        "bug was run, and have not been changed since.",
        "",
        "One check was changed after a result was seen. `scripted_rng` and `acceptance` first ran only in a field",
        "(h = 0.25), where no single flip has dE = 0, so the equivalent mutant `reject_zero_de` was invisible to",
        "both: a unit test showed this before the first full matrix run. Both checks now also run at h = 0. Their",
        "detection of `reject_zero_de` below is therefore not a blind result.",
        "",
    ]
    for alg, bug, results in rows:
        if not bug:
            continue
        info = ising.BUGS[bug]
        f = flagged(results)
        out += [
            f"## {bug} ({alg}){' — negative control' if info.negative_control else ''}",
            "",
            f"- Change: {info.description}",
            f"- Expected symptom: {info.symptom}",
            f"- Predicted: {', '.join(sorted(info.predicted)) or 'nothing'}",
            f"- Flagged: {', '.join(sorted(f)) or 'nothing'}",
            f"- Predicted but not flagged: {', '.join(sorted(info.predicted - f)) or '-'}",
            f"- Flagged but not predicted: {', '.join(sorted(f - info.predicted)) or '-'}",
            "",
        ]
    return "\n".join(out)


def details(rows) -> str:
    out = []
    for alg, bug, results in rows:
        out.append(f"### {alg} / {bug or '(baseline)'}")
        for c, r, secs in results:
            out.append(f"- {c.family} [{c.label}] {r.status} ({secs:.1f} s): {r.message}")
        out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    rows = run_all(progress=True)
    text = to_markdown(rows)
    print(text)
    if argv:
        path = Path(argv[0])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        path.with_name("ising_scorecard.md").write_text(scorecard(rows), encoding="utf-8")
        path.with_name("ising_details.md").write_text(details(rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
