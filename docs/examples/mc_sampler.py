"""A Metropolis sampler for the Gamma(3, 1) density p(x) ~ x^2 exp(-x), x > 0, checked against the exact mean 3.

The proposal is multiplicative, x' = x exp(0.5 z). It is not symmetric, so the acceptance ratio needs the
Hastings factor x'/x. The buggy sampler leaves it out and samples x^1 exp(-x) instead (mean 2).
Chains are independent, so the spread of the chain means gives an honest error bar despite autocorrelation.
"""
import numpy as np

from physverify.stochastic.stats import compare_chain_means, verdict


def chain_mean(seed, buggy, steps=20_000, burn=2_000):
    rng = np.random.default_rng(seed)
    x, total = 1.0, 0.0
    for i in range(steps):
        y = x * np.exp(0.5 * rng.normal())
        log_ratio = 2 * np.log(y / x) - (y - x)
        if not buggy:
            log_ratio += np.log(y / x)  # Hastings factor for the multiplicative proposal
        if np.log(rng.random()) < log_ratio:
            x = y
        if i >= burn:
            total += x
    return total / (steps - burn)


for buggy in (False, True):
    means = [chain_mean(seed, buggy) for seed in range(20)]
    r = verdict([compare_chain_means("mean of x", means, exact=3.0, resolution=0.05)])
    print("buggy:  " if buggy else "correct:", r.status, "-", r.message)
