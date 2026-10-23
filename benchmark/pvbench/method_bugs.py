"""Seeded bugs in numerical methods themselves, modelled on bugs found in public code.

The problem benchmark (pvbench.problems) seeds bugs into five solvers. Some bugs found in real
repositories are not bugs of a solver for one problem but of a method or a helper: a Butcher table with
the wrong order label, error-estimate weights that do not sum to zero, backward time-stepping with
stage times on the wrong side, a time loop that stops one step late, a spectral derivative that only
works for even grids, Dirichlet values written after the solve instead of inside the linear system, a
zero-flux wall made by copying the neighbour value, a source term without its factor dt, a grid spacing
off by one interval. This module seeds each of them, with a bug-free control, and names the check
meant to catch it. `run_all()` returns one row per case; tests/test_method_bugs.py requires every
prediction to come true.

Cases and the real codes they come from are listed in results/corpus/SUMMARY.md (by repository ID).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from physverify.butcher import check_tableau
from physverify.checks import FAIL, PASS, Result, run_check, Check
from physverify.mms import ManufacturedODE
from physverify.order import check_order
from physverify.studies import backward_mms_study, balance_check, size_sweep_check, time_grid_check

# --- Butcher tables ---------------------------------------------------------------------------------

HEUN_A = np.array([[0.0, 0.0], [1.0, 0.0]])
HEUN_B = np.array([0.5, 0.5])
RK4_A = np.array([[0, 0, 0, 0], [0.5, 0, 0, 0], [0, 0.5, 0, 0], [0, 0, 1, 0]], dtype=float)
RK4_B = np.array([1, 2, 2, 1]) / 6.0
# Bogacki-Shampine 3(2): main weights order 3, embedded order 2 (b_hat), error weights e = b - b_hat
BS_A = np.array([[0, 0, 0, 0], [0.5, 0, 0, 0], [0, 0.75, 0, 0], [2 / 9, 1 / 3, 4 / 9, 0]])
BS_B = np.array([2 / 9, 1 / 3, 4 / 9, 0])
BS_BHAT = np.array([7 / 24, 1 / 4, 1 / 3, 1 / 8])


def _tableau_case(A, b, claimed):
    return lambda: check_tableau(A, b, claimed=claimed)


# --- backward time-stepping -------------------------------------------------------------------------

MMS = ManufacturedODE(lambda t: np.array([np.exp(np.sin(t))]), lambda t, y: np.array([y[0] * np.cos(t)]))


def _rk4_back(stage_times_forward: bool):
    """RK4 from t_end down to 0. With the bug the stages are evaluated at t + h/2, t + h (the forward side)."""
    def integrate_back(source, y_end, t_end, n):
        h = t_end / n
        y, t = np.array(y_end, dtype=float), t_end

        def f(s, u):
            return MMS.rhs_ref(s, u) + source(s)

        for _ in range(n):
            sgn = 1.0 if stage_times_forward else -1.0
            k1 = -f(t, y)
            k2 = -f(t + sgn * h / 2, y + h / 2 * k1)
            k3 = -f(t + sgn * h / 2, y + h / 2 * k2)
            k4 = -f(t + sgn * h, y + h * k3)
            y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            t -= h
        return y
    return integrate_back


# --- time loops -------------------------------------------------------------------------------------

def _while_loop_times(n, t0=0.0, t1=2.0):
    h = (t1 - t0) / n
    t, times = t0, [t0]
    while t <= t1:
        t += h
        times.append(t)
    return times


def _counted_times(n, t0=0.0, t1=2.0):
    h = (t1 - t0) / n
    return [t0 + i * h for i in range(n + 1)]


# --- spectral derivative ----------------------------------------------------------------------------

def _spectral_derivative(halves_bug: bool):
    def check_at(n):
        L = 2 * np.pi
        x = np.arange(n) * L / n
        if halves_bug:  # wavenumbers built by splitting the array in two halves: only works for even n
            dx = L / n
            kmax = np.pi / dx
            k = np.arange(float(n))
            k[: int(n / 2)] = k[: int(n / 2)] * (kmax / (n / 2))
            k[int(n / 2):] = k[: int(n / 2)] - kmax
        else:
            k = 2 * np.pi * np.fft.fftfreq(n, L / n)
        d = np.real(np.fft.ifft(1j * k * np.fft.fft(np.sin(x))))
        return bool(np.max(np.abs(d - np.cos(x))) < 1e-10)
    return check_at


# --- heat equation boundaries and sources (batch 5) -------------------------------------------------

def _cn_dirichlet_error(n: int, boundary_in_system: bool) -> float:
    """Crank-Nicolson for u_t = u_xx on [0, 1], u = 0 at both ends, mode sin(pi x), t = 0.05, small dt.

    With the bug the matrix covers all n points, boundary rows included, and the Dirichlet values are
    written into the solution only after each solve, so the boundary nodes evolve freely meanwhile.
    """
    x = np.linspace(0.0, 1.0, n)
    dx, t_end, steps = x[1] - x[0], 0.05, 2000
    dt = t_end / steps
    lam = dt / dx**2
    u = np.sin(np.pi * x)
    if boundary_in_system:
        m = n - 2
        D = (np.diag(-2.0 * np.ones(m)) + np.diag(np.ones(m - 1), 1) + np.diag(np.ones(m - 1), -1)) * lam
        A, B = np.eye(m) - D / 2, np.eye(m) + D / 2
        v = u[1:-1]
        for _ in range(steps):
            v = np.linalg.solve(A, B @ v)
        u = np.concatenate([[0.0], v, [0.0]])
    else:
        D = (np.diag(-2.0 * np.ones(n)) + np.diag(np.ones(n - 1), 1) + np.diag(np.ones(n - 1), -1)) * lam
        A, B = np.eye(n) - D / 2, np.eye(n) + D / 2
        for _ in range(steps):
            u = np.linalg.solve(A, B @ u)
            u[0] = u[-1] = 0.0
    return float(np.max(np.abs(u - np.exp(-np.pi**2 * t_end) * np.sin(np.pi * x))))


def _dirichlet_case(boundary_in_system: bool):
    ns = (11, 21, 41, 81)
    return lambda: check_order([1.0 / (n - 1) for n in ns], [_cn_dirichlet_error(n, boundary_in_system) for n in ns], 2.0)


def _neumann_heat_change(n: int, mirror: bool) -> float:
    """Relative change of the total heat for u_t = u_xx on [0, 1] with insulated ends (explicit, 400 steps).

    Control: edge nodes updated with a mirrored ghost value, total heat by the trapezoid rule (exactly
    conserved). Bug: interior update, then u[0] = u[1], u[-1] = u[-2], total heat as sum(u) dx.
    """
    x = np.linspace(0.0, 1.0, n)
    dx = x[1] - x[0]
    dt = 0.25 * dx**2
    u = np.exp(-((x - 0.3) ** 2) / 0.01)

    def total(v):
        w = np.full(n, dx)
        if mirror:
            w[[0, -1]] = dx / 2
        return float(np.sum(w * v))

    start = total(u)
    for _ in range(400):
        new = u.copy()
        new[1:-1] = u[1:-1] + dt / dx**2 * (u[2:] - 2 * u[1:-1] + u[:-2])
        if mirror:
            new[0] = u[0] + dt / dx**2 * 2 * (u[1] - u[0])
            new[-1] = u[-1] + dt / dx**2 * 2 * (u[-2] - u[-1])
        else:
            new[0], new[-1] = new[1], new[-2]
        u = new
    return (total(u) - start) / start


def _source_gain(n: int, times_dt: bool) -> float:
    """Gain of u under a constant source S = 2 over T = 1 with no diffusion, in n steps; exactly S T = 2."""
    dt, u = 1.0 / n, 0.0
    for _ in range(n):
        u += 2.0 * dt if times_dt else 2.0
    return u


def _well_energy_error(n: int, spacing_from_intervals: bool) -> float:
    """Lowest level of the infinite square well [0, 2] (hbar = m = 1) with n - 1 interior points.

    n - 1 interior points split the well into n intervals, so dx = W/n; the bug uses W/(n - 1).
    """
    W = 2.0
    dx = W / n if spacing_from_intervals else W / (n - 1)
    m = n - 1
    H = (np.diag(np.full(m, 1.0 / dx**2)) + np.diag(np.full(m - 1, -0.5 / dx**2), 1)
         + np.diag(np.full(m - 1, -0.5 / dx**2), -1))
    return float(abs(np.linalg.eigvalsh(H)[0] - np.pi**2 / (2 * W**2)))


def _spacing_case(spacing_from_intervals: bool):
    ns = (50, 100, 200, 400)
    return lambda: check_order([2.0 / n for n in ns], [_well_energy_error(n, spacing_from_intervals) for n in ns], 2.0)


@dataclass(frozen=True)
class MethodCase:
    name: str
    buggy: bool
    description: str
    real_case: str  # repository ID in results/corpus/SUMMARY.md
    check: str
    run: Callable[[], Result]
    missed_by: str = ""  # a check that cannot see it, when that is the point


CASES = [
    MethodCase("tableau_ok", False, "RK4 table, label 4", "-", "butcher.check_tableau", _tableau_case(RK4_A, RK4_B, 4)),
    MethodCase("tableau_label_too_high", True, "Heun table (order 2) labelled order 3", "F09",
               "butcher.check_tableau", _tableau_case(HEUN_A, HEUN_B, 3)),
    MethodCase("embedded_ok", False, "Bogacki-Shampine embedded weights b_hat, label 2", "-",
               "butcher.check_tableau", _tableau_case(BS_A, BS_BHAT, 2)),
    MethodCase("error_weights_as_embedded", True,
               "published error weights e = b - b_hat subtracted from b again, so the embedded weights become e "
               "(they sum to 0)", "E09", "butcher.check_tableau", _tableau_case(BS_A, BS_B - BS_BHAT, 2)),
    MethodCase("backward_ok", False, "RK4 stepping backwards with stages at t - h/2, t - h", "-",
               "studies.backward_mms_study",
               lambda: backward_mms_study(_rk4_back(False), MMS, 2.0, (10, 20, 40, 80), 4)),
    MethodCase("backward_stage_times_forward", True, "RK4 stepping backwards with stages at t + h/2, t + h", "D08",
               "studies.backward_mms_study",
               lambda: backward_mms_study(_rk4_back(True), MMS, 2.0, (10, 20, 40, 80), 4),
               missed_by="any forward-in-time check, and backward runs of autonomous equations"),
    MethodCase("time_loop_ok", False, "loop over a counted number of steps", "-", "studies.time_grid_check",
               lambda: time_grid_check(_counted_times, 0.0, 2.0, (4, 8, 20))),
    MethodCase("while_loop_overshoot", True, "`while t <= t_end: t += h` takes one step too many when t lands on t_end",
               "D08", "studies.time_grid_check", lambda: time_grid_check(_while_loop_times, 0.0, 2.0, (4, 8, 20)),
               missed_by="order studies that read the state nearest t_end"),
    MethodCase("spectral_ok", False, "wavenumbers from numpy.fft.fftfreq", "-", "studies.size_sweep_check",
               lambda: size_sweep_check(_spectral_derivative(False))),
    MethodCase("spectral_even_only", True, "wavenumbers built from two halves of the array (fails for odd n)", "G10",
               "studies.size_sweep_check", lambda: size_sweep_check(_spectral_derivative(True)),
               missed_by="any study on power-of-two grids"),
    MethodCase("dirichlet_ok", False, "Crank-Nicolson solving only for interior nodes, Dirichlet values in the system",
               "-", "order.check_order", _dirichlet_case(True)),
    MethodCase("dirichlet_after_solve", True,
               "Crank-Nicolson matrix over all nodes, Dirichlet values written only after each solve", "H01",
               "order.check_order", _dirichlet_case(False),
               missed_by="a single run compared with a loose tolerance (the error is small but does not shrink)"),
    MethodCase("neumann_ok", False, "insulated ends with a mirrored ghost value, trapezoid total", "-",
               "studies.balance_check",
               lambda: balance_check(lambda n: _neumann_heat_change(n, True), 0.0, (21, 41, 81), tol=1e-12)),
    MethodCase("neumann_by_copy", True, "insulated ends made by copying the neighbour value after the update", "H54",
               "studies.balance_check",
               lambda: balance_check(lambda n: _neumann_heat_change(n, False), 0.0, (21, 41, 81), tol=1e-12),
               missed_by="a one-step test with the heat away from the walls"),
    MethodCase("source_ok", False, "source term multiplied by dt", "-", "studies.balance_check",
               lambda: balance_check(lambda n: _source_gain(n, True), 2.0, (10, 100), tol=1e-12)),
    MethodCase("source_without_dt", True, "source term added once per step without the factor dt", "H01",
               "studies.balance_check", lambda: balance_check(lambda n: _source_gain(n, False), 2.0, (10, 100), tol=1e-12),
               missed_by="any test with zero source"),
    MethodCase("spacing_ok", False, "n - 1 interior points with dx = W/n", "-", "order.check_order", _spacing_case(True)),
    MethodCase("spacing_off_by_one", True, "n - 1 interior points with dx = W/(n - 1)", "H19", "order.check_order",
               _spacing_case(False), missed_by="a single comparison at n = 100 with a 5% tolerance"),
]


def run_all() -> list[tuple[MethodCase, Result]]:
    return [(c, run_check(Check("method", c.name, c.run))) for c in CASES]


def to_markdown(rows) -> str:
    lines = ["| Case | Seeded bug | From | Check | Result | Missed by |", "|---|---|---|---|---|---|"]
    for c, r in rows:
        lines.append(f"| {c.name} | {'yes' if c.buggy else 'no (control)'} | {c.real_case} | `{c.check}` | {r.status} | {c.missed_by} |")
    return "\n".join(lines) + "\n"
