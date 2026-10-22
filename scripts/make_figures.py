"""Draw the convergence figure used in the README and on the documentation site.

    python scripts/make_figures.py

It runs the `physverify demo` solver (correct, and with the damping 10% too
large) and plots the error against the step size. tests/test_figures.py
requires the committed file to match, so the figure cannot go stale.
"""

import math
from pathlib import Path

from physverify.demo import checks
from physverify.checks import run_check

OUT = Path(__file__).resolve().parents[1] / "docs" / "images" / "convergence.svg"
W, H, L, R, T, B = 560, 340, 70, 30, 40, 50  # size and margins


def mms_result(damping_factor):
    check = next(c for c in checks(damping_factor) if c.family == "mms")
    return run_check(check)


def svg() -> str:
    good, bad = mms_result(1.0), mms_result(1.1)
    lx = [math.log10(h) for h in good.hs]
    ys = [math.log10(e) for r in (good, bad) for e in r.errors]
    x0, x1 = min(lx), max(lx)
    y0, y1 = math.floor(min(ys)), math.ceil(max(ys))

    def px(x, y):
        return (L + (x - x0) / (x1 - x0) * (W - L - R), T + (y1 - y) / (y1 - y0) * (H - T - B))

    def line(points, colour, dash=""):
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in (px(x, y) for x, y in points))
        style = f' stroke-dasharray="{dash}"' if dash else ""
        dots = "".join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.5" fill="{colour}"/>'
                       for a, b in (px(x, y) for x, y in points)) if not dash else ""
        return f'<polyline points="{d}" fill="none" stroke="{colour}" stroke-width="2.5"{style}/>{dots}'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'font-family="system-ui, sans-serif" font-size="13" role="img" '
        'aria-label="Error against step size for a correct and a broken solver">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        '<text x="20" y="24" font-size="15" font-weight="600" fill="#1d1d1f">'
        "Error against step size (log-log)</text>",
    ]
    for k in range(y0, y1 + 1):  # horizontal grid lines at powers of ten
        _, yy = px(x0, k)
        parts.append(f'<line x1="{L}" x2="{W - R}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#e4e4e8"/>')
        parts.append(f'<text x="{L - 8}" y="{yy + 4:.1f}" text-anchor="end" fill="#6b6b70">1e{k}</text>')
    for h in good.hs:
        xx, _ = px(math.log10(h), y0)
        parts.append(f'<text x="{xx:.1f}" y="{H - B + 18}" text-anchor="middle" fill="#6b6b70">{h:g}</text>')
    parts.append(f'<text x="{(L + W - R) / 2}" y="{H - 10}" text-anchor="middle" fill="#6b6b70">step size h</text>')
    finest = (lx[-1], math.log10(good.errors[-1]))  # expected slope 2 through the finest correct point
    parts.append(line([finest, (x1, finest[1] + 2 * (x1 - finest[0]))], "#8a8a93", "5 4"))
    parts.append(line(list(zip(lx, map(math.log10, good.errors))), "#1a7f37"))
    parts.append(line(list(zip(lx, map(math.log10, bad.errors))), "#b42318"))
    legend = [
        ("#1a7f37", "", f"correct solver: order {good.fitted:.2f}, {good.status}"),
        ("#b42318", "", f"damping 10% too large: {bad.status}"),
        ("#8a8a93", "5 4", "expected slope (order 2)"),
    ]
    for i, (colour, dash, text) in enumerate(legend):
        y = H - B - 64 + 20 * i
        style = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<line x1="{L + 210}" x2="{L + 238}" y1="{y - 4}" y2="{y - 4}" stroke="{colour}" '
                     f'stroke-width="2.5"{style}/>')
        parts.append(f'<text x="{L + 246}" y="{y}" fill="#1d1d1f">{text}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg(), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
