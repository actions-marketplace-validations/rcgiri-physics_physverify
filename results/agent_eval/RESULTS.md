# Agent evaluation of `confirm`: scored results

Design: [docs/plan_agent_eval.md](../../docs/plan_agent_eval.md). Run on 2026-11-15 with Claude Sonnet 5.5, one fresh agent per claim and arm, physverify frozen at `5f314dc`. One row per session in `rows.csv` (claim ID, release repository key, arm, verdict, hand verdict, seconds, sandbox runs). Tables from `score.py`; no model and no person judged a run.

**Status:** the 9 disagreements were read by a person on 2026-11-15. One hand verdict changed (`hand_changes.csv`): claim `c2fda0a914d` from not decidable to confirmed, because both arms computed the same packet-averaged reference and found the claimed gap. The tables are given before and after that change; the other eight hand verdicts stand.

## Before the reading by hand (22 claims; counts within this sample only)

| Measure | Arm S (scripts only) | Arm C (`confirm`) |
|---|---|---|
| Agreement with the hand verdict | 14 of 22 | 14 of 22 |
| False confirmation (hand: rejected) | 0 of 5 | 0 of 5 |
| False rejection (hand: confirmed) | 1 of 10 | 0 of 10 |
| Left open (hand: confirmed or rejected) | 0 of 15 | 1 of 15 |
| Right on the 15 claims with a settled hand verdict | 14 | 14 |
| Median wall time per session | 50 s | 91 s |
| Median sandbox runs per session | 1 | 2 |

Paired, claim by claim: arm C right and arm S wrong on 1 claim; arm S right and arm C wrong on 1 claim. On the other 20 the two arms were both right or both wrong.

- **Arm S's one miss:** a claim about a numerical method that misbehaves only beyond the repository's default run length. Arm S tested the defaults, saw no effect and said rejected. Arm C ran the case the claim names, got confirmed, and the claim file recorded the impact as latent.
- **Arm C's one miss:** the claim file declared a convention the repository does not state, so the verdict rule gave not decidable where the hand verdict is confirmed.
- **The 7 claims with a hand verdict of not decidable:** both arms settled all 7, so neither scores on them in the agreement row. The two arms gave the same verdict on 4 of them and different verdicts on 3 (`c4acc207e93`, `c8f61364c54`, `cabae897751`). Whether either is right needs the reading by hand.
- No timeouts. The audit of all 44 transcripts found no repository code run outside the sandbox (minor deviations listed in the private run log).

## After the reading by hand (one hand verdict changed)

| Measure | Arm S | Arm C |
|---|---|---|
| Agreement with the hand verdict | 15 of 22 | 15 of 22 |
| False confirmation | 0 of 5 | 0 of 5 |
| False rejection | 1 of 11 | 0 of 11 |
| Left open | 0 of 16 | 1 of 16 |
| Right on the 16 claims with a settled hand verdict | 15 | 15 |

The paired result is unchanged: 1 claim each way.

## What this does and does not show

- With 22 claims, one model and one run per session, a difference of one claim is noise. These numbers show no difference between the arms in right verdicts. They do not show that `confirm` makes no difference.
- Neither arm confirmed any of the 5 rejected claims. That is the whole pool of rejected claims left after the design's exclusions.
- Arm C took longer and used more runs, mostly for claim files that failed to load the first time.
- Run conditions: three sessions were voided and redone from scratch (one queue time-out, two cut off by the account's usage limit). From session 20 on, the prompt in both arms carries one more line about the run queue. All of this is listed in the private run log.
