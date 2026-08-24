from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from roberta.learning.pyramid import Exercise, select_level_exercises
from roberta.learning.pyramid_adjudicator_retry import PyramidAdjudicatorJsonRetryModel
from roberta.learning.pyramid_critical_revalidation import revalidate_critical_checkpoints
from roberta.learning.pyramid_exam import (
    ADJUDICATOR_SYSTEM_PROMPT,
    CHECKPOINT_SCHEMA,
    PREVIOUS_GRADING_SEMANTICS,
    PyramidExamError,
)


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


def _adjudication_messages() -> list[object]:
    return [
        SystemMessage(content=ADJUDICATOR_SYSTEM_PROMPT),
        HumanMessage(
            content=json.dumps(
                {
                    "schema": {"grades": []},
                    "items": [{"exercise_id": "q1"}],
                }
            )
        ),
    ]


def _malformed_grade_json() -> str:
    return (
        '{\n'
        '  "grades": [\n'
        '    {\n'
        '      "exercise_id": "q1",\n'
        '      " "grade": "PASS",\n'
        '      "failure_codes": [],\n'
        '      "critical_failure": false,\n'
        '      "grader_note": "qualified wording"\n'
        '    }\n'
        '  ]\n'
        '}'
    )


def test_adjudicator_invalid_json_gets_exactly_one_format_retry() -> None:
    class Model:
        def __init__(self) -> None:
            self.calls: list[list[object]] = []

        def invoke(self, messages, *args, **kwargs):
            self.calls.append(list(messages))
            if len(self.calls) == 1:
                return _Response(_malformed_grade_json())
            return _Response(
                json.dumps(
                    {
                        "grades": [
                            {
                                "exercise_id": "q1",
                                "grade": "PASS",
                                "failure_codes": [],
                                "critical_failure": False,
                                "grader_note": "qualified wording",
                            }
                        ]
                    }
                )
            )

    base = Model()
    wrapped = PyramidAdjudicatorJsonRetryModel(base)
    original = _adjudication_messages()

    response = wrapped.invoke(original)

    assert len(base.calls) == 2
    assert json.loads(response.content)["grades"][0]["grade"] == "PASS"
    assert len(base.calls[1]) == len(original) + 1
    assert base.calls[1][0].content == original[0].content
    assert base.calls[1][1].content == original[1].content
    retry_payload = json.loads(base.calls[1][-1].content)
    assert retry_payload["format_retry"] == 1
    assert "serialization-only retry" in retry_payload["instruction"]
    assert retry_payload["prior_parse_error"]["line"] == 5


def test_adjudicator_second_invalid_json_fails_closed_after_one_retry() -> None:
    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages, *args, **kwargs):
            self.calls += 1
            return _Response(_malformed_grade_json())

    base = Model()
    wrapped = PyramidAdjudicatorJsonRetryModel(base)

    with pytest.raises(PyramidExamError, match="format retry exhausted after one bounded retry"):
        wrapped.invoke(_adjudication_messages())

    assert base.calls == 2


def test_non_adjudicator_or_valid_json_is_never_retried() -> None:
    class Model:
        def __init__(self, response: str) -> None:
            self.response = response
            self.calls = 0

        def invoke(self, messages, *args, **kwargs):
            self.calls += 1
            return _Response(self.response)

    malformed = Model(_malformed_grade_json())
    wrapped_malformed = PyramidAdjudicatorJsonRetryModel(malformed)
    response = wrapped_malformed.invoke(
        [SystemMessage(content="not the Pyramid adjudicator"), HumanMessage(content="{}")]
    )
    assert response.content == _malformed_grade_json()
    assert malformed.calls == 1

    valid_but_wrong_schema = Model(json.dumps({"not_grades": []}))
    wrapped_valid = PyramidAdjudicatorJsonRetryModel(valid_but_wrong_schema)
    response = wrapped_valid.invoke(_adjudication_messages())
    assert json.loads(response.content) == {"not_grades": []}
    assert valid_but_wrong_schema.calls == 1


def _exercise() -> Exercise:
    return Exercise(
        exercise_id="q1",
        curriculum_id="c1",
        level=1,
        concept="benefits",
        subconcept="immutability",
        question="What does immutability mean?",
        expected_answer="It is practical rather than absolute.",
        source_refs=("source",),
        required_reasoning_points=("practical rather than absolute",),
        forbidden_inferences=("Do not claim absolute immutability.",),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_double_malformed_revalidation_publishes_no_partial_output(tmp_path: Path) -> None:
    exercise = _exercise()
    seed = "retry-audit-seed"
    selected = select_level_exercises(
        (exercise,),
        curriculum_id="c1",
        level=1,
        run_seed=seed,
        count=1,
    )
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    checkpoint = input_dir / "level_01_batch_0001.json"
    checkpoint.write_text(
        json.dumps(
            {
                "checkpoint_schema": CHECKPOINT_SCHEMA,
                "grading_semantics": PREVIOUS_GRADING_SEMANTICS,
                "exercise_ids": [selected[0].exercise_id],
                "grades": [
                    {
                        "exercise_id": selected[0].exercise_id,
                        "answer": "Data cannot be altered.",
                        "grade": "FAIL",
                        "score": 0.0,
                        "correct": False,
                        "failure_codes": ["factual_error"],
                        "critical_failure": True,
                        "grader_note": "Historical critical proposal.",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    original_sha = _sha256(checkpoint)

    class AlwaysMalformed:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages, *args, **kwargs):
            self.calls += 1
            return _Response(_malformed_grade_json())

    base = AlwaysMalformed()
    wrapped = PyramidAdjudicatorJsonRetryModel(base)

    with pytest.raises(PyramidExamError, match="format retry exhausted"):
        revalidate_critical_checkpoints(
            exercise_bank=(exercise,),
            grader_model=wrapped,
            input_dir=input_dir,
            output_dir=output_dir,
            curriculum_id="c1",
            level=1,
            run_seed=seed,
            batch_size=1,
            canonical_exam=False,
            question_count=1,
        )

    assert base.calls == 2
    assert _sha256(checkpoint) == original_sha
    assert not output_dir.exists()
