"""Run physverify's checks on the sibling projects and print one line per check.

    PYTHONPATH=src python scripts/audit_projects.py [--jsonl FILE] [projectile|projectile_v1|pendulum|lorenz|three_body ...]

With --jsonl, one JSON record per check is also written to FILE. The three-body Verlet checks and the solve_ivp
check need SciPy; without it only physics.py is tested.
"""

import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

from physverify.adapters import double_pendulum, lorenz, projectile_v1, projectile_v2, three_body
from physverify.checks import run_check

ADAPTERS = {
    "projectile": projectile_v2,
    "projectile_v1": projectile_v1,
    "pendulum": double_pendulum,
    "lorenz": lorenz,
    "three_body": three_body,
}


def git_head(folder: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(folder), "rev-parse", "HEAD"], capture_output=True, text=True)
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


args = sys.argv[1:]
jsonl = None
if "--jsonl" in args:
    i = args.index("--jsonl")
    jsonl = Path(args[i + 1])
    del args[i : i + 2]
which = args or list(ADAPTERS)
physverify_commit = git_head(Path(__file__).resolve().parents[1])
today = datetime.date.today().isoformat()
records = []
for name in which:
    module = ADAPTERS[name]
    source = module.source_path()
    project_commit = git_head(source.parent)
    print(f"===== {name}: {source}", flush=True)
    for check in module.checks():
        start = time.time()
        result = run_check(check)
        seconds = time.time() - start
        print(f"{check.family:9s} {check.label:58s} {result.status:12s} {result.message}  [{seconds:.1f}s]", flush=True)
        records.append(
            {
                "project": name,
                "project_commit": project_commit,
                "physverify_commit": physverify_commit,
                "date": today,
                "family": check.family,
                "label": check.label,
                "status": result.status,
                "message": result.message,
                "fitted_order": getattr(result, "fitted", None),
                "errors": [float(e) for e in getattr(result, "errors", ())],
                "seconds": round(seconds, 2),
            }
        )
if jsonl is not None:
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    with jsonl.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, default=lambda x: None if x != x else x) + "\n")
