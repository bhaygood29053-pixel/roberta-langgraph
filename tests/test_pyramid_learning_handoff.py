from __future__ import annotations

from dataclasses import replace
import json
import sys

import pytest

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_learning_handoff import (
    PyramidLearningHandoffError,
    build_pyramid_learning_handoffs,
    validate_pyramid_learning_handoff,
    write_pyramid_learning_handoffs_jsonl,
)
from roberta.learning.pyramid_remediation import WeakItem
from roberta.learning.pyramid_remediation_cli import main as remediation_main


def _exercise(*, source_refs: tuple[str, ...] = ("book-source",)) -> Exercise:
    return Exercise(
        exercise_id="q-shared-ledger",
        curriculum_id="c1",
        level=1,
        concept="ledger_models",
        subconcept="shared_ledger",
        question="What does the source mean by a shared ledger?",
        expected_answer="reference answer must not become handoff source truth",
        source_refs=source_refs,
    )


def _weak(*, grade: str = "PARTIAL", critical: bool = False) -> WeakItem:
    return WeakItem(
        exercise_id="q-shared-ledger",
        grade=grade,
        score=0.5 if grade == "PARTIAL" else (0.0 if grade == "FAIL" else 1.0),
        critical_failure=critical,
        failure_codes=("conceptual_mismatch",) if grade != "PASS" else (),
        answer="A shared ledger is jointly maintained by multiple participants.",
        grader_note="The response is narrower than the source concept.",
        checkpoint_file="level_01_batch_0002.json",
        checkpoint_sha256="a" * 64,
        checkpoint_schema="roberta-pyramid-checkpoint/v3",
        grading_semantics="question-first-adjudication/v1",
    )


def test_partial_failure_creates_deterministic_source_grounding_handoff():
    exercise = _exercise()
    weak = _weak()

    first = build_pyramid_learning_handoffs(
        (exercise,),
        (weak,),
        curriculum_id="c1",
        approved_source_refs=("book-source",),
    )
    second = build_pyramid_learning_handoffs(
        (exercise,),
        (weak,),
        curriculum_id="c1",
        approved_source_refs=("book-source",),
    )

    assert first == second
    assert len(first) == 1
    handoff = first[0]
    assert handoff.exercise_id == exercise.exercise_id
    assert handoff.concept == "ledger_models"
    assert handoff.subconcept == "shared_ledger"
    assert handoff.source_refs == ("book-source",)
    assert handoff.grade == "PARTIAL"
    assert handoff.failure_codes == ("conceptual_mismatch",)
    assert handoff.required_next_gate == "source_grounded_phase7_reconstruction"
    assert handoff.source_grounding_required is True
    assert handoff.phase8_candidate_creation_authorized is False
    assert handoff.source_truth_authorized is False
    assert handoff.live_state_authorized is False
    assert handoff.memory_promotion_authorized is False
    assert handoff.retention_authorized is False
    assert handoff.governance_mutation_authorized is False
    assert handoff.execution_authorized is False

    payload = handoff.to_mapping()
    assert "expected_answer" not in payload
    assert payload["grader_note_role"] == "diagnostic_only_not_source_evidence"
    assert validate_pyramid_learning_handoff(handoff) == handoff


def test_pass_without_critical_failure_does_not_create_handoff():
    assert build_pyramid_learning_handoffs(
        (_exercise(),),
        (_weak(grade="PASS"),),
        curriculum_id="c1",
        approved_source_refs=("book-source",),
    ) == ()


def test_critical_result_is_preserved_even_if_grade_is_pass():
    handoffs = build_pyramid_learning_handoffs(
        (_exercise(),),
        (_weak(grade="PASS", critical=True),),
        curriculum_id="c1",
        approved_source_refs=("book-source",),
    )
    assert len(handoffs) == 1
    assert handoffs[0].critical_failure is True


def test_unknown_exercise_or_unapproved_source_fails_closed():
    with pytest.raises(PyramidLearningHandoffError, match="exercise id"):
        build_pyramid_learning_handoffs(
            (_exercise(),),
            (replace(_weak(), exercise_id="missing"),),
            curriculum_id="c1",
            approved_source_refs=("book-source",),
        )

    with pytest.raises(PyramidLearningHandoffError, match="approved source"):
        build_pyramid_learning_handoffs(
            (_exercise(source_refs=("not-approved",)),),
            (_weak(),),
            curriculum_id="c1",
            approved_source_refs=("book-source",),
        )


def test_checkpoint_or_answer_change_changes_handoff_identity():
    exercise = _exercise()
    baseline = build_pyramid_learning_handoffs(
        (exercise,),
        (_weak(),),
        curriculum_id="c1",
        approved_source_refs=("book-source",),
    )[0]
    checkpoint_changed = build_pyramid_learning_handoffs(
        (exercise,),
        (replace(_weak(), checkpoint_sha256="b" * 64),),
        curriculum_id="c1",
        approved_source_refs=("book-source",),
    )[0]
    answer_changed = build_pyramid_learning_handoffs(
        (exercise,),
        (replace(_weak(), answer="Different answer"),),
        curriculum_id="c1",
        approved_source_refs=("book-source",),
    )[0]

    assert baseline.handoff_id != checkpoint_changed.handoff_id
    assert baseline.handoff_id != answer_changed.handoff_id


def test_handoff_jsonl_writer_preserves_validated_payload(tmp_path):
    handoff = build_pyramid_learning_handoffs(
        (_exercise(),),
        (_weak(),),
        curriculum_id="c1",
        approved_source_refs=("book-source",),
    )[0]
    path = tmp_path / "learning_handoffs.jsonl"
    write_pyramid_learning_handoffs_jsonl(path, (handoff,))

    payload = json.loads(path.read_text(encoding="utf-8").strip())
    assert payload == handoff.to_mapping()
    assert payload["retention_authorized"] is False


def test_remediation_cli_writes_learning_handoff_for_shared_ledger_failure(tmp_path, monkeypatch):
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    checkpoint = checkpoints / "level_01_batch_0002.json"
    checkpoint.write_text(
        json.dumps(
            {
                "checkpoint_schema": "roberta-pyramid-checkpoint/v3",
                "grading_semantics": "question-first-adjudication/v1",
                "exercise_ids": ["mb4e-l1-smoke-013"],
                "grades": [
                    {
                        "exercise_id": "mb4e-l1-smoke-013",
                        "answer": "A shared ledger is jointly maintained by multiple participants.",
                        "grade": "PARTIAL",
                        "score": 0.5,
                        "correct": False,
                        "failure_codes": ["conceptual_mismatch"],
                        "critical_failure": False,
                        "grader_note": "The answer is narrower than the source concept.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "remediation"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "roberta-pyramid-remediate",
            "--curriculum",
            "curricula/mastering_blockchain_4e_2023_smoke_l1",
            "--checkpoints",
            str(checkpoints),
            "--output",
            str(output),
            "--practice-per-weakness",
            "1",
            "--seed",
            "handoff-test",
        ],
    )

    assert remediation_main() == 0
    handoff_path = output / "learning_handoffs.jsonl"
    assert handoff_path.exists()
    payload = json.loads(handoff_path.read_text(encoding="utf-8").strip())
    assert payload["exercise_id"] == "mb4e-l1-smoke-013"
    assert payload["source_refs"] == ["mastering_blockchain_4e_2023"]
    assert payload["required_next_gate"] == "source_grounded_phase7_reconstruction"
    assert payload["retention_authorized"] is False
