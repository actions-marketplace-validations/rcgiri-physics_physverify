"""Manufactured solutions with symbolic derivatives (optional; needs SymPy).

    pip install physverify[symbolic]

Hand-derived source terms are a common place for the verification itself to
go wrong. Here you write the manufactured solution and the PDE operator once,
symbolically, and the source term is derived and turned into NumPy functions.

Example, the 1D heat equation u_t = alpha u_xx + s:

    import sympy as sp
    x, t = sp.symbols("x t")
    u = sp.exp(-t) * sp.sin(sp.pi * x)
    ms = manufactured_pde(u, lambda u: sp.diff(u, t) - 0.7 * sp.diff(u, x, 2), (x, t))
    ms.source(xs, 0.3)   # NumPy array of s at the points xs, time 0.3

The operator must be written independently of the code under test, for the same
reason as the ODE reference operator (see physverify.mms).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


def _sympy():
    try:
        import sympy
    except ImportError as exc:  # pragma: no cover - exercised only without sympy
        raise ImportError("physverify.symbolic needs SymPy: pip install physverify[symbolic]") from exc
    return sympy


@dataclass
class ManufacturedPDE:
    solution_expr: object
    source_expr: object
    solution: Callable
    source: Callable


def _vectorise(f, n_args):
    """lambdify returns a scalar for a constant expression; broadcast it to the inputs' shape."""

    def g(*args):
        value = f(*args)
        shape = np.broadcast(*[np.asarray(a) for a in args[:n_args]]).shape
        return np.broadcast_to(np.asarray(value, dtype=float), shape).copy() if shape else float(value)

    return g


def manufactured_pde(u_expr, operator: Callable, variables) -> ManufacturedPDE:
    """Source s = operator(u) for a manufactured solution u.

    `operator(u)` returns the PDE residual for u, written with sympy.diff, so that
    u solves  operator(u) = s  exactly. `variables` is the tuple of SymPy symbols
    the NumPy functions take, in order (for example (x, t) or (x, y, t)).
    """
    sp = _sympy()
    variables = tuple(variables)
    source_expr = sp.simplify(operator(u_expr))
    n = len(variables)
    return ManufacturedPDE(
        u_expr,
        source_expr,
        _vectorise(sp.lambdify(variables, u_expr, "numpy"), n),
        _vectorise(sp.lambdify(variables, source_expr, "numpy"), n),
    )


def manufactured_ode(u_exprs, rhs_ref: Callable, t_symbol):
    """A physverify.ManufacturedODE whose derivative is taken symbolically.

    `u_exprs` is a list of SymPy expressions in `t_symbol`, one per state component.
    """
    from .mms import ManufacturedODE

    sp = _sympy()
    u_f = sp.lambdify(t_symbol, list(u_exprs), "numpy")
    du_f = sp.lambdify(t_symbol, [sp.diff(e, t_symbol) for e in u_exprs], "numpy")
    return ManufacturedODE(
        lambda t: np.array(u_f(t), dtype=float),
        rhs_ref,
        du=lambda t: np.array(du_f(t), dtype=float),
    )
