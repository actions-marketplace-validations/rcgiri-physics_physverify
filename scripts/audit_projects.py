"""Run physverify's checks on the two sibling projects and print one line per check.

    PYTHONPATH=src python scripts/audit_projects.py [projectile|pendulum]
"""

import sys
import time

from physverify.adapters import double_pendulum, projectile_v2
from physverify.checks import run_check

ADAPTERS = {"projectile": projectile_v2, "pendulum": double_pendulum}

which = sys.argv[1:] or list(ADAPTERS)
for name in which:
    module = ADAPTERS[name]
    print(f"===== {name}: {module.source_path()}", flush=True)
    for check in module.checks():
        start = time.time()
        result = run_check(check)
        print(
            f"{check.family:9s} {check.label:42s} {result.status:12s} {result.message}  [{time.time() - start:.1f}s]",
            flush=True,
        )
