"""physverify scan --run: each probe finds its seeded defect and stays quiet on correct code."""

import textwrap

from physverify.cli import main
from physverify.probes import SKIP, probe
from physverify.scan import NOTE, WARN


def _write(tmp_path, name, src):
    p = tmp_path / name
    p.write_text(textwrap.dedent(src), encoding="utf-8")
    return p


def _by(findings, stage):
    return [f for f in findings if f.stage == stage]


def test_dead_argument_is_found(tmp_path):
    # J019-style: gamma is read, then overwritten, so it has no effect
    _write(tmp_path, "gas.py", '''
        def sound_speed(T, gamma=1.4, M=0.029):
            gamma = 1.4
            return (gamma * 8.314 * T / M) ** 0.5
        ''')
    d = _by(probe(tmp_path, probes=["deadargs"]), "deadargs")
    assert len(d) == 1 and d[0].level == WARN and "gamma" in d[0].message


def test_unused_argument_is_a_note_and_used_ones_are_quiet(tmp_path):
    _write(tmp_path, "osc.py", '''
        def energy(x, v, k=2.0, m=1.0, c=0.3):
            return 0.5 * m * v**2 + 0.5 * k * x**2
        ''')
    d = _by(probe(tmp_path, probes=["deadargs"]), "deadargs")
    assert [(f.level, "c" in f.message) for f in d] == [(NOTE, True)]


def test_jump_at_branch_point(tmp_path):
    # J400-style: the inner formula is off by a factor at rho = d/2
    _write(tmp_path, "field.py", '''
        def potential(rho, d=1.0):
            if rho < d / 2:
                return 2.0 * rho**2 / d**2
            return 1.0 - 2.0 * (d - rho)**2 / d**2 + 0.5
        def smooth(rho, d=1.0):
            if rho < d / 2:
                return 2.0 * rho**2 / d**2
            return 1.0 - 2.0 * (d - rho)**2 / d**2
        ''')
    b = _by(probe(tmp_path, probes=["branches"]), "branches")
    assert len(b) == 1 and "potential" in b[0].message and "d / 2" in b[0].message


def test_silent_nan_at_rest(tmp_path):
    # J409-style: the direction of v is taken without guarding v = 0
    _write(tmp_path, "drag.py", '''
        import numpy as np
        def drag(v, c=0.5):
            return -c * v**2 * v / np.abs(v)
        ''')
    e = _by(probe(tmp_path, probes=["edges"]), "edges")
    assert len(e) == 1 and "zero" in e[0].message


def test_broken_round_trip(tmp_path):
    _write(tmp_path, "conv.py", '''
        import math
        def deg_to_rad(x):
            return x * math.pi / 180
        def rad_to_deg(x):
            return x * 180 / math.pi
        def ev_to_j(x):
            return x * 1.602176634e-19
        def j_to_ev(x):
            return x / 1.602e-19
        ''')
    r = _by(probe(tmp_path, probes=["roundtrip"]), "roundtrip")
    assert len(r) == 1 and "ev_to_j" in r[0].message and r[0].level == WARN


def test_smoke_crash_and_timeout(tmp_path):
    _write(tmp_path, "crash.py", "x = [1, 2]\nprint(x[3])\n")
    _write(tmp_path, "slow.py", "while True:\n    pass\n")
    _write(tmp_path, "fine.py", "print(1 + 1)\n")
    s = {f.path: f for f in _by(probe(tmp_path, probes=["smoke"], timeout=5), "smoke")}
    assert s["crash.py"].level == WARN and "IndexError" in s["crash.py"].message
    assert s["slow.py"].level == SKIP
    assert "fine.py" not in s


def test_scripts_are_not_imported_for_function_probes(tmp_path):
    _write(tmp_path, "script.py", '''
        def f(x, unused=1.0):
            return x
        open("touched", "w").close()
        ''')
    assert probe(tmp_path, probes=["deadargs"]) == []
    assert not (tmp_path / "touched").exists()


def test_cli_run_flag(tmp_path, capsys):
    _write(tmp_path, "gas.py", '''
        def sound_speed(T, gamma=1.4):
            gamma = 1.4
            return (gamma * 287.0 * T) ** 0.5
        ''')
    assert main(["scan", str(tmp_path), "--only", "deadargs"]) == 2  # probes need --run
    assert main(["scan", str(tmp_path), "--run", "--only", "deadargs"]) == 1
    assert "gamma" in capsys.readouterr().out
    # deadargs is experimental: --run alone runs smoke and branches only
    assert main(["scan", str(tmp_path), "--run"]) == 0
    assert "gamma" not in capsys.readouterr().out


def test_jump_at_mask_boundary(tmp_path):
    # J400: a mask `inside = r <= d/2` selects the near-field formula; the far-field one does not meet it
    _write(tmp_path, "psf.py", '''
        import numpy as np
        def psf(rho, d):
            r = np.asarray(rho, float)
            out = np.empty_like(r)
            inside = r <= d / 2
            out[inside] = 1.0 + (2 * r[inside] / d) ** 2
            out[~inside] = d / (4 * r[~inside])
            return out
        ''')
    b = _by(probe(tmp_path, probes=["branches"]), "branches")
    assert len(b) == 1 and "rho" in b[0].message


def test_quiet_on_yes_no_answers_solver_controls_and_flags(tmp_path):
    # from the corpus sweep: none of these is a dead argument
    _write(tmp_path, "ok.py", '''
        def approximately_equal(a, b, tolerance=1e-9):
            return abs(a - b) <= tolerance
        def root(c, tol=1e-12, max_iter=100):
            x = c
            for _ in range(max_iter):
                x_new = 0.5 * (x + c / x)
                if abs(x_new - x) < tol:
                    break
                x = x_new
            return x
        def payoff(S, K=1.0, is_call=True):
            return max(S - K, 0.0) if is_call else max(K - S, 0.0)
        def spectrum(f, mode="lin"):
            return f if mode == "lin" else f * f
        ''')
    assert _by(probe(tmp_path, probes=["deadargs"]), "deadargs") == []


def test_script_that_needs_arguments_is_a_note(tmp_path):
    _write(tmp_path, "convert.py", "import sys\nname = sys.argv[1]\nprint(name)\n")
    s = _by(probe(tmp_path, probes=["smoke"]), "smoke")
    assert len(s) == 1 and s[0].level == NOTE


def test_own_module_in_another_folder_is_found(tmp_path):
    (tmp_path / "lib").mkdir()
    _write(tmp_path / "lib", "physics.py", "def ke(m, v):\n    return 0.5 * m * v * v\n")
    (tmp_path / "scripts").mkdir()
    _write(tmp_path / "scripts", "helpers.py", '''
        from physics import ke
        def energy(m, v, unused_g=9.8):
            g = 9.8
            return ke(m, v) + m * g * unused_g * 0
        ''')
    found = probe(tmp_path, probes=["deadargs"])
    assert not [f for f in found if f.level == SKIP]
    d = _by(found, "deadargs")
    assert len(d) == 1 and "unused_g" in d[0].message and d[0].path.startswith("scripts")


def test_quiet_on_sign_only_gated_and_clipped_arguments(tmp_path):
    _write(tmp_path, "more.py", '''
        import numpy as np
        def unwrap(delta_y, delta_theta, theta_prime):
            return 360.0 - theta_prime if np.sign(delta_y) == np.sign(delta_theta) else theta_prime
        def chain(N, J=1.0, eps=0.0, site=None):
            H = np.zeros((N, N))
            H[np.arange(N - 1), np.arange(1, N)] = J
            if site is not None:
                H[site, site] += eps
            return H
        def cp(u, v_wind):
            vel_sq = u**2
            vel_sq = np.clip(vel_sq, 0.0, (2.0 * v_wind) ** 2)
            return np.clip(1.0 - vel_sq / v_wind**2, -10.0, 5.0)
        ''')
    assert [f for f in _by(probe(tmp_path, probes=["deadargs"]), "deadargs") if f.level == WARN] == []


def test_siblings_disagree(tmp_path):
    # K18-style: a fast cumulative-sum STA/LTA and its loop twin; the fast one forgets the 1/nlta of the long window
    _write(tmp_path, "trig.py", '''
        import numpy as np
        def sta_lta(a, nsta=2, nlta=4):
            c = np.concatenate([[0.0], np.cumsum(np.asarray(a, float) ** 2)])
            n = len(c) - 1
            sta = np.array([(c[i + 1] - c[i + 1 - nsta]) / nsta for i in range(nlta, n)])
            lta = np.array([(c[i + 1] - c[i + 1 - nlta]) for i in range(nlta, n)])
            return sta / lta
        def sta_lta_py(a, nsta=2, nlta=4):
            a = np.asarray(a, float) ** 2
            return np.array([np.mean(a[i - nsta + 1:i + 1]) / np.mean(a[i - nlta + 1:i + 1]) for i in range(nlta, len(a))])
        def _trace_dense(m):
            return np.trace(np.atleast_2d(m))
        def _trace_sparse(m):
            return float(np.sum(np.diag(np.atleast_2d(m))))
        ''')
    s = _by(probe(tmp_path, probes=["siblings"]), "siblings")
    assert len(s) == 1 and s[0].level == WARN and "sta_lta_py" in s[0].message


def test_options_that_should_agree(tmp_path):
    _write(tmp_path, "ac.py", '''
        import numpy as np
        def autocorr(x, p=2, method="fft"):
            x = np.asarray(x, float)
            if method == "fft":
                X = np.fft.rfft(x, 2 * len(x))
                return np.fft.irfft(X * np.conj(X))[:p + 1]
            elif method == "time":
                return np.array([np.dot(x[:len(x) - k], x[k:]) for k in range(p + 1)])
            elif method == "biased":
                return np.array([np.dot(x[:len(x) - k], x[k:]) / len(x) for k in range(p + 1)])
        ''')
    s = _by(probe(tmp_path, probes=["siblings"]), "siblings")
    assert len(s) == 1 and s[0].level == NOTE and "'biased'" in s[0].message


def test_package_module_with_top_level_calls_is_probed_not_run(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    _write(pkg, "__init__.py", "")
    _write(pkg, "core.py", '''
        import numpy as np
        REGISTRY = []
        REGISTRY.append("trace")
        def trace_dense(m):
            return np.trace(np.atleast_2d(m))
        def trace_sparse(m):
            return np.trace(np.atleast_2d(m)) + 1.0
        ''')
    found = probe(tmp_path, probes=["smoke", "siblings"])
    assert [f.stage for f in found] == ["siblings"] and found[0].level == WARN


def test_known_answers_right_and_wrong(tmp_path):
    _write(tmp_path, "ops.py", '''
        import numpy as np
        def cumtrapz(y, x):
            return np.concatenate([[0.0], np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))])
        def cumulative_trapezoid_bad(y, x):
            return np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x).mean())  # uniform spacing assumed
        def running_mean(signal, radius):
            k = 2 * radius + 1
            c = np.cumsum(np.concatenate([[0.0], signal]))
            return (c[k:] - c[:-k]) / k
        def autocorr(x):
            x = np.asarray(x, float) - np.mean(x)
            r = np.fft.irfft(np.abs(np.fft.rfft(x, 2 * len(x))) ** 2)[:len(x)]
            return r / r[0]
        def moving_average(y, window):
            return np.convolve(y, np.ones(window), mode="valid") / (window - 1)
        ''')
    k = {f.message.split(":")[0]: f.level for f in _by(probe(tmp_path, probes=["known"]), "known")}
    assert k == {"cumulative_trapezoid_bad": WARN, "moving_average": NOTE}


def test_monotone_law_and_docstring(tmp_path):
    # K16-style: an Eyring formula with the sign of log(1 - a) lost rises with absorption
    _write(tmp_path, "room.py", '''
        import numpy as np
        def rt60_sabine(S, V, a, m=0.0, c=343.0):
            return (24 * np.log(10) / c) * V / (a * S + 4 * m * V)
        def rt60_eyring(S, V, a, m=0.0, c=343.0):
            return (24 * np.log(10) / c) * V / (S * np.log(1 - a) + 4 * m * V)
        def viscosity(T, A=1.0, B=1.0):
            """Liquid viscosity; it decreases with T (Andrade)."""
            return A * np.exp(-B / T) + 0.0 * T
        ''')
    m = _by(probe(tmp_path, probes=["monotone"]), "monotone")
    assert len(m) == 2 and {f.message.split(":")[0] for f in m} == {"rt60_eyring", "viscosity"}
    assert {f.level for f in m if "rt60" in f.message} == {WARN}


def test_dead_argument_false_alarms_from_the_corpus(tmp_path):
    # the K03, K30, J253, J401 and K36 shapes: each argument does matter, but not at inputs of order 1
    _write(tmp_path, "lib.py", '''
        import numpy as np
        HBAR = 1.054571817e-34
        def validate(name, var, max_val=10.0):
            if var > max_val:
                raise ValueError(f"{name!r} is too large")
            return float(var)
        def heat_capacity(T, a1, a2):
            if T < 258.15:
                T = 258.15
            return a1 * np.exp(a2 * (T - 273.15))
        def friction(Re, eps_D=0.0):
            if Re < 2300.0:
                return 64.0 / Re
            return 0.25 / np.log10(eps_D / 3.7 + 5.74 / Re**0.9) ** 2
        def width(t, sigma0, mass):
            return sigma0 * np.sqrt(1 + (HBAR * t / (2 * mass * sigma0**2)) ** 2)
        def dp(Re, D, roughness):
            return 64.0 / Re * D + 0.0 * np.log1p(roughness * Re / 1e9)
        ''')
    d = _by(probe(tmp_path, probes=["deadargs"]), "deadargs")
    assert not [f for f in d if f.level == WARN]
    assert not [f for f in d if "validate" in f.message]
