from __future__ import annotations

import json

import pytest

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import PyramidExamError, grade_batch


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


def _exercise(exercise_id: str, *, question: str) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id="mastering_blockchain_4e_2023_book01",
        level=1,
        concept="fundamentals",
        subconcept="calibration_recovery",
        question=question,
        expected_answer="A substantively correct answer to the question.",
        source_refs=("MB4E-TEST-SOURCE",),
        required_reasoning_points=("reference-only detail",),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
    )


def _grade_row(exercise_id: str, grade: str, codes: list[str], note: str, *, critical: bool = False) -> dict[str, object]:
    return {
        "exercise_id": exercise_id,
        "grade": grade,
        "failure_codes": codes,
        "critical_failure": critical,
        "grader_note": note,
    }


def test_single_part_invalid_incomplete_reasoning_gets_one_corrective_adjudication_to_pass() -> None:
    exercise = _exercise("MB4E-L01-00928", question="What characterizes this blockchain property?")
    answers = {exercise.exercise_id: "A substantively correct characterization."}

    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls == 1:
                return _Response(json.dumps({"grades": [
                    _grade_row(item["exercise_id"], "PARTIAL", ["incomplete_reasoning"], "Initial anchoring.")
                ]}))
            if self.calls == 2:
                assert item["question_explicitly_requests_multiple_elements"] is False
                return _Response(json.dumps({"grades": [
                    _grade_row(item["exercise_id"], "PARTIAL", ["incomplete_reasoning"], "Invalid second-pass code.")
                ]}))
            assert self.calls == 3
            assert payload["correction_attempt"] == 1
            assert item["question_explicitly_requests_multiple_elements"] is False
            assert "MUST NOT return incomplete_reasoning" in payload["instruction"]
            return _Response(json.dumps({"grades": [
                _grade_row(item["exercise_id"], "PASS", [], "Question is substantively answered.")
            ]}))

    model = Model()
    grades = grade_batch(model, (exercise,), answers)

    assert model.calls == 3
    assert grades[0].grade == "PASS"
    assert grades[0].failure_codes == ()


def test_corrective_adjudication_can_keep_genuine_defect_with_allowed_failure_code() -> None:
    exercise = _exercise("q-genuine", question="What characterizes this blockchain property?")
    answers = {exercise.exercise_id: "A related but materially narrower concept."}

    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls < 3:
                return _Response(json.dumps({"grades": [
                    _grade_row(item["exercise_id"], "PARTIAL", ["incomplete_reasoning"], "Invalid omission framing.")
                ]}))
            return _Response(json.dumps({"grades": [
                _grade_row(item["exercise_id"], "PARTIAL", ["conceptual_mismatch"], "Answer is materially too narrow.")
            ]}))

    model = Model()
    grades = grade_batch(model, (exercise,), answers)

    assert model.calls == 3
    assert grades[0].grade == "PARTIAL"
    assert grades[0].failure_codes == ("conceptual_mismatch",)


def test_corrective_adjudication_fails_closed_if_invalid_code_survives_retry() -> None:
    exercise = _exercise("q-stubborn", question="What characterizes this blockchain property?")
    answers = {exercise.exercise_id: "A concise answer."}

    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            return _Response(json.dumps({"grades": [
                _grade_row(item["exercise_id"], "PARTIAL", ["incomplete_reasoning"], "Still invalid.")
            ]}))

    model = Model()
    with pytest.raises(PyramidExamError, match="after corrective adjudication"):
        grade_batch(model, (exercise,), answers)

    assert model.calls == 3


def test_multi_part_question_can_retain_genuine_incomplete_reasoning_without_correction() -> None:
    exercise = _exercise("q-multi", question="Name two properties and explain why they matter.")
    answers = {exercise.exercise_id: "Only the first property."}

    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            if self.calls > 2:
                raise AssertionError("multi-part incomplete_reasoning must not trigger corrective adjudication")
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            return _Response(json.dumps({"grades": [
                _grade_row(item["exercise_id"], "PARTIAL", ["incomplete_reasoning"], "Second requested element is absent.")
            ]}))

    model = Model()
    grades = grade_batch(model, (exercise,), answers)

    assert model.calls == 2
    assert grades[0].grade == "PARTIAL"
    assert grades[0].failure_codes == ("incomplete_reasoning",)


def test_adjudicator_critical_failure_still_fails_closed_without_corrective_retry() -> None:
    exercise = _exercise("q-critical", question="What characterizes this blockchain property?")
    answers = {exercise.exercise_id: "A concise answer."}

    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls == 1:
                return _Response(json.dumps({"grades": [
                    _grade_row(item["exercise_id"], "PARTIAL", ["incomplete_reasoning"], "Send to adjudication.")
                ]}))
            if self.calls > 2:
                raise AssertionError("critical failure must fail closed before corrective retry")
            return _Response(json.dumps({"grades": [
                _grade_row(item["exercise_id"], "FAIL", ["hallucinated_fact"], "Critical forbidden fabrication.", critical=True)
            ]}))

    model = Model()
    with pytest.raises(PyramidExamError, match="cannot introduce a critical failure"):
        grade_batch(model, (exercise,), answers)

    assert model.calls == 2
