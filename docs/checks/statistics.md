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
