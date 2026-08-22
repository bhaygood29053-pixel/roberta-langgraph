from __future__ import annotations

import json

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_remediation import build_remediation_plan, load_weak_items, select_fresh_practice


def _exercise(index: int, concept: str, subconcept: str) -> Exercise:
    return Exercise(
        exercise_id=f"q{index}",
        curriculum_id="c1",
        level=1,
        concept=concept,
        subconcept=subconcept,
        question=f"Question {index}?",
        expected_answer=f"answer {index}",
        source_refs=(f"source-{concept}",),
    )


def test_remediation_groups_weaknesses_and_excludes_seen_questions(tmp_path):
    checkpoint = tmp_path / "level_01_batch_0001.json"
    checkpoint.write_text(json.dumps({
        "checkpoint_schema": "roberta-pyramid-checkpoint/v2",
        "grades": [
            {"exercise_id": "q1", "grade": "FAIL", "score": 0.0, "critical_failure": True,
             "failure_codes": ["factual_error"], "answer": "bad", "grader_note": "wrong"},
            {"exercise_id": "q2", "grade": "PARTIAL", "score": 0.5, "critical_failure": False,
             "failure_codes": ["incomplete_reasoning"], "answer": "half", "grader_note": "partial"},
            {"exercise_id": "q3", "grade": "PASS", "score": 1.0, "critical_failure": False,
             "failure_codes": [], "answer": "good", "grader_note": "ok"},
        ],
    }), encoding="utf-8")

    exercises = (
        _exercise(1, "types", "private"),
        _exercise(2, "types", "private"),
        _exercise(3, "types", "private"),
        _exercise(4, "types", "private"),
        _exercise(5, "types", "private"),
    )
    weak = load_weak_items(tmp_path)
    assert [item.exercise_id for item in weak] == ["q1", "q2"]

    plan = build_remediation_plan(exercises, weak)
    assert plan["weak_item_count"] == 2
    assert plan["weakness_count"] == 1
    target = plan["weaknesses"][0]
    assert target["concept"] == "types"
    assert target["subconcept"] == "private"
    assert target["fail_count"] == 1
    assert target["partial_count"] == 1
    assert target["critical_count"] == 1

    practice = select_fresh_practice(exercises, weak, per_weakness=2, seed="test")
    assert len(practice) == 2
    assert not {item.exercise_id for item in practice} & {"q1", "q2"}


def test_no_checkpoint_failures_returns_empty_tuple(tmp_path):
    checkpoint = tmp_path / "level_01_batch_0001.json"
    checkpoint.write_text(json.dumps({"grades": [
        {"exercise_id": "q1", "grade": "PASS", "score": 1.0, "critical_failure": False,
         "failure_codes": [], "answer": "good", "grader_note": "ok"}
    ]}), encoding="utf-8")
    assert load_weak_items(tmp_path) == ()
