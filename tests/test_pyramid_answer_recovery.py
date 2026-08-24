from __future__ import annotations

import json

import pytest

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_answer_recovery import MissingAnswerRetryModel
from roberta.learning.pyramid_exam import PyramidExamError, answer_batch


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


class SequencedModel:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = list(responses)
        self.payloads: list[dict[str, object]] = []

    def invoke(self, messages, *args, **kwargs):
        self.payloads.append(json.loads(messages[-1].content))
        return _Response(json.dumps(self.responses.pop(0)))


def _exercise(index: int) -> Exercise:
    return Exercise(
        exercise_id=f"q{index}",
        curriculum_id="c1",
        level=1,
        concept="fundamentals",
        question=f"Question {index}?",
        expected_answer=f"answer:q{index}",
        source_refs=("source-1",),
    )


def test_missing_answer_is_retried_only_for_missing_exercise():
    model = SequencedModel(
        [
            {"answers": [{"exercise_id": "q1", "answer": "first"}]},
            {"answers": [{"exercise_id": "q2", "answer": "recovered"}]},
        ]
    )

    answers = answer_batch(MissingAnswerRetryModel(model), (_exercise(1), _exercise(2)))

    assert answers == {"q1": "first", "q2": "recovered"}
    assert len(model.payloads) == 2
    assert [item["exercise_id"] for item in model.payloads[0]["exercises"]] == ["q1", "q2"]
    assert [item["exercise_id"] for item in model.payloads[1]["exercises"]] == ["q2"]


def test_missing_answer_recovery_is_bounded_and_still_fails_closed():
    model = SequencedModel(
        [
            {"answers": [{"exercise_id": "q1", "answer": "first"}]},
            {"answers": []},
        ]
    )

    with pytest.raises(PyramidExamError, match=r"missing=\['q2'\]"):
        answer_batch(MissingAnswerRetryModel(model), (_exercise(1), _exercise(2)))

    assert len(model.payloads) == 2


def test_unexpected_initial_id_is_not_retried_or_hidden():
    model = SequencedModel(
        [
            {
                "answers": [
                    {"exercise_id": "q1", "answer": "first"},
                    {"exercise_id": "rogue", "answer": "unexpected"},
                ]
            }
        ]
    )

    with pytest.raises(PyramidExamError, match=r"extra=\['rogue'\]"):
        answer_batch(MissingAnswerRetryModel(model), (_exercise(1), _exercise(2)))

    assert len(model.payloads) == 1


def test_opt_in_recovers_initial_id_substitution_by_retrying_only_missing_exercise():
    model = SequencedModel(
        [
            {
                "answers": [
                    {"exercise_id": "q1", "answer": "first"},
                    {"exercise_id": "rogue", "answer": "wrong-id"},
                ]
            },
            {"answers": [{"exercise_id": "q2", "answer": "recovered"}]},
        ]
    )

    answers = answer_batch(
        MissingAnswerRetryModel(model, recover_unexpected_initial_ids=True),
        (_exercise(1), _exercise(2)),
    )

    assert answers == {"q1": "first", "q2": "recovered"}
    assert len(model.payloads) == 2
    assert [item["exercise_id"] for item in model.payloads[1]["exercises"]] == ["q2"]


def test_opt_in_never_hides_unexpected_extra_when_expected_batch_is_complete():
    model = SequencedModel(
        [
            {
                "answers": [
                    {"exercise_id": "q1", "answer": "first"},
                    {"exercise_id": "q2", "answer": "second"},
                    {"exercise_id": "rogue", "answer": "unexpected"},
                ]
            }
        ]
    )

    with pytest.raises(PyramidExamError, match=r"extra=\['rogue'\]"):
        answer_batch(
            MissingAnswerRetryModel(model, recover_unexpected_initial_ids=True),
            (_exercise(1), _exercise(2)),
        )

    assert len(model.payloads) == 1


def test_unexpected_recovery_id_still_fails_closed():
    model = SequencedModel(
        [
            {"answers": [{"exercise_id": "q1", "answer": "first"}]},
            {"answers": [{"exercise_id": "rogue", "answer": "unexpected"}]},
        ]
    )

    with pytest.raises(PyramidExamError, match=r"extra=\['rogue'\]"):
        answer_batch(MissingAnswerRetryModel(model), (_exercise(1), _exercise(2)))

    assert len(model.payloads) == 2


def test_opt_in_unexpected_recovery_id_still_fails_closed():
    model = SequencedModel(
        [
            {
                "answers": [
                    {"exercise_id": "q1", "answer": "first"},
                    {"exercise_id": "rogue-initial", "answer": "wrong-id"},
                ]
            },
            {"answers": [{"exercise_id": "rogue-retry", "answer": "still-wrong"}]},
        ]
    )

    with pytest.raises(PyramidExamError, match=r"missing=\['q2'\].*extra=\['rogue-retry'\]"):
        answer_batch(
            MissingAnswerRetryModel(model, recover_unexpected_initial_ids=True),
            (_exercise(1), _exercise(2)),
        )

    assert len(model.payloads) == 2
