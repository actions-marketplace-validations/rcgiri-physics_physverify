"""SKIP status, per-check time budget, sandbox runner (writable copy, 3.14 shim), coverage and trajectory studies."""

import importlib.util
import math
import time
from pathlib import Path

import numpy as np

from physverify.checks import ERROR, FAIL, INCONCLUSIVE, PASS, SKIP, Check, Result, SkipCheck, requires, run_check
from physverify.cli import main
from physverify.mms import ManufacturedODE, mms_order_study
from physverify.report import run_checks, summary
from physverify.studies import coverage_check, trajectory_order_study

ROOT = Path(__file__).resolve().parents[1]


def _runner():
    spec = importlib.util.spec_from_file_location("pv_runner", ROOT / "sandbox" / "runner.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- SKIP ---

def test_missing_optional_dependency_is_skip_not_pass():
    def needs_missing():
        requires("numpy", "no_such_module_pv")
        return Result(PASS, "ran")

    r = run_check(Check("limit", "needs shapely", needs_missing))
    assert r.status == SKIP and "no_such_module_pv" in r.message
    assert not r.ok and not r.failed


def test_skip_counts_separately_and_does_not_fail_the_run(tmp_path):
    spec = tmp_path / "verify_skip.py"
    spec.write_text(
        "from physverify import Check, Result, SkipCheck\n"
        "def skipped():\n    raise SkipCheck('no GPU')\n"
        "def checks():\n    return [Check('limit', 'ok', lambda: Result('PASS', '')), Check('limit', 'gpu', skipped)]\n")
    outs = run_checks([Check("limit", "s", lambda: (_ for _ in ()).throw(SkipCheck("x")))])
    assert summary(outs)["skipped"] == 1 and summary(outs)["not_ok"] == 0
    assert main(["run", "--quiet", str(spec)]) == 0


# --- time budget ---

def _slow_study(delay):
    mms = ManufacturedODE(lambda t: np.array([np.sin(t)]), lambda t, y: np.array([0.0]))

    def integrate(src, y0, t_end, n):  # RK4 on y' = src(t)
        time.sleep(delay * n / 8)
        y, h = np.array(y0, float), t_end / n
        for k in range(n):
            t = k * h
            y = y + h / 6 * (np.asarray(src(t)) + 4 * np.asarray(src(t + h / 2)) + np.asarray(src(t + h)))
        return y

    return lambda: mms_order_study(integrate, mms, 1.0, [8, 16, 32, 64, 128], 4)


def test_budget_stops_adding_resolutions_and_says_so():
    r = run_check(Check("mms", "slow", _slow_study(0.05)), budget_s=0.5)
    assert "time budget: ran" in r.message
    assert len(r.hs) < 5
    assert run_check(Check("mms", "fast", _slow_study(0.0)), budget_s=30).status == PASS


def test_a_check_that_hangs_is_inconclusive_and_later_checks_run():
    hang = Check("limit", "hang", lambda: (time.sleep(5), Result(PASS))[1], budget_s=0.2)
    outs = run_checks([hang, Check("limit", "next", lambda: Result(PASS, ""))])
    assert outs[0].result.status == INCONCLUSIVE and outs[0].seconds < 2
    assert outs[1].result.status == PASS


def test_budget_keeps_errors_and_skips():
    assert run_check(Check("limit", "e", lambda: 1 / 0), budget_s=5).status == ERROR
    assert run_check(Check("limit", "s", lambda: requires("no_such_module_pv")), budget_s=5).status == SKIP


# --- sandbox runner ---

def test_py314_shim_puts_the_future_import_first():
    shim = _runner().py314_shim
    out = shim('"""Doc."""\nclass A:\n    def f(self) -> B: ...\nclass B: ...\n')
    assert out.startswith('"""Doc."""\nfrom __future__ import annotations\n')
    compile(out, "x", "exec")
    assert shim("#!/usr/bin/env python\nx = 1\n").splitlines()[:2] == ["#!/usr/bin/env python", "from __future__ import annotations"]
    assert shim("from __future__ import annotations\nx = 1\n") is None
    assert shim("def f(:\n") is None
    both = shim('"""d"""\nfrom __future__ import division\nx = 1\n')
    compile(both, "x", "exec")


def test_runner_reports_files_written_into_the_repository(tmp_path):
    r = _runner()
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "m.py").write_text("x = 1\n")
    before = r.snapshot(root)
    (root / "pkg" / "cache.npy").write_bytes(b"0")
    assert r.written(before, r.snapshot(root)) == ["pkg/cache.npy"]


# --- trajectory study ---

def _euler_runs(ns, t_end, short_by=0):
    runs = []
    for n in ns:
        h = t_end / n
        steps = n - short_by
        t = np.arange(steps + 1) * h
        y = np.empty(steps + 1)
        y[0] = 1.0
        for k in range(steps):
            y[k + 1] = y[k] * (1 - h)
        runs.append((t, y))
    return runs


def test_trajectory_study_measures_order_at_a_fixed_time():
    r = trajectory_order_study(_euler_runs([20, 40, 80, 160], 2.0), lambda t: math.exp(-t), 2.0, 1)
    assert r.status == PASS


def test_trajectory_study_flags_a_run_that_stops_one_step_short():
    r = trajectory_order_study(_euler_runs([20, 40, 80, 160], 2.0, short_by=1), lambda t: math.exp(-t), 2.0, 1)
    assert r.status == FAIL and "1 step(s) short" in r.message


def test_trajectory_study_notes_a_whole_number_of_periods():
    ns = [40, 80, 160, 320]
    runs = []
    for n in ns:
        h = 2 * math.pi / n
        t = np.arange(n + 1) * h
        q = np.cos(t + 0.3 * h * h * t)  # phase error O(h^2) at all times
        runs.append((t, q))
    r = trajectory_order_study(runs, math.cos, 2 * math.pi, 2, period=2 * math.pi)
    assert "whole period" in r.message


# --- coverage ---

def _gauss_mean(sigma_used):
    def simulate(mu, rng):
        return rng.normal(mu, 1.0, size=10)

    def interval(x, level):
        z = {0.68: 0.994457883, 0.95: 1.959963985}[level]
        half = z * sigma_used / math.sqrt(len(x))
        return x.mean() - half, x.mean() + half

    return simulate, interval


def test_coverage_of_a_correct_interval_passes():
    sim, iv = _gauss_mean(1.0)
    assert coverage_check(sim, iv, lambda rng: rng.uniform(-5, 5), level=0.68, trials=600).status == PASS


def test_coverage_of_an_overconfident_interval_fails():
    sim, iv = _gauss_mean(0.6)  # interval too narrow by the factor 0.6
    r = coverage_check(sim, iv, lambda rng: rng.uniform(-5, 5), level=0.68, trials=600)
    assert r.status == FAIL and "stated 0.68" in r.message
