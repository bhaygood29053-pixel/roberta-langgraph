from __future__ import annotations

import json

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import grade_batch


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


_EXPECTED = (
    "The chapter treats blockchain immutability as practical rather than absolute: "
    "accepted data is extremely difficult, but not conceptually impossible, to alter."
)


def _exercise(exercise_id: str, question: str) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id="mastering_blockchain_4e_2023_book01",
        level=1,
        concept="benefits",
        subconcept="immutability",
        question=question,
        expected_answer=_EXPECTED,
        source_refs=("MB4E-CH1-P53-56-BENEFITS-LIMITS",),
        question_type="definition",
        difficulty=2,
        required_reasoning_points=(_EXPECTED,),
        forbidden_inferences=("Do not claim absolute immutability.",),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
    )


def test_mb4e_equivalent_non_absolute_wording_is_not_rejected_for_missing_preferred_phrase():
    cases = (
        (
            _exercise("eq-extremely-difficult", "What conclusion about immutability is supported?"),
            "Once accepted, blockchain history is extremely difficult to alter.",
            "PASS",
        ),
        (
            _exercise("eq-practically-infeasible", "How should immutability be characterized?"),
            "Rewriting established blockchain history can be practically infeasible under normal operating assumptions.",
            "PASS",
        ),
        (
            _exercise("eq-economically-prohibitive", "Explain practical immutability."),
            "Changing established history may be economically prohibitive even though it is not conceptually impossible.",
            "PASS",
        ),
        (
            _exercise("eq-computationally-prohibitive", "Explain practical immutability."),
            "Rewriting sufficiently established history can be computationally prohibitive rather than absolutely impossible.",
            "PASS",
        ),
        (
            _exercise("eq-absolute-claim", "Explain immutability."),
            "Once data is recorded on a blockchain, it cannot be altered or deleted.",
            "FAIL",
        ),
    )
    exercises = tuple(item[0] for item in cases)
    answers = {exercise.exercise_id: answer for exercise, answer, _expected_grade in cases}

    class AnchoringThenSemanticAdjudicationModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            if "initial_grade" not in payload["items"][0]:
                return _Response(
                    json.dumps(
                        {
                            "grades": [
                                {
                                    "exercise_id": exercise.exercise_id,
                                    "grade": "FAIL",
                                    "failure_codes": ["factual_error"],
                                    "critical_failure": False,
                                    "grader_note": "Initial grader anchored on missing preferred wording.",
                                }
                                for exercise, _answer, _expected_grade in cases
                            ]
                        }
                    )
                )

            assert {item["exercise_id"] for item in payload["items"]} == {
                exercise.exercise_id for exercise, _answer, _expected_grade in cases
            }
            return _Response(
                json.dumps(
                    {
                        "grades": [
                            {
                                "exercise_id": exercise.exercise_id,
                                "grade": expected_grade,
                                "failure_codes": [] if expected_grade == "PASS" else ["factual_error"],
                                "critical_failure": False,
                                "grader_note": (
                                    "Equivalent qualified wording is non-absolute."
                                    if expected_grade == "PASS"
                                    else "The answer affirmatively claims absolute immutability."
                                ),
                            }
                            for exercise, _answer, expected_grade in cases
                        ]
                    }
                )
            )

    model = AnchoringThenSemanticAdjudicationModel()
    grades = grade_batch(model, exercises, answers)
    by_id = {grade.exercise_id: grade for grade in grades}

    assert model.calls == 2
    for exercise, _answer, expected_grade in cases:
        assert by_id[exercise.exercise_id].grade == expected_grade
        if expected_grade == "PASS":
            assert by_id[exercise.exercise_id].failure_codes == ()
        else:
            assert by_id[exercise.exercise_id].failure_codes == ("factual_error",)
