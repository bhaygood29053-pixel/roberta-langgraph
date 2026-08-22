from __future__ import annotations

import json

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import run_exam


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeExamModel:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        payload = json.loads(messages[-1].content)
        if "exercises" in payload:
            return _Response(
                json.dumps(
                    {
                        "answers": [
                            {"exercise_id": item["exercise_id"], "answer": f"answer:{item['exercise_id']}"}
                            for item in payload["exercises"]
                        ]
                    }
                )
            )
        return _Response(
            json.dumps(
                {
                    "grades": [
                        {
                            "exercise_id": item["exercise_id"],
                            "correct": True,
                            "failure_codes": [],
                            "critical_failure": False,
                            "grader_note": "ok",
                        }
                        for item in payload["items"]
                    ]
                }
            )
        )


def _exercise(index: int, *, integrity: bool = False, boss: bool = False) -> Exercise:
    return Exercise(
        exercise_id=f"q{index}",
        curriculum_id="c1",
        level=1,
        concept="fundamentals",
        question=f"Question {index}?",
        expected_answer=f"answer:q{index}",
        source_refs=("source-1",),
        integrity_question=integrity,
        boss_question=boss,
    )


def test_run_exam_batches_and_resumes_from_checkpoints(tmp_path):
    exercises = (
        _exercise(1),
        _exercise(2, integrity=True),
        _exercise(3),
        _exercise(4, boss=True),
    )
    model = FakeExamModel()
    first = run_exam(
        exercises=exercises,
        answer_model=model,
        grader_model=model,
        batch_size=2,
        checkpoint_dir=tmp_path,
        canonical_exam=False,
    )
    assert model.calls == 4
    assert first.level_result.passed is True
    assert first.level_result.correct_questions == 4
    assert first.level_result.boss_passed is True

    replay_model = FakeExamModel()
    replay = run_exam(
        exercises=exercises,
        answer_model=replay_model,
        grader_model=replay_model,
        batch_size=2,
        checkpoint_dir=tmp_path,
        canonical_exam=False,
    )
    assert replay_model.calls == 0
    assert replay.level_result == first.level_result


def test_failure_codes_and_critical_failure_are_summarized(tmp_path):
    class FailingModel(FakeExamModel):
        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            if "exercises" in payload:
                return _Response(json.dumps({"answers": [
                    {"exercise_id": item["exercise_id"], "answer": "bad"}
                    for item in payload["exercises"]
                ]}))
            return _Response(json.dumps({"grades": [
                {
                    "exercise_id": item["exercise_id"],
                    "correct": False,
                    "failure_codes": ["unsupported_inference"],
                    "critical_failure": bool(item["integrity_question"]),
                    "grader_note": "bad inference",
                }
                for item in payload["items"]
            ]}))

    exercises = (_exercise(1, integrity=True), _exercise(2, boss=True))
    result = run_exam(
        exercises=exercises,
        answer_model=FailingModel(),
        grader_model=FailingModel(),
        batch_size=2,
        checkpoint_dir=tmp_path,
        canonical_exam=False,
    )
    assert result.level_result.passed is False
    assert result.level_result.critical_failures == 1
    assert result.failure_counts == {"unsupported_inference": 2}
