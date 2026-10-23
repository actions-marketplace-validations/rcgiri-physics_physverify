"""Property-based checks of the reference physics and of the patch check (need Hypothesis)."""

import numpy as np
import pytest

from pvbench.problems import pendulum

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


@settings(max_examples=40, deadline=None)
@given(
    m1=st.floats(0.2, 5.0),
    m2=st.floats(0.2, 5.0),
    L1=st.floats(0.2, 3.0),
    L2=st.floats(0.2, 3.0),
)
def test_pendulum_normal_modes_match_the_linearised_reference_for_any_parameters(m1, m2, L1, L2):
    p = dict(m1=m1, m2=m2, L1=L1, L2=L2, g=9.81)
    omegas, growth = pendulum.linearized_omegas(pendulum.rhs_reference(p))
    expected = pendulum.small_oscillation_omegas(p)
    assert growth < 1e-5
    assert np.allclose(omegas, expected, rtol=1e-5)


@settings(max_examples=40, deadline=None)
@given(
    state=st.tuples(st.floats(-1.5, 1.5), st.floats(-1.5, 1.5), st.floats(-3, 3), st.floats(-3, 3)),
)
def test_pendulum_energy_is_conserved_by_the_reference_flow(state):
    """dE/dt = grad E . f = 0 at every state, checked by a central difference along f."""
    f = pendulum.rhs_reference()
    y = np.array(state)
    eps = 1e-6
    d = (pendulum.energy_reference(y + eps * f(0, y)) - pendulum.energy_reference(y - eps * f(0, y))) / (2 * eps)
    assert abs(d) < 1e-6 * (1 + np.max(np.abs(f(0, y))) ** 2)


@settings(max_examples=25, deadline=None)
@given(
    y0=st.tuples(*[st.floats(-2, 2)] * 4),
    slope=st.tuples(*[st.floats(-1, 1)] * 4),
)
def test_patch_is_exact_for_any_line_on_the_bug_free_pendulum(y0, slope):
    from pvbench.problems._common import make_integrate
    from physverify.studies import patch_study

    integrate = make_integrate(pendulum.rhs_seeded(frozenset()), frozenset())
    result = patch_study(integrate, pendulum.rhs_reference(), y0, slope, 1.0, (5, 10, 20))
    assert result.status == "EXACT", result.message


