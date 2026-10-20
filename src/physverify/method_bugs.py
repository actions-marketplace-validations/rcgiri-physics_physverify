"""Seeded bugs in numerical methods themselves, modelled on bugs found in public code.

The problem benchmark (physverify.problems) seeds bugs into five solvers. Some bugs found in real
repositories are not bugs of a solver for one problem but of a method or a helper: a Butcher table with
the wrong order label, error-estimate weights that do not sum to zero, backward time-stepping with
stage times on the wrong side, a time loop that stops one step late, a spectral derivative that only
works for even grids. This module seeds each of them, with a bug-free control, and names the check
meant to catch it. `run_all()` returns one row per case; tests/test_method_bugs.py requires every
prediction to come true.

Cases and the real codes they come from are listed in results/corpus/SUMMARY.md (by repository ID).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .butcher import check_tableau
from .checks import FAIL, PASS, Result, run_check, Check
from .mms import ManufacturedODE
from .studies import backward_mms_study, size_sweep_check, time_grid_check

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
]


def run_all() -> list[tuple[MethodCase, Result]]:
    return [(c, run_check(Check("method", c.name, c.run))) for c in CASES]


def to_markdown(rows) -> str:
    lines = ["| Case | Seeded bug | From | Check | Result | Missed by |", "|---|---|---|---|---|---|"]
    for c, r in rows:
        lines.append(f"| {c.name} | {'yes' if c.buggy else 'no (control)'} | {c.real_case} | `{c.check}` | {r.status} | {c.missed_by} |")
    return "\n".join(lines) + "\n"
