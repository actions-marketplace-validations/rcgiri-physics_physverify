"""SKIP when an optional package is missing; a time budget for a slow check."""
import time

from physverify import Check, Result, requires
from physverify.report import run_checks, to_text


def polygon_area():
    requires("shapely_not_installed_here")  # raises SkipCheck when the package is missing
    return Result("PASS", "polygon area matches")


def slow():
    time.sleep(10)
    return Result("PASS", "")


checks = [Check("limit", "polygon area", polygon_area), Check("limit", "slow check", slow, budget_s=1)]
print(to_text(run_checks(checks)))
