"""Draw docs/images/logo.png (400 x 400): a convergence plot, error falling on a straight line, and a check mark.

Drawn at 4x and scaled down for smooth edges. Needs Pillow (not a physverify dependency).
"""

from pathlib import Path

from PIL import Image, ImageDraw

S = 4  # supersampling factor
N = 400 * S
BG, FG, DOT, CHECK = (31, 78, 121), (255, 255, 255), (255, 255, 255), (76, 201, 140)


def p(x, y):  # design units are 0..400
    return (x * S, y * S)


img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, N - 1, N - 1], radius=72 * S, fill=BG)

# axes
w = 14 * S
d.line([p(80, 70), p(80, 320), p(330, 320)], fill=FG, width=w, joint="curve")
for end in (p(80, 70), p(80, 320), p(330, 320)):
    r = w // 2
    d.ellipse([end[0] - r, end[1] - r, end[0] + r, end[1] + r], fill=FG)

# error against step size on log axes: the points of a convergence study on a straight line
pts = [(118, 284), (163, 244), (208, 204), (253, 164)]
d.line([p(106, 295), p(265, 153)], fill=(255, 255, 255, 140), width=6 * S)
for x, y in pts:
    r = 17 * S
    d.ellipse([x * S - r, y * S - r, x * S + r, y * S + r], fill=DOT)

# check mark, upper right
d.line([p(262, 82), p(290, 110), p(342, 52)], fill=CHECK, width=24 * S, joint="curve")
for end in (p(262, 82), p(342, 52)):
    r = 12 * S
    d.ellipse([end[0] - r, end[1] - r, end[0] + r, end[1] + r], fill=CHECK)

out = Path(__file__).resolve().parents[1] / "docs" / "images" / "logo.png"
img.resize((400, 400), Image.LANCZOS).save(out, optimize=True)
print(out)
