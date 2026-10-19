"""Method of Manufactured Solutions for systems of ODEs.

You pick a smooth function u(t). Substituting it into an *independent*
reference operator f_ref leaves a residual s(t) = u'(t) - f_ref(t, u(t)).
The code under test is then run on  y' = f_test(t, y) + s(t).  If f_test
agrees with f_ref, u(t) is its exact solution and the error must shrink at the
scheme's design order. If f_test differs, the error stops shrinking.

Two points that are easy to get wrong:

* The reference operator must be written independently of the code under
  test. If s(t) is built from the code's own right-hand side, a wrong
  right-hand side passes.
* The error is measured at a fixed final time, so the code must be driven for
  an exact number of steps; see the `integrate` contract below.

The `integrate` contract used throughout:

    integrate(source, y0, t_end, n_steps) -> state at t_end

`source(t)` returns the additive forcing (a vector, or 0.0). The adapter for a
given code decides how to inject it.
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from .checks import OrderResult
from .order import check_order


def zero_source(t):
    return 0.0


def complex_step_derivative(u: Callable, t: float, h: float = 1e-30) -> np.ndarray:
    """du/dt to machine precision, for u written with NumPy functions of t.

    u must accept a complex t and avoid abs(), max() and similar non-analytic
    operations.
    """
    return np.imag(np.asarray(u(t + 1j * h), dtype=complex)) / h


class ManufacturedODE:
    def __init__(self, u: Callable, rhs_ref: Callable, du: Callable | None = None):
        self._u = u
        self.rhs_ref = rhs_ref
        self._du = du

    def value(self, t: float) -> np.ndarray:
        return np.asarray(self._u(t), dtype=float)

    def derivative(self, t: float) -> np.ndarray:
        if self._du is not None:
            return np.asarray(self._du(t), dtype=float)
        return complex_step_derivative(self._u, t)

    def forcing(self, t: float) -> np.ndarray:
        return self.derivative(t) - np.asarray(self.rhs_ref(t, self.value(t)), dtype=float)


def max_abs_error(a, b) -> float:
    with np.errstate(all="ignore"):
        return float(np.max(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))))


def mms_order_study(
    integrate: Callable,
    mms: ManufacturedODE,
    t_end: float,
    ns,
    expected_order: float,
    **order_kwargs,
) -> OrderResult:
    """Run `integrate` with the manufactured forcing at several step counts."""
    y0 = mms.value(0.0)
    y_exact = mms.value(t_end)
    hs, errs = [], []
    for n in ns:
        y_end = integrate(mms.forcing, y0, t_end, n)
        hs.append(t_end / n)
        errs.append(max_abs_error(y_end, y_exact))
    return check_order(hs, errs, expected_order, **order_kwargs)
