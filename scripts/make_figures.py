"""Draw the convergence figures used in the README and on the documentation site.

    python scripts/make_figures.py

convergence.svg runs the `physverify demo` solver (correct, and with the damping 10% too large);
heat_order.svg runs docs/examples/heat_order.py (correct, and with the grid spacing off by one point).
Each plots the error against the step size. tests/test_figures.py requires the committed files to match,
so the figures cannot go stale.
"""

import importlib.util
import math
from pathlib import Path

from physverify.checks import run_check
from physverify.demo import checks

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "convergence.svg"
OUT_HEAT = ROOT / "docs" / "images" / "heat_order.svg"
W, H, L, R, T, B = 560, 340, 70, 30, 40, 50  # size and margins


def mms_result(damping_factor):
    check = next(c for c in checks(damping_factor) if c.family == "mms")
    return run_check(check)


def svg() -> str:
    good, bad = mms_result(1.0), mms_result(1.1)
    return figure(good.hs, good.errors, bad.errors,
                  f"correct solver: order {good.fitted:.2f}, {good.status}", f"damping 10% too large: {bad.status}",
                  "Error against step size for a correct and a broken solver", "step size h")


def heat_svg() -> str:
    spec = importlib.util.spec_from_file_location("heat_order", ROOT / "docs" / "examples" / "heat_order.py")
    ex = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ex)
    (good, hs, eg), (bad, _, eb) = ex.study(False), ex.study(True)
    return figure(hs, eg, eb, f"correct solver: order {good.fitted:.2f}, {good.status}",
                  f"dx from points: order {bad.fitted:.2f}, {bad.status}",
                  "Error against grid spacing for a correct and a broken 1D heat solver", "grid spacing dx")


def figure(hs, good_errors, bad_errors, good_label, bad_label, aria, xlabel, order=2) -> str:
    lx = [math.log10(h) for h in hs]
    ys = [math.log10(e) for es in (good_errors, bad_errors) for e in es]
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
        f'aria-label="{aria}">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        '<text x="20" y="24" font-size="15" font-weight="600" fill="#1d1d1f">'
        "Error against step size (log-log)</text>",
    ]
    for k in range(y0, y1 + 1):  # horizontal grid lines at powers of ten
        _, yy = px(x0, k)
        parts.append(f'<line x1="{L}" x2="{W - R}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#e4e4e8"/>')
        parts.append(f'<text x="{L - 8}" y="{yy + 4:.1f}" text-anchor="end" fill="#6b6b70">1e{k}</text>')
    for h in hs:
        xx, _ = px(math.log10(h), y0)
        parts.append(f'<text x="{xx:.1f}" y="{H - B + 18}" text-anchor="middle" fill="#6b6b70">{h:g}</text>')
    parts.append(f'<text x="{(L + W - R) / 2}" y="{H - 10}" text-anchor="middle" fill="#6b6b70">{xlabel}</text>')
    finest = (lx[-1], math.log10(good_errors[-1]))  # expected slope through the finest correct point
    parts.append(line([finest, (x1, finest[1] + order * (x1 - finest[0]))], "#8a8a93", "5 4"))
    parts.append(line(list(zip(lx, map(math.log10, good_errors))), "#1a7f37"))
    parts.append(line(list(zip(lx, map(math.log10, bad_errors))), "#b42318"))
    legend = [
        ("#1a7f37", "", good_label),
        ("#b42318", "", bad_label),
        ("#8a8a93", "5 4", f"expected slope (order {order})"),
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
    for path, draw in ((OUT, svg), (OUT_HEAT, heat_svg)):
        path.write_text(draw(), encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
