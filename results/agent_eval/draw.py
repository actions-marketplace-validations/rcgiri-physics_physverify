"""Draw the claims for the agent evaluation (docs/plan_agent_eval.md, section 2).

Reads the private study files and runs no model:

    python -I draw.py STUDY_DIR OUT_DIR

STUDY_DIR holds claims.csv, sample*_results.csv, retest080/confirm_results*.csv
and release_repo_key_PRIVATE.csv. Writes OUT_DIR/pool.csv (every claim left
after the exclusion rules, in seeded order, with the reason when excluded) and
prints the counts. Nothing written here names a repository except the private
study ID column, so OUT_DIR must be private.
"""
import csv
import random
import sys
from collections import Counter
from pathlib import Path

SEED = 20261115
N_CONFIRMED = 10
MAX_PER_REPO = 2
USED_RUNS = ["retest080/confirm_results.csv", "retest080/confirm_results_2.csv"]
LABELS = ("confirmed", "rejected", "not_decidable")


def sampled(row):
    """A claim drawn in samples 1-5, the alarm sample or the pilot (not one only linked to the registry)."""
    note = row["note"]
    return row["adjudicator"].startswith("Codex (sample") or note.startswith(
        ("sample ", "alarm sample", "pilot check"))


def main(study, out):
    study, out = Path(study), Path(out)
    rows = list(csv.DictReader(open(study / "claims.csv", encoding="utf-8")))
    used = set()
    for f in USED_RUNS:
        used |= {r["claim_id"] for r in csv.DictReader(open(study / f, encoding="utf-8"))}
    never_tested = set()  # claims a sample checker did not assess on biosecurity grounds
    for f in sorted(study.glob("sample*_results.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            if "biosecurity" in (r.get("how", "") + r.get("evidence", "")):
                never_tested.add(r["repo_id"])
    key = {r["repo_id"]: r["repo_key"] for r in
           csv.DictReader(open(study / "release_repo_key_PRIVATE.csv", encoding="utf-8"))}

    pool, seen = [], set()
    for r in rows:
        if r["label"] not in LABELS or not sampled(r):
            continue
        cid = r["claim_id"].split("-")[0]
        reason = ""
        if cid in seen:
            reason = "duplicate (in two samples)"
        elif cid in used:
            reason = "already used in the two runs of ten"
        elif r["repo_id"] in never_tested:
            reason = "never tested (biosecurity)"
        elif not r["file"].endswith(".py") or "JavaScript" in r["note"]:
            reason = "not Python (the sandbox runs Python only)"
        seen.add(cid)
        pool.append(dict(claim_id=cid, study_id=r["repo_id"], repo_key=key.get(r["repo_id"], ""),
                         label=r["label"], model=r["model"], commit=r["commit"], file=r["file"],
                         line=r["line"], excluded=reason))

    rng = random.Random(SEED)
    rng.shuffle(pool)
    per_repo, n_conf = Counter(), 0
    for p in pool:
        p["role"] = ""
        if p["excluded"]:
            continue
        if p["label"] != "confirmed":
            p["role"] = "drawn"
        elif n_conf < N_CONFIRMED and per_repo[p["study_id"]] < MAX_PER_REPO:
            p["role"] = "drawn"
            per_repo[p["study_id"]] += 1
            n_conf += 1
        else:
            p["role"] = "reserve"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "pool.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pool[0]))
        w.writeheader()
        w.writerows(pool)
    left = Counter(p["label"] for p in pool if not p["excluded"])
    print("excluded:", dict(Counter(p["excluded"] for p in pool if p["excluded"])))
    print("pool left:", dict(left))
    print("drawn:", dict(Counter(p["label"] for p in pool if p["role"] == "drawn")))
    for lab in ("rejected", "not_decidable"):
        print(f"{lab}:", ", ".join(f"{p['study_id']} {p['claim_id']}" for p in pool
                                    if p["label"] == lab and not p["excluded"]))


if __name__ == "__main__":
    main(*sys.argv[1:3])
