# The `patch` check

A `patch` check runs the code on a manufactured solution that the discrete scheme should reproduce **exactly**, up to round-off, for every step size and grid. The expected error is zero, not small. Any error above the round-off floor is reported as a failure, whatever its order of convergence.

Order-of-convergence checks cannot see an error that is as small as the scheme's own truncation error and shrinks at the same rate. One example is an extra time step in a first-order scheme. The patch check can see it, because the expected error is zero.

Two kinds of patch solution are used here. Both statements below are claims about exact arithmetic. The tolerance section says how round-off is handled.

## 1. Explicit Runge-Kutta methods for ODEs: solutions linear in t

**Setting.** The ODE is y' = f(t, y) + s(t), where f is the code's right-hand side and s is the additive source hook (see the `integrate` contract in `physverify.mms`). The code advances with an explicit Runge-Kutta method with coefficients a_ij, b_i and c_i, using a fixed step h = t_end / n.

**Manufactured solution.** u(t) = y0 + m t, for a constant vector m. Its source is s(t) = m - f_ref(t, u(t)), where f_ref is the independently written reference operator.

**Claim.** Suppose the code satisfies three conditions:
- (a) f(t, y) = f_ref(t, y) at every point the stages visit;
- (b) every stage time is consistent with the stage state: c_i = sum_j a_ij;
- (c) the weights sum to one: sum_i b_i = 1.

Then the code returns u(t_k) exactly after every step k, for any h.

**Proof.** Suppose y_k = u(t_k). Take the stages in order. Assume every earlier stage derivative k_j equals m. Then stage i is at

  Y_i = y_k + h sum_j a_ij m = u(t_k) + c_i h m = u(t_k + c_i h).

Its derivative is therefore

  k_i = f(t_k + c_i h, Y_i) + s(t_k + c_i h) = f_ref(...) + m - f_ref(...) = m,

using (a) for the last step. So every stage derivative is m. The new state is y_{k+1} = y_k + h m sum_i b_i = u(t_k + h), using (c). Induction on k completes the proof.

Conditions (b) and (c) are exactly the consistency conditions. So the claim holds for every consistent explicit method, Euler, midpoint and classical RK4 included, whatever its order.

**What it catches** (all observed in `results/detection_matrix.md`):
- A right-hand side that differs from the reference at the sampled points. Examples: `gravity_sign`, the drag bugs, every pendulum equation bug.
- Weights that do not sum to one (`rk4_weights`).
- A stage evaluated at the wrong state (`rk4_full_step_stage2`), or at the wrong time (`rk4_stage4_time`). The forcing depends on time, so a stage time that is out of step with its stage state gives a wrong derivative.
- A wrong number of steps (`euler_extra_step`), or a wrong step size.

**What it cannot catch:**
- A consistent method that is the wrong one. Euler in place of RK4 (`euler_instead_of_rk4`) is still exact on a straight line. The order studies cover this case.
- A right-hand side that is wrong only away from the line u(t). The check samples one line through state space. Choose the line so that it crosses the regimes that matter: in `problems/projectile.py` the velocity is negative in x and changes in y, so that every drag branch is used.
- Bugs in code outside the stepper, such as landing interpolation or launch set-up. The `limit` family covers those.

**Adapters.** The `ProjectileV2` adapter reads time from x, so the line must have x = t. A line also never comes back to the ground, and `ProjectileV2.simulate()` runs until landing. So in forced runs the adapter adds a strong downward push once x is half a step past the measurement time. This only changes states after the ones being measured.

## 2. FTCS for the 1D heat equation: cubic in x, linear in t

**Setting.** The PDE is u_t = alpha u_xx + s(x, t) on [0, 1], with u = 0 at both ends. The scheme is forward Euler in time with the three-point Laplacian on N equally spaced nodes:

  u_j^{k+1} = u_j^k + dt [ alpha (u_{j+1}^k - 2 u_j^k + u_{j-1}^k) / dx^2 + s(x_j, t_k) ],   u_0 = u_{N-1} = 0.

**Manufactured solution.** u(x, t) = (1 + t) p(x), with p(x) = x - x^3. Then p(0) = p(1) = 0 and p'' = -6x. The source is s = u_t - alpha u_xx = p + 6 alpha (1 + t) x.

**Claim.** The scheme reproduces u at every node and every step, for any dx and dt.

**Proof.** The three-point second difference is exact for polynomials of degree up to 3: the Taylor remainder starts with the fourth derivative, which is zero for a cubic. So the scheme's Laplacian of u_j^k equals (1 + t_k) p''(x_j) exactly. The update then gives

  u_j^k + dt [ alpha (1 + t_k) p''(x_j) + p(x_j) - alpha (1 + t_k) p''(x_j) ] = u_j^k + dt p(x_j) = u(x_j, t_k + dt),

because u is linear in t. The boundary values are zero, and so is p at the ends.

**What it catches:**
- `extra_time_step`: one extra dt p(x).
- `source_time_shift`: the source evaluated at t_{k+1} adds dt^2 6 alpha x each step, O(dt) in total.
- `dx_off_by_one` and `alpha_ignored`: the Laplacian term no longer cancels.
- `unstable_dt`: the coupled runs use the same unstable step.

The first two have errors of the same order as FTCS's own truncation error, and no order study flags them.

**What it cannot catch:**
- Errors in terms that vanish on cubics.
- A wrong boundary treatment for nonzero boundary data, which this solution does not test.

## Round-off tolerance

"Exact" means at or below a floor.

| Check | Floor |
|---|---|
| ODE patch | 1e-11 |
| heat patch | 1e-12 |

The floor is raised in proportion to the solution's size once that size exceeds about 100 for the ODE patch, or 10 for the heat patch (`physverify.order.effective_floor`).

Observed errors on the bug-free codes:

| Case | Largest error |
|---|---|
| RK4, up to 160 steps | about 1e-14 |
| Euler, up to 640 steps | about 6e-14 |
| FTCS | about 3e-16 |

Every seeded bug that the check flags misses the floor by several orders of magnitude.

## Relation to earlier work

The name comes from the finite-element patch test. That test also asks a discretisation to reproduce a simple field (there, a polynomial displacement) exactly. For finite differences the related idea is that a stencil is exact on polynomials up to its degree. I have not read the finite-element patch-test literature or the "nearby problems" literature (Roy and others) in depth. Similar uses of an exactly reproduced manufactured solution may exist under other names, so no novelty is claimed here.
