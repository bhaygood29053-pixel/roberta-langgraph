from __future__ import annotations

import pytest

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_critical_origin import (
    PYRAMID_CRITICAL_ORIGIN_INHERITANCE_CONTRACT,
    inherit_critical_origins,
)
from roberta.learning.pyramid_exam import GradedAnswer
from roberta.learning.pyramid_practice import (
    PreparedTargetedPractice,
    evaluate_targeted_practice,
)


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
IMMUTABILITY = ("benefits", "immutability")


def _current_plan(*, key=IMMUTABILITY) -> dict[str, object]:
    return {
        "weak_item_count": 1,
        "weakness_count": 1,
        "weaknesses": [
            {
                "concept": key[0],
                "subconcept": key[1],
                "priority": 2,
                "fail_count": 1,
                "partial_count": 0,
                "critical_count": 0,
                "failure_codes": {"conceptual_mismatch": 1},
                "source_refs": ["mastering_blockchain_4e_2023"],
                "exercise_ids": ["weak-current"],
                "reference_targets": ["reference"],
            }
        ],
    }


def _inherited_plan(*, key=IMMUTABILITY, critical_count=1) -> dict[str, object]:
    return {
        "curriculum_id": CURRICULUM_ID,
        "weak_item_count": 1,
        "weakness_count": 1,
        "weaknesses": [
            {
                "concept": key[0],
                "subconcept": key[1],
                "priority": 5,
                "fail_count": 1,
                "partial_count": 0,
                "critical_count": critical_count,
                "failure_codes": {"unsupported_inference": 1},
                "source_refs": ["mastering_blockchain_4e_2023"],
                "exercise_ids": ["weak-prior"],
                "reference_targets": ["reference"],
            }
        ],
    }


def test_critical_origin_survives_later_noncritical_failure() -> None:
    effective = inherit_critical_origins(
        _current_plan(),
        [_inherited_plan(critical_count=2)],
        curriculum_id=CURRICULUM_ID,
    )

    weakness = effective["weaknesses"][0]
    assert weakness["critical_count"] == 2
    assert weakness["priority"] == 8
    assert effective["critical_origin_inheritance_contract"] == (
        PYRAMID_CRITICAL_ORIGIN_INHERITANCE_CONTRACT
    )
    assert effective["inherited_critical_weaknesses"] == [
        {"concept": "benefits", "subconcept": "immutability"}
    ]


def test_unrelated_historical_critical_weakness_does_not_widen_current_plan() -> None:
    effective = inherit_critical_origins(
        _current_plan(key=("architecture", "network_layer")),
        [_inherited_plan()],
        curriculum_id=CURRICULUM_ID,
    )

    weakness = effective["weaknesses"][0]
    assert weakness["critical_count"] == 0
    assert effective["inherited_critical_weaknesses"] == []


def test_inherited_plan_curriculum_mismatch_fails_closed() -> None:
    inherited = _inherited_plan()
    inherited["curriculum_id"] = "other_curriculum"

    with pytest.raises(ValueError, match="curriculum_id does not match"):
        inherit_critical_origins(
            _current_plan(),
            [inherited],
            curriculum_id=CURRICULUM_ID,
        )


def test_inherited_critical_origin_preserves_perfect_group_pass_requirement() -> None:
    effective = inherit_critical_origins(
        _current_plan(),
        [_inherited_plan()],
        curriculum_id=CURRICULUM_ID,
    )
    critical_count = int(effective["weaknesses"][0]["critical_count"])

    exercises = tuple(
        Exercise(
            exercise_id=f"supp-{index}",
            curriculum_id=CURRICULUM_ID,
            level=1,
            concept="benefits",
            subconcept="immutability",
            question=f"Immutability verification {index}",
            expected_answer="Changing blockchain history is extremely difficult rather than absolutely impossible.",
            source_refs=("mastering_blockchain_4e_2023",),
        )
        for index in range(7)
    )
    prepared = PreparedTargetedPractice(
        curriculum_id=CURRICULUM_ID,
        level=1,
        exercises=exercises,
        weakness_critical_counts=(("benefits", "immutability", critical_count),),
        original_weak_ids=("weak-current",),
        source_grounded_weak_items=1,
    )
    grades = tuple(
        GradedAnswer(
            exercise_id=exercise.exercise_id,
            answer="answer",
            grade="PASS" if index < 6 else "PARTIAL",
            score=1.0 if index < 6 else 0.5,
            correct=index < 6,
        )
        for index, exercise in enumerate(exercises)
    )

    report = evaluate_targeted_practice(prepared, grades)

    assert report.accuracy > report.required_accuracy
    assert report.weakness_results[0].critical_origin is True
    assert report.weakness_results[0].passed is False
    assert report.practice_passed is False
    assert report.canonical_attempt_authorized is False
