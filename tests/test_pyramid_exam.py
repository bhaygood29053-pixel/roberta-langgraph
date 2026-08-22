from __future__ import annotations

import json

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import _parse_json, PyramidExamError, run_exam


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


def test_parse_json_accepts_single_json_code_fence():
    parsed = _parse_json('```json\n{"grades": []}\n```', context="grader")
    assert parsed == {"grades": []}


def test_parse_json_accepts_unlabeled_single_code_fence():
    parsed = _parse_json('```\n{"answers": []}\n```', context="answer")
    assert parsed == {"answers": []}


def test_parse_json_does_not_repair_malformed_or_nested_fences():
    try:
        _parse_json('```json\n{"grades": []}\n```\nextra', context="grader")
    except PyramidExamError:
        pass
    else:
        raise AssertionError("trailing content must remain invalid")

    try:
        _parse_json('```json\n{"x": "```"}\n```', context="grader")
    except PyramidExamError:
        pass
    else:
        raise AssertionError("nested fence content must remain invalid")


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
    assert first.level_result.accuracy == 1.0
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
                    "grade": "FAIL",
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
    assert result.level_result.accuracy == 0.0
    assert result.failure_counts == {"unsupported_inference": 2}


def test_partial_credit_contributes_half_point_without_counting_as_full_pass(tmp_path):
    class PartialModel(FakeExamModel):
        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            if "exercises" in payload:
                return _Response(json.dumps({"answers": [
                    {"exercise_id": item["exercise_id"], "answer": f"answer:{item['exercise_id']}"}
                    for item in payload["exercises"]
                ]}))
            grades = []
            for index, item in enumerate(payload["items"]):
                if index == 0:
                    grade = "PASS"
                    codes = []
                elif index == 1:
                    grade = "PARTIAL"
                    codes = ["incomplete_reasoning"]
                else:
                    grade = "FAIL"
                    codes = ["factual_error"]
                grades.append({
                    "exercise_id": item["exercise_id"],
                    "grade": grade,
                    "failure_codes": codes,
                    "critical_failure": False,
                    "grader_note": grade.lower(),
                })
            return _Response(json.dumps({"grades": grades}))

    exercises = (_exercise(1), _exercise(2), _exercise(3, boss=True))
    result = run_exam(
        exercises=exercises,
        answer_model=PartialModel(),
        grader_model=PartialModel(),
        batch_size=3,
        checkpoint_dir=tmp_path,
        canonical_exam=False,
    )
    assert result.level_result.correct_questions == 1
    assert result.level_result.accuracy == 0.5
    assert result.level_result.boss_passed is False
    assert result.failure_counts == {"incomplete_reasoning": 1, "factual_error": 1}
    assert [item.grade for item in result.graded_answers] == ["PASS", "PARTIAL", "FAIL"]
    assert [item.score for item in result.graded_answers] == [1.0, 0.5, 0.0]


def test_old_checkpoint_schema_is_ignored_and_regraded(tmp_path):
    exercises = (_exercise(1), _exercise(2, boss=True))
    legacy = tmp_path / "level_01_batch_0001.json"
    legacy.write_text(json.dumps({
        "exercise_ids": ["q1", "q2"],
        "grades": [
            {"exercise_id": "q1", "answer": "old", "correct": False},
            {"exercise_id": "q2", "answer": "old", "correct": False},
        ],
    }), encoding="utf-8")

    model = FakeExamModel()
    result = run_exam(
        exercises=exercises,
        answer_model=model,
        grader_model=model,
        batch_size=2,
        checkpoint_dir=tmp_path,
        canonical_exam=False,
    )
    assert model.calls == 2
    assert result.level_result.accuracy == 1.0
    rewritten = json.loads(legacy.read_text(encoding="utf-8"))
    assert rewritten["checkpoint_schema"] == "roberta-pyramid-checkpoint/v2"
