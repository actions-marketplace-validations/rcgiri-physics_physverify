# Statistics and Monte Carlo

## Do the error bars mean what they say?

An inference code that reports 68% intervals should contain the true value in 68% of repeated experiments. `coverage_check` repeats the experiment: it draws a truth, simulates data, asks your code for an interval and counts how often the truth is inside. An exact binomial test decides; a correct code fails at most a fraction `alpha` (default 0.001) of the time.

```python
--8<-- "docs/examples/coverage.py"
```

Output:

```text
--8<-- "docs/examples/output/coverage.txt"
```

The second interval assumes half the real noise, so it is far too narrow and covers the truth only 30% of the time.

!!! warning "Draw the truth from the analysis prior"
    For a Bayesian analysis, the truth must be drawn from the same prior the analysis assumes. Drawing it from a narrower range gave a spurious coverage of 0.865 for a nominal 0.68 interval in a real study. That is why the prior sampler is a required argument.

## Monte Carlo samplers

`physverify.stochastic` checks samplers of the 2D Ising model against exact enumeration, detailed balance and a reference replay with the same random numbers. All 21 seeded bugs in its benchmark were caught with no false alarms. See [Ising checks](../ising.md).

## Direction sampling and moment tests

`physverify.stochastic.directions.check_direction_sampler(sample, law=, normal=)` draws directions from `sample(rng, n) -> (n, 3)` and tests the cosine to the normal against the isotropic, hemisphere or Lambertian (cosine-weighted) law with a Kolmogorov-Smirnov test, and the azimuth for uniformity. On correct samplers at alpha = 1e-3 it gave 1 false alarm in 4000 runs. A Lambertian sampler written as mu = xi instead of mu = sqrt(xi) fails, and so does one with mean mu 0.700 instead of 2/3 at the default 200 000 directions.

`physverify.stochastic.stats.check_moment(values, exact, atol, resolution=)` compares a sample mean with an exact value and says how large a deviation the test would catch (`detectable_deviation`). A tolerance set from the sample size can let a wrong term pass; with `resolution` given, such a test is INCONCLUSIVE instead of PASS.
