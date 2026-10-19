"""Kepler and Sod problems and the symbolic sources."""

import math

import numpy as np
import pytest

from physverify.problems import heat1d, kepler, pendulum, sod


# --- Sod: the exact Riemann solver against published values (Toro, table 4.3, test 1) ---


def test_sod_star_state_matches_toro():
    p, u = sod.star_state()
    assert p == pytest.approx(0.30313, abs=1e-5)
    assert u == pytest.approx(0.92745, abs=1e-5)
    rho_left_star = sod.sample(0.5 * u)[0]
    rho_right_star = sod.sample(1.2 * u)[0]
    assert rho_left_star == pytest.approx(0.42632, abs=1e-5)
    assert rho_right_star == pytest.approx(0.26557, abs=1e-5)


def test_sod_exact_solution_far_from_the_waves_is_the_initial_state():
    rho, u, p = sod.exact_sod(np.array([0.01, 0.99]), sod.T_END)
    assert np.allclose(rho, [1.0, 0.125]) and np.allclose(u, 0.0) and np.allclose(p, [1.0, 0.1])


def test_sod_rarefaction_is_continuous_at_its_tail():
    p, u = sod.star_state()
    c_star = math.sqrt(1.4 * p / sod.sample(0.5 * u)[0])
    tail = u - c_star
    inside, outside = sod.sample(tail - 1e-9), sod.sample(tail + 1e-9)
    assert np.allclose(inside, outside, atol=1e-6)


def test_conservation_check_is_exact_on_the_bug_free_solver():
    check = [c for c in sod.checks() if c.family == "invariant"][0]
    assert check.run().status == "EXACT"


# --- Kepler ---


def test_kepler_reference_conserves_energy_and_angular_momentum_along_the_flow():
    f = kepler.rhs_reference()
    rng = np.random.default_rng(1)
    for _ in range(20):
        z = np.concatenate([rng.uniform(0.5, 2.0, 2) * rng.choice([-1, 1], 2), rng.normal(size=2)])
        dz = f(0.0, z)
        x, y, vx, vy = z
        r = math.hypot(x, y)
        d_energy = vx * dz[2] + vy * dz[3] + (x * dz[0] + y * dz[1]) / r**3
        d_angular = dz[0] * vy + x * dz[3] - dz[1] * vx - y * dz[2]
        assert abs(d_energy) < 1e-12 and abs(d_angular) < 1e-12


def test_kepler_solver_matches_reference_operator():
    f_ref, f = kepler.rhs_reference(), kepler.rhs_seeded(frozenset())
    z = np.array([0.7, -0.4, 0.3, 1.1])
    assert np.allclose(f(0.0, z), f_ref(0.0, z), rtol=1e-14)


def test_kepler_inverse_r_force_keeps_angular_momentum():
    """Recorded reasoning: a central force conserves angular momentum whatever its radial law."""
    results = {c.label: c.run() for c in kepler.checks(frozenset(["inverse_r_force"])) if c.family == "invariant"}
    assert results["rk4 angular momentum"].ok
    assert not results["rk4"].ok  # energy


# --- symbolic manufactured sources (need SymPy) ---


def test_symbolic_sources_reproduce_the_hand_derived_heat_sources():
    sp = pytest.importorskip("sympy")
    from physverify.symbolic import manufactured_pde

    x, t = sp.symbols("x t")
    alpha = heat1d.ALPHA
    op = lambda u: sp.diff(u, t) - alpha * sp.diff(u, x, 2)  # noqa: E731
    sines = sp.sin(sp.pi * x) + sp.Rational(1, 2) * sp.sin(3 * sp.pi * x)
    cubic = x - x**3
    cases = [
        (sp.exp(-t) * sines, heat1d.source_manufactured, heat1d.u_manufactured),
        (sp.exp(-t) * cubic, heat1d.source_time_only, heat1d.u_time_only),
        ((1 + t) * sines, heat1d.source_space_only, heat1d.u_space_only),
        ((1 + t) * cubic, heat1d.source_patch, heat1d.u_patch),
    ]
    xs = np.linspace(0, 1, 23)
    for u, hand_source, hand_u in cases:
        ms = manufactured_pde(u, op, (x, t))
        for tt in (0.0, 0.037, 0.1):
            assert np.allclose(ms.source(xs, tt), hand_source(xs, tt), rtol=1e-12, atol=1e-12)
            assert np.allclose(ms.solution(xs, tt), hand_u(xs, tt), rtol=1e-12, atol=1e-12)


def test_symbolic_source_of_a_constant_is_broadcast():
    sp = pytest.importorskip("sympy")
    from physverify.symbolic import manufactured_pde

    x, t = sp.symbols("x t")
    ms = manufactured_pde(x * t, lambda u: sp.diff(u, t), (x, t))  # source is x
    ms2 = manufactured_pde(t + 0 * x, lambda u: sp.diff(u, t), (x, t))  # source is the constant 1
    assert np.allclose(ms.source(np.array([0.5, 2.0]), 1.0), [0.5, 2.0])
    assert ms2.source(np.array([0.5, 2.0, 3.0]), 1.0).shape == (3,)


def test_symbolic_ode_derivative_matches_complex_step():
    sp = pytest.importorskip("sympy")
    from physverify.symbolic import manufactured_ode

    t = sp.symbols("t")
    mms = manufactured_ode([sp.sin(t) * sp.exp(t / 3), sp.cos(2 * t)], lambda tt, y: np.zeros(2), t)
    for tt in (0.0, 0.4, 1.3):
        expected = [math.exp(tt / 3) * (math.cos(tt) + math.sin(tt) / 3), -2 * math.sin(2 * tt)]
        assert np.allclose(mms.derivative(tt), expected, rtol=1e-13, atol=1e-15)
