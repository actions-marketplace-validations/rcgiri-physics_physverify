"""The seeded-bug benchmark as a regression test.

For each bug: the checks that were predicted (by reasoning about what each
check can see) to flag it must do so. Bugs predicted to be invisible must stay
invisible, which documents the blind spot rather than hiding it. Bug-free
baselines must never raise a false alarm.
"""

import pytest

from pvbench.matrix import PROBLEMS, evaluate, Row


@pytest.fixture(scope="module")
def cache():
    return {}


def _row(cache, problem, bug):
    key = (problem, bug)
    if key not in cache:
        module = PROBLEMS[problem]
        bugs = frozenset([bug]) if bug else frozenset()
        cache[key] = Row(problem, bug, evaluate(module, bugs))
    return cache[key]


@pytest.mark.parametrize("problem", sorted(PROBLEMS))
def test_bug_free_baseline_has_no_false_alarms(cache, problem):
    row = _row(cache, problem, None)
    assert row.flagged() == {}, row.flagged()


CASES = [(name, bug) for name, mod in PROBLEMS.items() for bug in mod.BUGS]


@pytest.mark.parametrize("problem,bug", CASES)
def test_predicted_checks_flag_the_bug(cache, problem, bug):
    expected = PROBLEMS[problem].BUGS[bug].expected
    flagged = set(_row(cache, problem, bug).flagged())
    if expected:
        assert expected <= flagged, f"expected {sorted(expected)}, flagged {sorted(flagged)}"
    else:
        assert not flagged, f"documented blind spot is now detected by {sorted(flagged)}; update the catalogue"


def test_separate_refinement_alone_cannot_see_the_extra_time_step(cache):
    """Recorded finding. Refining dt and dx separately was expected to expose an extra time step.

    It does not: the extra step is an O(dt) error, the same order as forward Euler's own, so the
    time-only study still sees order 1 and the other studies still see their design order. Only the
    patch test, which expects an exact answer rather than a small one, flags it.
    """
    row = _row(cache, "heat1d", "extra_time_step")
    results = {(check.family, check.label): result for check, result in row.results}
    for label in ("FTCS coupled dt ~ dx^2", "FTCS time-only refinement", "FTCS space-only refinement"):
        assert results[("mms", label)].ok, label
    patch = results[("patch", "FTCS cubic in x, linear in t")]
    assert not patch.ok
    assert abs(patch.fitted - 1.0) < 0.2, patch.message  # the leftover error is first order in dt


def test_patch_test_passes_on_the_bug_free_heat_solver_to_round_off(cache):
    row = _row(cache, "heat1d", None)
    patch = {check.family: result for check, result in row.results}["patch"]
    assert patch.status == "EXACT" and max(patch.errors) < 1e-12


def test_every_bug_has_a_description_and_a_known_family():
    from physverify.checks import FAMILIES

    for module in PROBLEMS.values():
        for bug, info in module.BUGS.items():
            assert info.description
            assert info.expected <= set(FAMILIES), bug


def test_committed_tables_match_a_fresh_run(cache):
    """Rerunning the benchmark gives the committed tables, so others can reproduce them."""
    from pathlib import Path

    from pvbench.matrix import catalogue, to_markdown

    rows = [_row(cache, name, None) for name in PROBLEMS] + [_row(cache, n, b) for n, b in CASES]
    order = {(r.problem, r.bug): r for r in rows}
    rows = []
    for name, module in PROBLEMS.items():
        rows.append(order[(name, None)])
        rows += [order[(name, bug)] for bug in module.BUGS]
    results = Path(__file__).resolve().parents[1] / "results"
    assert to_markdown(rows) == (results / "detection_matrix.md").read_text(encoding="utf-8")
    assert catalogue(rows) == (results / "bug_catalogue.md").read_text(encoding="utf-8")


def test_every_bug_records_its_expected_symptom():
    for module in PROBLEMS.values():
        for bug, info in module.BUGS.items():
            assert info.symptom, f"{module.NAME}/{bug}"
