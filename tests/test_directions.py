"""Issue 47: direction sampling, moment-test resolution, operator invariants on a stretched grid."""

import numpy as np
import pytest

from physverify.operators import check_nullspace, stretched_grid
from physverify.stochastic.directions import check_direction_sampler
from physverify.stochastic.stats import check_moment, detectable_deviation


def _from_mu(mu, rng):
    phi = rng.uniform(0, 2 * np.pi, len(mu))
    s = np.sqrt(1 - mu ** 2)
    return np.column_stack([s * np.cos(phi), s * np.sin(phi), mu])


def iso(rng, n):
    return _from_mu(rng.uniform(-1, 1, n), rng)


def hemi(rng, n):
    return _from_mu(rng.uniform(0, 1, n), rng)


def lambert(rng, n):
    return _from_mu(np.sqrt(rng.uniform(0, 1, n)), rng)


def test_correct_samplers_pass():
    assert check_direction_sampler(iso).ok
    assert check_direction_sampler(hemi, law="hemisphere").ok
    r = check_direction_sampler(lambert, law="lambert")
    assert r.ok and "0.6667" in r.message


def test_wrong_laws_fail():
    assert not check_direction_sampler(hemi, law="lambert").ok          # mu = xi instead of sqrt(xi)
    assert not check_direction_sampler(lambert, law="hemisphere").ok
    # a slightly wrong cosine law, mean mu 0.700 instead of 2/3 (density proportional to mu^1.333)
    r = check_direction_sampler(lambda g, n: _from_mu(g.uniform(0, 1, n) ** (1 / 2.333), g), law="lambert")
    assert not r.ok and "0.6996" in r.message


def test_azimuth_and_norm_and_normal():
    def half_azimuth(rng, n):
        mu = rng.uniform(-1, 1, n)
        phi = rng.uniform(0, np.pi, n)
        s = np.sqrt(1 - mu ** 2)
        return np.column_stack([s * np.cos(phi), s * np.sin(phi), mu])
    r = check_direction_sampler(half_azimuth)
    assert not r.ok and "azimuth" in r.message
    assert not check_direction_sampler(lambda g, n: 2 * iso(g, n)).ok
    # Lambert about +x
    xl = lambda g, n: lambert(g, n)[:, [2, 0, 1]]  # noqa: E731
    assert check_direction_sampler(xl, law="lambert", normal=(1, 0, 0)).ok
    assert not check_direction_sampler(xl, law="lambert").ok


def test_false_alarm_rate():
    # alpha = 1e-3: about 0.4 expected in 400 runs; the full measurement (2 x 2000 runs) is in the module docstring
    fails = sum(not check_direction_sampler(lambert, law="lambert", n=5_000, seed=s).ok for s in range(400))
    assert fails <= 3, fails


def test_detectable_deviation_and_check_moment():
    # the stochastic-integrator case: atol 0.078 lets a deviation of 0.049 through
    rng = np.random.default_rng(1)
    v = rng.normal(0.049, 1.0, 400)
    r = check_moment(v, 0.0, atol=0.078, resolution=0.03)
    assert r.status == "INCONCLUSIVE" and "catches a deviation of" in r.message
    assert detectable_deviation(0.0, 1.0, 100, power=0.5) == pytest.approx(0.0, abs=1e-9)
    assert detectable_deviation(0.1, 1.0, 10_000, power=0.9) == pytest.approx(0.1 + 1.2816 / 100, rel=1e-3)
    assert check_moment(rng.normal(0, 1, 100_000), 0.0, atol=0.02, resolution=0.03).ok
    assert not check_moment(rng.normal(0.2, 1, 10_000), 0.0, atol=0.02).ok


def _laplacian(x, west_from_east=False):
    n = len(x)
    A = np.zeros((n, n))
    for i in range(1, n - 1):
        he, hw = x[i + 1] - x[i], x[i] - x[i - 1]
        ae = 2 / (he * (he + hw))
        aw = 2 / ((he if west_from_east else hw) * (he + hw))
        A[i, i - 1], A[i, i], A[i, i + 1] = aw, -aw - ae, ae
    return A


def test_stretched_grid_reveals_spacing_slip():
    x = stretched_grid(20, ratio=1.2)
    assert x[0] == 0 and x[-1] == 1 and np.all(np.diff(np.diff(x)) > 0)
    for grid in (np.linspace(0, 1, 21), x):
        assert check_nullspace(_laplacian(grid), len(grid), field=grid).ok
    assert check_nullspace(_laplacian(np.linspace(0, 1, 21), True), 21, field=np.linspace(0, 1, 21)).ok   # invisible
    assert not check_nullspace(_laplacian(x, True), len(x), field=x).ok                                  # seen
