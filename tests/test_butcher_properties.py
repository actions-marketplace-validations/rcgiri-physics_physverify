"""Linear order, stage order and stability checks on Butcher tables, against textbook values."""

import math

import numpy as np

from physverify.butcher import (a_stability_margin, check_tableau, is_stiffly_accurate, linear_order, r_infinity,
                                stability_function, stage_order, tableau_order)
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
