"""check_quadrature: degree of exactness of a rule from its nodes and weights (issue 44)."""

import numpy as np
import pytest

from physverify.stencils import check_quadrature, jacobi_moment


@pytest.mark.parametrize("n", [1, 2, 3, 5, 8])
def test_gauss_legendre_exact_to_2n_minus_1(n):
    x, w = np.polynomial.legendre.leggauss(n)
    r = check_quadrature(x, w, claimed=2 * n - 1)
    assert r.ok, r.message
    assert f"degree {2 * n - 1}" in r.message


def test_claim_above_degree_fails():
    x, w = np.polynomial.legendre.leggauss(3)
    r = check_quadrature(x, w, claimed=6)
    assert not r.ok and "degree 5" in r.message and "x^6" in r.message


def test_simpson_on_other_interval():
    # Simpson on [0, 2]: exact to degree 3
    assert check_quadrature([0, 1, 2], [1 / 3, 4 / 3, 1 / 3], claimed=3, interval=(0, 2)).ok
    assert not check_quadrature([0, 1, 2], [1 / 3, 4 / 3, 1 / 3], claimed=4, interval=(0, 2)).ok


def test_wrong_weight_scale_fails_at_degree_0():
    x, w = np.polynomial.legendre.leggauss(4)
    r = check_quadrature(x, w / 2, claimed=7)
    assert not r.ok and "x^0" in r.message


def test_radau_legendre():
    # 3-point Gauss-Radau on [-1, 1] with node -1: weights 2/9, (16 +- sqrt 6)/18; exact to degree 4
    s6 = np.sqrt(6)
    x = [-1, (1 - s6) / 5, (1 + s6) / 5]
    w = [2 / 9, (16 + s6) / 18, (16 - s6) / 18]
    assert check_quadrature(x, w, claimed=4).ok


def test_jacobi_moments_match_numerical_integral():
    xs, ws = np.polynomial.legendre.leggauss(200)
    for a, b in ((0, 0), (1, 0), (2, 1), (0.5, 1.5)):
        f = (1 - xs) ** a * (1 + xs) ** b
        for k in range(6):
            assert jacobi_moment(k, a, b) == pytest.approx(np.sum(ws * f * xs ** k), rel=1e-6, abs=1e-12)


def test_gauss_jacobi_and_swapped_weights():
    sp = pytest.importorskip("scipy.special")
    x, w = sp.roots_jacobi(4, 2.0, 1.0)   # weight (1-x)^2 (1+x)^1
    assert check_quadrature(x, w, claimed=7, alpha=2, beta=1).ok
    # alpha and beta swapped: the kind of mistake that is invisible when alpha == beta
    assert not check_quadrature(x, w, claimed=7, alpha=1, beta=2).ok


def test_one_point_gauss_jacobi_without_scipy():
    # one-point rule: node = first moment / zeroth moment, weight = zeroth moment; exact to degree 1
    a, b = 2.0, 0.5
    m0, m1 = jacobi_moment(0, a, b), jacobi_moment(1, a, b)
    assert check_quadrature([m1 / m0], [m0], claimed=1, alpha=a, beta=b).ok
    assert not check_quadrature([m1 / m0], [m0], claimed=1, alpha=b, beta=a).ok


def test_user_moments_and_bad_input():
    # Gauss-Laguerre with weight exp(-x) on [0, inf): moments k!
    from math import factorial
    x, w = np.polynomial.laguerre.laggauss(5)
    assert check_quadrature(x, w, claimed=9, interval=(0, np.inf), moments=factorial).ok
    assert not check_quadrature([0.0, np.nan], [1.0, 1.0], claimed=1).ok
    with pytest.raises(ValueError):
        check_quadrature([0, 1], [1], claimed=1)
    with pytest.raises(ValueError):
        check_quadrature([0, 1], [1, 1], claimed=1, interval=(0, 1), alpha=1)
