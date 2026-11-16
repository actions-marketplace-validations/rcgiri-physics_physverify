"""Linear order, stage order and stability checks on Butcher tables, against textbook values."""

import math

import numpy as np

from physverify.butcher import (
    a_stability_margin,
    check_tableau,
    is_stiffly_accurate,
    linear_order,
    r_infinity,
    stability_function,
    stage_order,
    tableau_order,
)
from physverify.checks import FAIL, PASS

S6, S3, G = math.sqrt(6), math.sqrt(3), 1 - 1 / math.sqrt(2)
RK4 = ([[0, 0, 0, 0], [.5, 0, 0, 0], [0, .5, 0, 0], [0, 0, 1, 0]], [1 / 6, 1 / 3, 1 / 3, 1 / 6])
TRAP = ([[0, 0], [.5, .5]], [.5, .5])
GAUSS2 = ([[1 / 4, 1 / 4 - S3 / 6], [1 / 4 + S3 / 6, 1 / 4]], [.5, .5])
RADAU3 = ([[(88 - 7 * S6) / 360, (296 - 169 * S6) / 1800, (-2 + 3 * S6) / 225],
           [(296 + 169 * S6) / 1800, (88 + 7 * S6) / 360, (-2 - 3 * S6) / 225],
           [(16 - S6) / 36, (16 + S6) / 36, 1 / 9]], [(16 - S6) / 36, (16 + S6) / 36, 1 / 9])
SDIRK2 = ([[G, 0], [1 - G, G]], [1 - G, G])
# order 2 but R(z) = 1 + z + z^2/2 + z^3/6: a Dahlquist test alone reports order 3
LIN3 = ([[0, 0, 0], [1, 0, 0], [0, 1 / 3, 0]], [1 / 6, 1 / 3, 1 / 2])


def test_linear_order_can_exceed_the_order():
    assert tableau_order(*LIN3) == 2 and linear_order(*LIN3) == 3
    r = check_tableau(*LIN3, claimed=2)
    assert r.status == PASS and "would overstate the order" in r.message
    assert check_tableau(*LIN3, claimed=2, claimed_linear=3).status == PASS
    assert check_tableau(*RK4, claimed=4, claimed_linear=5).status == FAIL


def test_linear_order_matches_the_stability_function():
    R = stability_function(*LIN3)
    z = 1e-2
    assert abs(R(z) - sum(z**k / math.factorial(k) for k in range(4))) < 1e-14


def test_stage_order_textbook_values():
    assert stage_order(*RK4[:1], b=RK4[1]) == 1
    assert stage_order(GAUSS2[0], b=GAUSS2[1]) == 2
    assert stage_order(RADAU3[0], b=RADAU3[1]) == 3
    assert stage_order(TRAP[0], b=TRAP[1]) == 2
    assert check_tableau(*SDIRK2, claimed=2, claimed_stage=2).status == FAIL


def test_r_infinity_and_a_stability():
    assert r_infinity(*RK4) == math.inf and a_stability_margin(*RK4) == -math.inf
    assert abs(r_infinity(*TRAP) + 1) < 1e-12 and a_stability_margin(*TRAP) > -1e-12
    assert abs(r_infinity(*GAUSS2) - 1) < 1e-12 and a_stability_margin(*GAUSS2) > -1e-12
    assert abs(r_infinity(*RADAU3)) < 1e-12 and abs(r_infinity(*SDIRK2)) < 1e-12
    # theta method with theta = 1/4 has a pole at z = 4 but |R(-inf)| = 3: not A-stable
    assert a_stability_margin([[0.25]], [1.0]) < 0


def test_stated_properties_are_checked_both_ways():
    r = check_tableau(*SDIRK2, claimed=2, l_stable=True, stiffly_accurate=True)
    assert r.status == PASS and "L-stable as stated" in r.message
    assert check_tableau(*TRAP, claimed=2, l_stable=True).status == FAIL
    assert check_tableau(*TRAP, claimed=2, a_stable=True, l_stable=False).status == PASS
    assert check_tableau(*GAUSS2, claimed=4, stiffly_accurate=True).status == FAIL
    assert is_stiffly_accurate(*RADAU3) and not is_stiffly_accurate(*GAUSS2)


def test_row_sums_that_differ_from_c_fail():
    # a real table had c[2] = 3/16 while row 2 of A sums to 3/13; the order conditions alone cannot see it
    A = np.array([[0, 0, 0, 0, 0], [1 / 7, 0, 0, 0, 0], [0, 3 / 13, 0, 0, 0], [0, 0, 1 / 3, 0, 0], [0, 0, 0, 2 / 3, 0]])
    b = [1 / 4, 0, 0, 0, 3 / 4]
    r = check_tableau(A, b, [0, 1 / 7, 3 / 16, 1 / 3, 2 / 3], claimed=3)
    assert r.status == FAIL and "row sums" in r.message
    assert check_tableau(A, b, A.sum(axis=1), claimed=3).status == PASS


def _gauss(s):
    """Gauss-Legendre table with s stages, from the nodes (Hairer & Wanner II, IV.5): A = C V^-1-type solve."""
    x, _w = np.polynomial.legendre.leggauss(s)
    c = (x + 1) / 2
    V = np.vander(c, s, increasing=True)
    b = np.linalg.solve(V.T, 1 / np.arange(1, s + 1))
    A = np.array([np.linalg.solve(V.T, ci ** np.arange(1, s + 1) / np.arange(1, s + 1)) for ci in c])
    return A, b, c


def test_gauss_methods_are_a_stable_despite_round_off():
    # Irksome GaussLegendre(5) gave a margin of -9e-10 before the scale-free test (RK census 2026-11-16)
    from physverify.butcher import a_stability_margin
    for s in range(1, 7):
        A, b, c = _gauss(s)
        assert a_stability_margin(A, b) >= 0, s
        assert check_tableau(A, b, c, claimed=min(2 * s, 8), a_stable=True).status == PASS, s
    assert a_stability_margin([[0.45]], [1.0]) < 0  # theta method below 1/2 stays not A-stable


def test_error_weights_must_sum_to_zero():
    A = [[0, 0, 0, 0], [1 / 2, 0, 0, 0], [0, 3 / 4, 0, 0], [2 / 9, 1 / 3, 4 / 9, 0]]
    b = [2 / 9, 1 / 3, 4 / 9, 0]
    bhat = [7 / 24, 1 / 4, 1 / 3, 1 / 8]
    bad = check_tableau(A, b, claimed=3, error_weights=bhat)  # the embedded solution stored as the error (probjax)
    assert bad.status == FAIL and "error weights sum to 1" in bad.message
    good = check_tableau(A, b, claimed=3, error_weights=[x - y for x, y in zip(b, bhat)], claimed_embedded=2)
    assert good.status == PASS and "embedded order 2 confirmed" in good.message


def test_additive_pair_coupling():
    from physverify.butcher import check_additive
    # Ascher, Ruuth & Spiteri (1997) ARS(2,2,2), gamma = 1 - 1/sqrt(2), delta = 1 - 1/(2 gamma): order 2 as a pair
    g = 1 - 1 / math.sqrt(2)
    d = 1 - 1 / (2 * g)
    AE, bE = [[0, 0, 0], [g, 0, 0], [d, 1 - d, 0]], [d, 1 - d, 0]
    AI, bI = [[0, 0, 0], [0, g, 0], [0, 1 - g, g]], [0, 1 - g, g]
    r = check_additive([AE, AI], [bE, bI], [[0, g, 1], [0, g, 1]], claimed=2)
    assert r.status == PASS, r.message
    # two different fourth-order methods on the same nodes: order 4 each, only 2 as a pair (mixed trees fail)
    c = [0, 0.5, 0.5, 1]
    E, bE = [[0, 0, 0, 0], [0.5, 0, 0, 0], [0, 0.5, 0, 0], [0, 0, 1, 0]], [1 / 6, 1 / 3, 1 / 3, 1 / 6]
    I, bI = [[0, 0, 0, 0], [0.5, 0, 0, 0], [-0.5, 1, 0, 0], [0, 0.5, 0.5, 0]], [1 / 6, 1 / 2, 1 / 6, 1 / 6]
    assert check_tableau(I, bI, c, claimed=4).status == PASS
    r = check_additive([E, I], [bE, bI], [c, c], claimed=4)
    assert r.status == FAIL and "coupling conditions hold only up to order 2" in r.message


def test_dense_output_and_point_values():
    from physverify.butcher import check_dense_output, dense_order
    A = [[0, 0, 0, 0], [1 / 2, 0, 0, 0], [0, 3 / 4, 0, 0], [2 / 9, 1 / 3, 4 / 9, 0]]  # Bogacki-Shampine, FSAL row
    # torchdiffeq 0.2.5 bosh3 midpoint y0 + h/2 k2: order 1 (outputs 4e4 x tol); the cubic Hermite value: order 3
    assert dense_order(A, [0, 1 / 2, 0, 0], thetas=[0.5]) == 1
    assert dense_order(A, [17 / 72, 1 / 6, 2 / 9, -1 / 8], thetas=[0.5]) == 3
    # cubic Hermite interpolant over the whole step, as weights b_i(theta) (Hairer, Norsett & Wanner I, II.6)
    b = np.array([2 / 9, 1 / 3, 4 / 9, 0])

    def herm(th):
        h01, h10, h11 = 3 * th ** 2 - 2 * th ** 3, th ** 3 - 2 * th ** 2 + th, th ** 3 - th ** 2
        w = h01 * b + h11 * np.array([0, 0, 0, 1.0])
        w[0] += h10
        return w
    assert check_dense_output(A, herm, claimed=3).status == PASS
    assert check_dense_output(A, lambda th: th * b, claimed=2).status == FAIL  # linear interpolation: order 1


def test_rosenbrock_and_w_order():
    from physverify.butcher import check_rosenbrock
    # Verwer et al. (1999) ROS2, gamma = 1 + 1/sqrt(2): order 2 for any Jacobian (W-method), L-stable
    g = 1 + 1 / math.sqrt(2)
    r = check_rosenbrock([[0, 0], [1, 0]], [[g, 0], [-2 * g, g]], [0.5, 0.5], claimed=2, w_method=True)
    assert r.status == PASS and "R(inf) = 0" in r.message, r.message
    # order 2 only with the exact Jacobian; a step-size study with a wrong Jacobian shows order 1
    m = ([[0, 0], [1, 0]], [[0.5, 0], [-1, 0.5]], [0, 1])
    assert check_rosenbrock(*m, claimed=2).status == PASS
    r = check_rosenbrock(*m, claimed=2, w_method=True)
    assert r.status == FAIL and "only up to 1" in r.message
    # linearly implicit Euler: order 1, not 2
    assert check_rosenbrock([[0]], [[1]], [1], claimed=2).status == FAIL
