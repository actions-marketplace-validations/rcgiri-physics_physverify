"""Direction sampling in Monte Carlo transport codes (issue #47).

A sampler returns unit vectors; mu = d . n is the cosine to a normal n. The exact laws:

- isotropic on the sphere: mu uniform on [-1, 1], CDF (mu + 1) / 2;
- isotropic on the hemisphere about n: mu uniform on [0, 1], CDF mu;
- Lambertian (cosine-weighted, diffuse wall emission or reflection): density 2 mu on [0, 1], CDF mu^2, mean 2/3
  (Modest, Radiative Heat Transfer, sec. 1.6). Sampling mu = sqrt(xi) gives it; mu = xi gives the hemisphere law.

The azimuth about n must be uniform for all three. The test is a Kolmogorov-Smirnov test on mu and one on the
azimuth, each at alpha / 2, so the false-alarm rate of the check is at most alpha (measured on
correct samplers at alpha = 1e-3, n = 20 000: 0 of 2000 runs for the Lambert law, 1 of 2000 for the isotropic law). In the corpus study a phonon-transport code drew
wall reflections with mean mu 0.700 instead of 2/3; at the default n = 200 000 that deviation is found.
"""

from __future__ import annotations

import math

import numpy as np

from ..checks import FAIL, PASS, Result

_LAWS = {
    "isotropic": (lambda m: (m + 1) / 2, 0.0),
    "hemisphere": (lambda m: np.clip(m, 0, 1), 0.5),
    "lambert": (lambda m: np.clip(m, 0, 1) ** 2, 2 / 3),
}


def ks_pvalue(d: float, n: int) -> float:
    """Asymptotic p-value of the one-sample Kolmogorov-Smirnov statistic d for n samples
    (Stephens' small-sample correction; Numerical Recipes 3rd ed., sec. 14.3.3)."""
    sq = math.sqrt(n)
    lam = (sq + 0.12 + 0.11 / sq) * d
    if lam < 0.2:
        return 1.0
    s = sum((-1) ** (k - 1) * math.exp(-2 * k * k * lam * lam) for k in range(1, 101))
    return float(min(1.0, max(0.0, 2 * s)))


def _ks(x, cdf) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    f = cdf(x)
    i = np.arange(1, n + 1)
    return float(max(np.max(i / n - f), np.max(f - (i - 1) / n)))


def check_direction_sampler(sample, *, law: str = "isotropic", normal=(0.0, 0.0, 1.0), n: int = 200_000,
                            seed: int = 0, alpha: float = 1e-3) -> Result:
    """Directions from `sample(rng, n) -> (n, 3)` follow `law` ("isotropic", "hemisphere" or "lambert") about `normal`.

    FAIL when a vector is not of unit length, when mu = d . normal does not follow the law, or when the azimuth
    about the normal is not uniform. The message gives the sample mean of mu next to the exact one.
    """
    if law not in _LAWS:
        raise ValueError(f"law must be one of {sorted(_LAWS)}, got {law!r}")
    d = np.asarray(sample(np.random.default_rng(seed), n), dtype=float)
    if d.ndim != 2 or d.shape[1] != 3:
        raise ValueError(f"the sampler must return an (n, 3) array, got shape {d.shape}")
    norm = np.linalg.norm(d, axis=1)
    if not np.all(np.isfinite(norm)) or np.max(np.abs(norm - 1)) > 1e-8:
        return Result(FAIL, f"the sampled directions are not unit vectors (|d| from {norm.min():.6g} to {norm.max():.6g})")
    nv = np.asarray(normal, dtype=float)
    nv = nv / np.linalg.norm(nv)
    mu = d @ nv
    cdf, mean = _LAWS[law]
    m = len(mu)
    p_mu = ks_pvalue(_ks(mu, cdf), m)
    # azimuth in the plane normal to nv
    e1 = np.cross(nv, [1.0, 0, 0] if abs(nv[0]) < 0.9 else [0, 1.0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(nv, e1)
    phi = np.arctan2(d @ e2, d @ e1)
    keep = np.abs(mu) < 1 - 1e-12
    p_phi = ks_pvalue(_ks(phi[keep], lambda x: (x + np.pi) / (2 * np.pi)), int(keep.sum()))
    se = float(np.std(mu) / math.sqrt(m))
    what = f"mean mu {np.mean(mu):.4f} (exact {mean:.4f}, standard error {se:.1g}) over {m} directions"
    if p_mu < alpha / 2:
        return Result(FAIL, f"the cosines to the normal do not follow the {law} law: KS p = {p_mu:.2g}; {what}")
    if p_phi < alpha / 2:
        return Result(FAIL, f"the azimuth about the normal is not uniform: KS p = {p_phi:.2g}; {what}")
    return Result(PASS, f"the directions follow the {law} law (KS p = {p_mu:.2g} for mu, {p_phi:.2g} for the azimuth); {what}")
