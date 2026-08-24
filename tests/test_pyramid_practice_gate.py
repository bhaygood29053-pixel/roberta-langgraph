from __future__ import annotations

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import GradedAnswer
from roberta.learning.pyramid_practice import PreparedTargetedPractice, evaluate_targeted_practice


def _exercise(exercise_id: str, concept: str, subconcept: str) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id="practice-gate",
        level=1,
        concept=concept,
        subconcept=subconcept,
        question=f"Question {exercise_id}?",
        expected_answer="answer",
        source_refs=("source",),
    )


def _grade(exercise_id: str, grade: str) -> GradedAnswer:
    score = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}[grade]
    return GradedAnswer(
        exercise_id=exercise_id,
        answer="answer",
        grade=grade,
        score=score,
        correct=grade == "PASS",
        failure_codes=() if grade == "PASS" else ("conceptual_mismatch",),
        critical_failure=False,
        grader_note="fixture",
    )


def test_overall_accuracy_cannot_mask_unresolved_noncritical_weakness() -> None:
    exercises = (
        _exercise("c1", "benefits", "immutability"),
        _exercise("c2", "benefits", "immutability"),
        _exercise("n1", "distributed_systems", "definition"),
        _exercise("n2", "distributed_systems", "definition"),
    )
    prepared = PreparedTargetedPractice(
        curriculum_id="practice-gate",
        level=1,
        exercises=exercises,
        weakness_critical_counts=(
            ("benefits", "immutability", 1),
            ("distributed_systems", "definition", 0),
        ),
        original_weak_ids=("old-c", "old-n"),
        source_grounded_weak_items=2,
    )
    report = evaluate_targeted_practice(
        prepared,
        (
            _grade("c1", "PASS"),
            _grade("c2", "PASS"),
            _grade("n1", "PASS"),
            _grade("n2", "PARTIAL"),
        ),
    )

    assert report.accuracy == 0.875
    assert report.critical_weaknesses_passed is True
    assert report.all_weaknesses_passed is False
    assert report.practice_passed is False
    assert report.canonical_attempt_authorized is False
