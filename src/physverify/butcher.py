"""Order of a Runge-Kutta method from its Butcher table, by the order conditions.

A Runge-Kutta method (A, b, c) has order p exactly when b . Phi(t) = 1 / gamma(t) for every rooted
tree t with at most p vertices (Butcher). This is algebra on the coefficients: it needs no test
problem, cannot be fooled by a lucky cancellation or a superconvergent test equation, and works the
same for explicit and implicit methods.

Lessons from testing other people's code: one package's `order` labels were wrong for 3 of its
tables (one claimed 4 where the table satisfies only the order-3 conditions), and another's embedded
weights for Tsitouras 5(4) did not even sum to 1. Order studies on test equations found both, but
were slower to adjudicate than this check.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from .checks import FAIL, PASS, Result


@lru_cache(maxsize=None)
def trees(order: int) -> tuple:
    """All rooted trees with `order` vertices, each a sorted tuple of child subtrees."""
    if order == 1:
        return ((),)
    out = set()

    def forests(n, max_child):
        # multisets of trees with n vertices in total, children in non-increasing canonical order
        if n == 0:
            yield ()
            return
        for k in range(n, 0, -1):
            for t in trees(k):
                if max_child is not None and (k, t) > max_child:
                    continue
                for rest in forests(n - k, (k, t)):
                    yield ((k, t),) + rest

    for forest in forests(order - 1, None):
        out.add(tuple(sorted((t for _, t in forest), key=repr)))
    return tuple(sorted(out, key=repr))


def _size(t) -> int:
    return 1 + sum(_size(s) for s in t)


def _gamma(t) -> int:
    g = _size(t)
    for s in t:
        g *= _gamma(s)
    return g


def _phi(t, A, e):
    v = e.copy()
    for s in t:
        v = v * (A @ _phi(s, A, e))
    return v


def order_residuals(A, b, max_order: int = 6) -> dict:
    """{order: largest |b . Phi(t) - 1/gamma(t)| over the trees of that order}."""
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    e = np.ones(len(b))
    return {p: max(abs(float(b @ _phi(t, A, e)) - 1.0 / _gamma(t)) for t in trees(p)) for p in range(1, max_order + 1)}


def tableau_order(A, b, *, max_order: int = 6, tol: float = 1e-8) -> int:
    """Highest p <= max_order such that every condition up to order p holds within tol."""
    p = 0
    for q, r in order_residuals(A, b, max_order).items():
        if r > tol:
            break
        p = q
    return p


def check_tableau(A, b, c=None, *, claimed: int, label: str = "", tol: float = 1e-8, max_order: int | None = None) -> Result:
    """PASS when the table has at least the claimed order; FAIL when it has less.

    The default tolerance 1e-8 accepts coefficients typed with 9 or 10 digits (a real package had
    residuals of 2e-10 for that reason), while a missing order shows residuals of 1e-4 or more.
    The message gives the residuals, so a table whose conditions hold only to about 1e-10 is visible, and a claim that is lower than the true
    order is noted rather than failed. If `c` is given, the row sums of A are compared with it.
    """
    top = max_order or claimed + 1
    res = order_residuals(A, b, top)
    p = tableau_order(A, b, max_order=top, tol=tol)
    shown = ", ".join(f"{q}: {r:.1e}" for q, r in res.items())
    prefix = f"{label}: " if label else ""
    notes = []
    if c is not None:
        rs = float(np.max(np.abs(np.asarray(A, float).sum(axis=1) - np.asarray(c, float))))
        if rs > tol:
            notes.append(f"row sums of A differ from c by {rs:.1e}")
    worst_kept = max((r for q, r in res.items() if q <= max(p, 1)), default=0.0)
    if p >= 1 and worst_kept > 1e-13:
        notes.append(f"conditions hold only to {worst_kept:.0e} (coefficients with limited digits?)")
    tail = ("; " + "; ".join(notes)) if notes else ""
    if p < claimed:
        return Result(FAIL, f"{prefix}claims order {claimed} but satisfies the order conditions only up to {p} "
                            f"(largest residual per order: {shown}){tail}")
    if p > claimed:
        return Result(PASS, f"{prefix}claims order {claimed}; the conditions hold up to at least {p}, so the claim is "
                            f"conservative ({shown}){tail}")
    return Result(PASS, f"{prefix}order {claimed} confirmed by the order conditions ({shown}){tail}")
