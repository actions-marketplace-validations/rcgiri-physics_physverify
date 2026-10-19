"""Checks against the author's own projects, which sit next to this repository.

The projects are only read: nothing is written into their folders. Set
PHYSVERIFY_PROJECTILE_DIR / PHYSVERIFY_PENDULUM_DIR to point somewhere else.
"""

import pytest

from physverify.adapters import double_pendulum, projectile_v2
from physverify.checks import run_check

projectile_missing = not projectile_v2.source_path().is_file()
pendulum_missing = not double_pendulum.source_path().is_file()


@pytest.fixture(scope="module")
def projectile_results():
    return {(c.family, c.label): run_check(c) for c in projectile_v2.checks()}


@pytest.fixture(scope="module")
def pendulum_results():
    return {(c.family, c.label): run_check(c) for c in double_pendulum.checks()}


@pytest.mark.skipif(projectile_missing, reason="projectile-simulation not found")
@pytest.mark.parametrize("mode", ["vacuum", "linear", "quadratic"])
@pytest.mark.parametrize("method", ["rk4", "euler"])
@pytest.mark.parametrize("family", ["mms", "reference"])
def test_projectile_v2_matches_independent_reference_at_design_order(projectile_results, mode, method, family):
    result = projectile_results[(family, f"{mode}/{method}")]
    assert result.ok, result.message


@pytest.mark.skipif(projectile_missing, reason="projectile-simulation not found")
@pytest.mark.parametrize("method", ["rk4", "euler"])
def test_projectile_v2_conserves_vacuum_energy_at_design_order(projectile_results, method):
    result = projectile_results[("invariant", f"vacuum/{method}")]
    assert result.ok, result.message


@pytest.mark.skipif(projectile_missing, reason="projectile-simulation not found")
def test_projectile_v2_landing_range_is_second_order(projectile_results):
    """Regression test for a finding made with physverify on 2026-10-19.

    simulate() used to read the range from the last point above ground. Its
    interpolation branch tested int(fraction) != 0, but fraction was between
    -0.08 and 0 for dt = 0.1, 0.01 and 0.001 (checked by hand), so the branch
    never ran and the range error was first order in dt (0.10 m at dt = 0.01)
    even though the integrator is fourth order. After linear interpolation of
    the landing point the observed order is 2 (error 1.2e-4 m at dt = 0.01).
    """
    result = projectile_results[("limit", "ProjectileV2 vacuum/rk4 range")]
    assert result.ok, result.message
    assert abs(result.fitted - 2.0) < 0.2, result.message


@pytest.mark.skipif(pendulum_missing, reason="double-pendulum-simulation not found")
@pytest.mark.parametrize("family", ["mms", "reference", "invariant", "limit", "patch"])
def test_double_pendulum_mechanics_passes_all_families(pendulum_results, family):
    results = [r for (fam, _), r in pendulum_results.items() if fam == family]
    assert results and all(r.ok for r in results), [r.message for r in results]


@pytest.mark.skipif(projectile_missing, reason="projectile-simulation not found")
@pytest.mark.parametrize("mode", ["vacuum", "linear", "quadratic"])
@pytest.mark.parametrize("method", ["rk4", "euler"])
def test_projectile_v2_reproduces_the_linear_patch_solution_and_whole_trajectory(projectile_results, mode, method):
    assert projectile_results[("patch", f"{mode}/{method}")].status == "EXACT"
    trajectory = projectile_results[("mms", f"{mode}/{method} (whole trajectory)")]
    assert trajectory.ok, trajectory.message


# Audit of the author's own projects.
from physverify.adapters import lorenz, projectile_v1, three_body  # noqa: E402

lorenz_missing = not lorenz.source_path().is_file()
three_body_missing = not three_body.source_path().is_file()
projectile_v1_missing = not projectile_v1.source_path().is_file()


@pytest.fixture(scope="module")
def three_body_results():
    return {(c.family, c.label): run_check(c) for c in three_body.checks()}


@pytest.mark.skipif(lorenz_missing, reason="lorenz-attractor-simulation not found")
def test_lorenz_passes_every_check():
    results = [(c.label, run_check(c)) for c in lorenz.checks()]
    assert len(results) == 7
    assert all(r.ok for _, r in results), [(label, r.message) for label, r in results if not r.ok]


@pytest.mark.skipif(projectile_v1_missing, reason="projectile-simulation not found")
@pytest.mark.parametrize("mode", ["vacuum", "linear", "quadratic"])
def test_projectile_v1_euler_is_first_order(mode):
    check = next(c for c in projectile_v1.checks() if c.label.startswith(f"v1 {mode}/"))
    result = run_check(check)
    assert result.ok, result.message


@pytest.mark.skipif(three_body_missing, reason="three-body-simulation not found")
def test_three_body_rhs_and_verlet_pass(three_body_results):
    bad = [(k, r.message) for k, r in three_body_results.items() if not r.ok]
    assert not bad, bad


@pytest.mark.skipif(three_body_missing, reason="three-body-simulation not found")
def test_three_body_driver_reaches_t_end(three_body_results):
    """Regression test for finding TB-1 (2026-10-19), fixed in three-body-simulation 73faf33."""
    key = ("reference", "run_verlet_simulation final state at t_end")
    if key not in three_body_results:
        pytest.skip("needs SciPy")
    assert three_body_results[key].ok, three_body_results[key].message


@pytest.mark.skipif(three_body_missing, reason="three-body-simulation not found")
def test_three_body_energy_function_matches_softened_dynamics(three_body_results):
    """Regression test for finding TB-2 (2026-10-19), fixed in three-body-simulation b83d173."""
    result = three_body_results[("invariant", "calculate_energy is the conserved quantity")]
    assert result.ok, result.message
