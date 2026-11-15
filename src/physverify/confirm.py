"""physverify confirm: run one suspected defect against a reference from the physics and record a verdict.

A claim file defines CLAIM (a literal dict: text, source, file, line, reference, impact), control() (a check
that must PASS, which shows the test can pass) and checks() (the correct behaviour). The verdict rules, the
ledger format and the safety rule are in docs/confirm.md (issue #54). This module finds no defects and writes
no references: both come from the person who writes the claim file.
"""

from __future__ import annotations

import ast
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

CONFIRMED, REJECTED, UNDECIDED = "confirmed", "rejected", "not decidable"
EXIT_CODES = {REJECTED: 0, CONFIRMED: 1, UNDECIDED: 2}
IMPACTS = ("used", "latent", "unknown")
REQUIRED = ("text", "source", "file", "line", "reference", "impact")
FILL_IN = "FILL IN"
DEFAULT_LEDGER = "confirm_ledger.jsonl"
DEFAULT_TIMEOUT = 300.0
LEDGER_VERSION = 1
_OK = ("PASS", "EXACT")

REFUSAL = ("physverify confirm runs the code under test. Give --trusted for code you trust, or run it inside the"
           " container described in sandbox/README.md (which sets PHYSVERIFY_REPO).")


class ClaimError(ValueError):
    """The claim file is incomplete or malformed; nothing was run."""


class Refused(RuntimeError):
    """confirm was asked to run code without --trusted and outside the sandbox."""


# --- reading the claim file (static: nothing is run) ---

def read_claim(path) -> dict:
    """CLAIM from the claim file, read with ast.literal_eval so a malformed claim is caught before any code runs."""
    path = Path(path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), str(path))
    except (OSError, ValueError) as exc:
        raise ClaimError(f"cannot read {path}: {exc}") from None
    except SyntaxError as exc:
        raise ClaimError(f"{path} is not valid Python: line {exc.lineno}: {exc.msg}") from None
    claim, functions = None, set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CLAIM" for t in node.targets):
            try:
                claim = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError, RecursionError):
                raise ClaimError(f"{path.name}: CLAIM must be a literal dict (strings and numbers only)") from None
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.add(node.name)
    if claim is None:
        raise ClaimError(f"{path.name} does not define CLAIM")
    if not isinstance(claim, dict):
        raise ClaimError(f"{path.name}: CLAIM is a {type(claim).__name__}, not a dict")
    missing = [k for k in REQUIRED if k not in claim]
    if missing:
        raise ClaimError(f"{path.name}: CLAIM is missing {', '.join(missing)}")
    for key in ("text", "source", "file", "reference", "impact"):
        if not isinstance(claim[key], str) or not claim[key].strip():
            raise ClaimError(f"{path.name}: CLAIM[{key!r}] must be a non-empty string")
        if claim[key].strip() == FILL_IN:
            raise ClaimError(f"{path.name}: CLAIM[{key!r}] is still {FILL_IN!r}")
    if isinstance(claim["line"], bool) or not isinstance(claim["line"], int) or claim["line"] < 1:
        raise ClaimError(f"{path.name}: CLAIM['line'] must be a line number (a positive integer)")
    if claim["impact"] not in IMPACTS:
        raise ClaimError(f"{path.name}: CLAIM['impact'] is {claim['impact']!r}; it must be one of {', '.join(IMPACTS)}")
    if "repo" in claim and not isinstance(claim["repo"], str):
        raise ClaimError(f"{path.name}: CLAIM['repo'] must be a path (a string)")
    for name in ("control", "checks"):
        if name not in functions:
            raise ClaimError(f"{path.name} does not define {name}()")
    return claim


# --- inside the child process ---

def _outcome(o) -> dict:
    return {"label": o.check.label, "family": o.check.family, "status": o.result.status,
            "message": o.result.message, "seconds": round(o.seconds, 4)}


def evaluate_claim(path) -> dict:
    """Load the claim file and run control() and checks(). Runs in the child process (physverify.isolate)."""
    from .checks import Check
    from .loaders import load_module_from_path
    from .report import run_checks

    path = Path(path).resolve()
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    try:
        module = load_module_from_path("physverify_claim", path)
        control = module.control()
        checks = list(module.checks())
    except Exception as exc:
        return {"load_error": f"{type(exc).__name__}: {exc}"}
    if not isinstance(control, Check):
        return {"load_error": f"control() returned {type(control).__name__}, not physverify.Check"}
    if not checks:
        return {"load_error": "checks() returned no checks"}
    for c in checks:
        if not isinstance(c, Check):
            return {"load_error": f"checks() returned {type(c).__name__}, not physverify.Check"}
    return {"control": _outcome(run_checks([control])[0]), "checks": [_outcome(o) for o in run_checks(checks)]}


# --- the verdict ---

def _names(items) -> str:
    return "; ".join(f"'{c['label']}' ({c['status']})" for c in items)


def _of(k: int, n: int) -> str:
    return f"{k} of {n} check" + ("s" if n != 1 else "")


def decide(control: dict, checks: list) -> tuple[str, str]:
    """Verdict and reason from the control and the checks (rules 3 to 6 of docs/confirm.md)."""
    if control["status"] not in _OK:
        return UNDECIDED, (f"the control '{control['label']}' is {control['status']}, not PASS, so the test itself"
                           " is not trusted")
    failed = [c for c in checks if c["status"] == "FAIL"]
    if failed:
        return CONFIRMED, f"the control passed and {_of(len(failed), len(checks))} failed: {_names(failed)}"
    open_ = [c for c in checks if c["status"] not in _OK]
    if open_:
        reason = f"the control passed and no check failed, but {_of(len(open_), len(checks))} did not pass: {_names(open_)}"
        if any(c["status"] == "ERROR" for c in open_):
            reason += ("; an ERROR is the code or the claim file raising an exception, which is not taken as"
                       " confirmation (write a check for the crash if the crash is the defect)")
        return UNDECIDED, reason
    if len(checks) == 1:
        return REJECTED, "the control passed and the check passed"
    return REJECTED, f"the control passed and all {len(checks)} checks passed"


# --- provenance ---

def _sha256(path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _git(folder, *args) -> str | None:
    """git output (stripped), or None when git is missing or the folder is not a checkout."""
    try:
        out = subprocess.run(["git", "-C", str(folder), *args], capture_output=True, text=True, timeout=20,
                             stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def _provenance(claim_path: Path, claim: dict) -> dict:
    """Hash of the file the claim is about, and the commit of the checkout that holds it."""
    base = claim_path.resolve().parent
    if claim.get("repo"):
        base = (base / claim["repo"]).resolve()
    elif os.environ.get("PHYSVERIFY_REPO"):
        base = Path(os.environ["PHYSVERIFY_REPO"])
    top = _git(base, "rev-parse", "--show-toplevel")
    root = Path(top) if top else base
    commit = os.environ.get("PHYSVERIFY_REPO_COMMIT") or None
    if commit is None and top:
        head = _git(root, "rev-parse", "HEAD")
        if head:
            dirty = _git(root, "status", "--porcelain", "--untracked-files=no")
            commit = head + ("-dirty" if dirty else "")
    # `file` is relative to the repository root; a claim kept next to the file in a sub-folder also works
    file_sha = _sha256(root / claim["file"]) or _sha256(base / claim["file"])
    return {"file_sha256": file_sha, "repo_commit": commit}


# --- the command ---

def is_trusted(trusted: bool, environ=None) -> bool:
    """confirm runs code only when the user says it is trusted or it runs inside the sandbox."""
    environ = os.environ if environ is None else environ
    return bool(trusted or environ.get("PHYSVERIFY_REPO"))


def append_ledger(record: dict, ledger) -> None:
    """Append one JSON line; an existing line is never rewritten."""
    ledger = Path(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def confirm_claim(path, *, trusted: bool = False, ledger=DEFAULT_LEDGER, timeout: float = DEFAULT_TIMEOUT,
                  allow_dependent_reference: str | None = None) -> dict:
    """Judge one claim file, append the result to the ledger and return it (the ledger line as a dict).

    Raises Refused, before anything is read or written, unless `trusted` or the sandbox (PHYSVERIFY_REPO).
    """
    from . import __version__
    from .isolate import run_isolated
    from .specscan import reference_notes

    if not is_trusted(trusted):
        raise Refused(REFUSAL)
    path = Path(path)
    record = {"ledger_version": LEDGER_VERSION,
              "date": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "physverify": __version__, "claim_file": str(path), "claim_sha256": _sha256(path)}
    record.update({k: None for k in REQUIRED})
    record.update({"file_sha256": None, "repo_commit": None, "verdict": UNDECIDED, "reason": "", "control": None,
                   "checks": [], "allow_dependent_reference": None, "timeout_s": timeout})

    def finish(verdict, reason, **extra):
        record.update(verdict=verdict, reason=reason, **extra)
        if ledger is not None:
            append_ledger(record, ledger)
        return record

    try:
        claim = read_claim(path)
    except ClaimError as exc:
        return finish(UNDECIDED, f"the claim file could not be loaded: {exc}")
    record.update({k: claim[k] for k in REQUIRED})
    if "repo" in claim:
        record["repo"] = claim["repo"]
    record.update(_provenance(path, claim))

    notes = reference_notes(path)
    if notes and not allow_dependent_reference:
        return finish(UNDECIDED, "the reference is not independent of the code under test: " + " | ".join(notes)
                      + " (give --allow-dependent-reference with a reason if this use is safe)")
    if notes:
        record["allow_dependent_reference"] = {"reason": allow_dependent_reference, "notes": notes}

    run = run_isolated("claim", [path.resolve()], timeout, cwd=path.resolve().parent)
    if run["status"] == "timeout":
        return finish(UNDECIDED, f"timed out after {timeout:g} s; the run was stopped and its checks are not reported",
                      stderr_tail=run["stderr_tail"])
    if run["status"] == "error":
        return finish(UNDECIDED, f"the run ended without a result: {run['error']}", stderr_tail=run["stderr_tail"])
    result = run["result"]
    if "load_error" in result:
        return finish(UNDECIDED, f"the claim file could not be loaded: {result['load_error']}",
                      stderr_tail=run["stderr_tail"])
    record["control"], record["checks"] = result["control"], result["checks"]
    return finish(*decide(result["control"], result["checks"]))


def format_verdict(record: dict) -> str:
    """The verdict in words: one line, one line per check, then the claim and its reference."""
    head = record["verdict"]
    if record.get("impact"):
        head += f" (impact: {record['impact']})"
    lines = [f"{head}: {record['reason']}"]
    for kind, c in [("control", record.get("control"))] + [("check", c) for c in record.get("checks") or []]:
        if c:
            lines.append(f"  {kind:8s} {c['status']:12s} {c['label']}: {c['message']}")
    if record.get("allow_dependent_reference"):
        lines.append(f"dependent reference allowed: {record['allow_dependent_reference']['reason']}")
    if record.get("text"):
        lines.append(f"claim: {record['text']} ({record['file']}:{record['line']}, from {record['source']})")
        lines.append(f"reference: {record['reference']}")
    return "\n".join(lines)


TEMPLATE = '''"""Claim file for `physverify confirm` (see docs/confirm.md).

The reference must come from the physics: a book, a paper or the project's README. Never compute it with the
code under test, or a bug in the code is copied into the reference and the check passes. Fill in every
"FILL IN" below; the claim is not run until they are filled in.
"""
import numpy as np  # noqa: F401

from physverify import Check, Result  # noqa: F401

CLAIM = {
    "text": %(text)r,
    "source": "FILL IN",  # who made the claim: a person, physverify scan, or a model and its name
    "file": %(file)r,
    "line": %(line)d,
    "reference": "FILL IN",  # book and section, paper and equation number, or README section
    "impact": "FILL IN",  # used, latent or unknown: do the repository's own scripts or defaults reach this code?
}


def control():
    """One check that must PASS: for example the same test on a case where the claimed effect is absent."""
    raise NotImplementedError("write the control check")


def checks():
    """The correct behaviour, on a case where the claimed effect is present; a FAIL confirms the claim."""
    raise NotImplementedError("write the checks")
'''


def write_template(path, text: str, file: str, line: int) -> Path:
    """Write a claim-file template; refuses to overwrite an existing file."""
    path = Path(path)
    if path.suffix != ".py":
        raise ValueError(f"{path}: a claim file must end in .py")
    if path.exists():
        raise FileExistsError(f"{path} exists; not overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE % {"text": text, "file": file, "line": line}, encoding="utf-8")
    return path
