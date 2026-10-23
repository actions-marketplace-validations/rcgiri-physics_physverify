"""Adapter for double-pendulum-simulation/src/mechanics.py.

Only the right-hand side (get_derivatives) and the energy (calculate_energy)
are tested. They are stepped with physverify's own RK4, because the project's
solvers.py needs SciPy. So these checks say nothing about solvers.py.
"""

from __future__ import annotations

import numpy as np

from physverify.checks import Check
from physverify.loaders import load_module_from_path
from ..problems import pendulum as P
from ..problems._common import make_integrate
from physverify.studies import ode_checks
from . import sibling_project

ENV_VAR = "PHYSVERIFY_PENDULUM_DIR"
FOLDER = "double-pendulum-simulation"


def source_path():
    return sibling_project(ENV_VAR, FOLDER) / "src" / "mechanics.py"


def load():
    return load_module_from_path("double_pendulum_mechanics_under_test", source_path())


def checks(module=None) -> list[Check]:
    module = module or load()
    params = dict(P.PARAMS)

    def rhs(t, y):
        return np.asarray(module.get_derivatives(t, y, params), dtype=float)

    def energy(y):
        return module.calculate_energy(y, **params)

    out = ode_checks(
        "mechanics.py RHS + physverify RK4",
        make_integrate(rhs, frozenset(), "rk4"),
        rhs_ref=P.rhs_reference(params),
        mms=P.manufactured(),
        y0_free=P.Y0_FREE,
        t_end=P.MMS_T_END,
        ns=P.NS_RK4,
        order=4.0,
        quantity=energy,
        patch=P.PATCH,
        integrate_trajectory=make_integrate(rhs, frozenset(), "rk4", trajectory=True),
    )
    out.append(P.frequency_check(rhs, label="mechanics.py small-oscillation frequencies"))
    return out
