"""How the verification families compare with ordinary unit tests on the seeded bugs.

    python -m pvbench.compare results/comparison.md

Strategies, each a set of checks run on every bug:

plain tests        one run per case, compared with a reference or a known value
                   within a fixed tolerance (each problem's `smoke_checks`)
reference only     the `reference` family: an order study against an independent solution
convergence only   the `mms` family
full suite         every family

A bug counts as caught by a strategy if at least one of its checks does not
pass. Runtime is the total time of that strategy's checks over all bugs and
baselines. The plain tests use tolerances of the size an ordinary test would
(0.1% for the ODE problems, 1% for the heat solver); a tighter tolerance would
catch more bugs and need a more accurate reference, which is what the order
studies provide without having to pick a tolerance.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from physverify.checks import run_check
from .matrix import PROBLEMS

STRATEGIES = {
    "plain tests": ("smoke",),
    "reference only": ("reference",),
    "convergence only": ("mms",),
    "full suite": ("mms", "reference", "invariant", "limit", "patch"),
}


@dataclass
class Outcome:
    problem: str
    bug: str | None
    failed: dict = field(default_factory=dict)  # family -> number of checks that did not pass
    seconds: dict = field(default_factory=dict)  # family -> total runtime


def run_case(module, bug) -> Outcome:
    bugs = frozenset([bug]) if bug else frozenset()
    out = Outcome(module.NAME, bug)
    for check in module.checks(bugs) + module.smoke_checks(bugs):
        start = time.perf_counter()
        result = run_check(check)
        out.seconds[check.family] = out.seconds.get(check.family, 0.0) + time.perf_counter() - start
        if not result.ok:
            out.failed[check.family] = out.failed.get(check.family, 0) + 1
    return out


def run_all() -> list:
    outcomes = []
    for module in PROBLEMS.values():
        outcomes.append(run_case(module, None))
        for bug in module.BUGS:
            outcomes.append(run_case(module, bug))
    return outcomes


def caught(outcome: Outcome, strategy: str) -> bool:
    return any(outcome.failed.get(f) for f in STRATEGIES[strategy])


def to_markdown(outcomes) -> str:
    bug_rows = [o for o in outcomes if o.bug]
    base_rows = [o for o in outcomes if not o.bug]
    lines = [
        "| Strategy | Bugs caught | Missed | False alarms on baselines | Runtime (s) |",
        "|---|---|---|---|---|",
    ]
    for name in STRATEGIES:
        hits = sum(caught(o, name) for o in bug_rows)
        alarms = sum(caught(o, name) for o in base_rows)
        secs = sum(o.seconds.get(f, 0.0) for o in outcomes for f in STRATEGIES[name])
        lines.append(f"| {name} | {hits} of {len(bug_rows)} | {len(bug_rows) - hits} | {alarms} of {len(base_rows)} | {secs:.1f} |")
    lines += ["", "| Problem | Bug | " + " | ".join(STRATEGIES) + " |", "|---|---|" + "---|" * len(STRATEGIES)]
    for o in bug_rows:
        cells = " | ".join("caught" if caught(o, s) else "**missed**" for s in STRATEGIES)
        lines.append(f"| {o.problem} | {o.bug} | {cells} |")
    lines += ["", "Runtimes depend on the machine; the other columns do not (the checks are deterministic)."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    text = to_markdown(run_all())
    print(text)
    if argv:
        path = Path(argv[0])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
