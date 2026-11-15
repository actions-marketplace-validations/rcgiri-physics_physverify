"""Fix the claim list from the feasibility results (docs/plan_agent_eval.md, section 2). Runs no model.

    python -I finalize.py OUT_DIR

Reads OUT_DIR/pool.csv and OUT_DIR/feasibility.csv. A drawn confirmed claim
that did not pass is replaced by the next passing reserve in the seeded order,
keeping at most two claims per repository. Rejected and not decidable claims
cannot be replaced (they are the whole pool); if fewer than 5 rejected claims
pass, the script stops. Writes OUT_DIR/claims_final.csv and prints each swap.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

MAX_PER_REPO = 2


def main(out):
    out = Path(out)
    pool = list(csv.DictReader(open(out / "pool.csv", encoding="utf-8")))
    feas = {r["claim_id"]: r for r in csv.DictReader(open(out / "feasibility.csv", encoding="utf-8"))}
    ok = lambda p: feas.get(p["claim_id"], {}).get("status") == "pass"  # noqa: E731
    drawn = [p for p in pool if p["role"] == "drawn"]
    bad_fixed = [p for p in drawn if p["label"] != "confirmed" and not ok(p)]
    if sum(p["label"] == "rejected" and ok(p) for p in drawn) < 5:
        sys.exit("fewer than 5 rejected claims pass: stop and revisit the design")
    for p in bad_fixed:
        print(f"cannot replace {p['label']} {p['study_id']} {p['claim_id']}: kept out")
    final = [p for p in drawn if ok(p)]
    per_repo = Counter(p["study_id"] for p in final if p["label"] == "confirmed")
    reserves = iter(p for p in pool if p["role"] == "reserve" and ok(p))
    for p in drawn:
        if p["label"] != "confirmed" or ok(p):
            continue
        for q in reserves:
            if per_repo[q["study_id"]] < MAX_PER_REPO:
                per_repo[q["study_id"]] += 1
                q = dict(q, replaces=p["claim_id"])
                final.append(q)
                print(f"replaced {p['study_id']} {p['claim_id']} ({feas[p['claim_id']]['detail'][:60]})"
                      f" by {q['study_id']} {q['claim_id']}")
                break
        else:
            print(f"no passing reserve left for {p['claim_id']}")
    fields = list(pool[0]) + ["replaces"]
    with open(out / "claims_final.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(final)
    print("final:", dict(Counter(p["label"] for p in final)))


if __name__ == "__main__":
    main(sys.argv[1])
