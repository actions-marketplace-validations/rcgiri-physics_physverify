"""Helpers and references added after batch 7 of the corpus study, each against an independent computation."""

import math

import numpy as np
import pytest

from physverify import references as R
from physverify.butcher import check_tableau
from physverify.checks import FAIL, INCONCLUSIVE, PASS
from physverify.loaders import run_script
from physverify.order import check_order
from physverify.smoke import CRASH, INPUT, OK, PARSES, smoke
from physverify.studies import damped_sinusoid_fit


def test_morse_levels_match_finite_difference_eigenvalues():
    # hbar = m = 1: omega_e = a sqrt(2 D), omega_e x_e = a^2 / 2
    D, a = 12.0, 1.0
    x = np.linspace(-2.5, 14.0, 4000)
    h = x[1] - x[0]
    V = D * (1 - np.exp(-a * x)) ** 2
    H = np.diag(1 / h**2 + V) - np.diag(np.full(len(x) - 1, 0.5 / h**2), 1) - np.diag(np.full(len(x) - 1, 0.5 / h**2), -1)
    E = np.linalg.eigvalsh(H)[:4]
    assert np.max(np.abs(E - R.morse_levels(np.arange(4), a * math.sqrt(2 * D), a * a / 2))) < 2e-3


def test_morse_width_is_the_distance_between_turning_points():
    D, a, E = 3.0, 1.7, 1.1
    V = lambda r: D * (1 - math.exp(-a * r)) ** 2 - E  # noqa: E731
    lo, hi = R._bisect(V, -2.0, 0.0), R._bisect(V, 0.0, 20.0)
    assert abs((hi - lo) - R.morse_turning_width(E, D, a)) < 1e-12


def test_deflection_matches_orbit_integration_and_weak_field():
    b = 1000.0
    assert abs(R.schwarzschild_deflection(b) / (4 / b + 15 * math.pi / (4 * b * b) + 128 / (3 * b**3)) - 1) < 2e-6  # 2 int - pi loses digits at large b
    # integrate u'' + u = 3 u^2 from far away (RK4 in phi) and read the outgoing direction
    b = 8.0
    u, du, phi, dphi = 1e-6, 1 / b, 0.0, 1e-4
    f = lambda u: 3 * u * u - u  # noqa: E731
    while True:
        k1u, k1d = du, f(u)
        k2u, k2d = du + 0.5 * dphi * k1d, f(u + 0.5 * dphi * k1u)
        k3u, k3d = du + 0.5 * dphi * k2d, f(u + 0.5 * dphi * k2u)
        k4u, k4d = du + dphi * k3d, f(u + dphi * k3u)
        u_new = u + dphi / 6 * (k1u + 2 * k2u + 2 * k3u + k4u)
        du = du + dphi / 6 * (k1d + 2 * k2d + 2 * k3d + k4d)
        phi += dphi
        if u_new <= 0:
            phi -= dphi * u_new / (u_new - u)  # linear interpolation to u = 0
            break
        u = u_new
    assert abs((phi - math.pi) - R.schwarzschild_deflection(8.0)) < 1e-4
    with pytest.raises(ValueError):
        R.schwarzschild_deflection(5.0)


def test_kerr_isco_is_the_minimum_of_the_circular_orbit_energy():
    for a, pro in ((0.0, True), (0.5, True), (0.5, False), (0.9, True)):
        s = 1 if pro else -1
        r = np.linspace(1.2, 12, 200001)
        E = (r**1.5 - 2 * r**0.5 + s * a) / (r**0.75 * np.sqrt(np.maximum(r**1.5 - 3 * r**0.5 + 2 * s * a, 1e-300)))
        E[r**1.5 - 3 * r**0.5 + 2 * s * a <= 0] = np.inf
        assert abs(r[np.argmin(E)] - R.kerr_isco(a, pro)) < 2e-3
    assert R.kerr_isco(1.0) == pytest.approx(1.0) and R.kerr_isco(1.0, False) == pytest.approx(9.0)


def test_inhour_period_is_the_slowest_eigenvalue_of_point_kinetics():
    beta = np.array([0.000266, 0.001491, 0.001316, 0.002849, 0.000896, 0.000182])
    lam = np.array([0.0127, 0.0317, 0.115, 0.311, 1.40, 3.87])
    L = 2e-5
    for rho in (0.002, 0.0005, -0.001, -0.01):
        A = np.zeros((7, 7))
        A[0, 0] = (rho - beta.sum()) / L
        A[0, 1:] = lam
        A[1:, 0] = beta / L
        A[1:, 1:] = -np.diag(lam)
        w = np.max(np.linalg.eigvals(A).real)
        assert abs(R.inhour_stable_period(rho, L, beta, lam) * w - 1) < 1e-8
    assert R.inhour_stable_period(-0.05, L, beta, lam) == pytest.approx(-1 / lam.min(), rel=0.02)


def test_qnm_table_is_close_to_the_eikonal_limit_and_rejects_unknown_modes():
    for l in (1, 2):  # scalar modes approach the eikonal (photon-sphere) value quickly
        w = R.schwarzschild_qnm(l, 0)
        eik = ((l + 0.5) - 0.5j) / (3 * math.sqrt(3))
        assert abs(w - eik) / abs(eik) < 0.02
    assert R.schwarzschild_qnm(2, 2).real < R.schwarzschild_qnm(2, 0).real  # the -6M/r^3 term lowers the barrier
    with pytest.raises(ValueError):
        R.schwarzschild_qnm(7, 2)


def test_references_listing_names_real_functions():
    for name in R.REFERENCES:
        assert callable(getattr(R, name))


def test_damped_sinusoid_fit_recovers_frequency_and_damping_after_a_pulse():
    t = np.arange(0, 200, 0.3)
    w0 = 0.4836 - 0.0968j
    y = np.exp(-0.0968 * (t - 50)) * np.cos(0.4836 * t + 0.3) * (t > 50) + 5 * np.exp(-((t - 40) / 4) ** 2)
    w = damped_sinusoid_fit(t, y, 70, 140)
    assert abs(w - w0) < 1e-6


def test_check_order_tol_alias_and_round_off_hints():
    hs = [0.1, 0.05, 0.025, 0.0125]
    errs = [h**2 for h in hs]
    assert check_order(hs, errs, 2.6, tol=0.7).status == PASS
    assert check_order(hs, errs, 2.6, tol=0.1).status == FAIL
    r = check_order([0.1, 0.05, 0.025], [3e-12, 5e-13, 4e-13], 4)
    assert r.status == INCONCLUSIVE and "coarser" in r.message
    r = check_order([0.1, 0.05, 0.025], [2e-11, 2.1e-11, 2.05e-11], 4)
    assert r.status == FAIL and "round-off" in r.message


def test_run_script_answers_input_prompts(tmp_path):
    p = tmp_path / "ask.py"
    p.write_text("n = int(input('n? '))\nx = float(input('x? '))\nresult = n * x\nprint(result)\n")
    g, out = run_script(p, inputs=[3, 1.5])
    assert g["result"] == 4.5 and "4.5" in out
    with pytest.raises(EOFError):
        run_script(p, inputs=[3])


def test_check_tableau_points_at_rounded_coefficients():
    A = [[0, 0, 0, 0], [0.5, 0, 0, 0], [0, 0.5, 0, 0], [0, 0, 1, 0]]
    b = [0.166667, 0.333333, 0.333333, 0.166667]  # classical RK4 typed with 6 digits
    r = check_tableau(A, b, claimed=4)
    assert r.status == FAIL and "too few digits" in r.message


def test_smoke_reports_parse_errors_crashes_and_input(tmp_path):
    (tmp_path / "good.py").write_text("x = 1 + 1\n")
    (tmp_path / "broken.py").write_text("def f(:\n    pass\n")
    (tmp_path / "crash.py").write_text("raise RuntimeError('boom')\n")
    (tmp_path / "ask.py").write_text("input('n? ')\n")
    got = {r.path.split("\\")[-1].split("/")[-1]: r.outcome for r in smoke(tmp_path, timeout=30)}
    assert got == {"good.py": OK, "broken.py": PARSES, "crash.py": CRASH, "ask.py": INPUT}
