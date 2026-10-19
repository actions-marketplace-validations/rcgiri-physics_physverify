"""Calibration of the statistical checks, and detection power against run length.

    python -m physverify.stochastic.calibrate results/ising_calibration.md

Calibration (milestone M2): many independent replicate runs of the bug-free
sampler, each analysed exactly as a check would. Two rates are counted:

* per comparison, the fraction of single t-tests rejected at nominal level a.
  This should be close to a; if it is much larger, the error bars are too small.
* per check, the fraction of verdicts that are FAIL at the check's
  false-alarm rate alpha (Bonferroni over its comparisons). It must not exceed
  alpha, and is expected to be below it because Bonferroni is conservative.

Power (milestone M3): for a few bugs, the probability that the exact-distribution
check flags the bug, as a function of the number of sweeps per chain.

The replicate runs are simulated together as one large set of independent chains.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

from ..checks import FAIL
from . import exact as X
from .checks import distribution_comparisons, moment_comparisons
from .sampler import IsingSampler
from .stats import t_critical, verdict


def binomial_interval(k, n, z=1.96):
    """Wilson score interval for a proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def _groups(e, m, R, C):
    for g in range(R):
        yield e[g * C:(g + 1) * C], m[g * C:(g + 1) * C]


def calibrate(R=1000, C=32, n_sweeps=200, seed=2026, levels=(0.05, 0.01), alpha_check=0.05):
    """Returns rows (test, T, per-comparison rejection rates at each level, FAIL rate of the check)."""
    sampler = IsingSampler("metropolis")
    rows = []
    for name, T in (("exact_distribution", 2.5), ("moments", X.T_C), ("moments", 1.8)):
        e, m = sampler.sample(4, T, 0.0, n_sweeps, seed=seed, n_chains=R * C)
        seed += 1
        per_level = {a: [0, 0] for a in levels}
        fails = 0
        for eg, mg in _groups(e, m, R, C):
            if name == "exact_distribution":
                comps = distribution_comparisons(eg, mg, 4, T)
            else:
                comps = moment_comparisons(eg, mg, X.exact_moments(4, T), "")
            for c in comps:
                for a in levels:
                    crit = t_critical(a, float(c.dof))
                    per_level[a][0] += abs(c.estimate - c.exact) > crit * c.se
                    per_level[a][1] += 1
            fails += verdict(comps, alpha_check).status == FAIL
        rows.append((name, T, {a: tuple(v) for a, v in per_level.items()}, fails, R))
    return rows


POWER_BUGS = (
    None,
    "reject_zero_de",
    "exp_de_times_t",
    "acceptance_table_off_by_one",
    "same_random_number",
    "sweep_skips_last_row",
    "heatbath_missing_2",
    "synchronous_update",
)
POWER_SWEEPS = (10, 25, 50, 100, 200)


def power(R=50, C=16, sweeps=POWER_SWEEPS, seed=3000, T=2.5):
    """Detection probability of exact_distribution (alpha 0.001) for each bug and run length."""
    from . import ising

    table = {}
    for bug in POWER_BUGS:
        algorithm = ising.BUGS[bug].algorithm if bug else "metropolis"
        sampler = IsingSampler(algorithm, frozenset([bug]) if bug else frozenset())
        probs = []
        for n in sweeps:
            e, m = sampler.sample(4, T, 0.0, n, seed=seed, n_chains=R * C)
            seed += 1
            hits = sum(verdict(distribution_comparisons(eg, mg, 4, T)).status == FAIL for eg, mg in _groups(e, m, R, C))
            probs.append(hits / R)
        table[bug or "(no bug)"] = probs
    return table


def power_svg(table, sweeps=POWER_SWEEPS, width=560, height=300) -> str:
    """A small line chart of detection probability against sweeps per chain (log x axis)."""
    pad_l, pad_r, pad_t, pad_b = 46, 170, 14, 36
    x0, x1 = math.log10(sweeps[0]), math.log10(sweeps[-1])

    def px(n):
        return pad_l + (math.log10(n) - x0) / (x1 - x0) * (width - pad_l - pad_r)

    def py(p):
        return pad_t + (1 - p) * (height - pad_t - pad_b)

    colours = ["#6b6b70", "#9a6700", "#2f5bd3", "#1a7f37", "#b42318", "#8250df", "#0a7ea4", "#bf3989"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" font-family="sans-serif" font-size="11">']
    parts.append(f'<rect width="{width}" height="{height}" fill="white"/>')
    for p in (0, 0.5, 1):
        parts.append(f'<line x1="{pad_l}" x2="{width - pad_r}" y1="{py(p):.1f}" y2="{py(p):.1f}" stroke="#ddd"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{py(p) + 4:.1f}" text-anchor="end">{p:g}</text>')
    for n in sweeps:
        parts.append(f'<text x="{px(n):.1f}" y="{height - pad_b + 16}" text-anchor="middle">{n}</text>')
    parts.append(f'<text x="{(pad_l + width - pad_r) / 2:.1f}" y="{height - 4}" text-anchor="middle">sweeps per chain (16 chains per run)</text>')
    parts.append(f'<text x="12" y="{(pad_t + height - pad_b) / 2:.1f}" transform="rotate(-90 12 {(pad_t + height - pad_b) / 2:.1f})" text-anchor="middle">P(flagged)</text>')
    for k, (name, probs) in enumerate(table.items()):
        col = colours[k % len(colours)]
        pts = " ".join(f"{px(n):.1f},{py(p):.1f}" for n, p in zip(sweeps, probs))
        dash = ' stroke-dasharray="4 3"' if name in ("(no bug)", "reject_zero_de") else ""
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"{dash}/>')
        parts.append(f'<text x="{width - pad_r + 8}" y="{pad_t + 12 + 15 * k}" fill="{col}">{name}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def to_markdown(cal, table, R_power=50) -> str:
    lines = [
        "# Ising checks: calibration and power",
        "",
        "Generated by `python -m physverify.stochastic.calibrate results/ising_calibration.md`.",
        "",
        "## Calibration on the bug-free Metropolis sampler",
        "",
        "Each replicate is 32 independent chains of 200 sweeps on L = 4 (after the sampler's burn-in of 100),",
        "analysed exactly as the check analyses its chains. 95% Wilson intervals in brackets.",
        "",
        "| Test | T | Comparisons | Rejected at 0.05 | Rejected at 0.01 | Check FAIL rate at alpha = 0.05 |",
        "|---|---|---|---|---|---|",
    ]
    for name, T, per, fails, R in cal:
        k5, n5 = per[0.05]
        k1, n1 = per[0.01]
        lo5, hi5 = binomial_interval(k5, n5)
        lo1, hi1 = binomial_interval(k1, n1)
        lo, hi = binomial_interval(fails, R)
        lines.append(
            f"| {name} | {T:.4g} | {n5} | {k5 / n5:.4f} [{lo5:.4f}, {hi5:.4f}] | {k1 / n1:.4f} [{lo1:.4f}, {hi1:.4f}] "
            f"| {fails} of {R} = {fails / R:.3f} [{lo:.3f}, {hi:.3f}] |"
        )
    lines += [
        "",
        "Reading: per-comparison rejection rates near the nominal level mean the error bars are right; the check-level",
        "FAIL rate must stay at or below its alpha (Bonferroni makes it conservative). The checks themselves use",
        "alpha = 0.001, which cannot be measured directly with 1000 replicates; the 0.05 runs test the same machinery.",
        "",
        "## Power: probability that `exact_distribution` flags a bug",
        "",
        f"{R_power} replicate runs per cell, each 16 chains on L = 4 at T = 2.5, alpha = 0.001.",
        "",
        "| Bug | " + " | ".join(f"{n} sweeps" for n in POWER_SWEEPS) + " |",
        "|---|" + "---|" * len(POWER_SWEEPS),
    ]
    for name, probs in table.items():
        lines.append(f"| {name} | " + " | ".join(f"{p:.2f}" for p in probs) + " |")
    lines += [
        "",
        "`(no bug)` should stay near 0 (false alarms). `reject_zero_de` is the equivalent mutant: it keeps the",
        "Boltzmann distribution, so a distribution check should not flag it at any run length.",
        "",
        "![power curves](ising_power.svg)",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cal = calibrate()
    print("calibration done", file=sys.stderr)
    table = power()
    text = to_markdown(cal, table)
    print(text)
    if argv:
        path = Path(argv[0])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        path.with_name("ising_power.svg").write_text(power_svg(table), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
