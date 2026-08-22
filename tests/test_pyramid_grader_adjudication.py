from __future__ import annotations

import json

import pytest

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import (
    GRADING_SEMANTICS,
    PyramidExamError,
    _question_explicitly_requests_multiple_elements,
    grade_batch,
    run_exam,
)


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


def _smoke_exercise(
    exercise_id: str,
    *,
    question: str,
    expected_answer: str,
    reasoning_points: tuple[str, ...],
    subconcept: str,
) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id="mastering_blockchain_4e_2023_smoke_l1",
        level=1,
        concept="ledger_models",
        subconcept=subconcept,
        question=question,
        expected_answer=expected_answer,
        source_refs=("mastering_blockchain_4e_2023",),
        question_type="definition",
        difficulty=2,
        required_reasoning_points=reasoning_points,
        grading_rubric_id="pyramid-question-first-v1",
    )


def test_question_first_adjudication_fixes_reference_anchoring_without_erasing_concept_mismatch():
    exercises = (
        _smoke_exercise(
            "mb4e-l1-smoke-013",
            question="What does the source mean by a shared ledger?",
            expected_answer=(
                "It is a generic shared application or database used by a public community or consortium; "
                "blockchains fall within this broad category."
            ),
            reasoning_points=(
                "generic shared database/application",
                "can be shared by public or consortium",
            ),
            subconcept="shared_ledger",
        ),
        _smoke_exercise(
            "mb4e-l1-smoke-016",
            question="What characterizes a permissioned ledger?",
            expected_answer=(
                "Participants and verifiers are known or preselected, access is controlled, and an agreement "
                "protocol can maintain the shared state without requiring open mining."
            ),
            reasoning_points=(
                "known/preselected participants or verifiers",
                "regulated access/agreement protocol",
                "mining is not inherently required",
            ),
            subconcept="permissioned_ledger",
        ),
    )
    answers = {
        "mb4e-l1-smoke-013": (
            "A shared ledger is a distributed, append-only record of transactions that is shared across multiple "
            "participants, each holding a copy, and updated through consensus."
        ),
        "mb4e-l1-smoke-016": (
            "A permissioned ledger restricts participation to known, authorized entities, with controlled access "
            "to read/write and consensus."
        ),
    }

    class AnchoringThenAdjudicatingModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            if "initial_grade" not in payload["items"][0]:
                return _Response(json.dumps({
                    "grades": [
                        {
                            "exercise_id": "mb4e-l1-smoke-013",
                            "grade": "PARTIAL",
                            "failure_codes": ["incomplete_reasoning"],
                            "critical_failure": False,
                            "grader_note": (
                                "Provides a standard definition of a shared ledger but misses the source's emphasis "
                                "that it is a generic shared application/database."
                            ),
                        },
                        {
                            "exercise_id": "mb4e-l1-smoke-016",
                            "grade": "PARTIAL",
                            "failure_codes": ["incomplete_reasoning"],
                            "critical_failure": False,
                            "grader_note": (
                                "Correctly identifies restricted access and known authorized entities, but omits "
                                "the source's point that open mining is not required."
                            ),
                        },
                    ]
                }))

            assert all(
                item["question_explicitly_requests_multiple_elements"] is False
                for item in payload["items"]
            )
            return _Response(json.dumps({
                "grades": [
                    {
                        "exercise_id": "mb4e-l1-smoke-013",
                        "grade": "PARTIAL",
                        "failure_codes": ["conceptual_mismatch"],
                        "critical_failure": False,
                        "grader_note": "The answer substitutes a narrower DLT/blockchain-style concept.",
                    },
                    {
                        "exercise_id": "mb4e-l1-smoke-016",
                        "grade": "PASS",
                        "failure_codes": [],
                        "critical_failure": False,
                        "grader_note": "The question is substantively answered; open mining was reference-only detail.",
                    },
                ]
            }))

    model = AnchoringThenAdjudicatingModel()
    grades = grade_batch(model, exercises, answers)

    assert model.calls == 2
    assert grades[0].grade == "PARTIAL"
    assert grades[0].failure_codes == ("conceptual_mismatch",)
    assert grades[1].grade == "PASS"
    assert grades[1].failure_codes == ()


def test_question_first_adjudication_fails_closed_if_single_part_incomplete_reasoning_survives():
    exercise = _smoke_exercise(
        "mb4e-l1-smoke-016",
        question="What characterizes a permissioned ledger?",
        expected_answer="Known participants, controlled access, and no requirement for open mining.",
        reasoning_points=("known participants", "controlled access", "open mining not required"),
        subconcept="permissioned_ledger",
    )
    answers = {
        exercise.exercise_id: "A permissioned ledger restricts participation to known authorized entities."
    }

    class StubbornAnchoringModel:
        def invoke(self, messages):
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            return _Response(json.dumps({
                "grades": [{
                    "exercise_id": item["exercise_id"],
                    "grade": "PARTIAL",
                    "failure_codes": ["incomplete_reasoning"],
                    "critical_failure": False,
                    "grader_note": "Still demanding a reference-only detail.",
                }]
            }))

    with pytest.raises(PyramidExamError, match="does not explicitly request multiple elements"):
        grade_batch(StubbornAnchoringModel(), (exercise,), answers)


def test_follow_up_explain_is_an_explicit_multi_part_question():
    assert _question_explicitly_requests_multiple_elements(
        "Can a permissioned blockchain be public according to the source? Explain."
    ) is True


def test_independent_failure_codes_are_not_sent_to_omission_adjudicator():
    exercise = _smoke_exercise(
        "q-mixed",
        question="Explain two properties of a permissioned ledger.",
        expected_answer="Known participants and controlled access.",
        reasoning_points=("known participants", "controlled access"),
        subconcept="permissioned_ledger",
    )
    answers = {exercise.exercise_id: "It is open to everyone."}

    class MixedFailureModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            if self.calls > 1:
                raise AssertionError("mixed independent failures must not be adjudicated")
            return _Response(json.dumps({
                "grades": [{
                    "exercise_id": exercise.exercise_id,
                    "grade": "FAIL",
                    "failure_codes": ["factual_error", "incomplete_reasoning"],
                    "critical_failure": False,
                    "grader_note": "Wrong access model and incomplete response.",
                }]
            }))

    model = MixedFailureModel()
    grades = grade_batch(model, (exercise,), answers)

    assert model.calls == 1
    assert grades[0].grade == "FAIL"
    assert grades[0].failure_codes == ("factual_error", "incomplete_reasoning")


def test_current_schema_checkpoint_without_new_grading_semantics_is_regraded(tmp_path):
    exercises = (
        Exercise(
            exercise_id="q1",
            curriculum_id="c1",
            level=1,
            concept="fundamentals",
            question="Question 1?",
            expected_answer="answer:q1",
            source_refs=("source-1",),
        ),
        Exercise(
            exercise_id="q2",
            curriculum_id="c1",
            level=1,
            concept="fundamentals",
            question="Question 2?",
            expected_answer="answer:q2",
            source_refs=("source-1",),
            boss_question=True,
        ),
    )
    checkpoint = tmp_path / "level_01_batch_0001.json"
    checkpoint.write_text(json.dumps({
        "checkpoint_schema": "roberta-pyramid-checkpoint/v3",
        "exercise_ids": ["q1", "q2"],
        "grades": [
            {
                "exercise_id": "q1",
                "answer": "stale",
                "grade": "FAIL",
                "score": 0.0,
                "correct": False,
                "failure_codes": ["incomplete_reasoning"],
                "critical_failure": False,
                "grader_note": "old grading semantics",
            },
            {
                "exercise_id": "q2",
                "answer": "stale",
                "grade": "FAIL",
                "score": 0.0,
                "correct": False,
                "failure_codes": ["incomplete_reasoning"],
                "critical_failure": False,
                "grader_note": "old grading semantics",
            },
        ],
    }), encoding="utf-8")

    class PassingModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            if "exercises" in payload:
                return _Response(json.dumps({
                    "answers": [
                        {"exercise_id": item["exercise_id"], "answer": f"answer:{item['exercise_id']}"}
                        for item in payload["exercises"]
                    ]
                }))
            return _Response(json.dumps({
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
            }))

    model = PassingModel()
    outcome = run_exam(
        exercises=exercises,
        answer_model=model,
        grader_model=model,
        batch_size=2,
        checkpoint_dir=tmp_path,
        canonical_exam=False,
    )

    assert model.calls == 2
    assert outcome.level_result.accuracy == 1.0
    rewritten = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert rewritten["checkpoint_schema"] == "roberta-pyramid-checkpoint/v3"
    assert rewritten["grading_semantics"] == GRADING_SEMANTICS
