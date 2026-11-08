"""Coverage of a straight-line fit: the stated 68% interval on the slope should contain the true slope 68% of the time.

np.polyfit(..., cov=True) scales the covariance by the scatter of the residuals; cov="unscaled" assumes unit
noise, which is wrong here (noise 0.3), so its intervals are too wide.
"""
import numpy as np

from physverify.studies import coverage_check

x = np.linspace(0.0, 1.0, 20)


def simulate(slope, rng):
    return 1.0 + slope * x + rng.normal(0.0, 0.3, size=x.size)


def interval(cov_mode):
    def iv(y, level):
        z = 0.994457883  # two-sided 68% normal quantile
        p, c = np.polyfit(x, y, 1, cov=cov_mode)
        half = z * np.sqrt(c[0, 0])
        return p[0] - half, p[0] + half
    return iv


def prior(rng):
    return rng.uniform(-2.0, 2.0)


for name, mode in (("cov=True:      ", True), ("cov='unscaled':", "unscaled")):
    r = coverage_check(simulate, interval(mode), prior, level=0.68)
    print(name, r.status, "-", r.message)
