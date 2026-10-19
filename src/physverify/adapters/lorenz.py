"""Adapter for lorenz-attractor-simulation/src/mechanics.py (lorenz_derivatives).

The project integrates with SciPy's solve_ivp, so only the right-hand side is
under test here; it is stepped with physverify's own RK4. The flow is chaotic
(largest Lyapunov exponent about 0.906), so trajectories are compared only up
to t = 1, well inside one Lyapunov time's worth of growth (exp(0.9) < 3).
Beyond that the project is checked through exact properties of the flow:
fixed points, the constant divergence -(sigma + 1 + beta), and the Jacobian
that scripts/calculate_lyapunov.py writes by hand.
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np

from ..checks import EXACT, FAIL, PASS, Check, Result
from ..loaders import load_module_from_path
from ..mms import ManufacturedODE
from ..problems._common import make_integrate
from ..studies import ode_checks
from . import sibling_project

ENV_VAR = "PHYSVERIFY_LORENZ_DIR"
FOLDER = "lorenz-attractor-simulation"
PARAMS = {"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0}
Y0_FREE = np.array([1.0, 1.0, 1.0])
T_END = 1.0
NS_RK4 = (100, 200, 400, 800)


def source_path():
    return sibling_project(ENV_VAR, FOLDER) / "src" / "mechanics.py"


def lyapunov_path():
    return sibling_project(ENV_VAR, FOLDER) / "scripts" / "calculate_lyapunov.py"


def load():
    return load_module_from_path("lorenz_mechanics_under_test", source_path())


def rhs_reference(p=PARAMS):
    """From docs/theory.md, written in matrix-free form independently of the code."""
    s, r, b = p["sigma"], p["rho"], p["beta"]

    def f(t, u):
        x, y, z = u
        return np.array([s * y - s * x, r * x - x * z - y, x * y - b * z])

    return f


def manufactured() -> ManufacturedODE:
    def u(t):
        return np.array([2.0 * np.sin(t), 1.0 + np.cos(1.7 * t), 20.0 + 3.0 * np.sin(0.6 * t)])

    return ManufacturedODE(u, rhs_reference())


def fixed_points(p=PARAMS):
    c = math.sqrt(p["beta"] * (p["rho"] - 1.0))
    return [np.zeros(3), np.array([c, c, p["rho"] - 1.0]), np.array([-c, -c, p["rho"] - 1.0])]


def central_jacobian(f, u, h=1e-3):
    """Centred differences are exact (to round-off) for a quadratic field like Lorenz."""
    jac = np.zeros((3, 3))
    for j in range(3):
        e = np.zeros(3)
        e[j] = h
        jac[:, j] = (np.asarray(f(0.0, u + e)) - np.asarray(f(0.0, u - e))) / (2 * h)
    return jac


SAMPLE_POINTS = [np.array(v) for v in ([1.0, 1.0, 1.0], [-8.3, 4.1, 27.0], [12.0, -3.0, 5.5], [0.0, 0.0, 0.0])]


def fixed_point_check(rhs) -> Check:
    def run():
        worst = max(float(np.max(np.abs(rhs(0.0, p)))) for p in fixed_points())
        if worst <= 1e-12 * 30:
            return Result(EXACT, f"all three fixed points are zeros of the field (largest |f| = {worst:.1e})")
        return Result(FAIL, f"field is {worst:.3g} at a fixed point")

    return Check("limit", "fixed points 0 and (+-sqrt(beta(rho-1)), ., rho-1)", run)


def divergence_check(rhs) -> Check:
    expected = -(PARAMS["sigma"] + 1.0 + PARAMS["beta"])

    def run():
        divs = [float(np.trace(central_jacobian(rhs, p))) for p in SAMPLE_POINTS]
        worst = max(abs(d - expected) for d in divs)
        if worst <= 1e-9:
            return Result(EXACT, f"divergence {divs[0]:.12f} = -(sigma+1+beta) at {len(divs)} points")
        return Result(FAIL, f"divergence differs from {expected:.6f} by {worst:.3g}")

    return Check("invariant", "flow divergence is constant -(sigma+1+beta)", run)


def jacobian_check(rhs, jacobian) -> Check:
    def run():
        worst = max(
            float(np.max(np.abs(np.asarray(jacobian(p, PARAMS)) - central_jacobian(rhs, p)))) for p in SAMPLE_POINTS
        )
        if worst <= 1e-9:
            return Result(EXACT, f"hand-written Jacobian matches the field's derivative (max diff {worst:.1e})")
        return Result(FAIL, f"hand-written Jacobian differs from the field's derivative by {worst:.3g}")

    return Check("limit", "calculate_lyapunov.py Jacobian vs derivative of the field", run)


def load_function(path, name):
    """One top-level function from a script, without running the script's imports.

    The script appends to sys.path and imports SciPy at module level; only the
    function's own source is executed here, with numpy as np in scope.
    """
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {"np": np}
    exec(compile(ast.Module([node], []), str(path), "exec"), namespace)
    return namespace[name]


def checks(module=None) -> list[Check]:
    module = module or load()

    def rhs(t, y):
        return np.asarray(module.lorenz_derivatives(t, y, PARAMS), dtype=float)

    out = ode_checks(
        "mechanics.py RHS + physverify RK4",
        make_integrate(rhs, frozenset(), "rk4"),
        rhs_ref=rhs_reference(),
        mms=manufactured(),
        y0_free=Y0_FREE,
        t_end=T_END,
        ns=NS_RK4,
        order=4.0,
        patch=(np.array([1.0, -2.0, 15.0]), np.array([0.5, 1.5, -2.0])),
        integrate_trajectory=make_integrate(rhs, frozenset(), "rk4", trajectory=True),
    )
    out += [fixed_point_check(rhs), divergence_check(rhs)]
    if lyapunov_path().is_file():
        out.append(jacobian_check(rhs, load_function(lyapunov_path(), "lorenz_jacobian")))
    return out
