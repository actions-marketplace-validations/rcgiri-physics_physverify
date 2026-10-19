"""Result types shared by every check."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

PASS = "PASS"
FAIL = "FAIL"
EXACT = "EXACT"  # error below the noise floor at every resolution
INCONCLUSIVE = "INCONCLUSIVE"
ERROR = "ERROR"  # the code under test raised an exception

FAMILIES = ("mms", "reference", "invariant", "limit")


@dataclass
class Result:
    status: str
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status in (PASS, EXACT)


@dataclass
class OrderResult(Result):
    expected: float = float("nan")
    fitted: float = float("nan")
    hs: tuple = ()
    errors: tuple = ()


@dataclass
class Check:
    """One runnable check. `family` says which kind of evidence it gives:

    mms        manufactured-solution order study against an independent reference operator
    reference  comparison with an independently written reference solution
    invariant  drift of a conserved quantity as the resolution is refined
    limit      a known limiting case (analytic range, normal-mode frequencies, ...)
    """

    family: str
    label: str
    run: Callable[[], Result]


def run_check(check: Check) -> Result:
    try:
        with np.errstate(all="ignore"):  # a buggy code may overflow; the order check reports non-finite errors
            return check.run()
    except Exception as exc:  # the code under test may crash; that is a finding too
        return Result(ERROR, f"{type(exc).__name__}: {exc}")
