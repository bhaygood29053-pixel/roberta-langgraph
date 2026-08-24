from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from roberta.learning.pyramid import Exercise, PYRAMID_CONTRACT
from roberta.learning.pyramid_critical_blocker_supplemental import (
    CRITICAL_BLOCKER_SUPPLEMENTAL_ID_PREFIX,
    MB4E_SOURCE_REF,
    build_critical_checkpoint_view,
    mb4e_immutability_critical_blocker_bank,
)
from roberta.learning.pyramid_exam import GRADING_SEMANTICS, GradedAnswer
from roberta.learning.pyramid_practice import PreparedTargetedPractice, evaluate_targeted_practice
from roberta.learning.pyramid_remediation import load_weak_items
from roberta.learning.pyramid_remediation_cli import main as remediation_main
from roberta.learning.pyramid_supplemental_practice import prepare_supplemental_targeted_practice


CURRICULUM_ID = "critical-blocker-fixture"


def _exercise(exercise_id: str, *, question: str = "What is practical immutability?") -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id=CURRICULUM_ID,
        level=1,
        concept="benefits",
        subconcept="immutability",
        question=question,
        expected_answer="Accepted history is extremely difficult, but not conceptually impossible, to alter.",
        source_refs=(MB4E_SOURCE_REF,),
        required_reasoning_points=("practical rather than absolute",),
        forbidden_inferences=("Do not claim absolute immutability.",),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
    )


def _write_curriculum(tmp_path: Path) -> Path:
    root = tmp_path / "curriculum"
    root.mkdir()
    exercises = (_exercise("q1"), _exercise("q2", question="Why is immutability useful?"))
    manifest = {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": CURRICULUM_ID,
        "title": "Critical blocker fixture",
        "source_type": "test",
        "approved_source_refs": [MB4E_SOURCE_REF],
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
                    "required_reasoning_points": list(item.required_reasoning_points),
                    "forbidden_inferences": list(item.forbidden_inferences),
                    "grading_rubric_id": item.grading_rubric_id,
                    "integrity_question": False,
                    "boss_question": False,
                    "requires_live_data": False,
                }
            )
            + "\n"
            for item in exercises
        ),
        encoding="utf-8",
    )
    return root


def _write_checkpoint_dir(
    root: Path,
    *,
    semantics: str = GRADING_SEMANTICS,
    include_noncritical_fail: bool = True,
) -> Path:
    root.mkdir()
    grades = [
        {
            "exercise_id": "q1",
            "answer": "It cannot be altered.",
            "grade": "FAIL",
            "score": 0.0,
            "correct": False,
            "failure_codes": ["factual_error"],
            "critical_failure": True,
            "grader_note": "absolute immutability",
        },
        {
            "exercise_id": "q2",
            "answer": "good",
            "grade": "PASS" if not include_noncritical_fail else "FAIL",
            "score": 1.0 if not include_noncritical_fail else 0.0,
            "correct": not include_noncritical_fail,
            "failure_codes": [] if not include_noncritical_fail else ["factual_error"],
            "critical_failure": False,
            "grader_note": "ordinary result",
        },
    ]
    (root / "level_01_batch_0001.json").write_text(
        json.dumps(
            {
                "checkpoint_schema": "roberta-pyramid-checkpoint/v3",
                "grading_semantics": semantics,
                "exercise_ids": ["q1", "q2"],
                "grades": grades,
            }
        ),
        encoding="utf-8",
    )
    return root


def _grade(exercise_id: str, grade: str) -> GradedAnswer:
    score = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}[grade]
    return GradedAnswer(
        exercise_id=exercise_id,
        answer=f"answer-{exercise_id}",
        grade=grade,
        score=score,
        correct=grade == "PASS",
        failure_codes=() if grade == "PASS" else ("factual_error",),
        critical_failure=False,
        grader_note="fixture",
    )


def test_critical_only_loading_is_explicit_and_requires_v3(tmp_path: Path) -> None:
    checkpoints = _write_checkpoint_dir(tmp_path / "v3")

    ordinary = load_weak_items(checkpoints)
    critical = load_weak_items(
        checkpoints,
        critical_only=True,
        required_grading_semantics=GRADING_SEMANTICS,
    )

    assert [item.exercise_id for item in ordinary] == ["q1", "q2"]
    assert [item.exercise_id for item in critical] == ["q1"]
    assert critical[0].critical_failure is True

    v2 = _write_checkpoint_dir(tmp_path / "v2", semantics="question-first-adjudication/v2")
    with pytest.raises(ValueError, match="grading semantics must equal"):
        load_weak_items(v2, critical_only=True, required_grading_semantics=GRADING_SEMANTICS)


def test_critical_checkpoint_view_filters_without_mutating_source(tmp_path: Path) -> None:
    source = _write_checkpoint_dir(tmp_path / "source")
    original = (source / "level_01_batch_0001.json").read_bytes()
    destination = tmp_path / "critical-view"

    manifest = build_critical_checkpoint_view(source_dir=source, output_dir=destination)
    derived = json.loads((destination / "level_01_batch_0001.json").read_text(encoding="utf-8"))

    assert [row["exercise_id"] for row in derived["grades"]] == ["q1"]
    assert derived["exercise_ids"] == ["q1"]
    assert manifest["critical_exercise_ids"] == ["q1"]
    assert (source / "level_01_batch_0001.json").read_bytes() == original


def test_critical_checkpoint_view_rejects_v2(tmp_path: Path) -> None:
    source = _write_checkpoint_dir(tmp_path / "source", semantics="question-first-adjudication/v2")
    with pytest.raises(RuntimeError, match="grading semantics must equal"):
        build_critical_checkpoint_view(source_dir=source, output_dir=tmp_path / "view")
    assert not (tmp_path / "view").exists()


def test_critical_blocker_remediation_emits_handoff_when_canonical_pool_is_exhausted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    curriculum = _write_curriculum(tmp_path)
    checkpoints = _write_checkpoint_dir(tmp_path / "checkpoints", include_noncritical_fail=False)
    output = tmp_path / "remediation"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pyramid-remediation",
            "--curriculum",
            str(curriculum),
            "--checkpoints",
            str(checkpoints),
            "--critical-blockers-only",
            "--output",
            str(output),
            "--practice-per-weakness",
            "1",
        ],
    )

    assert remediation_main() == 0
    stdout = capsys.readouterr().out
    plan = json.loads((output / "remediation_plan.json").read_text(encoding="utf-8"))

    assert plan["critical_blocker_mode"] is True
    assert plan["weak_item_count"] == 1
    assert plan["weakness_count"] == 1
    assert plan["canonical_practice_exhausted"] is True
    assert plan["supplemental_fallback_required"] is True
    assert plan["practice_question_count"] == 0
    assert plan["learning_handoff_count"] == 1
    assert "NEXT_GATE source_grounded_phase7_reconstruction_for_supplemental" in stdout
    assert "CANONICAL_ATTEMPT_AUTHORIZED false" in stdout


def test_fresh_second_immutability_bank_supports_ten_unseen_questions(tmp_path: Path) -> None:
    curriculum = _write_curriculum(tmp_path)
    full = _write_checkpoint_dir(tmp_path / "full", include_noncritical_fail=False)
    critical_view = tmp_path / "critical-view"
    build_critical_checkpoint_view(source_dir=full, output_dir=critical_view)
    reconstructions = tmp_path / "reconstructions.jsonl"
    reconstructions.write_text(json.dumps({"exercise_id": "q1"}) + "\n", encoding="utf-8")

    bank = mb4e_immutability_critical_blocker_bank(CURRICULUM_ID)
    assert len(bank) == 12
    assert len({item.exercise_id for item in bank}) == 12
    assert all(item.exercise_id.startswith(CRITICAL_BLOCKER_SUPPLEMENTAL_ID_PREFIX) for item in bank)
    assert all(item.source_refs == (MB4E_SOURCE_REF,) for item in bank)

    seen = tmp_path / "prior-supplemental"
    seen.mkdir()
    (seen / "level_01_batch_0001.json").write_text(
        json.dumps(
            {
                "grades": [
                    {"exercise_id": bank[0].exercise_id},
                    {"exercise_id": bank[1].exercise_id},
                ]
            }
        ),
        encoding="utf-8",
    )

    preparation = prepare_supplemental_targeted_practice(
        curriculum_dir=curriculum,
        checkpoint_dir=critical_view,
        reconstructions_path=reconstructions,
        exclude_checkpoint_dirs=(seen,),
        questions_per_weakness=10,
        seed="fresh-ten",
        supplemental_bank=bank,
    )

    selected = {item.exercise_id for item in preparation.prepared.exercises}
    assert len(selected) == 10
    assert bank[0].exercise_id not in selected
    assert bank[1].exercise_id not in selected
    assert preparation.current_weakness_keys == (("benefits", "immutability"),)
    assert preparation.prepared.critical_weakness_keys == {("benefits", "immutability")}


def test_critical_origin_ten_question_gate_requires_ten_of_ten() -> None:
    bank = mb4e_immutability_critical_blocker_bank(CURRICULUM_ID)[:10]
    prepared = PreparedTargetedPractice(
        curriculum_id=CURRICULUM_ID,
        level=1,
        exercises=bank,
        weakness_critical_counts=(("benefits", "immutability", 5),),
        original_weak_ids=("q1",),
        source_grounded_weak_items=1,
    )

    nine_pass = [_grade(item.exercise_id, "PASS") for item in bank]
    nine_pass[-1] = _grade(bank[-1].exercise_id, "PARTIAL")
    failed = evaluate_targeted_practice(prepared, nine_pass)
    assert failed.accuracy == 0.95
    assert failed.critical_weaknesses_passed is False
    assert failed.practice_passed is False
    assert failed.canonical_attempt_authorized is False

    perfect = evaluate_targeted_practice(
        prepared,
        [_grade(item.exercise_id, "PASS") for item in bank],
    )
    assert perfect.accuracy == 1.0
    assert perfect.critical_failures == 0
    assert perfect.critical_weaknesses_passed is True
    assert perfect.practice_passed is True
    assert perfect.canonical_attempt_authorized is True
    assert perfect.next_gate == "new_canonical_level_1_attempt"
    assert perfect.phase8_candidate_creation_authorized is False
    assert perfect.source_truth_authorized is False
    assert perfect.live_state_authorized is False
    assert perfect.memory_promotion_authorized is False
    assert perfect.retention_authorized is False
    assert perfect.governance_mutation_authorized is False
    assert perfect.execution_authorized is False
