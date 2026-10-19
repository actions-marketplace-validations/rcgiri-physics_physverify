"""The seeded-bug benchmark as a regression test.

For each bug: the checks that were predicted (by reasoning about what each
check can see) to flag it must do so. Bugs predicted to be invisible must stay
invisible, which documents the blind spot rather than hiding it. Bug-free
baselines must never raise a false alarm.
"""

import pytest

from physverify.matrix import PROBLEMS, evaluate, Row


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


def test_every_bug_has_a_description_and_a_known_family():
    from physverify.checks import FAMILIES

    for module in PROBLEMS.values():
        for bug, info in module.BUGS.items():
            assert info.description
            assert info.expected <= set(FAMILIES), bug
