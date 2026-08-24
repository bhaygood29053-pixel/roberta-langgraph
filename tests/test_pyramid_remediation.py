from __future__ import annotations

import json

import pytest

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_remediation import (
    build_remediation_plan,
    load_seen_exercise_ids,
    load_weak_items,
    select_fresh_practice,
)


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


def _write_checkpoint(path, grades):
    path.write_text(json.dumps({
        "checkpoint_schema": "roberta-pyramid-checkpoint/v2",
        "grades": grades,
    }), encoding="utf-8")


def test_remediation_groups_weaknesses_and_excludes_seen_questions(tmp_path):
    checkpoint = tmp_path / "level_01_batch_0001.json"
    _write_checkpoint(checkpoint, [
        {"exercise_id": "q1", "grade": "FAIL", "score": 0.0, "critical_failure": True,
         "failure_codes": ["factual_error"], "answer": "bad", "grader_note": "wrong"},
        {"exercise_id": "q2", "grade": "PARTIAL", "score": 0.5, "critical_failure": False,
         "failure_codes": ["incomplete_reasoning"], "answer": "half", "grader_note": "partial"},
        {"exercise_id": "q3", "grade": "PASS", "score": 1.0, "critical_failure": False,
         "failure_codes": [], "answer": "good", "grader_note": "ok"},
    ])

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

    seen = load_seen_exercise_ids((tmp_path,))
    assert seen == ("q1", "q2", "q3")
    practice = select_fresh_practice(
        exercises,
        weak,
        per_weakness=2,
        seed="test",
        excluded_exercise_ids=seen,
    )
    assert {item.exercise_id for item in practice} == {"q4", "q5"}


def test_cumulative_exclusion_blocks_prior_checkpoint_questions(tmp_path):
    current = tmp_path / "current"
    prior = tmp_path / "prior"
    current.mkdir()
    prior.mkdir()
    _write_checkpoint(current / "level_01_batch_0001.json", [
        {"exercise_id": "q1", "grade": "FAIL", "score": 0.0, "critical_failure": False,
         "failure_codes": ["factual_error"], "answer": "bad", "grader_note": "wrong"},
        {"exercise_id": "q2", "grade": "PASS", "score": 1.0, "critical_failure": False,
         "failure_codes": [], "answer": "good", "grader_note": "ok"},
    ])
    _write_checkpoint(prior / "level_01_batch_0001.json", [
        {"exercise_id": "q3", "grade": "PASS", "score": 1.0, "critical_failure": False,
         "failure_codes": [], "answer": "good", "grader_note": "ok"},
    ])
    exercises = tuple(_exercise(index, "types", "private") for index in range(1, 6))
    weak = load_weak_items(current)
    seen = load_seen_exercise_ids((current, prior))

    assert seen == ("q1", "q2", "q3")
    practice = select_fresh_practice(
        exercises,
        weak,
        per_weakness=2,
        seed="test",
        excluded_exercise_ids=seen,
    )
    assert {item.exercise_id for item in practice} == {"q4", "q5"}


def test_seen_exercise_loading_rejects_missing_or_empty_checkpoint_directory(tmp_path):
    with pytest.raises(ValueError, match="checkpoint directory does not exist"):
        load_seen_exercise_ids((tmp_path / "missing",))

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="contains no Pyramid checkpoints"):
        load_seen_exercise_ids((empty,))


def test_seen_exercise_loading_rejects_malformed_checkpoint(tmp_path):
    checkpoint = tmp_path / "level_01_batch_0001.json"
    checkpoint.write_text("not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot read exclusion checkpoint"):
        load_seen_exercise_ids((tmp_path,))


def test_fresh_practice_fails_closed_when_cumulative_history_exhausts_weakness(tmp_path):
    checkpoint = tmp_path / "level_01_batch_0001.json"
    _write_checkpoint(checkpoint, [
        {"exercise_id": "q1", "grade": "FAIL", "score": 0.0, "critical_failure": False,
         "failure_codes": ["factual_error"], "answer": "bad", "grader_note": "wrong"},
        {"exercise_id": "q2", "grade": "PASS", "score": 1.0, "critical_failure": False,
         "failure_codes": [], "answer": "good", "grader_note": "ok"},
    ])
    exercises = (
        _exercise(1, "types", "private"),
        _exercise(2, "types", "private"),
    )
    weak = load_weak_items(tmp_path)
    seen = load_seen_exercise_ids((tmp_path,))

    with pytest.raises(ValueError, match="cumulative checkpoint history exhausted fresh practice"):
        select_fresh_practice(
            exercises,
            weak,
            per_weakness=1,
            seed="test",
            excluded_exercise_ids=seen,
        )


def test_legacy_singleton_weakness_can_still_emit_handoff_without_practice(tmp_path):
    checkpoint = tmp_path / "level_01_batch_0001.json"
    _write_checkpoint(checkpoint, [
        {"exercise_id": "q1", "grade": "FAIL", "score": 0.0, "critical_failure": False,
         "failure_codes": ["factual_error"], "answer": "bad", "grader_note": "wrong"},
    ])
    exercises = (_exercise(1, "types", "private"),)
    weak = load_weak_items(tmp_path)
    seen = load_seen_exercise_ids((tmp_path,))

    assert select_fresh_practice(
        exercises,
        weak,
        per_weakness=1,
        seed="test",
        excluded_exercise_ids=seen,
    ) == ()


def test_no_checkpoint_failures_returns_empty_tuple(tmp_path):
    checkpoint = tmp_path / "level_01_batch_0001.json"
    _write_checkpoint(checkpoint, [
        {"exercise_id": "q1", "grade": "PASS", "score": 1.0, "critical_failure": False,
         "failure_codes": [], "answer": "good", "grader_note": "ok"}
    ])
    assert load_weak_items(tmp_path) == ()
