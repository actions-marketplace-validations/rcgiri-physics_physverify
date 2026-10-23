"""physverify scan: each stage finds its pattern, and stays quiet on correct code."""

import json
import textwrap

from physverify.cli import main
from physverify.scan import NOTE, WARN, scan


def _write(tmp_path, name, src):
    p = tmp_path / name
    p.write_text(textwrap.dedent(src), encoding="utf-8")
    return p


def _by_stage(findings, stage):
    return [f for f in findings if f.stage == stage]


def test_correct_rk4_table_is_a_note_only(tmp_path):
    _write(tmp_path, "rk.py", '''
        def rk4():
            A = [[0, 0, 0, 0], [0.5, 0, 0, 0], [0, 0.5, 0, 0], [0, 0, 1, 0]]
            b = [1/6, 1/3, 1/3, 1/6]
            c = [0, 0.5, 0.5, 1]
            return A, b, c
        ''')
    t = _by_stage(scan(tmp_path)[0], "tables")
    assert len(t) == 1 and t[0].level == NOTE and "order 4" in t[0].message


def test_table_below_its_claimed_order_and_bad_row_sum(tmp_path):
    # Heun's third-order table with a32 typed wrong, labelled order 3, and c that does not match
    _write(tmp_path, "rk.py", '''
        import numpy as np
        def method_order3():
            A = np.array([[0, 0, 0], [1/3, 0, 0], [0, 0.6, 0]])
            b = np.array([1/4, 0, 3/4])
            c = [0, 1/3, 2/3]
            return A, b, c
        ''')
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN
    assert "suggests order 3" in t.message and "row 2 of A sums to" in t.message


def test_error_weights_must_sum_to_zero(tmp_path):
    _write(tmp_path, "rk.py", '''
        A = [[0, 0], [1, 0]]
        b = [0.5, 0.5]
        e = [0.5, -0.47]
        ''')
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN and "sum to 0.03" in t.message


def test_vector_that_is_not_weights_is_not_a_table(tmp_path):
    _write(tmp_path, "m.py", '''
        A = [[1, 0], [2, 3]]
        b = [4, 5]
        ''')
    assert not _by_stage(scan(tmp_path)[0], "tables")


def test_grid_spacing_mismatch_same_file(tmp_path):
    _write(tmp_path, "g.py", '''
        import numpy as np
        def grid(L, N):
            x = np.linspace(0, L, N)
            dx = L / N
            return x, dx
        def interior(W, N):
            x = np.linspace(0, W, N + 1)[1:-1]
            dx = W / (N - 1)
            return x, dx
        ''')
    g = _by_stage(scan(tmp_path)[0], "grid")
    assert [f.line for f in g] == [5, 9] and all(f.level == WARN for f in g)


def test_correct_grid_spacings_are_quiet(tmp_path):
    _write(tmp_path, "g.py", '''
        import numpy as np
        def grid(L, N, a, b):
            x = np.linspace(0, L, N + 1)
            dx = L / N
            y = np.linspace(a, b, N)
            dy = (b - a) / (N - 1)
            z = np.linspace(0, L, N, endpoint=False)
            dz = L / N
            return x, dx, y, dy, z, dz
        ''')
    assert not _by_stage(scan(tmp_path)[0], "grid")


def test_grid_mismatch_across_files_is_a_note(tmp_path):
    _write(tmp_path, "ham.py", '''
        class H:
            def __init__(self, N, extent):
                self.N, self.extent = N, extent
                self.dx = extent / N
        ''')
    _write(tmp_path, "particle.py", '''
        import numpy as np
        def grid(H):
            return np.linspace(-H.extent / 2, H.extent / 2, H.N)
        ''')
    (g,) = _by_stage(scan(tmp_path)[0], "grid")
    assert g.level == NOTE and g.path == "ham.py"


def test_inverse_pairs_and_constants(tmp_path):
    _write(tmp_path, "c.py", '''
        g = 9
        def cart_to_polar(x): return x
        def polar_to_cart(x): return x
        def s2z(x): return x
        def z2s(x): return x
        ''')
    f = scan(tmp_path)[0]
    assert len(_by_stage(f, "pairs")) == 2
    assert _by_stage(f, "constants")


def test_unparsable_file_is_reported_not_raised(tmp_path):
    _write(tmp_path, "bad.py", "def f(:\n")
    findings, unparsed = scan(tmp_path)
    assert findings == [] and len(unparsed) == 1


def test_cli_exit_codes_and_json(tmp_path, capsys):
    _write(tmp_path, "g.py", "import numpy as np\nx = np.linspace(0, L, N)\ndx = L / N\n")
    assert main(["scan", str(tmp_path)]) == 1
    assert main(["scan", str(tmp_path), "--only", "pairs"]) == 0
    assert main(["scan", str(tmp_path), "--only", "nope"]) == 2
    capsys.readouterr()
    assert main(["scan", str(tmp_path), "--json", "-"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["warn"] == 1 and data["findings"][0]["stage"] == "grid"


def test_grid_of_another_size_is_not_flagged(tmp_path):
    # element length L/n next to a plotting grid of n*100 points (a false alarm in the corpus rescan)
    _write(tmp_path, "fem.py", '''
        import numpy as np
        L, n = 1.0, 10
        h = L / n
        x = np.linspace(0, L, n * 100)
        ''')
    assert not _by_stage(scan(tmp_path)[0], "grid")


def test_grid_mismatch_in_another_function_is_a_note(tmp_path):
    _write(tmp_path, "s.py", '''
        import numpy as np
        class Spectra:
            def bins(self):
                self.dv = self.vmax / self.nbins
            def velocities(self):
                return np.linspace(0, self.vmax, self.nbins)
        ''')
    (g,) = _by_stage(scan(tmp_path)[0], "grid")
    assert g.level == NOTE and "another function" in g.message


def test_constants_skip_ordinary_numbers_and_group_repeats(tmp_path):
    _write(tmp_path, "c.py", '''
        a = 3.3        # within 10% of pi, but an ordinary number
        b = 2.5        # within 10% of e
        y = 9.7 * 2    # near g, but not assigned to a gravity name
        p1 = 3.14
        p2 = 3.14
        G = 6.67e-11
        ''')
    (c,) = _by_stage(scan(tmp_path)[0], "constants")
    assert "pi" in c.message and "also lines 6" in c.message


def test_order_stated_by_a_property_wins_over_the_docstring(tmp_path):
    _write(tmp_path, "rk.py", '''
        class RK32:
            """Explicit Runge-Kutta of order 2."""
            A = [[0, 0, 0], [0.5, 0, 0], [0, 1, 0]]
            b = [0, 1, 0]
            c = [0, 0.5, 1]

            @property
            def order(self):
                return 3
        ''')
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN and "order 3 stated in the code" in t.message


def test_awkward_literals_do_not_stop_the_scan(tmp_path):
    _write(tmp_path, "odd.py", '''
        import numpy as np
        A = np.array([[0, 0], [1, 0]]) / 2.0
        big = 10 ** 400
        x = big / 3
        y = 123456789 ** 50 / 7
        ''')
    findings, unparsed = scan(tmp_path)
    assert unparsed == []


def test_tables_written_as_fraction_strings(tmp_path):
    _write(tmp_path, "rk.py", '''
        def midpoint():
            A = [["0", "0"], ["1/2", "0"]]
            b = ["0", "1"]
            c = ["0", "1/2"]
            return A, b, c
        ''')
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert "order 2" in t.message and t.level == NOTE


def test_slice_step_is_its_own_grid(tmp_path):
    _write(tmp_path, "p.py", '''
        import numpy as np
        def plot(xmin, xmax, n):
            x = np.linspace(xmin, xmax, n)
            g = np.mgrid[xmin:xmax:(xmax - xmin) / n]
            return x, g
        ''')
    assert not _by_stage(scan(tmp_path)[0], "grid")


_RK4_CODE = '''
    def rk4(f, t, y, h):
        k1 = f(t, y)
        k2 = f(t + h / 2, y + h / 2 * k1)
        k3 = f(t + h / 2, y + h / 2 * k2)
        k4 = f(t + h, y + h * k3)
        return y + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    '''


def test_stages_written_as_code_correct_rk4(tmp_path):
    _write(tmp_path, "rk.py", _RK4_CODE)
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == NOTE and "4 stages, order 4" in t.message


def test_stage_fed_with_the_wrong_earlier_stage(tmp_path):
    # Heun's third-order method with k1 where k2 belongs (a real defect found by the corpus rescan)
    _write(tmp_path, "rk.py", '''
        def heun3(model, t, x, h):
            k1 = model(t, x)
            k2 = model(t + 1/3 * h, x + 1/3 * h * k1)
            k3 = model(t + 2/3 * h, x + 2/3 * h * k1)
            return h * (1/4 * k1 + 3/4 * k3)
        ''')
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN and "order 2" in t.message and "suggests order 3" in t.message


def test_stage_time_and_docstring_table(tmp_path):
    _write(tmp_path, "rk.py", """
        import numpy as np
        def heun(fun, x, y0):
            '''
            Explicit Heun 2nd order
             0 | 0   0
             1 | 1   0
            ---------
               | 1/2 1/2
            '''
            h = x[1] - x[0]
            y = np.zeros((len(x), 1))
            for n in range(len(x) - 1):
                k1 = h * fun(x[n], y[n, :])
                k2 = h * fun(x[n], y[n, :] + k1)
                y[n + 1, :] = y[n, :] + k1 / 2.0 + k2 / 2.0
            return y
        """)
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN and "stage 2 is evaluated at t + 0 h" in t.message
    assert "matches the Butcher table in its docstring" in t.message


def test_stage_without_the_step_size(tmp_path):
    _write(tmp_path, "rk.py", '''
        def rk3(f, t, y, h):
            k1 = f(t, y)
            k2 = f(t + h / 2, y + h / 2 * k1)
            k3 = f(t + h, y - k1 + 2 * k2)
            return y + h * (k1 + 4 * k2 + k3) / 6
        ''')
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN and "without the step size h" in t.message


def test_function_that_is_not_a_stepper_is_ignored(tmp_path):
    _write(tmp_path, "m.py", '''
        def energy(pot, x, v, m):
            a = pot(x, 1) + pot(x, 2)
            return 0.5 * m * v**2 + a
        ''')
    assert not _by_stage(scan(tmp_path)[0], "tables")


def test_autonomous_and_split_systems_are_not_flagged(tmp_path):
    _write(tmp_path, "rk.py", '''
        def rk4(dt, state, p):
            k1 = derivatives(state, p)
            k2 = derivatives(state + 0.5 * dt * k1, p)
            k3 = derivatives(state + 0.5 * dt * k2, p)
            k4 = derivatives(state + dt * k3, p)
            return state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

        def rk4_second_order(f, x, y, z, h):
            k1 = h * z
            l1 = h * f(x, y, z)
            k2 = h * (z + 0.5 * l1)
            l2 = h * f(x + 0.5 * h, y + 0.5 * k1, z + 0.5 * l1)
            k3 = h * (z + 0.5 * l2)
            l3 = h * f(x + 0.5 * h, y + 0.5 * k2, z + 0.5 * l2)
            k4 = h * (z + l3)
            l4 = h * f(x + h, y + k3, z + l3)
            return y + (k1 + 2 * k2 + 2 * k3 + k4) / 6.0, z + (l1 + 2 * l2 + 2 * l3 + l4) / 6.0
        ''')
    assert not [f for f in _by_stage(scan(tmp_path)[0], "tables") if f.level == WARN]


def test_wrong_weights_against_the_docstring(tmp_path):
    _write(tmp_path, "rk.py", """
        def ode4(f, y, x, h):
            '''
            Runge-Kutta 4th order
             0   | 0   0   0   0
             1/2 | 1/2 0   0   0
             1/2 | 0   1/2 0   0
             1   | 0   0   1   0
            -----------------------
                 | 1/6 1/3 1/3 1/6
            '''
            k1 = h * f(x, y)
            k2 = h * f(x + h / 2, y + k1 / 2)
            k3 = h * f(x + h / 2, y + k2 / 2)
            k4 = h * f(x + h, y + k3)
            return y + k1 / 3 + k2 / 6 + k3 / 6 + k4 / 3
        """)
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN and "order 2" in t.message and "docstring" in t.message


def test_table_passed_to_a_constructor(tmp_path):
    # error weights that sum to 0.97 instead of 0 (the Tsit5 defect reported in the corpus study)
    _write(tmp_path, "tab.py", '''
        def Heun():
            """Heun's method."""
            return ButcherTableau(
                a=torch.tensor([[0.0, 0.0], [1.0, 0.0]]),
                b=torch.tensor([0.5, 0.5]),
                c=torch.tensor([0.0, 1.0]),
                b_error=torch.tensor([0.5 - 0.03, -0.5]),
                order=2,
            )
        ''')
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN and "in Heun" in t.message and "sum to -0.03" in t.message


def test_inherited_table_built_by_slices(tmp_path):
    _write(tmp_path, "rk.py", '''
        import numpy as np
        class SDIRK2:
            g = 1
            A = np.zeros((2, 2))
            A[0, :1] = [1 - 2 ** -0.5]
            A[1, :2] = [2 ** -0.5, 1 - 2 ** -0.5]
            b = A[-1]
            c = np.array([1 - 2 ** -0.5, 1.0])
            order = 2

        class Labelled(SDIRK2):
            order = 3
        ''')
    t = _by_stage(scan(tmp_path)[0], "tables")
    by_name = {("Labelled" in f.message): f for f in t}
    assert by_name[False].level == NOTE and "order 2" in by_name[False].message
    assert by_name[True].level == WARN and "order 3 stated in the code" in by_name[True].message


def test_stated_embedded_order(tmp_path):
    _write(tmp_path, "rk.py", '''
        class Heun21:
            A = [[0, 0], [1, 0]]
            b = [0.5, 0.5]
            b2 = [1, 0]
            order = 2
            orderEmbedded = 2
        ''')
    (t,) = _by_stage(scan(tmp_path)[0], "tables")
    assert t.level == WARN and "embedded weights b2 have order 1, but order 2 is stated" in t.message
