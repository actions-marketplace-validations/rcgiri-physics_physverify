"""Do the error bars mean what they say? 68% intervals should contain the truth 68% of the time."""
import math

from physverify.studies import coverage_check


def simulate(mu, rng):
    return rng.normal(mu, 2.0, size=25)  # 25 measurements with noise 2.0


def interval(sigma_assumed):
    def iv(data, level):
        half = 0.994457883 * sigma_assumed / math.sqrt(len(data))  # z for a 68% two-sided interval
        m = data.mean()
        return m - half, m + half
    return iv


def prior(rng):  # the truth is drawn from the prior the analysis assumes
    return rng.uniform(-10, 10)


print("right noise:    ", coverage_check(simulate, interval(2.0), prior, level=0.68).message)
print("noise too small:", coverage_check(simulate, interval(1.0), prior, level=0.68).message)
