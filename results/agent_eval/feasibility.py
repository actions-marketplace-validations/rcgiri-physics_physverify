"""Feasibility check for the drawn claims (docs/plan_agent_eval.md, section 2). Runs no model.

    python -I feasibility.py POOL_CSV CORPUS_DIR [IMAGE]

CORPUS_DIR is the sandbox corpus folder ($PHYSVERIFY_CORPUS), holding repos/<id>
and deps/<id>. For each drawn claim: the clone is present and checked out at
the claim's commit, the cited file exists and is Python,
and the file's top-level imports load through `sandbox.py run` (no network,
the repository's installed deps). Nothing from the repository runs on the
host; inside the container only the cited file's import statements run (which
may execute the imported modules' top-level code), not the file itself. Writes feasibility.csv next to
POOL_CSV.
"""
import ast
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox" / "sandbox.py"

PROBE = r"""
import importlib, sys, os
R = os.environ.get('PHYSVERIFY_REPO', '/repo')
sys.path[:0] = [R] + [os.path.join(r, d) for r, ds, _ in os.walk(R) for d in ds if d in ('src', 'python', 'lib')]
sys.path.insert(0, os.path.dirname(os.path.join(R, sys.argv[1])))
bad = []
for m in sys.argv[2:]:
    try:
        importlib.import_module(m)
    except Exception as e:
        bad.append(f'{m} ({type(e).__name__})')
print('MISSING: ' + '; '.join(bad) if bad else 'OK')
"""


def top_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    mods = set()
    for node in tree.body:  # top level only: what must load before the code runs
        if isinstance(node, ast.Import):
            mods |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module)
    return sorted(mods)


def check(row, trees, image):
    tree = trees / "repos" / row["study_id"]
    if not tree.is_dir():
        return "fail", "clone not present"
    head = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-C", str(tree), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    if not head.startswith(row["commit"]):
        return "fail", f"clone at {head[:7]}, claim made at {row['commit']}"
    f = tree / row["file"]
    if not f.is_file():  # some reviews cite paths from a subfolder of the repository
        hits = [h for h in tree.rglob(Path(row["file"]).name)
                if ".git" not in h.parts and h.as_posix().endswith(row["file"])]
        if len(hits) != 1:
            return "fail", "cited file not in tree" if not hits else "cited path is ambiguous"
        f = hits[0]
    rel = f.relative_to(tree).as_posix()
    if f.suffix != ".py":
        return "fail", "cited file is not Python"
    try:
        mods = top_imports(f)
    except SyntaxError as e:
        return "fail", f"file does not parse: {e.msg}"
    return probe(row["study_id"], rel, mods, image)


def probe(repo_id, rel, mods, image):
    """Run PROBE through sandbox.py run, the same path the study's checks used (deps, copy, shims)."""
    work = Path(tempfile.mkdtemp(prefix="pv-feas-"))
    (work / "probe.py").write_text(PROBE, encoding="utf-8")
    env = dict(os.environ, PHYSVERIFY_IMAGE=image, MSYS_NO_PATHCONV="1")
    out = subprocess.run([sys.executable, "-I", str(SANDBOX), "run", repo_id, str(work / "probe.py"), rel, *mods],
                         capture_output=True, text=True, timeout=600, env=env)
    lines = [ln for ln in out.stdout.splitlines() if ln.startswith(("OK", "MISSING"))]
    last = lines[-1] if lines else "no output: " + (out.stderr.strip()[-200:] or out.stdout.strip()[-200:])
    if last == "OK":
        return "pass", f"{len(mods)} imports load"
    return "needs deps", last


def main(pool_csv, trees, image="physverify-sandbox:1"):
    pool_csv, trees = Path(pool_csv), Path(trees)
    rows = [r for r in csv.DictReader(open(pool_csv, encoding="utf-8")) if r["role"] in ("drawn", "reserve")]
    res = []
    for r in rows:
        # reserves are checked too, so a replacement is known in advance
        status, why = check(r, trees, image)
        res.append(dict(claim_id=r["claim_id"], study_id=r["study_id"], label=r["label"],
                        role=r["role"], status=status, detail=why))
        print(f"{r['role']:8} {r['label']:14} {r['study_id']:5} {r['claim_id']}  {status}: {why}")
    with open(pool_csv.with_name("feasibility.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res[0]))
        w.writeheader()
        w.writerows(res)


if __name__ == "__main__":
    main(*sys.argv[1:4])
