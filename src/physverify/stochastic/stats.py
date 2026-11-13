"""Statistics for Monte Carlo checks: error bars, autocorrelation and verdicts.

Design (docs/plan_ising.md, section 4):

* Every estimate is a mean over independent chains (each chain is burned in and
  then averaged). Chains are independent by construction, so the standard error
  is the spread of the chain means over sqrt(n_chains), with no
  autocorrelation model needed. Within one chain, `tau_int` and `blocked_error`
  give the error bar for codes that report one.
* A check makes m comparisons with exact values. Each uses a two-sided Student-t
  test with n_chains - 1 degrees of freedom at level alpha / m (Bonferroni),
  so the false-alarm rate of a whole check is at most alpha.
* Verdicts: FAIL when some comparison is significant; INCONCLUSIVE when none is,
  but the test could not have detected a deviation as large as the stated
  resolution (critical value times standard error > resolution); PASS otherwise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from ..checks import FAIL, INCONCLUSIVE, PASS, Result

ALPHA_CHECK = 1e-3  # false-alarm rate of one statistical check


def _t_pdf(x, nu):
    c = math.lgamma((nu + 1) / 2) - math.lgamma(nu / 2) - 0.5 * math.log(nu * math.pi)
    return np.exp(c - (nu + 1) / 2 * np.log1p(x * x / nu))


def t_sf(x: float, nu: float) -> float:
    """P(T > x) for Student's t with nu degrees of freedom (x >= 0), by Simpson's rule on the pdf."""
    x = abs(float(x))
    if nu > 1e6:
        return 0.5 * math.erfc(x / math.sqrt(2))
    # integrate in u = atan(t), dt = du / cos(u)^2: smooth even for the long tails of few degrees of freedom, where
    # Simpson's rule in t on [0, x] with x in the thousands misses the peak (nu = 1, alpha 1e-4 gave 11437, not 6366)
    n = 4000
    a = math.atan(x)
    u = np.linspace(0.0, a, n + 1)
    w = np.ones(n + 1)
    w[1:-1:2], w[2:-1:2] = 4, 2
    integral = float((w * _t_pdf(np.tan(u), nu) / np.cos(u) ** 2).sum() * a / (3 * n))
    return max(0.0, 0.5 - integral)


@lru_cache(maxsize=4096)
def t_critical(alpha_two_sided: float, nu: float) -> float:
    """x with P(|T| > x) = alpha, by bisection (cached: checks ask for the same few values)."""
    lo, hi = 0.0, 50.0
    while 2 * t_sf(hi, nu) > alpha_two_sided and hi < 1e7:  # few degrees of freedom: 636.6 for nu=1, alpha=1e-3
        lo, hi = hi, 2 * hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if 2 * t_sf(mid, nu) > alpha_two_sided:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def tau_int(series, c: float = 6.0) -> float:
    """Integrated autocorrelation time with Sokal's automatic window (window W >= c * tau)."""
    x = np.asarray(series, dtype=float)
    x = x - x.mean()
    n = len(x)
    var = float(np.dot(x, x)) / n
    if n < 4 or var == 0.0:
        return 0.5
    f = np.fft.rfft(x, 2 * n)
    acf = np.fft.irfft(f * np.conj(f))[:n] / (n * var)
    tau = 0.5
    for w in range(1, n):
        tau += acf[w]
        if w >= c * tau:
            break
    return max(tau, 0.5)


def blocked_error(series) -> float:
    """Standard error of the mean of a correlated series: sqrt(2 tau var / n)."""
    x = np.asarray(series, dtype=float)
    return float(np.sqrt(2.0 * tau_int(x) * x.var() / len(x)))


@dataclass
class Comparison:
    name: str
    estimate: float
    se: float
    exact: float
    resolution: float
    dof: float


def compare_chain_means(name, per_chain_values, exact, resolution, min_se=0.0) -> Comparison:
    """Mean over independent chains, with the spread of the chain means as its standard error.

    `min_se` is a floor for the standard error: for the frequency of a rare event the
    chain-to-chain spread can be zero when the event never happens, which would make
    any small expected probability look like a certain deviation.
    """
    v = np.asarray(per_chain_values, dtype=float)
    se = float(v.std(ddof=1) / math.sqrt(len(v))) if len(v) > 1 else float("inf")
    return Comparison(name, float(v.mean()), max(se, float(min_se)), float(exact), float(resolution), len(v) - 1)


def verdict(comparisons, alpha: float = ALPHA_CHECK) -> Result:
    """Bonferroni-corrected t-tests; see the module docstring for PASS, FAIL and INCONCLUSIVE."""
    if not comparisons:
        return Result(INCONCLUSIVE, "no comparisons were made, so nothing was tested")
    m = len(comparisons)
    worst, worst_ratio, unresolved = None, -1.0, []
    for c in comparisons:
        if not (np.isfinite(c.estimate) and np.isfinite(c.se)):
            return Result(FAIL, f"{c.name}: non-finite estimate")
        crit = t_critical(alpha / m, float(c.dof))
        dev = abs(c.estimate - c.exact)
        if c.se == 0.0:
            ratio = math.inf if dev > 1e-12 * max(1.0, abs(c.exact)) else 0.0
        else:
            ratio = dev / (crit * c.se)
        if ratio > worst_ratio:
            worst, worst_ratio = c, ratio
        if crit * c.se > c.resolution:
            unresolved.append(c.name)
    w = worst
    detail = f"{w.name} = {w.estimate:.5g} +- {w.se:.2g}, exact {w.exact:.5g}"
    level = f"(Bonferroni over {m}, false-alarm rate {alpha:g})"
    if worst_ratio > 1.0:
        sigmas = abs(w.estimate - w.exact) / w.se if w.se > 0 else math.inf
        return Result(FAIL, f"{detail}: off by {sigmas:.1f} standard errors {level}")
    if unresolved:
        return Result(
            INCONCLUSIVE,
            f"no significant deviation, but the error bars cannot resolve a deviation of the stated size for "
            f"{len(unresolved)} of {m} comparisons (first: {unresolved[0]}) {level}",
        )
    return Result(PASS, f"all {m} comparisons agree; largest: {detail} {level}")


def detectable_deviation(atol: float, std: float, n: int, *, power: float = 0.9) -> float:
    """Smallest true deviation of a mean that the test |mean - exact| <= atol fails with probability `power`.

    The sample mean has standard error std / sqrt(n), so a deviation d is caught with probability `power` when
    d >= atol + z_power * std / sqrt(n) (normal approximation). A moment test whose tolerance comes from the sample
    size can pass while a term is wrong: in one stochastic-integrator test atol was 0.078 and a deviation of 0.049
    from a wrong term passed. Report this number next to such a test.
    """
    z = math.sqrt(2) * _erfinv(2 * power - 1)
    return float(atol + z * std / math.sqrt(n))


def _erfinv(y: float) -> float:
    lo, hi = -6.0, 6.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if math.erf(mid) < y else (lo, mid)
    return (lo + hi) / 2


def check_moment(values, exact: float, atol: float, *, resolution: float | None = None, power: float = 0.9) -> Result:
    """The mean of independent `values` is within `atol` of `exact`, with the size of deviation the test can see.

    FAIL when |mean - exact| > atol. INCONCLUSIVE when it passes but a deviation of `resolution` (the smallest
    error that matters for the physics) would pass too with probability above 1 - `power`. PASS otherwise.
    """
    v = np.asarray(values, dtype=float).ravel()
    mean, std, n = float(np.mean(v)), float(np.std(v, ddof=1)), v.size
    dev = abs(mean - exact)
    seen = detectable_deviation(atol, std, n, power=power)
    msg = f"mean {mean:.6g}, exact {exact:.6g}, |difference| {dev:.3g}, tolerance {atol:.3g}; " \
          f"this test catches a deviation of {seen:.3g} or more {power:.0%} of the time"
    if dev > atol:
        return Result(FAIL, msg)
    if resolution is not None and seen > resolution:
        return Result(INCONCLUSIVE, msg + f", larger than the resolution {resolution:.3g}: loosen nothing, use more samples or a smaller atol")
    return Result(PASS, msg)
