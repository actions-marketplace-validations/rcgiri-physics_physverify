You are checking one suspected defect that a code reviewer reported in a physics code. Decide whether it is real.

The claim, the cited file and line, and the repository folder are in {WORK}/claim.md. Read it first.

Rules:
- You may read any file in the repository folder. Do not run anything from it on this computer, and do not read any other folder except {WORK}.
- Write your scripts in {WORK} (directly in that folder, no subfolders). Run code only through the sandbox, with this command:
  `{PY} -I {HARNESS}/session.py run {SESSION} SCRIPT.py [ARGS]`
  Inside the sandbox the repository is at the path in the environment variable `PHYSVERIFY_REPO`, Python 3.12 with NumPy, SciPy, SymPy and Matplotlib is available, and there is no network.
- You have at most 6 sandbox runs and 20 minutes. A run past either limit is refused.
- The reference you compare with must come from the physics: a textbook, a paper, or the repository's own README. Never derive it from the code under test, or a bug in the code is copied into the reference and the check passes. Say where each equation came from.
- Choose one verdict: **confirmed** (a run shows the claimed defect), **rejected** (a run shows the claimed defect is not there), or **not decidable** (you cannot settle it with a run, for example a convention the repository does not state, or the code cannot be run).
{ARM_PARAGRAPH}
When you are done, run `{PY} -I {HARNESS}/session.py done {SESSION}` and then reply with one sentence of reason, the name of the script that settled it, and as the very last line exactly one of:
VERDICT: confirmed
VERDICT: rejected
VERDICT: not decidable
