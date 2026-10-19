"""Find numeric literals in source code that are close to, but not equal to, a physical constant.

Lessons from testing other people's code: a gravitational constant in au^3 / (Msun yr^2) of
39.4769 (Gaussian, 365.25-day year) next to an orbital speed of 2 pi (which assumes 4 pi^2 = 39.4784),
g = 9 in a projectile game, pi typed as 3.14. None of these is necessarily a bug, but each is worth
one look, and an adapter's reference must use the code's value, not the textbook one.

`scan(path)` returns notes, never failures: the code may be right to round.
"""

from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from pathlib import Path

# name: (accepted values, unit, comment)
KNOWN = {
    "pi": ((math.pi,), "", "use math.pi or numpy.pi"),
    "e (Euler)": ((math.e,), "", "use math.e or numpy.e"),
    "g": ((9.80665, 9.81, 9.8), "m/s^2", "standard gravity 9.80665"),
    "G (SI)": ((6.67430e-11, 6.674e-11, 6.67e-11), "m^3 kg^-1 s^-2", "CODATA 2018: 6.67430e-11"),
    "G M_sun / 4 pi^2 (au, yr)": ((4 * math.pi**2,), "au^3 Msun^-1 yr^-2",
                                  "4 pi^2 is exact for a 1 au, 1 yr circular orbit; 39.4769 is the Gaussian value for a 365.25-day year"),
    "c": ((299792458.0, 3e8, 2.998e8), "m/s", "exact: 299792458"),
    "h (Planck)": ((6.62607015e-34,), "J s", "exact: 6.62607015e-34"),
    "hbar": ((1.054571817e-34,), "J s", "1.054571817e-34"),
    "k_B": ((1.380649e-23,), "J/K", "exact: 1.380649e-23"),
    "e (charge)": ((1.602176634e-19,), "C", "exact: 1.602176634e-19"),
    "m_e": ((9.1093837015e-31,), "kg", "9.1093837015e-31"),
    "epsilon_0": ((8.8541878128e-12,), "F/m", "8.8541878128e-12"),
    "T_c (2D Ising)": ((2 / math.log(1 + math.sqrt(2)),), "J/k_B", "2 / ln(1 + sqrt 2) = 2.269185314"),
}


@dataclass
class Note:
    line: int
    literal: str
    constant: str
    nearest: float
    relative: float
    comment: str

    def __str__(self):
        return (f"line {self.line}: {self.literal} is {self.relative:+.2g} relative to {self.constant} "
                f"({self.nearest:.10g}); {self.comment}")


def _digits(x: float) -> int:
    """Significant digits of a literal as written (3.14 -> 3)."""
    s = repr(x).lower().split("e")[0].replace("-", "").replace(".", "").lstrip("0")
    return max(len(s.rstrip("0")), 1)


def check_value(value: float, *, max_rel: float = 0.1):
    """(constant, nearest accepted value, relative difference) for a near miss, else None.

    A value equal to an accepted value, or equal to it to the precision written with
    at least 4 digits, is not a near miss: 3.1416 for pi and 9.81 for g are fine;
    3.14 and 9 are noted.
    """
    if value == 0 or not math.isfinite(value):
        return None
    best = None
    for name, (accepted, _unit, comment) in KNOWN.items():
        for ref in accepted:
            rel = value / ref - 1
            if abs(rel) > max_rel:
                continue
            if value == ref:
                return None
            written = 0.5 * 10 ** (1 - _digits(value))  # half a unit in the last written digit, relative
            if _digits(value) >= 4 and abs(rel) <= written * 1.0000001:
                return None  # matches to the precision written, with at least 4 digits
            if best is None or abs(rel) < abs(best[2]):
                best = (name, ref, rel, comment)
    return best


# names under which a short literal (an integer, or fewer than 3 digits) is still taken to mean the constant
NAMES = {"g": {"g", "grav", "gravity", "g_acc", "gacc"}, "G (SI)": {"G"}, "pi": {"pi", "PI"}, "c": {"c"}}


def _assigned_names(tree):
    """id(value node) -> names it is assigned to, for simple `name = literal` statements."""
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            out[id(node.value)] = {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and node.value is not None and isinstance(node.target, ast.Name):
            out[id(node.value)] = {node.target.id}
    return out


def scan(path, *, max_rel: float = 0.1) -> list[Note]:
    """Near-miss constants among the numeric literals of a Python file.

    Literals with 3 or more significant digits are compared with every constant.
    Integers and shorter literals (9, 3.1, 10) are so common that they are noted
    only when assigned to a name that suggests the constant (g = 9).
    """
    path = Path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
    names = _assigned_names(tree)
    notes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            v = float(node.value)
            hit = check_value(abs(v), max_rel=max_rel)
            if hit and (isinstance(node.value, int) or _digits(v) < 3):
                if not names.get(id(node), set()) & NAMES.get(hit[0], set()):
                    hit = None
            if hit:
                name, ref, rel, comment = hit
                notes.append(Note(node.lineno, ast.unparse(node), name, ref, rel, comment))
    return sorted(notes, key=lambda n: n.line)
