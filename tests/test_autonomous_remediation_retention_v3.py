from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage

from roberta.learning.autonomous_remediation import (
    AUTONOMOUS_REMEDIATION_VERSION,
    CANDIDATE_REMEDIATION_MEMORY_CONTRACT,
    REMEDIATION_LANE_NAMESPACE,
    AutonomousRemediationError,
    CandidateRemediationAnswerModel,
    CandidateRemediationConcept,
    StageTransferLearnedConceptAnswerModel,
    _provisional_concepts,
    run_autonomous_remediation,
)
from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import GradedAnswer, summarize_exam
from roberta.learning.pyramid_learned_concepts import LearnedConcept


CURRICULUM_ID = "retention-v4-fixture"
LEVEL = 11


def _exercise() -> Exercise:
    return Exercise(
        exercise_id="RETENTION-V4-WEAK",
        curriculum_id=CURRICULUM_ID,
        level=LEVEL,
        concept="on_chain_analysis",
        subconcept="bounded_interpretation",
        question="Explain the bounded on-chain analysis principle.",
        expected_answer="On-chain observations must be interpreted within the cited evidence and must not invent live state.",
        source_refs=("mb4e-source", "stage11-target-01"),
        required_reasoning_points=(
            "Interpret the observation within cited evidence without inventing live state.",
        ),
        forbidden_inferences=("Do not invent current balances or execution authority.",),
        grading_rubric_id="RETENTION-V4-TEST",
    )


def _failed_outcome(exercise: Exercise):
    return summarize_exam(
        (exercise,),
        (
            GradedAnswer(
                exercise_id=exercise.exercise_id,
                answer="I do not know.",
                grade="FAIL",
                score=0.0,
                correct=False,
            ),
        ),
        canonical_exam=False,
    )


def _passing_outcome(exercises):
    grades = tuple(
        GradedAnswer(
            exercise_id=item.exercise_id,
            answer=item.expected_answer,
            grade="PASS",
            score=1.0,
            correct=True,
        )
        for item in exercises
    )
    return summarize_exam(exercises, grades, canonical_exam=False)


def _failing_outcome(exercises):
    grades = []
    for index, item in enumerate(exercises):
        grades.append(
            GradedAnswer(
                exercise_id=item.exercise_id,
                answer="Incomplete retention." if index == 0 else item.expected_answer,
                grade="FAIL" if index == 0 else "PASS",
                score=0.0 if index == 0 else 1.0,
                correct=index != 0,
            )
        )
    return summarize_exam(exercises, tuple(grades), canonical_exam=False)


def _provisional(exercise: Exercise) -> CandidateRemediationConcept:
    candidates = _provisional_concepts(
        curriculum_id=CURRICULUM_ID,
        level=LEVEL,
        weak=(exercise,),
    )
    assert len(candidates) == 1
    return candidates[0]


class CaptureModel:
    def __init__(self) -> None:
        self.payload = None

    def invoke(self, messages, *_args, **_kwargs):
        self.payload = json.loads(messages[-1].content)
        return SimpleNamespace(content="{}")


def test_candidate_retention_memory_is_unverified_and_contains_no_source_or_grading_material() -> None:
    exercise = _exercise()
    capture = CaptureModel()
    candidate = _provisional(exercise)
    assert isinstance(candidate, CandidateRemediationConcept)
    assert not isinstance(candidate, LearnedConcept)
    assert not hasattr(candidate, "to_mapping")
    wrapper = CandidateRemediationAnswerModel(capture, (candidate,))

    wrapper.invoke(
        [
            HumanMessage(
                content=json.dumps(
                    {
                        "instruction": "Answer independently.",
                        "exercises": [
                            {
                                "exercise_id": exercise.exercise_id,
                                "question": exercise.question,
                                "concept": exercise.concept,
                                "subconcept": exercise.subconcept,
                            }
                        ],
                    }
                )
            )
        ]
    )

    assert capture.payload is not None
    routed = capture.payload["exercises"][0]
    memory = routed["remediation_candidate_memory"]
    assert memory == {
        "contract": CANDIDATE_REMEDIATION_MEMORY_CONTRACT,
        "principle": exercise.expected_answer,
        "promotion_status": "candidate_unverified",
    }
    for prohibited in (
        "expected_answer",
        "reference_reasoning_points",
        "forbidden_inferences",
        "remediation_context",
        "source_evidence",
        "source_refs",
        "learned_concept_memory",
        "learned_concept_memories",
    ):
        assert prohibited not in routed
    instruction = capture.payload["instruction"]
    assert "unpromoted candidate lesson" in instruction
    assert "not source evidence" in instruction
    assert "verified durable memory" in instruction

    with pytest.raises(
        AutonomousRemediationError,
        match="prohibited grading/source/memory material",
    ):
        wrapper.invoke(
            [
                HumanMessage(
                    content=json.dumps(
                        {
                            "exercises": [
                                {
                                    "exercise_id": exercise.exercise_id,
                                    "question": exercise.question,
                                    "concept": exercise.concept,
                                    "subconcept": exercise.subconcept,
                                    "expected_answer": exercise.expected_answer,
                                }
                            ]
                        }
                    )
                )
            ]
        )


def test_bounded_retention_prompt_prevents_pretrained_fact_override() -> None:
    exercise = Exercise(
        exercise_id="RETENTION-V4-REGTEST",
        curriculum_id=CURRICULUM_ID,
        level=LEVEL,
        concept="bitcoin_node_modes",
        subconcept="regtest",
        question="Explain the validated regtest principle.",
        expected_answer=(
            "Regtest mode creates a local private blockchain where the user controls block "
            "generation for testing, and blocks require 100 confirmations before the reward can be used."
        ),
        source_refs=("mastering_blockchain_4e_2023", "AUTO-S11-93a84713e72fa5c6"),
    )
    capture = CaptureModel()
    wrapper = CandidateRemediationAnswerModel(
        capture,
        (_provisional(exercise),),
        bounded_to_candidate=True,
    )

    wrapper.invoke(
        [
            HumanMessage(
                content=json.dumps(
                    {
                        "instruction": "Answer independently.",
                        "exercises": [
                            {
                                "exercise_id": exercise.exercise_id,
                                "question": exercise.question,
                                "concept": exercise.concept,
                                "subconcept": exercise.subconcept,
                            }
                        ],
                    }
                )
            )
        ]
    )

    instruction = capture.payload["instruction"]
    assert "complete allowed lesson content" in instruction
    assert "without adding, correcting, replacing, or contradicting factual claims from prior knowledge" in instruction
    assert "do not introduce factual assertions that are not entailed by it" in instruction
    assert "does not authorize the candidate as source truth" in instruction
    routed = capture.payload["exercises"][0]
    assert routed["remediation_candidate_memory"]["principle"] == exercise.expected_answer
    assert routed["remediation_candidate_memory"]["promotion_status"] == "candidate_unverified"


def test_remediation_v4_uses_fresh_namespace_and_bounded_candidate_memory_for_retention(
    tmp_path, monkeypatch
) -> None:
    exercise = _exercise()
    failed = _failed_outcome(exercise)
    output_dir = tmp_path / "remediation"
    old_v2 = (
        output_dir
        / "lanes"
        / "stage-bound-boss-synthesis-v2"
        / "retention_checkpoints"
        / "level_11_batch_0001.json"
    )
    old_v2.parent.mkdir(parents=True)
    old_v2.write_text("immutable-v2-failure-evidence", encoding="utf-8")
    old_v3 = (
        output_dir
        / "lanes"
        / "stage-bound-boss-synthesis-v3"
        / "retention_checkpoints"
        / "level_11_batch_0001.json"
    )
    old_v3.parent.mkdir(parents=True)
    old_v3.write_text("immutable-v3-failure-evidence", encoding="utf-8")

    failed_checkpoints = tmp_path / "failed"
    failed_checkpoints.mkdir()
    (failed_checkpoints / "level_11_batch_0001.json").write_text(
        "failed-stage-11-evidence", encoding="utf-8"
    )
    learned_path = tmp_path / "learned.json"
    calls = []

    def passing_exam(*, exercises, answer_model, checkpoint_dir, **_kwargs):
        calls.append((Path(checkpoint_dir).name, answer_model, Path(checkpoint_dir)))
        return _passing_outcome(exercises)

    monkeypatch.setattr(
        "roberta.learning.autonomous_remediation.run_exam",
        passing_exam,
    )

    promoted = run_autonomous_remediation(
        curriculum_id=CURRICULUM_ID,
        level=LEVEL,
        bank=(exercise,),
        failed_outcome=failed,
        model=object(),
        output_dir=output_dir,
        failed_checkpoint_dir=failed_checkpoints,
        learned_concepts_path=learned_path,
        batch_size=10,
    )

    assert AUTONOMOUS_REMEDIATION_VERSION == "1.3.0"
    assert REMEDIATION_LANE_NAMESPACE == "stage-bound-boss-synthesis-v4"
    assert [name for name, _, _ in calls] == [
        "grounded_checkpoints",
        "retention_checkpoints",
        "transfer_checkpoints",
    ]
    assert isinstance(calls[0][1], CandidateRemediationAnswerModel)
    assert isinstance(calls[1][1], CandidateRemediationAnswerModel)
    assert isinstance(calls[2][1], StageTransferLearnedConceptAnswerModel)
    assert calls[0][1]._bounded_to_candidate is False
    assert calls[1][1]._bounded_to_candidate is True
    assert all("stage-bound-boss-synthesis-v4" in str(path) for _, _, path in calls)
    assert all("stage-bound-boss-synthesis-v3" not in str(path) for _, _, path in calls)
    assert all("stage-bound-boss-synthesis-v2" not in str(path) for _, _, path in calls)
    assert old_v2.read_text(encoding="utf-8") == "immutable-v2-failure-evidence"
    assert old_v3.read_text(encoding="utf-8") == "immutable-v3-failure-evidence"

    lane_root = output_dir / "lanes" / REMEDIATION_LANE_NAMESPACE
    report = json.loads((lane_root / "retention_report.json").read_text(encoding="utf-8"))
    manifest = json.loads((lane_root / "retention_manifest.json").read_text(encoding="utf-8"))
    promotion = json.loads((lane_root / "promotion.json").read_text(encoding="utf-8"))

    assert report["retention_mode"] == "closed-source-bounded-candidate-memory-v2"
    assert report["candidate_memory_injected"] is True
    assert report["raw_source_context_injected"] is False
    assert report["answer_grading_material_injected"] is False
    assert manifest["retention_mode"] == "closed-source-bounded-candidate-memory-v2"
    assert manifest["candidate_memory_injected_into_retention"] is True
    assert manifest["raw_source_context_injected_into_retention"] is False
    assert manifest["answer_grading_material_injected_into_retention"] is False
    assert promotion["checkpoint_namespace"] == REMEDIATION_LANE_NAMESPACE
    assert promotion["candidate_memory_retention_passed"] is True
    assert promotion["transfer_passed"] is True
    assert len(promoted) == 1
    assert learned_path.exists()


def test_failed_candidate_memory_retention_blocks_transfer_and_promotion(
    tmp_path, monkeypatch
) -> None:
    exercise = _exercise()
    failed = _failed_outcome(exercise)
    output_dir = tmp_path / "remediation"
    failed_checkpoints = tmp_path / "failed"
    failed_checkpoints.mkdir()
    (failed_checkpoints / "level_11_batch_0001.json").write_text(
        "failed-stage-11-evidence", encoding="utf-8"
    )
    learned_path = tmp_path / "learned.json"
    calls = []

    def retention_failure(*, exercises, answer_model, checkpoint_dir, **_kwargs):
        calls.append((Path(checkpoint_dir).name, answer_model))
        if Path(checkpoint_dir).name == "retention_checkpoints":
            return _failing_outcome(exercises)
        return _passing_outcome(exercises)

    monkeypatch.setattr(
        "roberta.learning.autonomous_remediation.run_exam",
        retention_failure,
    )

    with pytest.raises(
        AutonomousRemediationError,
        match="closed-source bounded candidate-memory remediation retention did not pass perfectly",
    ):
        run_autonomous_remediation(
            curriculum_id=CURRICULUM_ID,
            level=LEVEL,
            bank=(exercise,),
            failed_outcome=failed,
            model=object(),
            output_dir=output_dir,
            failed_checkpoint_dir=failed_checkpoints,
            learned_concepts_path=learned_path,
            batch_size=10,
        )

    assert [name for name, _ in calls] == [
        "grounded_checkpoints",
        "retention_checkpoints",
    ]
    assert isinstance(calls[1][1], CandidateRemediationAnswerModel)
    assert calls[1][1]._bounded_to_candidate is True
    assert not learned_path.exists()
    assert not (output_dir / "promotion.json").exists()
    assert not (
        output_dir
        / "lanes"
        / REMEDIATION_LANE_NAMESPACE
        / "promotion.json"
    ).exists()
