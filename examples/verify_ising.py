"""A physverify spec for the Ising sampler in examples/ising_checkerboard.py.

    physverify run examples/verify_ising.py --html ising_report.html

Takes about a minute. The checks that need single-site updates (scripted_rng,
acceptance) do not apply to a checkerboard code and are left out.
"""

from ising_checkerboard import CheckerboardIsing

from physverify.stochastic.checks import ising_checks


def checks():
    return ising_checks(CheckerboardIsing())
