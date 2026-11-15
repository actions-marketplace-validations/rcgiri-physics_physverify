# Does `confirm` help a coding agent? Design (issue #31)

Status: design only, written 2026-11-15 before any run. Nothing here has been measured.

Issue #31 asks whether agents find more seeded bugs with physverify than without. Since November 2026 the tool's job is to confirm a suspected defect, not to find one ([ROADMAP.md](https://github.com/rcgiri-physics/physverify/blob/main/ROADMAP.md)), so this design tests that job on real claims. Seeded bugs stay with #28 and #30.

## 1. Question

On the same suspected defects, does an agent that has `physverify confirm` reach the right verdict more often, and a wrong one less often, than the same agent with only its own scripts?

"Right" means agreement with the hand verdict already recorded in the 100-repository study ([Checking an AI code review](ai-review.md)). Those verdicts came from one adjudicator with scripts written with an AI assistant, so they are a comparison, not ground truth.

## 2. Claims

- **Pool:** the study's sampled review claims (samples 1 to 5, the alarm sample and the pilot) with a hand verdict of confirmed, rejected or not decidable. Left out, each by a stated rule:
  - the 20 claims already run through `confirm` (the two runs of ten on 2026-11-15), because the verdict rules and the docs were changed from them;
  - "real but minor" claims: their hand verdict has no single `confirm` verdict to compare with;
  - claims on the virus-assembly simulation, which were never tested, on biosecurity grounds;
  - claims whose code is not Python (the sandbox runs Python only);
  - a claim that appears in two samples is counted once.
- **What is left** (from `draw.py`, which prints the exact pool): 32 confirmed, 5 rejected, 7 not decidable.
- **Draw:** 22 claims by a script with a fixed seed: 10 confirmed (seeded, at most two per repository), and all 5 rejected and all 7 not decidable, since that is the whole pool. No draw is involved for those twelve, and a rejected or unsettled claim that fails the feasibility check cannot be replaced. If fewer than 5 rejected claims pass, the run stops and the design is revisited before any agent runs.
- **Feasibility is settled before any agent runs:** a script (no model) checks that the tree is present, that the cited file exists and is Python, and that its imports load in the sandbox image (with the repository's own folders on the path). A confirmed claim that fails is replaced by the next one in the seeded order, and the replacement is listed.
- The same 22 claims go to both arms, so the comparison is paired.

## 3. Arms

Both arms use Claude Sonnet 5.5, in a fresh session per claim, inside the sandbox ([sandbox/README.md](https://github.com/rcgiri-physics/physverify/blob/main/sandbox/README.md)).

| | Arm S (scripts only) | Arm C (`confirm`) |
|---|---|---|
| Given | the claim text unedited, file, line, the repository tree at its commit | the same |
| Tools | Python and the repository's dependencies; physverify not installed | the same, plus physverify at commit `5f314dc` and `docs/confirm.md` |
| Image | `physverify-sandbox:1` with physverify uninstalled before the run; the trial runs check that `import physverify` fails | `physverify-sandbox:1` rebuilt from `5f314dc` |
| Must return | a last line `VERDICT: confirmed`, `VERDICT: rejected` or `VERDICT: not decidable`; one sentence of reason; the script it ran | the claim file and the ledger line |
| Verdict that is scored | the `VERDICT:` line; a missing or malformed line is scored as not decidable and marked | the one in the ledger, even if the agent's prose says otherwise |

Rules for both arms:
- **Not given:** the hand verdict, the old confirmation script, other models' reviews, the issue drafts, the study tables. In the two earlier runs the drafters translated an existing script; here the agent starts from the claim alone, which was never measured.
- **Same limits:** 20 minutes of wall time and 6 sandbox runs per claim. Out of time or runs is scored as not decidable and marked as a timeout.
- **Same prompt** except for one paragraph that names `confirm`. Both prompts say the reference must come from the physics, never from the code under test, so that arm C is not helped by that advice alone.
- **Order:** arm and claim order are shuffled by the seeded script; a session never sees another session's output.
- Arm C uses the command line. As a side check, 6 of the 22 claims (seeded) are also run through the MCP tool `confirm_claim`, with the server running inside the container and `PHYSVERIFY_REPO` set. This set-up has never been tried: it must work in the two trials, or the side check is dropped and the drop is reported. Its results are reported separately and are not part of the headline numbers.

Before the scored runs, the harness is tried on two of the 20 already-used claims, in both arms. Those trials are not scored.

## 4. Scoring (fixed now)

A script compares verdict strings; no model and no person judges a run.

Per arm, a 3 by 3 table of agent verdict against hand verdict, and from it:

| Measure | Definition |
|---|---|
| Agreement | same verdict as the hand verdict, of 22 |
| False confirmation | agent says confirmed, hand verdict is rejected (of 5) |
| False rejection | agent says rejected, hand verdict is confirmed (of 10) |
| Left open | agent says not decidable where the hand verdict is confirmed or rejected (of 15) |
| Time | wall seconds from session start to verdict; number of sandbox runs; tokens when the client reports them |

- The 7 claims with a hand verdict of not decidable count only in agreement. An arm that settles one is listed by name, not counted as right or wrong.
- The paired result is given claim by claim: how many claims arm C got right and arm S wrong, and the reverse.
- After scoring, every disagreement with a hand verdict is read by a person. A hand verdict changes only by a dated entry with its reason, and the tables are then given both ways, before and after.
- Counts within these 22 claims only. No significance claim and no general rate.

## 5. Size and cost

22 claims, 2 arms, 1 run each: 44 scored sessions, plus 6 MCP sessions and 2 trials in each arm (54 in all). At 20 minutes at most per session and four at a time, the runs fit in about half a day; the reading of disagreements takes the rest of a day or two.

## 6. What is committed

- Public, in `results/agent_eval/`: the two prompts, the draw, feasibility and scoring scripts, the frozen physverify commit, and one row per session (claim ID, the release repository key `R…` from the public study release, arm, verdict, hand verdict, seconds, runs). Corpus study IDs are not published, because the private lists link them to repositories.
- Private: the session transcripts, scripts, claim files and ledgers, because they name the repositories. A repository is named in public only when its defect is already confirmed by its maintainer ([Confirmed by maintainers](confirmed.md)).

## 7. Limits to state with the result

- 22 claims, one model, one run per session: a difference of one or two claims is noise.
- The false-confirmation and left-open numbers rest on the whole remaining pool of rejected (5) and unsettled (7) claims, with no draw involved; there is nothing else to test them on.
- The hand verdicts come from one adjudicator, and their scripts were written with an assistant of the same family as the model under test. Claims made by the same model stay in the pool (leaving them out would shrink the 5 rejected claims further) and are marked in the table.
- The 22 held-out claims were not used to change `confirm`, but the unsettled ones were read when the `convention` and `scope` keys were designed (issue #71), so that part is not fully out of sample.
- Arm C's verdict comes from a fixed rule and arm S's from the agent's own statement. That is the difference being tested, but it also means arm S can say "not decidable" more freely.
- Both arms confirm claims that a reviewer already made. Nothing here measures finding defects.

## 8. Decided before the first run (2026-11-15)

1. **The model:** Claude Sonnet 5.5 in both arms. It costs less over 54 sessions, and a middle model is closer to what most users run. A stronger model may get most claims right in both arms and leave no difference to see in 22 claims.
2. **Issue #31** is reworded to the question in section 1, with a link to this design.
3. **Frozen commit:** `5f314dc` (main after #72).
