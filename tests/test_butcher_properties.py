"""Linear order, stage order and stability checks on Butcher tables, against textbook values."""

import math

import numpy as np

from physverify import butcher
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


def test_additive_different_nodes_note():
    from physverify.butcher import check_additive
    # explicit midpoint (c = 0, 1/2) with the trapezoidal rule (c = 0, 1): order 2 each, order 1 together
    # (a step-size study on a split linear problem gives 1.07 at the finest pair)
    AE, bE = [[0, 0], [0.5, 0]], [0, 1]
    AI, bI = [[0, 0], [0.5, 0.5]], [0.5, 0.5]
    r = check_additive([AE, AI], [bE, bI], [[0, 0.5], [0, 1]], claimed=2)
    assert r.status == FAIL and "coupling conditions hold only up to order 1" in r.message
    assert "complete for an autonomous problem" in r.message


def test_audit_fixes():
    import numpy as np
    import pytest

    from physverify.butcher import (
        TABLES,
        check_additive,
        check_dense_output,
        check_rosenbrock,
        check_tableau,
        rosenbrock_residuals,
        w_condition_count,
    )
    # W-method conditions: markings below a branch count (published 1, 2, 5, 13, 37)
    assert [w_condition_count(p) for p in range(1, 6)] == [1, 2, 5, 13, 37]
    rng = np.random.default_rng(3)
    al = np.tril(rng.uniform(-1, 1, (4, 4)), -1)
    G = np.tril(rng.uniform(-1, 1, (4, 4)), -1) + 0.4 * np.eye(4)
    b = rng.uniform(0, 1, 4)
    e = np.ones(4)
    marked = abs(float(b @ ((al @ G @ al @ e) * (al @ e))))  # the order-4 condition the old code skipped
    assert rosenbrock_residuals(al, G, b, 4, w_method=True)[4] >= marked
    rk4 = TABLES["rk4"]
    with pytest.raises(ValueError):  # one fixed vector at ten thetas was a confident wrong FAIL
        check_dense_output(rk4["A"], rk4["b"], claimed=4)
    assert check_dense_output(rk4["A"], rk4["b"], claimed=4, thetas=[1.0]).ok
    # FSAL dense weights (one more stage) need b; an s x (s-1) table is padded
    dp = TABLES["dormand_prince_5_4"]
    A6 = np.array(dp["A"])[:6, :6]
    with pytest.raises(ValueError, match="FSAL"):
        check_dense_output(A6, dp["b"], claimed=5, thetas=[1.0])
    assert check_dense_output(A6, dp["b"][:6], claimed=5, thetas=[1.0], b=dp["b"][:6]).ok
    assert check_dense_output(np.array(rk4["A"])[:, :3], rk4["b"], claimed=4, thetas=[1.0]).ok
    # different nodes noticed without cs; max_order below claimed no longer a false FAIL
    r = check_additive([[[0, 0], [0.5, 0]], [[0, 0], [1, 0]]], [[0, 1], [0.5, 0.5]], claimed=2)
    assert "different nodes" in r.message
    assert check_tableau(rk4["A"], rk4["b"], claimed=4, max_order=2).ok
    g = 1 + 1 / np.sqrt(2)
    assert check_rosenbrock([[0, 0], [1, 0]], [[g, 0], [-2 * g, g]], [0.5, 0.5], claimed=2, max_order=1).ok
    with pytest.raises(ValueError):
        check_rosenbrock([[0, 0], [1, 0]], [[g, 0], [-2 * g, g]], [0.5, 0.5], claimed=2, embedded=[1, 0])
    # error weights that are not b - embedded
    bs = TABLES["bogacki_shampine_3_2"]
    good = np.array(bs["b"]) - np.array(bs["embedded"])
    assert check_tableau(bs["A"], bs["b"], claimed=3, embedded=bs["embedded"], error_weights=good).ok
    r = check_tableau(bs["A"], bs["b"], claimed=3, embedded=bs["embedded"], error_weights=good * 2)
    assert not r.ok and "not b - embedded" in r.message


def test_rosenbrock_c_and_d_against_row_sums():
    import numpy as np

    from physverify.butcher import check_rosenbrock
    # Hairer's RODAS (METH = 1) in transformed form, as stored in Boost.odeint rosenbrock4, converted back
    g = 0.25
    C = np.zeros((6, 6))
    A = np.zeros((6, 6))
    C[1, 0] = -5.6688
    C[2, :2] = [-2.430093356833875, -0.2063599157091915]
    C[3, :3] = [-0.1073529058151375, -9.594562251023355, -20.47028614809616]
    C[4, :4] = [7.496443313967647, -10.24680431464352, -33.99990352819905, 11.70890893206160]
    C[5, :5] = [8.083246795921522, -7.981132988064893, -31.52159432874371, 16.31930543123136, -6.058818238834054]
    A[1, 0] = 1.544
    A[2, :2] = [0.9466785280815826, 0.2557011698983284]
    A[3, :3] = [3.314825187068521, 2.896124015972201, 0.9986419139977817]
    A[4, :4] = [1.221224509226641, 6.019134481288629, 12.53708332932087, -0.6878860361058950]
    A[5, :4], A[5, 4] = A[4, :4], 1.0
    G = np.linalg.inv(np.diag(np.full(6, 1 / g)) - C)
    alpha = A @ G
    b = np.append(A[4, :4], [1.0, 1.0]) @ G
    c = [0, 0.386, 0.21, 0.63, 1, 1]
    good = [0.25, -0.1043, 0.1035, -0.0362, 0, 0]
    r = check_rosenbrock(alpha, G, b, claimed=4, c=c, d=good, tol=1e-6)
    assert r.ok and "d agrees" in r.message and "c agrees" in r.message, r.message
    boost = [0.25, -0.1043, 0.1035, +0.0362, 0, 0]
    r = check_rosenbrock(alpha, G, b, claimed=4, c=c, d=boost, tol=1e-6)
    assert not r.ok and "d[3]" in r.message and "sign flipped" in r.message, r.message


def test_quadratic_order_reported_when_claim_fails():
    # 4 stages solved for the order-4 conditions of trees with at most 2 children per vertex, not b.c^3 = 1/4
    A = [[0, 0, 0, 0], [0.25, 0, 0, 0], [-0.2399999999999998, 0.8399999999999999, 0, 0],
         [-10.406095819197485, 15.05167430991065, -4.645578490713166, 0]]
    b = [0.43159889773048743, -0.38095238095238104, 0.992063492063492, -0.042710008841598354]
    assert butcher.tableau_order(A, b) == 3
    assert butcher.quadratic_order(A, b) == 4
    r = butcher.check_tableau(A, b, claimed=4)
    assert r.status == "FAIL" and "quadratic in y" in r.message and "order 4" in r.message
    rk4 = butcher.TABLES["rk4"]
    assert butcher.quadratic_order(rk4["A"], rk4["b"]) >= 4
    assert "quadratic" not in butcher.check_tableau(rk4["A"], rk4["b"], claimed=5).message


def test_rosenbrock_dense_output_rodas3p():
    """Rodas3P and its embedded Rodas23W with their dense outputs (Steinebach, JuliaCon 2023, Table 1):
    b_i(t) = t (b_i - c_i) + t^2 (c_i - d_i) + t^3 d_i, orders 3 and 2; a changed coefficient must fail."""
    from physverify.butcher import check_rosenbrock
    al = np.zeros((5, 5)); al[1, 0] = 4 / 9
    al[3, :3] = al[4, :3] = [-217 / 384, 183 / 128, 13 / 96]
    be = np.array([[1 / 3, 0, 0, 0, 0], [0, 1 / 3, 0, 0, 0], [-1 / 12, 3 / 4, 1 / 3, 0, 0],
                   [3 / 8, 3 / 8, -1 / 12, 1 / 3, 0], [33 / 8, -27 / 8, -3 / 4, 2 / 3, 1 / 3]])
    G = be - al
    b, bh = be[4], np.r_[be[3, :4], 0]
    c = np.array([51 / 4, -27 / 2, -9 / 4, 8 / 3, 1 / 3]); d = np.array([-135 / 8, 135 / 8, 3, -3, 0])
    ch = np.array([-3 / 8, -3 / 8, 1 / 12, 19 / 30, 1 / 30])

    def dense(bb, cc, dd):
        return lambda t: t * (bb - cc) + t ** 2 * (cc - dd) + t ** 3 * dd

    r = check_rosenbrock(al, G, b, claimed=3, dense=dense(b, c, d), claimed_dense=3)
    assert r.status == PASS and "dense output has order 3" in r.message
    r = check_rosenbrock(al, G, bh, claimed=2, w_method=True, dense=dense(bh, ch, 0 * d), claimed_dense=2)
    assert r.status == PASS
    assert check_rosenbrock(al, G, b, claimed=3, dense=dense(b, c, d), claimed_dense=4).status == FAIL
    c2 = c.copy(); c2[1] += 1e-3
    assert check_rosenbrock(al, G, b, claimed=3, dense=dense(b, c2, d), claimed_dense=3).status == FAIL
    r = check_rosenbrock(al, G, b, claimed=3, dense=dense(b, c, d)(0.5), claimed_dense=3, thetas=[0.5])
    assert r.status == PASS and "point value" in r.message
