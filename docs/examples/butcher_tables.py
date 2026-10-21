"""Check Runge-Kutta tables by algebra: order, linear order, stage order, stability."""
import math

from physverify.butcher import check_tableau, r_infinity, stage_order

RK4 = ([[0, 0, 0, 0], [.5, 0, 0, 0], [0, .5, 0, 0], [0, 0, 1, 0]], [1 / 6, 1 / 3, 1 / 3, 1 / 6], [0, .5, .5, 1])
print("RK4:", check_tableau(*RK4, claimed=4).message)

# labelled order 3, but only order 2; its linear order is 3, so a test on y' = -y looks fine
A, b, c = [[0, 0, 0], [1 / 3, 0, 0], [0, 1, 0]], [1 / 2, 0, 1 / 2], [0, 1 / 3, 1]
r = check_tableau(A, b, c, claimed=3)
print("labelled 3:", r.status, "-", r.message)
print("labelled 2, linear 3:", check_tableau(A, b, c, claimed=2, claimed_linear=3).status)

# a typo in the nodes c: the order conditions cannot see it, the row sums can
r = check_tableau(*RK4[:2], [0, .5, .4, 1], claimed=4)
print("typo in c:", r.status, "-", r.message.split(";")[0])

g = 1 - 1 / math.sqrt(2)  # two-stage SDIRK: L-stable and stiffly accurate
SDIRK = ([[g, 0], [1 - g, g]], [1 - g, g])
print("SDIRK:", check_tableau(*SDIRK, claimed=2, l_stable=True, stiffly_accurate=True).message)

TRAP = ([[0, 0], [.5, .5]], [.5, .5])  # trapezoid rule: A-stable but not L-stable
r = check_tableau(*TRAP, claimed=2, l_stable=True)
print("trapezoid claimed L-stable:", r.status, "-", r.message.split(";")[0])
print("R(inf) of the trapezoid rule:", r_infinity(*TRAP), "| stage order of SDIRK:", stage_order(SDIRK[0], b=SDIRK[1]))
