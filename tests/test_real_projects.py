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
@pytest.mark.parametrize("family", ["mms", "reference", "invariant", "limit"])
def test_double_pendulum_mechanics_passes_all_families(pendulum_results, family):
    results = [r for (fam, _), r in pendulum_results.items() if fam == family]
    assert results and all(r.ok for r in results), [r.message for r in results]
