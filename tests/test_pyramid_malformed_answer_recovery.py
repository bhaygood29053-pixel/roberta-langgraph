from __future__ import annotations

import json

import pytest

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_answer_recovery import MissingAnswerRetryModel
from roberta.learning.pyramid_exam import PyramidExamError, answer_batch


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


class RawSequencedModel:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.payloads: list[dict[str, object]] = []

    def invoke(self, messages, *args, **kwargs):
        self.payloads.append(json.loads(messages[-1].content))
        return _Response(self.responses.pop(0))


def _exercise(index: int) -> Exercise:
    return Exercise(
        exercise_id=f"q{index}",
        curriculum_id="c1",
        level=2,
        concept="fundamentals",
        question=f"Question {index}?",
        expected_answer=f"answer:q{index}",
        source_refs=("source-1",),
    )


def _valid_response() -> str:
    return json.dumps(
        {
            "answers": [
                {"exercise_id": "q1", "answer": "first"},
                {"exercise_id": "q2", "answer": "second"},
            ]
        }
    )


def test_malformed_json_gets_one_full_batch_retry():
    model = RawSequencedModel(["{\"answers\":[", _valid_response()])

    answers = answer_batch(MissingAnswerRetryModel(model), (_exercise(1), _exercise(2)))

    assert answers == {"q1": "first", "q2": "second"}
    assert len(model.payloads) == 2
    assert [item["exercise_id"] for item in model.payloads[1]["exercises"]] == ["q1", "q2"]
    assert "structurally invalid" in str(model.payloads[1]["instruction"])


@pytest.mark.parametrize(
    "malformed",
    [
        {"answers": [{"exercise_id": "q1", "answer": "first"}, {"answer": "second"}]},
        {"answers": [{"exercise_id": "q1", "answer": "first"}, {"exercise_id": "q2"}]},
        {"answers": [{"exercise_id": "q1", "answer": "first"}, "not-an-object"]},
    ],
)
def test_malformed_answer_row_gets_one_full_batch_retry(malformed):
    model = RawSequencedModel([json.dumps(malformed), _valid_response()])

    answers = answer_batch(MissingAnswerRetryModel(model), (_exercise(1), _exercise(2)))

    assert answers == {"q1": "first", "q2": "second"}
    assert len(model.payloads) == 2
    assert [item["exercise_id"] for item in model.payloads[1]["exercises"]] == ["q1", "q2"]


def test_malformed_full_batch_retry_fails_closed_after_two_calls():
    model = RawSequencedModel(["{\"answers\":[", "{\"answers\":["])

    with pytest.raises(PyramidExamError, match="returned invalid JSON"):
        answer_batch(MissingAnswerRetryModel(model), (_exercise(1), _exercise(2)))

    assert len(model.payloads) == 2


def test_full_batch_retry_does_not_chain_into_a_third_missing_only_call():
    incomplete_retry = json.dumps({"answers": [{"exercise_id": "q1", "answer": "first"}]})
    model = RawSequencedModel(["{\"answers\":[", incomplete_retry])

    with pytest.raises(PyramidExamError, match=r"missing=\['q2'\]"):
        answer_batch(MissingAnswerRetryModel(model), (_exercise(1), _exercise(2)))

    assert len(model.payloads) == 2
