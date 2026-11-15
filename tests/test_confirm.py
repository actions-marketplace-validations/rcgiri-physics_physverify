"""physverify confirm: one case per verdict rule in docs/confirm.md, the ledger, isolation and the safety rule."""

import json

import pytest

from physverify import cli
from physverify.confirm import (
    CONFIRMED,
    REJECTED,
    UNDECIDED,
    Refused,
    confirm_claim,
    decide,
    format_verdict,
    read_claim,
    write_template,
)

BASE_CLAIM = {
    "text": "value() returns the wrong number",
    "source": "test",
    "file": "solver.py",
    "line": 1,
    "reference": "the README says value() is 1",
    "impact": "used",
}


def write_claim(folder, control="PASS", checks=("FAIL",), claim=None, extra=""):
    """A claim file whose control and checks return the given statuses; 'ERROR' raises, 'SOLVER' asks solver.py."""
    (folder / "solver.py").exists() or (folder / "solver.py").write_text("def value():\n    return 1\n")

    def make(status):
        if status == "ERROR":
            return "lambda: 1 / 0"
        if status == "SOLVER":
            return "lambda: Result(PASS if solver.value() == 1 else FAIL, f'value() is {solver.value()}, the README says 1')"
        if status == "HANG":
            return "lambda: (time.sleep(60), Result(PASS))[1]"
        return f"lambda: Result({status!r}, 'returned {status}')"

    body = "\n".join([
        "import time",
        "import solver",
        "from physverify import Check, Result",
        "from physverify.checks import PASS, FAIL",
        f"CLAIM = {claim or BASE_CLAIM!r}",
        extra,
        "def control():",
        f"    return Check('limit', 'control case', {make(control)})",
        "def checks():",
        "    return [" + ", ".join(f"Check('limit', 'check {i}', {make(s)})" for i, s in enumerate(checks)) + "]",
        "",
    ])
    path = folder / "claim.py"
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def outside_sandbox(monkeypatch):
    monkeypatch.delenv("PHYSVERIFY_REPO", raising=False)
    monkeypatch.delenv("PHYSVERIFY_REPO_COMMIT", raising=False)


def judge(path, tmp_path, **kw):
    kw.setdefault("trusted", True)
    kw.setdefault("ledger", tmp_path / "ledger.jsonl")
    kw.setdefault("timeout", 60)
    return confirm_claim(path, **kw)


# --- one case per verdict rule ---

def test_control_that_does_not_pass_gives_not_decidable(tmp_path):
    r = judge(write_claim(tmp_path, control="FAIL", checks=("FAIL",)), tmp_path)
    assert r["verdict"] == UNDECIDED and "control" in r["reason"] and "not trusted" in r["reason"]


def test_control_passes_and_a_check_fails_gives_confirmed(tmp_path):
    r = judge(write_claim(tmp_path, checks=("PASS", "FAIL")), tmp_path)
    assert r["verdict"] == CONFIRMED and "1 of 2 checks failed" in r["reason"] and "'check 1'" in r["reason"]


def test_control_passes_and_every_check_passes_gives_rejected(tmp_path):
    r = judge(write_claim(tmp_path, control="EXACT", checks=("PASS", "EXACT")), tmp_path)
    assert r["verdict"] == REJECTED and [c["status"] for c in r["checks"]] == ["PASS", "EXACT"]


@pytest.mark.parametrize("status", ["INCONCLUSIVE", "ERROR", "SKIP"])
def test_an_open_check_with_none_failing_gives_not_decidable_with_the_reason(tmp_path, status):
    r = judge(write_claim(tmp_path, checks=("PASS", status)), tmp_path)
    assert r["verdict"] == UNDECIDED and f"'check 1' ({status})" in r["reason"]
    if status == "ERROR":
        assert "ZeroDivisionError" in r["checks"][1]["message"] and "not taken as confirmation" in r["reason"]


def test_a_fail_wins_over_an_inconclusive_check(tmp_path):
    assert judge(write_claim(tmp_path, checks=("INCONCLUSIVE", "FAIL")), tmp_path)["verdict"] == CONFIRMED


def test_a_hanging_claim_times_out_as_not_decidable(tmp_path):
    r = judge(write_claim(tmp_path, checks=("HANG",)), tmp_path, timeout=3)
    assert r["verdict"] == UNDECIDED and r["reason"].startswith("timed out after 3 s") and r["checks"] == []


def test_a_dependent_reference_is_not_decidable_and_runs_nothing(tmp_path):
    extra = "def exact():\n    return solver.value()\n"
    path = write_claim(tmp_path, checks=("HANG",), extra=extra)  # would time out if it ran
    r = judge(path, tmp_path, timeout=3)
    assert r["verdict"] == UNDECIDED and "not independent" in r["reason"] and r["control"] is None


def test_allow_dependent_reference_runs_and_records_the_reason(tmp_path):
    extra = "def exact():\n    return solver.value()\n"
    r = judge(write_claim(tmp_path, checks=("FAIL",), extra=extra), tmp_path,
              allow_dependent_reference="value() only reads a constant table")
    assert r["verdict"] == CONFIRMED
    assert r["allow_dependent_reference"]["reason"] == "value() only reads a constant table"
    assert "exact()" in r["allow_dependent_reference"]["notes"][0]


@pytest.mark.parametrize("impact", ["used", "latent", "unknown"])
def test_impact_is_reported_and_never_changes_the_verdict(tmp_path, impact):
    r = judge(write_claim(tmp_path, checks=("FAIL",), claim={**BASE_CLAIM, "impact": impact}), tmp_path)
    assert r["verdict"] == CONFIRMED and r["impact"] == impact


def test_decide_counts_exact_as_a_passing_control():
    ok = {"label": "c", "status": "EXACT"}
    assert decide(ok, [{"label": "x", "status": "PASS"}])[0] == REJECTED


# --- load errors ---

@pytest.mark.parametrize("claim, words", [
    ({k: v for k, v in BASE_CLAIM.items() if k != "reference"}, "missing reference"),
    ({**BASE_CLAIM, "impact": "minor"}, "must be one of used, latent, unknown"),
    ({**BASE_CLAIM, "source": "FILL IN"}, "still 'FILL IN'"),
    ({**BASE_CLAIM, "line": "10"}, "positive integer"),
])
def test_an_incomplete_claim_is_a_load_error_and_is_still_recorded(tmp_path, claim, words):
    r = judge(write_claim(tmp_path, checks=("HANG",), claim=claim), tmp_path, timeout=3)
    assert r["verdict"] == UNDECIDED and words in r["reason"] and r["control"] is None
    assert len((tmp_path / "ledger.jsonl").read_text().splitlines()) == 1


def test_control_returning_something_else_is_a_load_error(tmp_path):
    path = write_claim(tmp_path)
    path.write_text(path.read_text().replace("return Check('limit', 'control case'", "return ('limit', 'control case'"))
    r = judge(path, tmp_path)
    assert r["verdict"] == UNDECIDED and "control() returned tuple" in r["reason"]


# --- ledger, isolation, safety ---

def test_the_ledger_appends_and_never_rewrites(tmp_path):
    path = write_claim(tmp_path, checks=("FAIL",))
    ledger = tmp_path / "ledger.jsonl"
    judge(path, tmp_path)
    first = ledger.read_bytes()
    judge(path, tmp_path)
    data = ledger.read_bytes()
    assert data.startswith(first) and len(data.splitlines()) == 2
    a, b = (json.loads(line) for line in data.splitlines())
    assert a["claim_sha256"] == b["claim_sha256"] and a["verdict"] == b["verdict"] == CONFIRMED
    for key in ("text", "source", "reason", "impact", "physverify", "date", "repo_commit", "file_sha256", "checks"):
        assert key in a
    assert a["checks"][0]["message"] == "returned FAIL"


def test_a_second_run_after_editing_the_solver_sees_the_edit(tmp_path):
    path = write_claim(tmp_path, checks=("SOLVER",))
    assert judge(path, tmp_path)["verdict"] == REJECTED
    (tmp_path / "solver.py").write_text("def value():\n    return 2\n")  # same size, same second
    r = judge(path, tmp_path)
    assert r["verdict"] == CONFIRMED and "value() is 2" in r["checks"][0]["message"]


def test_refuses_without_trusted_and_writes_nothing(tmp_path):
    path = write_claim(tmp_path, checks=("FAIL",))
    with pytest.raises(Refused, match="sandbox/README.md"):
        judge(path, tmp_path, trusted=False)
    assert not (tmp_path / "ledger.jsonl").exists()
    assert cli.main(["confirm", str(path), "--ledger", str(tmp_path / "ledger.jsonl")]) == 2
    assert not (tmp_path / "ledger.jsonl").exists()


def test_runs_inside_the_sandbox_without_trusted(tmp_path, monkeypatch):
    monkeypatch.setenv("PHYSVERIFY_REPO", str(tmp_path))
    monkeypatch.setenv("PHYSVERIFY_REPO_COMMIT", "abc123")
    r = judge(write_claim(tmp_path, checks=("FAIL",)), tmp_path, trusted=False)
    assert r["verdict"] == CONFIRMED and r["repo_commit"] == "abc123" and r["file_sha256"]


# --- command line ---

@pytest.mark.parametrize("checks, code", [(("PASS",), 0), (("FAIL",), 1), (("INCONCLUSIVE",), 2)])
def test_exit_codes(tmp_path, checks, code, capsys):
    path = write_claim(tmp_path, checks=checks)
    assert cli.main(["confirm", str(path), "--trusted", "--ledger", str(tmp_path / "l.jsonl")]) == code
    out = capsys.readouterr().out
    assert out.startswith({0: REJECTED, 1: CONFIRMED, 2: UNDECIDED}[code]) and "control" in out


def test_json_to_stdout_is_the_ledger_line(tmp_path, capsys):
    path = write_claim(tmp_path, checks=("FAIL",))
    ledger = tmp_path / "l.jsonl"
    assert cli.main(["confirm", str(path), "--trusted", "--ledger", str(ledger), "--json", "-"]) == 1
    assert json.loads(capsys.readouterr().out) == json.loads(ledger.read_text())


def test_an_installed_library_in_the_reference_is_not_code_under_test(tmp_path):
    # study re-test J163: the repository wraps healpy and the reference is healpy's own routine
    lib = tmp_path.parent / f"{tmp_path.name}_site"
    lib.mkdir()
    (lib / "skylib.py").write_text("def corners():\n    return 4\n")
    extra = (f"import sys\nsys.path.insert(0, {str(lib)!r})\nimport skylib\n"
             "def exact():\n    return skylib.corners()\n")
    r = judge(write_claim(tmp_path, checks=("FAIL",), extra=extra), tmp_path)
    assert r["verdict"] == CONFIRMED and r["allow_dependent_reference"] is None
    assert r["reference_libraries"] == ["skylib"]
    assert "installed libraries" in format_verdict(r)


def test_a_module_of_the_repository_in_the_reference_is_still_noted(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("def value():\n    return 1\n")
    extra = "import pkg\ndef reference():\n    return pkg.value()\n"
    r = judge(write_claim(tmp_path, checks=("HANG",), extra=extra), tmp_path, timeout=3)
    assert r["verdict"] == UNDECIDED and "not independent" in r["reason"] and "pkg" in r["reason"]


def test_a_windows_path_in_the_claim_text_gives_a_load_error_in_words(tmp_path):
    path = write_claim(tmp_path)
    # the claim file then holds 'see C:\Users\me\solver.py' with single backslashes: \U starts an escape
    path.write_text(path.read_text(encoding="utf-8").replace(
        "value() returns the wrong number", r"see C:\Users\me\solver.py"), encoding="utf-8")
    r = judge(path, tmp_path)
    assert r["verdict"] == UNDECIDED and "Windows path" in r["reason"] and "confirm init --text" in r["reason"]


def test_a_failing_check_that_reports_an_exception_says_so():
    ok = {"label": "c", "status": "PASS", "message": ""}
    crash = {"label": "k", "status": "FAIL", "message": "the call raised TypeError: shape 6x6"}
    wrong = {"label": "w", "status": "FAIL", "message": "got 3, expected 2"}
    assert "the code raised an exception" in decide(ok, [crash])[1]
    assert "exception" not in decide(ok, [wrong])[1]


def test_init_writes_a_template_that_will_not_run_until_filled_in(tmp_path, capsys):
    path = tmp_path / "claim_x.py"
    assert cli.main(["confirm", "init", str(path), "--text", "k3 uses k1", "--file", "rk.py", "--line", "7"]) == 0
    text = path.read_text()
    assert "Never compute it with the" in text and "must come from the physics" in text and "def control()" in text and "def checks()" in text
    with pytest.raises(ValueError, match="FILL IN"):
        read_claim(path)
    assert cli.main(["confirm", "init", str(path), "--text", "t", "--file", "f", "--line", "1"]) == 2  # no overwrite
    with pytest.raises(ValueError):
        write_template(tmp_path / "claim.txt", "t", "f", 1)


# --- review fixes ---

def test_output_after_the_result_at_exit_does_not_change_the_verdict(tmp_path):
    extra = "import atexit, os\natexit.register(lambda: os.write(1, b'{\"late\": 1} printed at exit\\n'))\n"
    r = judge(write_claim(tmp_path, checks=("FAIL",), extra=extra), tmp_path)
    assert r["verdict"] == CONFIRMED


def test_a_timeout_also_stops_the_processes_the_code_started(tmp_path):
    import time

    beat = tmp_path / "grandchild_heartbeat"  # rewritten every 0.2 s while the grandchild lives (30 s at most)
    code = (f"import time, pathlib\nfor i in range(150):\n    pathlib.Path({str(beat)!r}).write_text(str(i))\n"
            "    time.sleep(0.2)\n")
    extra = f"import subprocess, sys\nGRAND = subprocess.Popen([sys.executable, '-c', {code!r}])\n"
    start = time.monotonic()
    r = judge(write_claim(tmp_path, checks=("HANG",), extra=extra), tmp_path, timeout=8)
    assert time.monotonic() - start < 20  # not held up by a grandchild that keeps the output pipes open
    assert r["verdict"] == UNDECIDED and r["reason"].startswith("timed out")
    assert beat.exists()  # the grandchild did start before the time limit
    first = beat.read_text()
    time.sleep(1.5)
    assert beat.read_text() == first  # and it is no longer running


def test_an_annotated_claim_and_imported_functions_are_accepted(tmp_path):
    (tmp_path / "solver.py").write_text("def value():\n    return 1\n")
    (tmp_path / "helpers.py").write_text(
        "from physverify import Check, Result\n"
        "def control():\n    return Check('limit', 'control case', lambda: Result('PASS'))\n"
        "def checks():\n    return [Check('limit', 'check 0', lambda: Result('FAIL', 'wrong'))]\n")
    path = tmp_path / "claim.py"
    path.write_text(f"CLAIM: dict = {BASE_CLAIM!r}\nfrom helpers import control, checks\n")
    assert judge(path, tmp_path)["verdict"] == CONFIRMED


@pytest.mark.parametrize("timeout", [0, -1, "abc", float("inf")])
def test_a_bad_timeout_is_refused(tmp_path, timeout):
    with pytest.raises(ValueError, match="timeout"):
        judge(write_claim(tmp_path), tmp_path, timeout=timeout)
    assert not (tmp_path / "ledger.jsonl").exists()


@pytest.mark.parametrize("value", ["0", "-5", "abc"])
def test_the_command_refuses_a_bad_timeout(tmp_path, value):
    with pytest.raises(SystemExit) as exc:
        cli.main(["confirm", str(write_claim(tmp_path)), "--trusted", "--timeout", value])
    assert exc.value.code == 2


def test_init_refuses_a_line_below_one(tmp_path):
    path = tmp_path / "claim_x.py"
    assert cli.main(["confirm", "init", str(path), "--text", "t", "--file", "f.py", "--line", "0"]) == 2
    assert not path.exists()


def test_an_interrupt_while_waiting_stops_the_child_and_its_processes(tmp_path, monkeypatch):
    import subprocess
    import time

    from physverify.isolate import run_isolated

    beat = tmp_path / "grandchild_heartbeat"
    code = (f"import time, pathlib\nfor i in range(150):\n    pathlib.Path({str(beat)!r}).write_text(str(i))\n"
            "    time.sleep(0.2)\n")
    extra = f"import subprocess, sys\nGRAND = subprocess.Popen([sys.executable, '-c', {code!r}])\n"
    path = write_claim(tmp_path, checks=("HANG",), extra=extra)
    started = []
    real = subprocess.Popen.communicate

    def interrupted(self, *args, **kwargs):  # Ctrl-C arriving while the parent waits
        if started:
            return real(self, *args, **kwargs)
        started.append(self)
        deadline = time.monotonic() + 30
        while not beat.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        raise KeyboardInterrupt

    monkeypatch.setattr(subprocess.Popen, "communicate", interrupted)
    with pytest.raises(KeyboardInterrupt):
        run_isolated("claim", [path.resolve()], 60, cwd=tmp_path)
    assert beat.exists()
    started[0].wait(timeout=10)  # the child is gone
    first = beat.read_text()
    time.sleep(1.5)
    assert beat.read_text() == first  # and so is the process it started


@pytest.mark.parametrize("value", [0, True, False])
def test_zero_and_booleans_are_not_timeouts(value):
    from physverify.confirm import parse_timeout

    with pytest.raises(ValueError, match="timeout"):
        parse_timeout(value)
