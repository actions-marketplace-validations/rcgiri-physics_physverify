"""Invariants of discretised operators and solvers that need no exact solution.

Four properties a correct discretisation has whatever its order:

- `check_nullspace`: a discrete Laplacian, gradient or divergence applied to a constant field gives zero at every
  interior point (a constant is in the null space of the continuous operator, and consistent stencils keep it there).
- `check_uniform_state`: a uniform state with no flow and no source is a steady solution of conservation laws, so a
  time step must leave it unchanged.
- `check_advection_direction`: a feature carried by a velocity u moves by u t (Toro, Riemann Solvers, ch. 2).
  Magnitude checks pass for a solver that integrates U_t - F_x = 0 instead of U_t + F_x = 0; this one does not.
- `check_force_gradient`: a conservative force is minus the gradient of its potential, F = -dU/dr.

In the 2026-11-01 corpus sessions these four found four bugs that exact-solution comparisons had missed or
needed far more work for: a scrambled polar-grid diffusion matrix (row sums 22 and 44 instead of 0), a
Lax-Wendroff scheme that heated still water by 0.9 K in 5 s, an Euler solver that moved fluid at -u, and a
screened-Coulomb force at 36-59 % of -dU/dr. Each passed on the correct codes it was tried on.

`check_path` tests the geometry a builder produced: a wire or path has no jumps and closes where it should (corpus
session of 2026-11-06: a wire helper that always continued from vertex 1 gave a square coil 39 % too little field).
"""

from __future__ import annotations

import numpy as np

from .checks import FAIL, PASS, Result


def _interior(shape, interior):
    if interior is None:
        return tuple(slice(1, n - 1) if n > 2 else slice(None) for n in shape)
    if isinstance(interior, int):
        return tuple(slice(interior, n - interior) for n in shape)
    return interior


def check_nullspace(operator, shape, *, field=None, interior=None, rtol: float = 1e-10, scale=None) -> Result:
    """An operator applied to a field in its null space (a constant by default) is zero away from the boundary.

    `operator` is a matrix (dense or scipy sparse, acting on the flattened field) or a function field -> field.
    `shape` is the grid shape; `field` defaults to ones. `interior` is a tuple of slices, an int width, or None
    for one cell in from every edge (boundary rows hold boundary conditions, which need not vanish).
    The tolerance is relative to `scale`, by default the size of the operator applied to a non-constant field
    (so 1/dx^2 entries do not make round-off look like a failure).
    """
    shape = tuple(np.atleast_1d(shape))
    f = np.ones(shape) if field is None else np.asarray(field, dtype=float).reshape(shape)

    def apply(v):
        if callable(operator):
            return np.asarray(operator(v.copy()), dtype=float).reshape(shape)
        return np.asarray(operator @ v.ravel(), dtype=float).reshape(shape)

    out = apply(f)
    sl = _interior(shape, interior)
    if scale is None:
        rng = np.random.default_rng(0)
        scale = float(np.max(np.abs(apply(rng.standard_normal(shape))[sl]))) or 1.0
    worst = float(np.max(np.abs(out[sl]))) if out[sl].size else 0.0
    what = "a constant field" if field is None else "the given null-space field"
    if worst > rtol * scale:
        idx = np.unravel_index(int(np.argmax(np.abs(_mask(out, sl)))), shape)
        return Result(FAIL, f"the operator applied to {what} is not zero inside the domain: largest value {worst:.3g}"
                            f" at index {tuple(int(i) for i in idx)} ({worst / scale:.2g} of the operator's size);"
                            " stencil weights or their indices are wrong")
    return Result(PASS, f"the operator maps {what} to zero at all interior points (largest {worst:.2g},"
                        f" {worst / scale:.1g} of the operator's size)")


def _mask(out, sl):
    m = np.zeros_like(out)
    m[sl] = out[sl]
    return m


def check_uniform_state(step, state, *, n_steps: int = 10, rtol: float = 1e-10, atol: float = 0.0) -> Result:
    """A uniform state with no flow and no source is unchanged by time stepping.

    `step(state) -> new_state` advances one step; `state` is the uniform initial state (any array, or a tuple of
    arrays). FAIL names the largest change. A scheme that returns an updated value where a flux or rate is
    expected (or the reverse), a source that is never zero, or a wrong sign in a boundary term shows up here.
    """
    def flat(s):
        return np.concatenate([np.ravel(np.asarray(a, dtype=float)) for a in (s if isinstance(s, (tuple, list)) else [s])])

    s0 = flat(state)
    s = state
    for k in range(1, n_steps + 1):
        s = step(s)
        cur = flat(s)
        if cur.shape != s0.shape:
            return Result(FAIL, f"step {k} changed the state's size from {s0.size} to {cur.size}")
        dev = np.abs(cur - s0)
        # a zero component (a still velocity) has no relative scale, so allow round-off on the state's size too
        tol = atol + rtol * np.abs(s0) + 64 * np.finfo(float).eps * float(np.max(np.abs(s0), initial=0.0))
        if not np.all(np.isfinite(cur)) or np.any(dev > tol):
            i = int(np.nanargmax(np.where(np.isfinite(dev), dev, np.inf)))
            return Result(FAIL, f"a uniform state changed after {k} step(s): component {i} went from {s0[i]:.6g}"
                                f" to {cur[i]:.6g}; a still, uniform state must stay unchanged")
    return Result(PASS, f"a uniform state stayed unchanged for {n_steps} steps (largest change"
                        f" {float(np.max(np.abs(flat(s) - s0))):.2g})")


def _shift(a, b, dx):
    """Periodic shift of b relative to a (b(x) ~ a(x - s)), from the cross-correlation peak with sub-cell refinement."""
    a = a - a.mean()
    b = b - b.mean()
    c = np.fft.ifft(np.conj(np.fft.fft(a)) * np.fft.fft(b)).real
    n = len(c)
    k = int(np.argmax(c))
    cm, c0, cp = c[(k - 1) % n], c[k], c[(k + 1) % n]
    den = cm - 2 * c0 + cp
    frac = 0.5 * (cm - cp) / den if den != 0 else 0.0
    s = (k + frac) % n
    if s > n / 2:
        s -= n
    return s * dx


def check_advection_direction(evolve, x, u, t, *, initial=None, rtol: float = 0.1) -> Result:
    """A feature carried by velocity `u` moves by u t, in the direction of u.

    `evolve(initial, t) -> field` runs the code under test on a periodic 1-D grid `x` (uniform) for time `t` and
    returns the advected field (density, tracer, a velocity component...). `initial` defaults to a smooth bump at
    one third of the domain. The shift is measured from the periodic cross-correlation, so u t should be well
    below half the domain. FAIL when the feature moves the wrong way (a sign error in the flux divergence or in
    a neighbour-index convention) or by more than `rtol` off u t.
    """
    x = np.asarray(x, dtype=float)
    dx = float(x[1] - x[0])
    L = dx * len(x)
    if initial is None:
        x0 = x[0] + L / 3
        w = L / 20
        initial = 1.0 + 0.2 * np.exp(-((x - x0) / w) ** 2)
    initial = np.asarray(initial, dtype=float)
    expected = u * t
    if abs(expected) >= L / 2:
        raise ValueError("u t must be smaller than half the periodic domain for the shift to be unambiguous")
    out = np.asarray(evolve(initial.copy(), t), dtype=float).reshape(initial.shape)
    s = _shift(initial, out, dx)
    if expected != 0 and np.sign(s) != np.sign(expected) and abs(s) > 0.5 * dx:
        return Result(FAIL, f"the feature moved by {s:.4g}, opposite to the velocity (expected u t = {expected:.4g});"
                            " the solver advects at -u: check the sign of the flux divergence and the neighbour indexing")
    if abs(s - expected) > rtol * abs(expected) + 0.5 * dx:
        return Result(FAIL, f"the feature moved by {s:.4g}, expected u t = {expected:.4g}"
                            f" ({abs(s - expected) / abs(expected):.1%} off, tolerance {rtol:.0%} + half a cell)")
    return Result(PASS, f"the feature moved by {s:.4g} for u t = {expected:.4g}: right direction and speed")


def check_force_gradient(potential, force, r, *, rel_step: float = 1e-6, rtol: float = 1e-5, atol: float = 0.0) -> Result:
    """A conservative force equals minus the derivative of its potential: F(r) = -dU/dr.

    `potential(r)` and `force(r)` take a scalar or array of separations (wrap a function that returns (U, F)
    as `lambda r: f(r)[0]` and `lambda r: f(r)[1]`). The derivative is a central difference with step
    `rel_step * r`. Radial convention: positive F is repulsive. FAIL lists the separations where F differs.
    """
    r = np.atleast_1d(np.asarray(r, dtype=float))
    h = rel_step * np.maximum(np.abs(r), 1e-300)
    vf = np.vectorize(lambda z: float(potential(z)))
    ff = np.vectorize(lambda z: float(force(z)))
    dudr = (vf(r + h) - vf(r - h)) / (2 * h)
    ref = -dudr
    got = ff(r)
    bad = np.abs(got - ref) > atol + rtol * np.abs(ref)
    if np.any(bad):
        i = int(np.argmax(np.abs(got - ref) / np.maximum(np.abs(ref), 1e-300)))
        ratio = got[i] / ref[i] if ref[i] != 0 else np.inf
        return Result(FAIL, f"F != -dU/dr at {int(bad.sum())} of {len(r)} separations; at r = {r[i]:.4g}"
                            f" F = {got[i]:.6g} but -dU/dr = {ref[i]:.6g} (ratio {ratio:.4g})")
    return Result(PASS, f"F = -dU/dr at all {len(r)} separations (central difference, rtol {rtol:g})")


def check_path(vertices, *, segment_lengths=None, closed: bool = False, rtol: float = 1e-8) -> Result:
    """A path built by a helper has the segments it was asked for: no jumps, and closed if it should be.

    `vertices` has shape (n, dim). `segment_lengths` is one length or one per segment. A correct solver gives a wrong
    answer on a wrong path, so test the builder separately from the field or transport calculation.
    """
    v = np.asarray(vertices, dtype=float)
    if v.ndim != 2 or len(v) < 2:
        raise ValueError("vertices must have shape (n, dim) with n >= 2")
    lengths = np.linalg.norm(np.diff(v, axis=0), axis=1)
    size = float(np.max(np.abs(v - v[0]))) or 1.0
    if segment_lengths is not None:
        want = np.broadcast_to(np.asarray(segment_lengths, dtype=float), lengths.shape)
        wrong = np.nonzero(np.abs(lengths - want) > rtol * np.maximum(want, size))[0]
        if wrong.size:
            k = int(wrong[0])
            return Result(FAIL, f"segment {k} from {v[k].tolist()} to {v[k + 1].tolist()} has length {lengths[k]:.6g},"
                                f" expected {want[k]:.6g} ({wrong.size} of {lengths.size} segments are wrong); the path jumps"
                                " or a segment started from the wrong vertex")
    if closed:
        gap = float(np.linalg.norm(v[-1] - v[0]))
        if gap > rtol * size:
            return Result(FAIL, f"the path should close but ends {gap:.6g} from its start: {v[0].tolist()} to {v[-1].tolist()}")
    what = "and closes" if closed else "and is not required to close"
    return Result(PASS, f"the {lengths.size} segments have the expected lengths {what}" if segment_lengths is not None
                  else f"the path of {lengths.size} segments closes" if closed else f"the path has {lengths.size} segments; no property was requested")


def stretched_grid(n: int, a: float = 0.0, b: float = 1.0, *, ratio: float = 1.1):
    """n + 1 nodes from a to b whose spacings grow by `ratio` from one cell to the next.

    Run the operator invariants (`check_nullspace`, `check_uniform_state`) on such a grid as well as a uniform
    one: a west-face coefficient built from the east spacing gives the right answer whenever the spacings are
    equal, so it is invisible on a uniform grid (corpus study: row sums 24 to 184 instead of 0 on a stretched
    grid, exactly 0 on a uniform one). For a second-derivative operator pass a linear field too: it is in the
    null space on any grid, and a wrong spacing shows up there even when a constant still gives zero.
    """
    if n < 1 or ratio <= 0:
        raise ValueError("need n >= 1 and ratio > 0")
    h = ratio ** np.arange(n)
    x = np.concatenate([[0.0], np.cumsum(h)])
    return a + (b - a) * x / x[-1]
