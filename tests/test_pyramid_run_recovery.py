from __future__ import annotations

import json
from types import SimpleNamespace

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import answer_batch
from roberta.learning.pyramid_run_cli import _build_answer_model


def _exercise(exercise_id: str) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id="runner-recovery-fixture",
        level=1,
        concept="benefits",
        subconcept="immutability",
        question=f"Question for {exercise_id}",
        expected_answer="Reference answer",
        source_refs=("fixture-source",),
        required_reasoning_points=(),
        forbidden_inferences=(),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
    )


def test_canonical_runner_recovers_one_initial_id_substitution() -> None:
    first = _exercise("MB4E-L01-01143")
    missing = _exercise("MB4E-L01-01144")

    class SubstitutionModel:
        def __init__(self) -> None:
            self.calls = 0
            self.requests: list[dict[str, object]] = []

        def invoke(self, messages):
            self.calls += 1
            request = json.loads(messages[-1].content)
            self.requests.append(request)
            if self.calls == 1:
                return SimpleNamespace(
                    content=json.dumps(
                        {
                            "answers": [
                                {"exercise_id": first.exercise_id, "answer": "first-answer"},
                                {"exercise_id": "MB4E-L01-01145", "answer": "wrong-id-answer"},
                            ]
                        }
                    )
                )
            return SimpleNamespace(
                content=json.dumps(
                    {
                        "answers": [
                            {"exercise_id": missing.exercise_id, "answer": "recovered-answer"}
                        ]
                    }
                )
            )

    model = SubstitutionModel()
    answer_model = _build_answer_model(model, ())
    answers = answer_batch(answer_model, (first, missing))

    assert model.calls == 2
    assert set(answers) == {first.exercise_id, missing.exercise_id}
    assert answers[first.exercise_id] == "first-answer"
    assert answers[missing.exercise_id] == "recovered-answer"
    assert [item["exercise_id"] for item in model.requests[1]["exercises"]] == [missing.exercise_id]
    assert model.requests[1]["instruction"].startswith("Recovery pass:")
