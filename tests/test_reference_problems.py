"""The reference implementations are what everything else is measured against,
so they are checked here against closed forms and against each other."""

import math

import numpy as np
import pytest

from physverify.mms import zero_source
from pvbench.problems import heat1d, pendulum, projectile
from pvbench.problems._common import make_integrate
from physverify.steppers import integrate_fixed, rk4


def test_pendulum_explicit_reference_matches_mass_matrix_form():
    ref, seeded = pendulum.rhs_reference(), pendulum.rhs_seeded(frozenset())
    rng = np.random.default_rng(1)
    worst = max(np.max(np.abs(ref(0, y) - seeded(0, y))) for y in rng.uniform(-3, 3, size=(500, 4)))
    assert worst < 1e-10


def test_pendulum_reference_conserves_its_energy():
    y0 = np.array([1.2, -0.4, 0.3, 0.9])  # large amplitude
    y = integrate_fixed(pendulum.rhs_reference(), y0, 0.0, 2.0, 4000, rk4)
    e0, e1 = pendulum.energy_reference(y0), pendulum.energy_reference(y)
    assert abs(e1 - e0) < 1e-8


def test_pendulum_closed_form_frequencies_match_the_linearized_reference():
    omegas, growth = pendulum.linearized_omegas(pendulum.rhs_reference())
    assert growth < 1e-6
    assert np.allclose(omegas, pendulum.small_oscillation_omegas(), rtol=1e-6)


def test_pendulum_equal_masses_and_lengths_give_two_plus_minus_root_two():
    p = dict(m1=1.0, m2=1.0, L1=1.0, L2=1.0, g=9.81)
    expected = [math.sqrt(9.81 * (2 - math.sqrt(2))), math.sqrt(9.81 * (2 + math.sqrt(2)))]
    assert np.allclose(pendulum.small_oscillation_omegas(p), expected, rtol=1e-12)


def test_projectile_linear_drag_reference_matches_the_readme_closed_form():
    p = projectile.PARAMS
    k, g = p["b"] / p["m"], p["g"]
    vx0, vy0, t = 10.0, 12.0, 1.0
    x = vx0 / k * (1 - math.exp(-k * t))
    y = (vy0 + g / k) / k * (1 - math.exp(-k * t)) - g * t / k
    z = integrate_fixed(projectile.rhs_reference("linear"), [0.0, 0.0, vx0, vy0], 0.0, t, 2000, rk4)
    assert abs(z[0] - x) < 1e-9 and abs(z[1] - y) < 1e-9


def test_projectile_vacuum_reference_matches_the_parabola():
    z = integrate_fixed(projectile.rhs_reference("vacuum"), [0.0, 0.0, 10.0, 12.0], 0.0, 1.5, 300, rk4)
    assert abs(z[0] - 15.0) < 1e-10 and abs(z[1] - (12 * 1.5 - 0.5 * 9.81 * 1.5**2)) < 1e-10


def test_projectile_seeded_solver_without_bugs_reproduces_vacuum_range():
    v0, angle = 30.0, 40.0
    exact = projectile.range_vacuum_exact(v0, angle)
    assert abs(projectile.range_seeded(v0, angle, 1e-3, frozenset()) - exact) < 1e-5


def test_projectile_seeded_integrator_without_bugs_equals_reference_stepper():
    f = projectile.rhs_reference("quadratic")
    integ = make_integrate(projectile.rhs_seeded("quadratic", frozenset()), frozenset(), "rk4")
    a = integ(zero_source, projectile.Y0_FREE, 1.0, 50)
    b = integrate_fixed(f, projectile.Y0_FREE, 0.0, 1.0, 50, rk4)
    assert np.max(np.abs(a - b)) < 1e-12


def test_heat_manufactured_source_equals_u_t_minus_alpha_u_xx():
    x, t, e = 0.37, 0.21, 1e-4
    u = heat1d.u_manufactured
    u_t = (u(x, t + e) - u(x, t - e)) / (2 * e)
    u_xx = (u(x + e, t) - 2 * u(x, t) + u(x - e, t)) / e**2
    assert abs(heat1d.source_manufactured(x, t) - (u_t - heat1d.ALPHA * u_xx)) < 1e-4


def test_heat_manufactured_solution_satisfies_the_boundary_conditions():
    for t in (0.0, 0.05, 0.1):
        assert abs(heat1d.u_manufactured(0.0, t)) < 1e-15
        assert abs(heat1d.u_manufactured(1.0, t)) < 1e-14


HEAT_PAIRS = [
    (heat1d.u_manufactured, heat1d.source_manufactured),
    (heat1d.u_time_only, heat1d.source_time_only),
    (heat1d.u_space_only, heat1d.source_space_only),
    (heat1d.u_patch, heat1d.source_patch),
]


@pytest.mark.parametrize("u,source", HEAT_PAIRS)
def test_every_heat_source_equals_u_t_minus_alpha_u_xx(u, source):
    x, t, e = 0.37, 0.21, 1e-4
    u_t = (u(x, t + e) - u(x, t - e)) / (2 * e)
    u_xx = (u(x + e, t) - 2 * u(x, t) + u(x - e, t)) / e**2
    assert abs(source(x, t) - (u_t - heat1d.ALPHA * u_xx)) < 1e-4


@pytest.mark.parametrize("u,source", HEAT_PAIRS)
def test_every_heat_manufactured_solution_vanishes_at_both_ends(u, source):
    for t in (0.0, 0.1):
        assert abs(u(0.0, t)) < 1e-15 and abs(u(1.0, t)) < 1e-14


def test_heat_patch_solution_is_reproduced_to_round_off_for_any_grid_and_step():
    """The premise of the patch test: cubic in x and linear in t lie inside FTCS's discrete solution space."""
    for n_nodes, n_steps in ((9, None), (33, None), (17, 500), (11, 3000)):
        x, u = heat1d.solve(n_nodes, frozenset(), lambda xx: heat1d.u_patch(xx, 0.0), heat1d.source_patch, n_steps)
        assert np.max(np.abs(u - heat1d.u_patch(x, heat1d.T_END))) < 1e-12


def test_heat_time_only_error_is_nearly_independent_of_the_grid():
    """The time-only study isolates time stepping: the cubic profile adds no spatial error of its own.

    With the step count fixed, the error at a given x is therefore almost the same on every grid.
    It is not identical, because the time-stepping error is itself smoothed by the discrete
    Laplacian, which brings in a cross term of order dt * dx^2. So the grid-to-grid difference is
    small and shrinks as the grid is refined. Grids of 9, 33 and 65 nodes all contain x = 0.25, 0.5
    and 0.75.
    """
    errors_by_grid = []
    for n_nodes in (9, 33, 65):
        x, u = heat1d.solve(
            n_nodes, frozenset(), lambda xx: heat1d.u_time_only(xx, 0.0), heat1d.source_time_only, n_steps=2000
        )
        error = u - heat1d.u_time_only(x, heat1d.T_END)
        last = n_nodes - 1
        errors_by_grid.append(np.array([error[last // 4], error[last // 2], error[3 * last // 4]]))
    coarse, medium, fine = errors_by_grid
    assert np.max(np.abs(fine)) > 1e-7  # there is a real time-stepping error to compare
    assert np.max(np.abs(coarse - fine) / np.abs(fine)) < 1e-2  # nearly grid-independent
    assert np.max(np.abs(medium - fine)) < np.max(np.abs(coarse - fine))  # and the difference shrinks
