"""Checks added after testing other people's repositories (sandbox/README.md).

Each test reproduces, in a few lines, the pattern a real code had, and shows the new check sees it.
"""

import numpy as np

from physverify.checks import FAIL, PASS
from physverify.constants import check_value, scan
from physverify.loaders import load_definitions_from_path
from physverify.mms import ManufacturedODE
from physverify.order import check_order
from physverify.steppers import rk4
from physverify.studies import backward_mms_study, time_grid_check


def while_loop_times(t0, t1, n):
    """`while t <= t_end: t += h`, as in a real RK4 library."""
    h = (t1 - t0) / n
    t, times = t0, [t0]
    while t <= t1:
        t += h
        times.append(t)
    return times


def counted_times(t0, t1, n):
    h = (t1 - t0) / n
    return [t0 + i * h for i in range(n + 1)]


def test_time_grid_check_catches_the_extra_step_only_for_exact_binary_steps():
    bad = time_grid_check(lambda n: while_loop_times(0.0, 2.0, n), 0.0, 2.0, (4, 8, 20))
    assert bad.status == FAIL
    assert "h=0.5" in bad.message and "h=0.25" in bad.message and "h=0.1:" not in bad.message
    assert time_grid_check(lambda n: counted_times(0.0, 2.0, n), 0.0, 2.0, (4, 8, 20)).status == PASS


MMS = ManufacturedODE(lambda t: np.array([np.exp(np.sin(t))]), lambda t, y: np.array([y[0] * np.cos(t)]))


def backward(stage_time_sign):
    """RK4 from t_end down to 0; stage_time_sign = +1 reproduces the bug (stages at t + h/2 while stepping back)."""
    def integrate_back(source, y_end, t_end, n):
        h = t_end / n
        y, t = np.array(y_end, dtype=float), t_end
        g = lambda s, u: -(MMS.rhs_ref(s, u) + source(s))  # dy/d(-t)
        for _ in range(n):
            if stage_time_sign > 0:
                y = rk4(g, t, y, h)
            else:
                y = rk4(lambda s, u: g(-s, u), -t, y, h)
            t -= h
        return y
    return integrate_back


def test_backward_study_separates_wrong_stage_times():
    ns = (10, 20, 40, 80)
    assert backward_mms_study(backward(-1), MMS, 2.0, ns, 4).status == PASS
    bad = backward_mms_study(backward(+1), MMS, 2.0, ns, 4)
    assert bad.status == FAIL and bad.fitted < 1.5


def test_order_check_says_when_the_steps_are_too_coarse():
    hs = np.array([0.04, 0.02, 0.01, 0.005])
    errs = hs**4 / (1 + 40 * hs)  # pre-asymptotic: pairwise orders 3.47, 3.64, 3.78, climbing toward 4
    r = check_order(hs, errs, 4.0)
    assert r.status == FAIL and "pre-asymptotic" in r.message
    assert "pre-asymptotic" not in check_order(hs, hs**2, 4.0).message


def test_constant_near_misses(tmp_path):
    assert check_value(3.14)[0] == "pi" and check_value(3.1416) is None
    assert check_value(39.47692640889762)[0].startswith("G M_sun") and check_value(4 * np.pi**2) is None
    assert check_value(9.81) is None and check_value(6.674e-11) is None
    src = tmp_path / "game.py"
    src.write_text("g = 9\nn = 10\nU = 110\nG = 39.47692640889762\nx = 3.14 * 2\n")
    names = [n.constant for n in scan(src)]
    assert names == ["g", "G M_sun / 4 pi^2 (au, yr)", "pi"]


def test_load_definitions_skips_the_script_body(tmp_path):
    src = tmp_path / "sim.py"
    src.write_text(
        "import math\nimport argparse\nargs = argparse.ArgumentParser().parse_args(['--bogus'])\n"
        "J = 2.0\nraise SystemExit('the simulation ran')\n"
        "def energy(s):\n    return -J * s * math.cos(0)\n"
        "def cell():\n    def inner(x):\n        return x + 1\n    return inner\n"
    )
    mod = load_definitions_from_path("sim_defs", src, keep=("J",), inner=("inner",))
    assert mod.energy(3.0) == -6.0 and mod.inner(1) == 2


def test_butcher_order_conditions():
    from physverify.butcher import check_tableau, tableau_order, trees

    assert [len(trees(n)) for n in range(1, 8)] == [1, 1, 2, 4, 9, 20, 48]
    A = np.array([[0, 0, 0, 0], [0.5, 0, 0, 0], [0, 0.5, 0, 0], [0, 0, 1, 0]])
    b = np.array([1 / 6, 1 / 3, 1 / 3, 1 / 6])
    assert tableau_order(A, b) == 4
    assert check_tableau(A, b, [0, 0.5, 0.5, 1], claimed=4).status == PASS
    # a real case: an order-3 table labelled as order 4
    bad = check_tableau(A, b, claimed=5)
    assert bad.status == FAIL and "only up to 4" in bad.message
    s = np.sqrt(15)
    gauss3 = np.array([[5 / 36, 2 / 9 - s / 15, 5 / 36 - s / 30], [5 / 36 + s / 24, 2 / 9, 5 / 36 - s / 24],
                       [5 / 36 + s / 30, 2 / 9 + s / 15, 5 / 36]])
    assert tableau_order(gauss3, [5 / 18, 4 / 9, 5 / 18], max_order=7) == 6  # implicit tables work too
    # coefficients typed with few digits are noted
    rough = check_tableau(np.round(gauss3, 8), [5 / 18, 4 / 9, 5 / 18], claimed=6, tol=1e-6)
    assert rough.status == PASS and "limited digits" in rough.message


def test_order_check_flags_non_monotone_errors():
    hs = np.array([0.1, 0.05, 0.025, 0.0125])
    errs = np.array([1e-6, 1e-8, 2e-8, 1e-8])  # leading term changes sign between the second and third
    r = check_order(hs, errs, 4.0, floor=1e-14)
    assert r.status == FAIL and "not monotone" in r.message


def test_order_check_explains_a_step_independent_error():
    hs = np.array([0.004, 0.002, 0.001, 0.0005])
    r = check_order(hs, np.array([0.0164, 0.0164, 0.0163, 0.0163]), 2.0)  # the MD cutoff-crossing case
    assert r.status == FAIL and "independent of the step" in r.message
