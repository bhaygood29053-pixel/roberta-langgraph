from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import pytest

from roberta.learning.pyramid import Exercise, PYRAMID_CONTRACT
from roberta.learning.pyramid_exam import GradedAnswer
from roberta.learning.pyramid_practice import TargetedPyramidPracticeError, evaluate_targeted_practice
from roberta.learning.pyramid_supplemental_practice import (
    MB4E_SOURCE_REF,
    SUPPLEMENTAL_ID_PREFIX,
    mb4e_level1_supplemental_bank,
    prepare_supplemental_targeted_practice,
    supplemental_manifest,
)


CURRICULUM_ID = "supplemental-fixture"
TARGETS = (
    ("architecture", "network_layer"),
    ("architecture", "p2p_layer"),
    ("benefits", "immutability"),
    ("types", "monolithic_polylithic"),
    ("types", "tokenized"),
)


def _canonical_exercise(exercise_id: str, concept: str, subconcept: str) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id=CURRICULUM_ID,
        level=1,
        concept=concept,
        subconcept=subconcept,
        question=f"Canonical question {exercise_id}?",
        expected_answer=f"Canonical answer {exercise_id}",
        source_refs=("source-a",),
        question_type="reasoning",
        grading_rubric_id="pyramid-question-first-v1",
    )


def _canonical_bank() -> tuple[Exercise, ...]:
    return tuple(
        _canonical_exercise(f"weak-{index}", concept, subconcept)
        for index, (concept, subconcept) in enumerate(TARGETS, start=1)
    )


def _write_curriculum(tmp_path: Path, *, overlap_id: str | None = None) -> Path:
    root = tmp_path / "curriculum"
    root.mkdir()
    bank = list(_canonical_bank())
    if overlap_id is not None:
        bank.append(_canonical_exercise(overlap_id, "architecture", "network_layer"))
    manifest = {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": CURRICULUM_ID,
        "title": "Supplemental practice fixture",
        "source_type": "test",
        "approved_source_refs": ["source-a"],
        "levels": [1],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "exercises.jsonl").write_text(
        "".join(
            json.dumps(
                {
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
                    "integrity_question": False,
                    "boss_question": False,
                    "requires_live_data": False,
                }
            )
            + "\n"
            for item in bank
        ),
        encoding="utf-8",
    )
    return root


def _write_checkpoints(tmp_path: Path) -> Path:
    root = tmp_path / "checkpoints"
    root.mkdir()
    grades = []
    for item in _canonical_bank():
        grades.append(
            {
                "exercise_id": item.exercise_id,
                "answer": "wrong",
                "grade": "FAIL",
                "score": 0.0,
                "correct": False,
                "failure_codes": ["conceptual_mismatch"],
                "critical_failure": False,
                "grader_note": "fixture",
            }
        )
    (root / "level_1_batch_0001.json").write_text(
        json.dumps(
            {
                "checkpoint_schema": "roberta-pyramid-checkpoint/v3",
                "grading_semantics": "question-first-adjudication/v2",
                "grades": grades,
            }
        ),
        encoding="utf-8",
    )
    return root


def _write_inherited_plan(tmp_path: Path) -> Path:
    path = tmp_path / "prior-plan.json"
    path.write_text(
        json.dumps(
            {
                "curriculum_id": CURRICULUM_ID,
                "weakness_count": 1,
                "weaknesses": [
                    {
                        "concept": "benefits",
                        "subconcept": "immutability",
                        "critical_count": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_reconstructions(tmp_path: Path) -> Path:
    path = tmp_path / "reconstructions.jsonl"
    path.write_text(
        "".join(json.dumps({"exercise_id": item.exercise_id}) + "\n" for item in _canonical_bank()),
        encoding="utf-8",
    )
    return path


def _supplemental_bank(*, overlap: bool = False, omit: tuple[str, str] | None = None) -> tuple[Exercise, ...]:
    bank = []
    for index, (concept, subconcept) in enumerate(TARGETS, start=1):
        if omit == (concept, subconcept):
            continue
        exercise_id = f"SUP-{index}"
        if overlap and (concept, subconcept) == ("architecture", "network_layer"):
            exercise_id = "weak-1"
        bank.append(
            Exercise(
                exercise_id=exercise_id,
                curriculum_id=CURRICULUM_ID,
                level=1,
                concept=concept,
                subconcept=subconcept,
                question=f"Supplemental question for {concept}/{subconcept}?",
                expected_answer=f"Supplemental answer for {concept}/{subconcept}",
                source_refs=("source-a",),
                question_type="supplemental_reasoning",
                grading_rubric_id="pyramid-question-first-v1",
            )
        )
    return tuple(bank)


def _prepare(tmp_path: Path, *, bank: tuple[Exercise, ...] | None = None):
    curriculum = _write_curriculum(tmp_path)
    checkpoints = _write_checkpoints(tmp_path)
    inherited = _write_inherited_plan(tmp_path)
    reconstructions = _write_reconstructions(tmp_path)
    return prepare_supplemental_targeted_practice(
        curriculum_dir=curriculum,
        checkpoint_dir=checkpoints,
        reconstructions_path=reconstructions,
        inherited_remediation_plan_paths=(inherited,),
        questions_per_weakness=1,
        seed="fixture",
        supplemental_bank=bank or _supplemental_bank(),
    )


def _grade(exercise_id: str, grade: str) -> GradedAnswer:
    score = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}[grade]
    return GradedAnswer(
        exercise_id=exercise_id,
        answer=f"answer-{exercise_id}",
        grade=grade,
        score=score,
        correct=grade == "PASS",
        failure_codes=() if grade == "PASS" else ("conceptual_mismatch",),
        critical_failure=False,
        grader_note="fixture",
    )


def test_mb4e_supplemental_bank_is_five_by_five_and_noncanonical_in_shape() -> None:
    bank = mb4e_level1_supplemental_bank("mastering_blockchain_4e_2023_book01")
    counts = Counter((item.concept, item.subconcept) for item in bank)

    assert len(bank) == 25
    assert counts == Counter({key: 5 for key in TARGETS})
    assert len({item.exercise_id for item in bank}) == 25
    assert all(item.exercise_id.startswith(SUPPLEMENTAL_ID_PREFIX) for item in bank)
    assert all(item.source_refs == (MB4E_SOURCE_REF,) for item in bank)
    assert all(not item.integrity_question and not item.boss_question for item in bank)
    assert all(not item.requires_live_data for item in bank)


def test_prepare_supplemental_practice_inherits_critical_origin_without_canonical_overlap(tmp_path: Path) -> None:
    preparation = _prepare(tmp_path)
    prepared = preparation.prepared

    assert len(prepared.exercises) == 5
    assert {(item.concept, item.subconcept) for item in prepared.exercises} == set(TARGETS)
    assert prepared.critical_weakness_keys == {("benefits", "immutability")}
    assert preparation.canonical_bank_overlap is False
    assert not {item.exercise_id for item in prepared.exercises} & {item.exercise_id for item in _canonical_bank()}
    assert set(preparation.current_weak_ids) == {item.exercise_id for item in _canonical_bank()}


def test_supplemental_practice_fails_closed_on_canonical_id_overlap(tmp_path: Path) -> None:
    curriculum = _write_curriculum(tmp_path)
    checkpoints = _write_checkpoints(tmp_path)
    inherited = _write_inherited_plan(tmp_path)
    reconstructions = _write_reconstructions(tmp_path)

    with pytest.raises(TargetedPyramidPracticeError, match="overlap canonical curriculum"):
        prepare_supplemental_targeted_practice(
            curriculum_dir=curriculum,
            checkpoint_dir=checkpoints,
            reconstructions_path=reconstructions,
            inherited_remediation_plan_paths=(inherited,),
            questions_per_weakness=1,
            supplemental_bank=_supplemental_bank(overlap=True),
        )


def test_supplemental_practice_fails_closed_when_active_weakness_has_no_fresh_bank_question(tmp_path: Path) -> None:
    curriculum = _write_curriculum(tmp_path)
    checkpoints = _write_checkpoints(tmp_path)
    inherited = _write_inherited_plan(tmp_path)
    reconstructions = _write_reconstructions(tmp_path)

    with pytest.raises(TargetedPyramidPracticeError, match="does not contain enough fresh questions"):
        prepare_supplemental_targeted_practice(
            curriculum_dir=curriculum,
            checkpoint_dir=checkpoints,
            reconstructions_path=reconstructions,
            inherited_remediation_plan_paths=(inherited,),
            questions_per_weakness=1,
            supplemental_bank=_supplemental_bank(omit=("types", "tokenized")),
        )


def test_inherited_critical_supplemental_group_requires_perfect_pass_even_above_85_percent(tmp_path: Path) -> None:
    preparation = _prepare(tmp_path)
    prepared = preparation.prepared
    grades = []
    for item in prepared.exercises:
        grade = "PARTIAL" if (item.concept, item.subconcept) == ("benefits", "immutability") else "PASS"
        grades.append(_grade(item.exercise_id, grade))

    report = evaluate_targeted_practice(prepared, grades)

    assert report.accuracy == 0.9
    assert report.critical_weaknesses_passed is False
    assert report.all_weaknesses_passed is False
    assert report.practice_passed is False
    assert report.canonical_attempt_authorized is False


def test_supplemental_manifest_denies_canonical_ledger_and_all_authority(tmp_path: Path) -> None:
    preparation = _prepare(tmp_path)
    payload = supplemental_manifest(preparation, checkpoint_binding="a" * 64)

    assert payload["canonical_bank_overlap"] is False
    assert payload["canonical_exam"] is False
    assert payload["ledger_mutation_authorized"] is False
    assert payload["phase8_candidate_creation_authorized"] is False
    assert payload["source_truth_authorized"] is False
    assert payload["live_state_authorized"] is False
    assert payload["memory_promotion_authorized"] is False
    assert payload["retention_authorized"] is False
    assert payload["governance_mutation_authorized"] is False
    assert payload["execution_authorized"] is False
