"""Agent-evaluation harness (docs/plan_agent_eval.md, section 3). Standard library only.

    python -I session.py new CLAIMS_CSV CLAIM_ID ARM SESSIONS_DIR   # make a session folder, print its path
    python -I session.py run SESSION_DIR SCRIPT [ARGS...]            # one sandbox run (counts toward the limit)
    python -I session.py confirm SESSION_DIR CLAIM_FILE              # arm C: physverify confirm (one run)
    python -I session.py prompt SESSION_DIR                          # print the session's prompt
    python -I session.py done SESSION_DIR                            # stop the clock, read the verdict

Every run goes through sandbox.py with the image `physverify-sandbox:eval-noverify`
(physverify removed). Arm C gets physverify only as a copy of src/physverify at
FROZEN in its work folder. At most RUN_LIMIT runs and TIME_LIMIT seconds per
session; past either, the session is scored as not decidable (timeout).
"""
import contextlib
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

FROZEN = "5f314dc"
IMAGE = "physverify-sandbox:eval-noverify"
RUN_LIMIT = 6
TIME_LIMIT = 20 * 60
ROOT = Path(__file__).resolve().parents[3]
SANDBOX = ROOT / "sandbox" / "sandbox.py"
CORPUS = Path(os.environ.get("PHYSVERIFY_CORPUS", "G:/physverify-corpus"))
MEMORY = "2g"  # the same for both arms, whatever the agent's shell sets
LOCK = CORPUS / "agent_eval.lock"
VERDICT = re.compile(r"^VERDICT:\s*(confirmed|rejected|not decidable)\s*$", re.M)


def load(sdir):
    return json.loads((Path(sdir) / "session.json").read_text(encoding="utf-8"))


def save(sdir, s):
    (Path(sdir) / "session.json").write_text(json.dumps(s, indent=1), encoding="utf-8")


@contextlib.contextmanager
def queue():
    """One sandbox run at a time: the Docker VM has room for one 2 GB run, and runs on one repository share /out."""
    t0 = time.time()
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            time.sleep(2)
    try:
        yield time.time() - t0
    finally:
        os.close(fd)
        os.unlink(LOCK)


def elapsed(s):
    """Session seconds, not counting time spent waiting in the run queue."""
    return time.time() - s["start"] - sum(r.get("wait", 0) for r in s["runs"])


def new(claims_csv, claim_id, arm, sessions):
    row = next(r for r in csv.DictReader(open(claims_csv, encoding="utf-8")) if r["claim_id"] == claim_id)
    sdir = (Path(sessions) / f"{arm}_{claim_id}").resolve()
    work = sdir / "work"
    work.mkdir(parents=True, exist_ok=False)
    (work / "claim.md").write_text(
        f"# Claim\n\nRepository folder (read only): {CORPUS / 'repos' / row['repo_id']}\n"
        f"Cited file: {row['file']}\nCited line: {row['line']}\nSource: {row['model']}\n\n"
        f"## Claim text, unedited\n\n{row['claim_text']}\n", encoding="utf-8")
    if arm == "C":
        tar = sdir / "pv.tar"
        subprocess.run(["git", "-C", str(ROOT), "archive", "-o", str(tar), FROZEN, "src/physverify", "docs/confirm.md"],
                       check=True)
        with tarfile.open(tar) as t:
            t.extractall(sdir / "frozen", filter="data")
        tar.unlink()
        shutil.move(str(sdir / "frozen" / "src" / "physverify"), str(work / "physverify"))
        shutil.move(str(sdir / "frozen" / "docs" / "confirm.md"), str(work / "confirm.md"))
        shutil.rmtree(sdir / "frozen")
        shutil.copy(Path(__file__).with_name("confirm_entry.py"), work / "_confirm_entry.py")
    # sandbox.py keeps deps for a non-default image in deps-<tag>/; point that at the study's deps/<id>
    deps, link = CORPUS / "deps" / row["repo_id"], CORPUS / f"deps-{IMAGE.rsplit(':', 1)[-1]}" / row["repo_id"]
    if deps.is_dir() and any(deps.iterdir()) and not link.exists():
        link.parent.mkdir(exist_ok=True)
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(deps)], check=True, capture_output=True)
    save(sdir, dict(claim_id=claim_id, repo_id=row["repo_id"], arm=arm, start=time.time(), runs=[]))
    print(sdir.resolve())


def _run(sdir, script, args, wait=None):
    if wait is None:
        with queue() as w:
            return _run(sdir, script, args, w)
    sdir = Path(sdir)
    s = load(sdir)
    if len(s["runs"]) >= RUN_LIMIT or elapsed(s) - wait > TIME_LIMIT:
        s["timeout"] = True
        save(sdir, s)
        sys.exit("LIMIT REACHED: no more runs. Give your verdict now.")
    script = (sdir / "work" / script).resolve()
    if script.parent != (sdir / "work").resolve() or not script.is_file():
        sys.exit("the script must be a file directly inside the session's work folder")
    env = {k: v for k, v in os.environ.items() if not k.startswith("PHYSVERIFY_")}  # no limits set by the agent
    env.update(PHYSVERIFY_IMAGE=IMAGE, PHYSVERIFY_CORPUS=str(CORPUS), PHYSVERIFY_MEMORY=MEMORY,
               MSYS_NO_PATHCONV="1", PYTHONIOENCODING="utf-8")
    t0 = time.time()
    out = subprocess.run([sys.executable, "-I", str(SANDBOX), "run", s["repo_id"], str(script), *args],
                         capture_output=True, text=True, env=env, encoding="utf-8", errors="replace")
    n = len(s["runs"]) + 1
    (sdir / f"run{n}.log").write_text(out.stdout + "\n--- stderr ---\n" + out.stderr, encoding="utf-8")
    s["runs"].append(dict(script=script.name, args=args, rc=out.returncode, seconds=round(time.time() - t0, 1),
                          wait=round(wait, 1)))
    save(sdir, s)
    print(out.stdout[-6000:])
    print(out.stderr[-3000:], file=sys.stderr)
    print(f"[run {n} of {RUN_LIMIT}, exit code {out.returncode}]")
    return s


def confirm(sdir, claim_file):
    s = load(sdir)
    if s["arm"] != "C":
        sys.exit("confirm is arm C only")
    ledger = CORPUS / "out" / s["repo_id"] / "confirm_ledger.jsonl"
    with queue() as w:
        before = ledger.read_text(encoding="utf-8").splitlines() if ledger.exists() else []
        _run(sdir, "_confirm_entry.py", [claim_file], w)
        after = ledger.read_text(encoding="utf-8").splitlines() if ledger.exists() else []
    new_lines = after[len(before):]
    with open(Path(sdir) / "ledger.jsonl", "a", encoding="utf-8") as f:
        f.writelines(ln + "\n" for ln in new_lines)


def prompt(sdir):
    """Print the session's prompt: prompt.md with the arm's paragraph from arm_paragraphs.md."""
    sdir = Path(sdir).resolve()
    s = load(sdir)
    s["start"] = time.time()  # the clock starts when the agent gets its prompt
    save(sdir, s)
    here = Path(__file__).resolve().parent
    paras = (here / "arm_paragraphs.md").read_text(encoding="utf-8").split("## ")
    para = next(p for p in paras if p.startswith(s["arm"] + "\n"))[2:].strip()
    text = (here / "prompt.md").read_text(encoding="utf-8").replace("{ARM_PARAGRAPH}", para)
    for k, v in dict(WORK=sdir / "work", SESSION=sdir, PY=Path(sys.executable), HARNESS=here).items():
        text = text.replace("{" + k + "}", v.as_posix())
    print(text)


def done(sdir):
    sdir = Path(sdir)
    s = load(sdir)
    s["seconds"] = round(elapsed(s), 1)
    if s["arm"] == "C":
        lines = (sdir / "ledger.jsonl").read_text(encoding="utf-8").splitlines() if (sdir / "ledger.jsonl").exists() else []
        s["verdict"] = json.loads(lines[-1])["verdict"] if lines else "not decidable"
        s["verdict_note"] = "last ledger line" if lines else "no ledger line"
    else:
        ans = (sdir / "work" / "answer.md")
        m = VERDICT.findall(ans.read_text(encoding="utf-8")) if ans.exists() else []
        s["verdict"] = m[-1] if m else "not decidable"
        s["verdict_note"] = "VERDICT line" if m else "missing or malformed VERDICT line"
    if s.get("timeout"):
        s["verdict"], s["verdict_note"] = "not decidable", "timeout"
    save(sdir, s)
    print(s["verdict"], "|", s["verdict_note"], "|", s["seconds"], "s |", len(s["runs"]), "runs")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:]
    {"new": new, "run": lambda d, sc, *a: _run(d, sc, list(a)), "confirm": confirm, "prompt": prompt, "done": done}[cmd](*rest)
