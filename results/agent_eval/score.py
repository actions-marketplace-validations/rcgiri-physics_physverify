"""Score the agent-evaluation sessions (docs/plan_agent_eval.md, section 4). Runs no model, judges nothing.

    python -I score.py CLAIMS_CSV SESSIONS_DIR OUT_CSV

CLAIMS_CSV has claim_id, label (the hand verdict) and repo_key; each session
folder has the session.json that harness/session.py wrote. Writes one public row
per session (claim ID, release repository key, arm, verdicts, seconds, runs) and
prints the tables of section 4. Counts within these claims only.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

V = ("confirmed", "rejected", "not decidable")


def main(claims_csv, sessions, out_csv):
    hand = {r["claim_id"]: r for r in csv.DictReader(open(claims_csv, encoding="utf-8"))}
    rows = []
    for f in sorted(Path(sessions).glob("*/session.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        h = hand[s["claim_id"]]
        rows.append(dict(claim_id=s["claim_id"], repo_key=h.get("repo_key", ""), arm=s["arm"],
                         verdict=s.get("verdict", "not decidable"), note=s.get("verdict_note", "not finished"),
                         hand=h["label"].replace("_", " "), seconds=s.get("seconds", ""), runs=len(s["runs"])))
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    by = {}
    for arm in sorted({r["arm"] for r in rows}):
        rs = [r for r in rows if r["arm"] == arm]
        by[arm] = {r["claim_id"]: r for r in rs}
        t = Counter((r["verdict"], r["hand"]) for r in rs)
        n = Counter(r["hand"] for r in rs)
        print(f"\nArm {arm}: agent verdict (rows) against hand verdict (columns)")
        print(" " * 15 + "".join(f"{v:>15}" for v in V))
        for a in V:
            print(f"{a:>15}" + "".join(f"{t[(a, h)]:>15}" for h in V))
        print(f"agreement {sum(r['verdict'] == r['hand'] for r in rs)} of {len(rs)}; "
              f"false confirmation {t[('confirmed', 'rejected')]} of {n['rejected']}; "
              f"false rejection {t[('rejected', 'confirmed')]} of {n['confirmed']}; "
              f"left open {t[('not decidable', 'confirmed')] + t[('not decidable', 'rejected')]} "
              f"of {n['confirmed'] + n['rejected']}; timeouts {sum(r['note'] == 'timeout' for r in rs)}")
        settled = [r["claim_id"] for r in rs if r["hand"] == "not decidable" and r["verdict"] != "not decidable"]
        if settled:
            print("settled a hand-unsettled claim:", ", ".join(settled))
    if {"S", "C"} <= by.keys():
        both = by["S"].keys() & by["C"].keys()
        ok = {a: {c for c in both if by[a][c]["verdict"] == by[a][c]["hand"]} for a in ("S", "C")}
        print(f"\npaired, {len(both)} claims: C right and S wrong {len(ok['C'] - ok['S'])}; "
              f"S right and C wrong {len(ok['S'] - ok['C'])}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
