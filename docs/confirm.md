# Confirming one suspected defect

This page is the design of `physverify confirm` (issue #54), kept as its specification.

`physverify confirm` takes **one** suspected defect, runs checks against a reference written from the physics, and records a verdict: *confirmed*, *rejected* or *not decidable*. A suspicion can come from a person, from `physverify scan`, or from an AI code review ([Checking an AI code review](ai-review.md)).

It does **not** find defects, and it does **not** write the reference. A person (or an assistant the person supervises) writes the claim file, and the reference in it must come from a book, a paper or the project's README, never from the code under test. The command only makes the run repeatable and the verdict rule fixed, and keeps a record of every run.

`confirm` **runs the code**. Use it on code you trust, or inside the container described in [sandbox/README.md](https://github.com/rcgiri-physics/physverify/blob/main/sandbox/README.md).

## 1. The claim file

A claim file is a Python file, like a spec. Its folder is put on `sys.path`, so it can import the solver next to it. It defines three things at its top level. `CLAIM` may carry a type annotation (`CLAIM: dict = {...}`); `control` and `checks` may be defined there or imported (`from helpers import control, checks`). A name bound only inside an `if` block or a function is not seen, because the file is read before it runs.

### `CLAIM`

A literal dict (strings and numbers only, so it can be read without running the file) with these keys, all required:

| Key | Meaning |
|---|---|
| `text` | the claim as it was stated, unedited ("the RK4 stage `k3` is evaluated at `t + h` instead of `t + h/2`") |
| `source` | who made the claim: a person, `physverify scan`, or a model with its name |
| `file` | the file the claim is about, relative to the repository root |
| `line` | the line number in that file (an integer) |
| `reference` | where the correct equation comes from: book and section, paper and equation number, or the README section |
| `impact` | `used`, `latent` or `unknown`: whether the repository's own scripts or defaults reach the code path |

`CLAIM` that is not a literal dict, a missing key, an empty or `"FILL IN"` string, a `line` that is not an integer, or an `impact` outside the three values is a load error (exit 2, nothing is run).

`impact` is about reach, not size. `used`: a script or default setting in the repository runs the faulty path. `latent`: the path is reachable only by an option, argument or input that the repository itself never uses. `unknown`: not looked at. The person writing the claim decides it; `confirm` does not check it.

### `control()`

Returns one `physverify.Check` that must PASS. It shows two things: that the reference is right, and that the test can pass at all. Typical controls:
- the same check on a case where the claimed effect is absent (the faulty term multiplies zero, the bad branch is not taken, a constant coefficient where the claim is about a variable one);
- the same check with the reference on an independent solver (`scipy.integrate.solve_ivp` at tight tolerance) in place of the code under test.

A control that fails means the test itself is not trusted, so the claim cannot be judged by it.

### `checks()`

Returns a non-empty list of `physverify.Check` that state the correct behaviour on a case where the claimed effect is present. If the claim is right, at least one of them FAILs.

### Example (shortened)

```python
"""Claim: the midpoint step uses a full step for the half step (docs/examples/confirm)."""
import numpy as np
from physverify import Check, ManufacturedODE, mms_order_study

import solver  # the code under test

CLAIM = {
    "text": "integrate() advances the half step by h instead of h/2, so the method is first order",
    "source": "reviewer: a person",
    "file": "solver.py",
    "line": 14,
    "reference": "Hairer, Norsett and Wanner, Solving ODEs I, sec. II.1: the explicit midpoint rule is second order",
    "impact": "used",
}


def reference_rhs(t, y):  # the harmonic oscillator, written again from the physics
    return np.array([y[1], -4.0 * y[0]])


def control():
    # with a zero right-hand side the half step does not matter, so the check must pass
    ...


def checks():
    return [Check("mms", "midpoint rule is second order", lambda: mms_order_study(...))]
```

Complete, runnable claim files are in [the worked examples](#8-worked-examples).

## 2. Verdict rules

The rules are applied in this order (the refusal in section 5 comes before all of them). The first that matches gives the verdict.

| # | Situation | Verdict | Exit |
|---|---|---|---|
| 0 | the claim file cannot be loaded, `CLAIM` is incomplete, or `control()`/`checks()` is missing or returns something that is not a `Check` | load error | 2 |
| 1 | `specscan.reference_notes` reports that a reference uses the code under test, and `--allow-dependent-reference` was not given | not decidable: the reference is not independent | 2 |
| 2 | the run did not finish within `--timeout` | not decidable: timed out | 2 |
| 3 | the control is not PASS or EXACT | not decidable: the control did not pass, so the test is not trusted | 2 |
| 4 | the control passed and at least one check is FAIL | confirmed | 1 |
| 5 | the control passed, no check failed, and some check is INCONCLUSIVE, ERROR or SKIP | not decidable, naming each such check and its status | 2 |
| 6 | the control passed and every check is PASS or EXACT | rejected | 0 |

Notes on the rules:
- Rule 1 is static (it reads the claim file and runs nothing), so it is applied before any code runs. `--allow-dependent-reference "REASON"` takes a reason in words; the reason and the notes it overrides are recorded in the ledger. `reference_notes` is a heuristic: it looks at functions whose names say they are references. No note does not prove the reference independent.
- Rule 3 counts EXACT as a pass for the control: EXACT means the error is at round-off at every resolution, which is a stronger pass.
- Rule 4 puts a FAIL ahead of an INCONCLUSIVE or ERROR in another check: one failing check of the correct behaviour, with a passing control, is enough.
- An ERROR in a check (the code under test raised an exception) is not counted as confirmation, because the exception may come from the adapter rather than from the claimed defect. The message says so, and the person can turn the crash into a check if the crash is the defect.
- `impact` is printed next to the verdict and **never changes it**. "Confirmed, latent" is how the study's "real but minor" is expressed: the defect is real, and the repository's own runs do not reach it.

The printed verdict is one line, then one line for the control and one per check, each saying in plain words what was tested, then the claim and its reference. This is the output of the first worked example (section 8):

```
--8<-- "docs/examples/output/confirm_claim_damping_sign.txt"
```

## 3. The ledger

Each run appends exactly one JSON line to the ledger file (`--ledger FILE`, default `confirm_ledger.jsonl` in the current directory). The file is opened in append mode and the line is written in one call; an existing line is never rewritten or removed. Running the same claim again adds a new line, so the history of a claim (before and after a fix, for example) stays readable.

Fields of one line:

| Field | Content |
|---|---|
| `ledger_version` | 1 |
| `date` | UTC time of the run, ISO 8601 |
| `physverify` | the physverify version |
| `claim_file` | path of the claim file as given |
| `claim_sha256` | SHA-256 of the claim file's bytes |
| `text`, `source`, `file`, `line`, `reference`, `impact` | copied from `CLAIM` |
| `file_sha256` | SHA-256 of the file the claim is about, when it can be found; otherwise null |
| `repo_commit` | `git rev-parse HEAD` of the checkout that holds that file, with `-dirty` added when tracked files have uncommitted changes; `PHYSVERIFY_REPO_COMMIT` inside the sandbox; otherwise null |
| `verdict` | `confirmed`, `rejected` or `not decidable` |
| `reason` | one sentence in plain words (the reason in the table above, with the check names) |
| `control` | `{label, family, status, message, seconds}` or null when it did not run |
| `checks` | a list of `{label, family, status, message, seconds}` |
| `allow_dependent_reference` | null, or `{reason, notes}` when the flag was given |
| `timeout_s` | the time limit used |
| `stderr_tail` | the last 2000 characters of the child's stderr, only after an error or a timeout |

A load error is also written to the ledger, with `verdict` set to `not decidable` and the error as the reason, so every attempt is recorded. If the claim file cannot be read at all, the line has no `CLAIM` fields.

The repository root for `file` is found from the claim file's folder (or from `$PHYSVERIFY_REPO` inside the sandbox): the git checkout that contains it, else that folder itself; if `file` is not found from the root, it is looked up next to the claim file. A claim file kept outside the repository (an adapter folder) may give `CLAIM["repo"]`, a path relative to the claim file. This is the one optional key.

## 4. Isolation and time limit

Each claim runs in a fresh Python subprocess (`physverify.isolate`), started in the claim's folder with that folder first on `sys.path`. The child writes no `.pyc` files, so a same-size edit made within one second is still seen, and nothing is added to the repository. The parent waits at most `--timeout` seconds (default 300) for the whole run, control and checks together, then kills the child and every process it started (`taskkill /T` on Windows, the child's own process group elsewhere; a process that detaches itself on purpose can escape). A non-numeric, zero or negative `--timeout` is refused. A timeout gives "not decidable: timed out after S s" and the checks that had finished are not reported, because the child is killed before it reports.

The child writes its results as one JSON object on stdout after a marker line, and sends everything the code under test prints to stderr, so solver output cannot corrupt the result. Only the first JSON value after the marker is read, so text the code writes to the real stdout at exit (an `atexit` handler, a C or Fortran library flushing its buffer) is ignored. stderr is kept (the last 2000 characters) in the ledger line as `stderr_tail` when the run ends in an error or a timeout.

Because each run starts a new interpreter, an edit to the solver between two runs is always seen. This also removes the stale-module problem of the long-running MCP server (`agent.py`), where `load_spec` has to clear `sys.modules` and `.pyc` files by hand. The MCP tool `run_checks` uses the same runner, with its own time limit (`timeout` argument, default 600 s); a run that is stopped is reported as a load error of each spec.

The per-check budget (`Check.budget_s`) still applies inside the child; `--timeout` is the outer limit.

## 5. Safety

`confirm` runs the code under test. It refuses, with exit 2 and a message pointing to `sandbox/README.md`, unless either:
- `--trusted` is given (the user says the code is theirs or reviewed), or
- `PHYSVERIFY_REPO` is set, which the sandbox runner sets inside the container.

Nothing is run and nothing is written to the ledger when it refuses. The MCP tool `confirm_claim` (step 5) takes the same rule: an argument `trusted: true`, or `PHYSVERIFY_REPO` set in the server's environment.

## 6. Command line

```
physverify confirm CLAIM.py [--ledger FILE] [--timeout S] [--json -|FILE] [--trusted]
                            [--allow-dependent-reference REASON]
physverify confirm init CLAIM.py --text "..." --file F --line N
```

- `--json -` prints the ledger line (the same JSON object) to stdout instead of the text verdict; `--json FILE` writes it to a file. The ledger is written either way.
- `confirm init` writes a template with `CLAIM` (the given `text`, `file` and `line`; `source`, `reference` and `impact` left as `"FILL IN"`, which fails the load check until filled in), and stubs of `control()` and `checks()`. A comment at the top says that the reference must come from the physics (book, paper, README), never from the code under test. It refuses to overwrite an existing file.
- Exit codes: 0 rejected, 1 confirmed, 2 not decidable, a load error or a refusal.

`confirm init` is a subcommand name, so a claim file cannot be called `init`; a claim file must end in `.py`.

## 7. MCP tool

`physverify mcp` offers `confirm_claim` next to `run_checks`. Arguments: `claim` (required), `trusted`, `ledger`, `timeout`, `allow_dependent_reference`. It returns the text verdict followed by the ledger line as JSON, and appends to the ledger like the command. Without `trusted: true` and outside the sandbox it returns an error and runs nothing.

## 8. Worked examples

[`docs/examples/confirm/`](https://github.com/rcgiri-physics/physverify/tree/main/docs/examples/confirm) has three small solvers written for these docs and one claim file for each. The tests run them and compare the output shown here.

**Confirmed.** `oscillator.py` adds `+gamma*v` where the damping term should be `-gamma*v`. The control turns damping off, where the sign does not matter; the check turns it on.

```
--8<-- "docs/examples/output/confirm_claim_damping_sign.txt"
```

**Rejected.** A review says velocity Verlet in `verlet.py` is only first order. The control is a free particle, where the claimed mistake would make no difference; the check measures the order on the harmonic oscillator.

```
--8<-- "docs/examples/output/confirm_claim_verlet_order.txt"
```

**Not decidable.** The claim file reads the `half_life` argument of `decay.py` as a decay rate, so its reference is for a different equation and the control fails. Nothing can be said about the claim until the reference is fixed (here: rate = ln 2 / half_life, as `decay.py` documents). A wrong convention in the reference is the most common way a check goes wrong; see [Troubleshooting](troubleshooting.md).

```
--8<-- "docs/examples/output/confirm_claim_rk4_stage.txt"
```

## 9. What is not in scope

- Calling an AI model from the package, or generating references or claims.
- Changes to `physverify scan`.
- Statistical claims (a sampler's distribution): a single control/check pair has no measured false-alarm rate for them, so they are a later step (ROADMAP.md).
