"""Command line.

    physverify run SPEC.py [SPEC.py ...] [--json FILE|-] [--html FILE] [--quiet]
    physverify matrix [OUT.md]
    physverify compare [OUT.md]

`run` exits 0 when every check passes (PASS or EXACT), 1 when any does not,
and 2 when a spec cannot be loaded. A spec is a Python file defining
`checks()`; see examples/verify_damped_oscillator.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__


def _cmd_run(args) -> int:
    from .report import load_spec, run_checks, to_html, to_json, to_text

    outcomes = []
    for spec in args.specs:
        try:
            checks = load_spec(spec)
        except Exception as exc:
            print(f"physverify: cannot load {spec}: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
        outcomes += run_checks(checks)
    source = ", ".join(str(Path(s)) for s in args.specs)
    if args.json == "-":
        print(to_json(outcomes, source))
    else:
        if not args.quiet:
            print(to_text(outcomes))
        if args.json:
            Path(args.json).write_text(to_json(outcomes, source), encoding="utf-8")
    if args.html:
        Path(args.html).write_text(to_html(outcomes, source=source), encoding="utf-8")
    return 0 if all(o.result.ok for o in outcomes) else 1


def _cmd_matrix(args) -> int:
    from . import matrix

    return matrix.main([args.out] if args.out else [])


def _cmd_compare(args) -> int:
    from . import compare

    return compare.main([args.out] if args.out else [])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="physverify", description="Verification checks for physics simulation code.")
    parser.add_argument("--version", action="version", version=f"physverify {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the checks defined in one or more spec files")
    run.add_argument("specs", nargs="+", help="Python files that define checks()")
    run.add_argument("--json", metavar="FILE", help="write results as JSON to FILE, or to stdout with -")
    run.add_argument("--html", metavar="FILE", help="write a self-contained HTML report")
    run.add_argument("--quiet", action="store_true", help="no text output")
    run.set_defaults(func=_cmd_run)

    m = sub.add_parser("matrix", help="run the seeded-bug benchmark")
    m.add_argument("out", nargs="?", help="also write the tables next to this Markdown file")
    m.set_defaults(func=_cmd_matrix)

    c = sub.add_parser("compare", help="compare the families with plain tests on the seeded bugs")
    c.add_argument("out", nargs="?", help="also write the table to this Markdown file")
    c.set_defaults(func=_cmd_compare)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
