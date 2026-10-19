"""Adapter for three-body-simulation/src (planar three-body problem, G = 1).

Under test:
  physics.get_derivatives          stepped with physverify's RK4 (mms, reference, patch)
  integrators.verlet_step          the project's own velocity-Verlet step (second order)
  integrators.run_verlet_simulation the driver around it
  integrators.run_simulation       the solve_ivp wrapper (needs SciPy)

The code softens gravity with epsilon = 1e-4, as docs/theory.md allows
("(r^2 + eps^2)^1.5"), so the reference uses the same softening. The energy
function in physics.py does not soften; that mismatch is reported separately.
Verlet has no source-term hook, so there is no MMS check of it (row 25 of the
audit plan); it is covered by a reference solution, exact invariants and exact
time reversal instead. The package uses relative imports and SciPy, so it is
loaded as a package; without SciPy only physics.py is tested.
"""

from __future__ import annotations

import importlib.util
import math
import sys

import numpy as np

from ..checks import EXACT, FAIL, PASS, Check, Result
from ..mms import ManufacturedODE, max_abs_error, zero_source
from ..order import check_exact, check_order
from ..problems._common import make_integrate
from ..steppers import integrate_fixed, rk4
from ..studies import invariant_study, ode_checks, reference_study
from . import sibling_project

ENV_VAR = "PHYSVERIFY_THREE_BODY_DIR"
FOLDER = "three-body-simulation"
EPS = 1e-4  # softening length used by physics.py
MASSES = np.array([1.0, 1.0, 1.0])

# Figure-eight initial condition (Chenciner and Montgomery), used only as a smooth, bounded test orbit.
_X1 = np.array([0.97000436, -0.24308753])
_V3 = np.array([-0.93240737, -0.86473146])
Y0_FREE = np.concatenate([_X1, -_X1, [0.0, 0.0], -_V3 / 2, -_V3 / 2, _V3])
T_END = 1.0
NS_RK4 = (100, 200, 400, 800)
NS_VERLET = (200, 400, 800, 1600)


def src_dir():
    return sibling_project(ENV_VAR, FOLDER) / "src"


def source_path():
    return src_dir() / "physics.py"


def load():
    """Import the project's src package under a private name, without writing __pycache__."""
    name = "three_body_src_under_test"
    old_flag = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(
            name, src_dir() / "__init__.py", submodule_search_locations=[str(src_dir())]
        )
        package = importlib.util.module_from_spec(spec)
        sys.modules[name] = package
        try:
            spec.loader.exec_module(package)
        except ImportError:
            # __init__ imports integrators, which needs SciPy; fall back to physics.py alone
            for key in [k for k in sys.modules if k == name or k.startswith(name + ".")]:
                sys.modules.pop(key)
            physics_spec = importlib.util.spec_from_file_location(name + "_physics", source_path())
            physics = importlib.util.module_from_spec(physics_spec)
            physics_spec.loader.exec_module(physics)
            return physics, None
        return sys.modules[name + ".physics"], sys.modules[name + ".integrators"]
    finally:
        sys.dont_write_bytecode = old_flag


def rhs_reference(masses=MASSES, eps=EPS):
    """a_i = sum_j m_j (r_j - r_i) / (|r_j - r_i|^2 + eps^2)^1.5, written pair by pair."""
    masses = np.asarray(masses, dtype=float)

    def f(t, y):
        r = y[:6].reshape(3, 2)
        a = np.zeros((3, 2))
        for i in range(3):
            for j in range(i + 1, 3):
                d = r[j] - r[i]
                w = (d @ d + eps * eps) ** -1.5
                a[i] += masses[j] * w * d
                a[j] -= masses[i] * w * d
        return np.concatenate([y[6:], a.ravel()])

    return f


def energy_reference(y, masses=MASSES, eps=EPS):
    """Energy of the softened system: the potential is -m_i m_j / sqrt(r^2 + eps^2)."""
    r = y[:6].reshape(3, 2)
    v = y[6:].reshape(3, 2)
    e = 0.5 * float(np.sum(masses * np.sum(v * v, axis=1)))
    for i in range(3):
        for j in range(i + 1, 3):
            d = r[j] - r[i]
            e -= masses[i] * masses[j] / math.sqrt(d @ d + eps * eps)
    return e


def momentum(y, masses=MASSES):
    return (masses[:, None] * y[6:].reshape(3, 2)).sum(axis=0)


def angular_momentum(y, masses=MASSES):
    r = y[:6].reshape(3, 2)
    v = y[6:].reshape(3, 2)
    return float(np.sum(masses * (r[:, 0] * v[:, 1] - r[:, 1] * v[:, 0])))


def manufactured() -> ManufacturedODE:
    def u(t):
        pos = [np.cos(t), 0.3 * np.sin(t), -0.8 + 0.2 * np.sin(1.3 * t), 0.9, 0.1 * t, -1.0 + 0.4 * np.cos(t)]
        vel = [np.sin(0.7 * t), 0.5, -0.3 + 0.1 * t, np.cos(1.1 * t), 0.2, -0.4 * np.sin(t)]
        return np.array(pos + vel)

    return ManufacturedODE(u, rhs_reference())


def verlet_integrate(integrators, masses=MASSES):
    def integrate(source, y0, t_end, n):
        if source is not zero_source:
            raise ValueError("verlet_step has no source-term hook")
        y = np.array(y0, dtype=float)
        for _ in range(n):
            y = integrators.verlet_step(y, masses, t_end / n)
        return y

    return integrate


def _exact_drift(label, integrate, quantity, ns, t_end=T_END, y0=Y0_FREE):
    def run():
        q0 = np.atleast_1d(quantity(y0))
        hs, errs = [], []
        for n in ns:
            hs.append(t_end / n)
            errs.append(float(np.max(np.abs(np.atleast_1d(quantity(integrate(zero_source, y0, t_end, n))) - q0))))
        return check_exact(hs, errs, scale=max(float(np.max(np.abs(y0))), 1.0))

    return Check("invariant", label, run)


def reversibility_check(integrate, ns=NS_VERLET) -> Check:
    """Velocity Verlet is time-symmetric: forward, flip velocities, forward again, flip: back to the start."""

    def run():
        hs, errs = [], []
        for n in ns:
            y = integrate(zero_source, Y0_FREE, T_END, n)
            y = np.concatenate([y[:6], -y[6:]])
            y = integrate(zero_source, y, T_END, n)
            y = np.concatenate([y[:6], -y[6:]])
            hs.append(T_END / n)
            errs.append(max_abs_error(y, Y0_FREE))
        return check_exact(hs, errs, floor=1e-11, scale=float(np.max(np.abs(Y0_FREE))))

    return Check("patch", "verlet_step time reversal", run)


def binary_closure_check(integrators, ns=NS_VERLET) -> Check:
    """Two unit masses on a circular orbit of separation 1; the third body has zero mass.

    Period T = 2 pi / sqrt(2) up to a softening correction of order eps^2 (about 1e-8),
    far below the Verlet error at these steps. The orbit must close at second order.
    """
    masses = np.array([1.0, 1.0, 0.0])
    v = math.sqrt(0.5) * (1.0 + EPS * EPS) ** -0.75  # circular speed with softened force
    y0 = np.array([-0.5, 0.0, 0.5, 0.0, 30.0, 0.0, 0.0, -v, 0.0, v, 0.0, 0.0])
    omega = 2.0 * v  # angular speed of each body about the centre
    period = 2.0 * math.pi / omega
    integrate = verlet_integrate(integrators, masses)

    def run():
        hs, errs = [], []
        for n in ns:
            y = integrate(zero_source, y0, period, n)
            hs.append(period / n)
            errs.append(max_abs_error(y[[0, 1, 2, 3, 6, 7, 8, 9]], y0[[0, 1, 2, 3, 6, 7, 8, 9]]))
        return check_order(hs, errs, 2.0)

    return Check("limit", "verlet_step two-body circular orbit closes after one period", run)


def driver_end_time_check(integrators, ns=NS_VERLET) -> Check:
    """run_verlet_simulation((0, T), dt) should return the state at T, at Verlet's second order."""
    y_ref = integrate_fixed(rhs_reference(), Y0_FREE, 0.0, T_END, 16 * max(ns), rk4)

    def run():
        hs, errs, last = [], [], []
        for n in ns:
            times, states = integrators.run_verlet_simulation(Y0_FREE, MASSES, (0.0, T_END), T_END / n)
            hs.append(T_END / n)
            errs.append(max_abs_error(states[:, -1], y_ref))
            last.append(float(times[-1]))
        result = check_order(hs, errs, 2.0, scale=float(np.max(np.abs(y_ref))))
        result.message += f"; last time returned {last[0]:.6g} for t_end = {T_END:g}, dt = {hs[0]:.3g}"
        return result

    return Check("reference", "run_verlet_simulation final state at t_end", run)


def energy_function_check(physics) -> Check:
    """physics.calculate_energy against the softened energy that the dynamics conserves."""

    def run():
        e_code = float(physics.calculate_energy(Y0_FREE, MASSES)[0])
        e_soft = energy_reference(Y0_FREE)
        diff = abs(e_code - e_soft)
        if diff <= 1e-12:
            return Result(EXACT, f"matches the softened energy (diff {diff:.1e})")
        return Result(
            FAIL,
            f"differs from the energy the softened dynamics conserves by {diff:.2g} "
            f"(relative {diff / abs(e_soft):.1g}): potential is not softened",
        )

    return Check("invariant", "calculate_energy is the conserved quantity", run)


def solve_ivp_check(integrators, physics) -> Check:
    def run():
        t_end = 2.0
        y_ref = integrate_fixed(rhs_reference(), Y0_FREE, 0.0, t_end, 20000, rk4)
        sol = integrators.run_simulation(physics.get_derivatives, (0.0, t_end), Y0_FREE, MASSES)
        err = max_abs_error(sol.y[:, -1], y_ref)
        if err <= 1e-7:
            return Result(PASS, f"default rtol=1e-9 reaches {err:.1e} at t = {t_end:g}")
        return Result(FAIL, f"error {err:.3g} at default tolerances")

    return Check("reference", "run_simulation (solve_ivp RK45) at default tolerances", run)


def checks(loaded=None) -> list[Check]:
    physics, integrators = loaded or load()

    def rhs(t, y):
        return np.asarray(physics.get_derivatives(t, np.asarray(y, dtype=float), MASSES), dtype=float)

    rk4_int = make_integrate(rhs, frozenset(), "rk4")
    out = ode_checks(
        "get_derivatives + physverify RK4",
        rk4_int,
        rhs_ref=rhs_reference(),
        mms=manufactured(),
        y0_free=Y0_FREE,
        t_end=T_END,
        ns=NS_RK4,
        order=4.0,
        quantity=energy_reference,
        patch=(manufactured().value(0.0), np.array([0.1, -0.2, 0.3, 0.05, -0.1, 0.2] + [0.0] * 6)),
        integrate_trajectory=make_integrate(rhs, frozenset(), "rk4", trajectory=True),
    )
    out.append(energy_function_check(physics))
    if integrators is None:
        return out
    verlet = verlet_integrate(integrators)
    out += [
        Check("reference", "verlet_step", lambda: reference_study(verlet, rhs_reference(), Y0_FREE, T_END, NS_VERLET, 2.0)),
        Check(
            "invariant",
            "verlet_step energy",
            lambda: invariant_study(verlet, energy_reference, Y0_FREE, T_END, NS_VERLET, 2.0),
        ),
        _exact_drift("verlet_step total momentum", verlet, momentum, NS_VERLET),
        _exact_drift("verlet_step angular momentum", verlet, angular_momentum, NS_VERLET),
        reversibility_check(verlet),
        binary_closure_check(integrators),
        driver_end_time_check(integrators),
        solve_ivp_check(integrators, physics),
    ]
    return out
