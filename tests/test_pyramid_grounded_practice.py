from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
import pytest

from roberta.learning.pyramid import Exercise, PYRAMID_CONTRACT
from roberta.learning.pyramid_exam import answer_batch
from roberta.learning.pyramid_grounded_practice import (
    GROUNDED_PRACTICE_CHECKPOINT_NAMESPACE,
    GROUNDED_PRACTICE_CONTEXT_CONTRACT,
    GroundedPracticeAnswerModel,
    GroundedPracticeContext,
    load_grounded_practice_contexts,
    run_grounded_targeted_practice,
)
from roberta.learning.pyramid_practice import (
    PreparedTargetedPractice,
    TargetedPyramidPracticeError,
)
from roberta.learning.pyramid_source_reconstruction import (
    PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT,
    PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE,
    PYRAMID_SOURCE_RECONSTRUCTION_VERSION,
)


CURRICULUM_ID = "grounded-practice-fixture"


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
        _exercise("weak-1", "benefits", "immutability"),
        _exercise("fresh-1", "benefits", "immutability"),
    )


def _write_curriculum(tmp_path: Path) -> Path:
    root = tmp_path / "curriculum"
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_contract": "roberta-pyramid-manifest/v1",
                "curriculum_contract": PYRAMID_CONTRACT,
                "curriculum_id": CURRICULUM_ID,
                "title": "Grounded targeted-practice fixture",
                "source_type": "test",
                "approved_source_refs": ["source-a"],
                "levels": [1],
            }
        ),
        encoding="utf-8",
    )
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
                    "integrity_question": item.integrity_question,
                    "boss_question": item.boss_question,
                    "requires_live_data": item.requires_live_data,
                }
            )
            + "\n"
            for item in _bank()
        ),
        encoding="utf-8",
    )
    return root


def _prepared() -> PreparedTargetedPractice:
    fresh = _bank()[1]
    return PreparedTargetedPractice(
        curriculum_id=CURRICULUM_ID,
        level=1,
        exercises=(fresh,),
        weakness_critical_counts=(("benefits", "immutability", 1),),
        original_weak_ids=("weak-1",),
        source_grounded_weak_items=1,
    )


def _write_reconstruction(tmp_path: Path, *, text: str = "Source evidence about immutability.") -> Path:
    weak = _bank()[0]
    path = tmp_path / "reconstructions.jsonl"
    row = {
        "reconstruction_contract": PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT,
        "reconstruction_version": PYRAMID_SOURCE_RECONSTRUCTION_VERSION,
        "curriculum_id": CURRICULUM_ID,
        "exercise_id": weak.exercise_id,
        "level": weak.level,
        "concept": weak.concept,
        "subconcept": weak.subconcept,
        "question": weak.question,
        "source_grounded": True,
        "evidence_packet_status": "ok",
        "evidence_anchors": [
            {
                "anchor_id": "E1",
                "text": text,
                "fusion_rank": 1,
            }
        ],
        "required_next_gate": PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE,
        "phase8_candidate_creation_authorized": False,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "retention_authorized": False,
        "governance_mutation_authorized": False,
        "execution_authorized": False,
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    return path


def test_loader_rebinds_source_evidence_to_original_curriculum_weakness(tmp_path: Path) -> None:
    curriculum = _write_curriculum(tmp_path)
    reconstructions = _write_reconstruction(tmp_path)

    contexts = load_grounded_practice_contexts(
        curriculum_dir=curriculum,
        reconstructions_path=reconstructions,
        prepared=_prepared(),
    )

    assert len(contexts) == 1
    assert contexts[0].key == ("benefits", "immutability")
    assert contexts[0].anchors == (("E1", "Source evidence about immutability."),)


def test_loader_rejects_reconstruction_without_source_text(tmp_path: Path) -> None:
    curriculum = _write_curriculum(tmp_path)
    reconstructions = _write_reconstruction(tmp_path, text="")

    with pytest.raises(TargetedPyramidPracticeError, match="evidence text is missing"):
        load_grounded_practice_contexts(
            curriculum_dir=curriculum,
            reconstructions_path=reconstructions,
            prepared=_prepared(),
        )


class _CaptureAnswerModel:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def invoke(self, messages: object, *args: object, **kwargs: object) -> AIMessage:
        payload = json.loads(messages[-1].content)
        self.payloads.append(payload)
        return AIMessage(
            content=json.dumps(
                {
                    "answers": [
                        {
                            "exercise_id": item["exercise_id"],
                            "answer": "Grounded answer",
                        }
                        for item in payload["exercises"]
                    ]
                }
            )
        )


class _PassGraderModel:
    def invoke(self, messages: object, *args: object, **kwargs: object) -> AIMessage:
        payload = json.loads(messages[-1].content)
        return AIMessage(
            content=json.dumps(
                {
                    "grades": [
                        {
                            "exercise_id": item["exercise_id"],
                            "grade": "PASS",
                            "failure_codes": [],
                            "critical_failure": False,
                            "grader_note": "ok",
                        }
                        for item in payload["items"]
                    ]
                }
            )
        )


def test_answer_adapter_injects_matching_source_evidence_without_grading_reference() -> None:
    capture = _CaptureAnswerModel()
    context = GroundedPracticeContext(
        concept="benefits",
        subconcept="immutability",
        anchors=(("E1", "Canonical source excerpt."),),
    )
    adapter = GroundedPracticeAnswerModel(capture, (context,))
    request = {
        "instruction": "Answer independently.",
        "exercises": [
            {
                "exercise_id": "fresh-1",
                "question": "Fresh transfer question?",
                "concept": "benefits",
                "subconcept": "immutability",
            }
        ],
    }

    adapter.invoke([HumanMessage(content=json.dumps(request))])

    exercise_payload = capture.payloads[0]["exercises"][0]
    remediation = exercise_payload["remediation_context"]
    assert remediation["contract"] == GROUNDED_PRACTICE_CONTEXT_CONTRACT
    assert remediation["source_evidence"] == [
        {"anchor_id": "E1", "text": "Canonical source excerpt."}
    ]
    assert "expected_answer" not in exercise_payload
    assert "reference_reasoning_points" not in exercise_payload


def test_answer_adapter_fails_closed_without_matching_weakness_context() -> None:
    adapter = GroundedPracticeAnswerModel(_CaptureAnswerModel(), ())
    request = {
        "instruction": "Answer independently.",
        "exercises": [
            {
                "exercise_id": "fresh-1",
                "question": "Fresh transfer question?",
                "concept": "benefits",
                "subconcept": "immutability",
            }
        ],
    }

    with pytest.raises(TargetedPyramidPracticeError, match="no source-grounded remediation context"):
        adapter.invoke([HumanMessage(content=json.dumps(request))])


def test_grounded_targeted_practice_uses_new_checkpoint_namespace(tmp_path: Path) -> None:
    output = tmp_path / "practice"
    legacy = output / "checkpoints"
    legacy.mkdir(parents=True)
    (legacy / "level_01_batch_0001.json").write_text("legacy-unconditioned", encoding="utf-8")
    context = GroundedPracticeContext(
        concept="benefits",
        subconcept="immutability",
        anchors=(("E1", "Canonical source excerpt."),),
    )

    report = run_grounded_targeted_practice(
        prepared=_prepared(),
        contexts=(context,),
        answer_model=_CaptureAnswerModel(),
        grader_model=_PassGraderModel(),
        output_dir=output,
        batch_size=1,
    )

    assert report.practice_passed is True
    assert (output / GROUNDED_PRACTICE_CHECKPOINT_NAMESPACE / "level_01_batch_0001.json").is_file()
    assert (legacy / "level_01_batch_0001.json").read_text(encoding="utf-8") == "legacy-unconditioned"


def test_canonical_answer_payload_remains_closed_book() -> None:
    exercise = _bank()[1]
    capture = _CaptureAnswerModel()

    answer_batch(capture, (exercise,))

    payload = capture.payloads[0]
    assert "remediation_context" not in payload["exercises"][0]
    assert "expected_answer" not in payload["exercises"][0]
