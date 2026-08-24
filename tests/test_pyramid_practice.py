from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import AIMessage
import pytest

from roberta.learning.pyramid import Exercise, PYRAMID_CONTRACT
from roberta.learning.pyramid_exam import GradedAnswer
from roberta.learning.pyramid_practice import (
    TARGETED_PRACTICE_FAIL_NEXT_GATE,
    TARGETED_PRACTICE_PASS_NEXT_GATE,
    PreparedTargetedPractice,
    TargetedPyramidPracticeError,
    evaluate_targeted_practice,
    prepare_targeted_practice,
    run_targeted_practice,
)
from roberta.learning.pyramid_remediation import write_practice_jsonl
from roberta.learning.pyramid_source_reconstruction import (
    PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT,
    PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE,
    PYRAMID_SOURCE_RECONSTRUCTION_VERSION,
)


CURRICULUM_ID = "practice-fixture"


def _exercise(exercise_id: str, concept: str, subconcept: str) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id=CURRICULUM_ID,
        level=1,
        concept=concept,
        subconcept=subconcept,
        question=f"Question for {exercise_id}?",
        expected_answer=f"Expected answer for {exercise_id}",
        source_refs=("source-a",),
        question_type="reasoning",
        grading_rubric_id="pyramid-question-first-v1",
    )


def _bank() -> tuple[Exercise, ...]:
    return (
        _exercise("weak-critical", "benefits", "immutability"),
        _exercise("weak-normal", "distributed_systems", "definition"),
        _exercise("practice-critical-1", "benefits", "immutability"),
        _exercise("practice-critical-2", "benefits", "immutability"),
        _exercise("practice-normal-1", "distributed_systems", "definition"),
        _exercise("practice-normal-2", "distributed_systems", "definition"),
    )


def _write_curriculum(tmp_path: Path) -> Path:
    root = tmp_path / "curriculum"
    root.mkdir()
    manifest = {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": CURRICULUM_ID,
        "title": "Targeted practice fixture",
        "source_type": "test",
        "approved_source_refs": ["source-a"],
        "levels": [1],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "exercises.jsonl").write_text(
        "".join(json.dumps({
            "exercise_id": item.exercise_id,
            "curriculum_id": item.curriculum_id,
            "level": item.level,
            "concept": item.concept,
            "subconcept": item.subconcept,
            "question": item.question,
            "expected_answer": item.expected_answer,
            "source_refs": list(item.source_refs),
            "question_type": item.question_type,
            "grading_rubric_id": item.grading_rubric_id,
            "integrity_question": item.integrity_question,
            "boss_question": item.boss_question,
            "requires_live_data": item.requires_live_data,
        }) + "\n" for item in _bank()),
        encoding="utf-8",
    )
    return root


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    curriculum = _write_curriculum(tmp_path)
    practice = tmp_path / "practice.jsonl"
    fresh = tuple(item for item in _bank() if item.exercise_id.startswith("practice-"))
    write_practice_jsonl(practice, fresh)

    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({
        "curriculum_id": CURRICULUM_ID,
        "practice_question_count": 4,
        "weak_item_count": 2,
        "weakness_count": 2,
        "weaknesses": [
            {
                "concept": "benefits",
                "subconcept": "immutability",
                "critical_count": 1,
                "exercise_ids": ["weak-critical"],
            },
            {
                "concept": "distributed_systems",
                "subconcept": "definition",
                "critical_count": 0,
                "exercise_ids": ["weak-normal"],
            },
        ],
    }), encoding="utf-8")

    reconstructions = tmp_path / "reconstructions.jsonl"
    rows = []
    for exercise_id in ("weak-critical", "weak-normal"):
        rows.append({
            "reconstruction_contract": PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT,
            "reconstruction_version": PYRAMID_SOURCE_RECONSTRUCTION_VERSION,
            "curriculum_id": CURRICULUM_ID,
            "exercise_id": exercise_id,
            "source_grounded": True,
            "evidence_packet_status": "ok",
            "evidence_anchors": [{"anchor_id": f"a-{exercise_id}"}],
            "required_next_gate": PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE,
            "phase8_candidate_creation_authorized": False,
            "source_truth_authorized": False,
            "live_state_authorized": False,
            "memory_promotion_authorized": False,
            "retention_authorized": False,
            "governance_mutation_authorized": False,
            "execution_authorized": False,
        })
    reconstructions.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    return curriculum, practice, plan, reconstructions


def _grade(exercise_id: str, grade: str, *, critical_failure: bool = False) -> GradedAnswer:
    score = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}[grade]
    return GradedAnswer(
        exercise_id=exercise_id,
        answer=f"answer-{exercise_id}",
        grade=grade,
        score=score,
        correct=grade == "PASS",
        failure_codes=() if grade == "PASS" else ("conceptual_mismatch",),
        critical_failure=critical_failure,
        grader_note="fixture",
    )


def test_prepare_targeted_practice_binds_fresh_rows_and_source_grounded_weak_items(tmp_path: Path) -> None:
    curriculum, practice, plan, reconstructions = _write_inputs(tmp_path)

    prepared = prepare_targeted_practice(
        curriculum_dir=curriculum,
        practice_path=practice,
        remediation_plan_path=plan,
        reconstructions_path=reconstructions,
    )

    assert prepared.curriculum_id == CURRICULUM_ID
    assert prepared.level == 1
    assert len(prepared.exercises) == 4
    assert prepared.source_grounded_weak_items == 2
    assert prepared.critical_weakness_keys == {("benefits", "immutability")}
    assert not {item.exercise_id for item in prepared.exercises} & set(prepared.original_weak_ids)


def test_prepare_targeted_practice_rejects_tampered_practice_row(tmp_path: Path) -> None:
    curriculum, practice, plan, reconstructions = _write_inputs(tmp_path)
    rows = [json.loads(line) for line in practice.read_text(encoding="utf-8").splitlines()]
    rows[0]["question"] = "Tampered question?"
    practice.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    with pytest.raises(TargetedPyramidPracticeError, match="does not match validated curriculum"):
        prepare_targeted_practice(
            curriculum_dir=curriculum,
            practice_path=practice,
            remediation_plan_path=plan,
            reconstructions_path=reconstructions,
        )


def test_prepare_targeted_practice_requires_complete_source_grounded_coverage(tmp_path: Path) -> None:
    curriculum, practice, plan, reconstructions = _write_inputs(tmp_path)
    first = reconstructions.read_text(encoding="utf-8").splitlines()[0]
    reconstructions.write_text(first + "\n", encoding="utf-8")

    with pytest.raises(TargetedPyramidPracticeError, match="coverage does not match"):
        prepare_targeted_practice(
            curriculum_dir=curriculum,
            practice_path=practice,
            remediation_plan_path=plan,
            reconstructions_path=reconstructions,
        )


def test_verification_gate_requires_perfect_critical_weakness_even_when_overall_floor_is_met() -> None:
    exercises = tuple(item for item in _bank() if item.exercise_id.startswith("practice-"))
    prepared = PreparedTargetedPractice(
        curriculum_id=CURRICULUM_ID,
        level=1,
        exercises=exercises,
        weakness_critical_counts=(
            ("benefits", "immutability", 1),
            ("distributed_systems", "definition", 0),
        ),
        original_weak_ids=("weak-critical", "weak-normal"),
        source_grounded_weak_items=2,
    )
    grades = (
        _grade("practice-critical-1", "PASS"),
        _grade("practice-critical-2", "PARTIAL"),
        _grade("practice-normal-1", "PASS"),
        _grade("practice-normal-2", "PASS"),
    )

    report = evaluate_targeted_practice(prepared, grades)

    assert report.accuracy == 0.875
    assert report.required_accuracy == 0.85
    assert report.critical_weaknesses_passed is False
    assert report.practice_passed is False
    assert report.canonical_attempt_authorized is False
    assert report.next_gate == TARGETED_PRACTICE_FAIL_NEXT_GATE
    assert report.retention_authorized is False
    assert report.execution_authorized is False


def test_verification_gate_passes_only_to_new_canonical_attempt() -> None:
    exercises = tuple(item for item in _bank() if item.exercise_id.startswith("practice-"))
    prepared = PreparedTargetedPractice(
        curriculum_id=CURRICULUM_ID,
        level=1,
        exercises=exercises,
        weakness_critical_counts=(
            ("benefits", "immutability", 1),
            ("distributed_systems", "definition", 0),
        ),
        original_weak_ids=("weak-critical", "weak-normal"),
        source_grounded_weak_items=2,
    )
    grades = tuple(_grade(item.exercise_id, "PASS") for item in exercises)

    report = evaluate_targeted_practice(prepared, grades)

    assert report.practice_passed is True
    assert report.canonical_attempt_authorized is True
    assert report.next_gate == TARGETED_PRACTICE_PASS_NEXT_GATE
    assert report.memory_promotion_authorized is False
    assert report.governance_mutation_authorized is False


class _OneResponseModel:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.invoke_count = 0

    def invoke(self, messages: object) -> AIMessage:
        self.invoke_count += 1
        return AIMessage(content=json.dumps(self.payload))


class _FailIfInvokedModel:
    def invoke(self, messages: object) -> AIMessage:
        raise AssertionError("model should not be invoked when practice checkpoint is reusable")


def test_targeted_practice_uses_separate_restart_safe_checkpoints(tmp_path: Path) -> None:
    exercises = tuple(item for item in _bank() if item.exercise_id.startswith("practice-"))
    prepared = PreparedTargetedPractice(
        curriculum_id=CURRICULUM_ID,
        level=1,
        exercises=exercises,
        weakness_critical_counts=(
            ("benefits", "immutability", 1),
            ("distributed_systems", "definition", 0),
        ),
        original_weak_ids=("weak-critical", "weak-normal"),
        source_grounded_weak_items=2,
    )
    answers = _OneResponseModel({
        "answers": [
            {"exercise_id": item.exercise_id, "answer": f"answer-{item.exercise_id}"}
            for item in exercises
        ]
    })
    grader = _OneResponseModel({
        "grades": [
            {
                "exercise_id": item.exercise_id,
                "grade": "PASS",
                "failure_codes": [],
                "critical_failure": False,
                "grader_note": "ok",
            }
            for item in exercises
        ]
    })
    output = tmp_path / "practice-output"

    first = run_targeted_practice(
        prepared=prepared,
        answer_model=answers,
        grader_model=grader,
        output_dir=output,
        batch_size=4,
    )
    assert first.practice_passed is True
    assert answers.invoke_count == 1
    assert grader.invoke_count == 1
    assert (output / "checkpoints" / "level_01_batch_0001.json").is_file()
    assert (output / "practice_results.jsonl").is_file()
    assert (output / "practice_report.json").is_file()

    second = run_targeted_practice(
        prepared=prepared,
        answer_model=_FailIfInvokedModel(),
        grader_model=_FailIfInvokedModel(),
        output_dir=output,
        batch_size=4,
    )
    assert second.practice_passed is True
