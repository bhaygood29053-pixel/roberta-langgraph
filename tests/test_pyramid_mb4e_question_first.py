from __future__ import annotations

import json

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import GRADING_SEMANTICS, grade_batch, run_exam


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


_EXPECTED = (
    "The chapter treats blockchain immutability as practical rather than absolute: "
    "accepted data is extremely difficult, but not conceptually impossible, to alter."
)
_REASONING = (_EXPECTED,)
_FORBIDDEN = ("Do not claim absolute immutability.",)


def _exercise(exercise_id: str, question: str, *, critical: bool = False) -> Exercise:
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
        required_reasoning_points=_REASONING,
        forbidden_inferences=_FORBIDDEN,
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
        integrity_question=critical,
    )


def test_real_mb4e_immutability_regressions_correct_false_positives_without_weakening_true_failures():
    cases = (
        (
            _exercise("MB4E-L01-00841", "Explain immutability within the chapter's discussion of benefits."),
            "Immutability is presented as a benefit because once data is recorded in a block and confirmed by the network, it cannot be altered or deleted without enormous computational effort, providing a tamper-evident and permanent record.",
            "PARTIAL",
            False,
        ),
        (
            _exercise("MB4E-L01-00843", "What principle about immutability should Roberta apply when reasoning about benefits?"),
            "Immutability means that once data is recorded on the blockchain, it cannot be altered or deleted, providing a permanent and tamper-evident history that builds trust and reduces fraud.",
            "FAIL",
            False,
        ),
        (
            _exercise("MB4E-L01-00844", "What distinction or role does immutability have within benefits?"),
            "Immutability serves as a foundational benefit that ensures data integrity and auditability, distinguishing blockchain from traditional databases by preventing retroactive changes and fostering trust among participants.",
            "FAIL",
            False,
        ),
        (
            _exercise("MB4E-L01-00845", "Why is immutability important to understanding benefits?", critical=True),
            "Immutability is important because it ensures that once data is recorded on a blockchain, it cannot be altered or deleted. This provides a tamper-evident and permanent record, which builds trust and enables verifiable audit trails, reducing fraud and disputes.",
            "FAIL",
            True,
        ),
        (
            _exercise("MB4E-L01-00847", "What conclusion about immutability is supported by Chapter 1?"),
            "Chapter 1 supports the conclusion that immutability is a key benefit of blockchain because once data is recorded in a block and added to the chain, it is extremely difficult to alter or delete. This is achieved through cryptographic hashing and the distributed nature of the ledger, where changing a single block would require altering all subsequent blocks and gaining control of the majority of the network. Immutability provides a trustworthy and permanent record of transactions, enhancing transparency and auditability.",
            "FAIL",
            False,
        ),
        (
            _exercise("MB4E-L01-00848", "Teach back the chapter's point about immutability in one concise explanation.", critical=True),
            "Immutability means that once data is recorded on a blockchain, it cannot be altered or deleted, providing a permanent and tamper-evident record of transactions.",
            "FAIL",
            True,
        ),
        (
            _exercise("MB4E-L01-00856", "What follows from the chapter's explanation of immutability?", critical=True),
            "Immutability means once data is recorded, it cannot be altered, providing a permanent and tamper-evident history.",
            "FAIL",
            True,
        ),
        (
            _exercise("MB4E-L01-00857", "If auditing an answer about immutability, what source-supported point must be present?", critical=True),
            "The point that once data is recorded on the blockchain, it cannot be altered or deleted, ensuring historical integrity.",
            "FAIL",
            True,
        ),
        (
            _exercise("MB4E-L01-00858", "Which foundational idea should Roberta remember about immutability?", critical=True),
            "Immutability means that once data is recorded on the blockchain, it cannot be altered or deleted. Roberta should remember that this property is achieved through cryptographic hashing and the linked structure of blocks, providing tamper-evidence and a permanent, auditable history of all transactions.",
            "FAIL",
            True,
        ),
    )
    exercises = tuple(case[0] for case in cases)
    answers = {case[0].exercise_id: case[1] for case in cases}

    class InitialAnchoringThenQuestionFirstModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            if "initial_grade" not in payload["items"][0]:
                grades = []
                for exercise, _answer, initial_grade, critical in cases:
                    grades.append(
                        {
                            "exercise_id": exercise.exercise_id,
                            "grade": initial_grade,
                            "failure_codes": ["factual_error"],
                            "critical_failure": critical,
                            "grader_note": "Initial grader treated missing preferred wording or absolute language as factual_error.",
                        }
                    )
                return _Response(json.dumps({"grades": grades}))

            assert {item["exercise_id"] for item in payload["items"]} == {
                "MB4E-L01-00841",
                "MB4E-L01-00843",
                "MB4E-L01-00844",
                "MB4E-L01-00847",
            }
            for item in payload["items"]:
                assert item["grading_rubric_id"] == "MB4E-L1-RUBRIC-V1"
                assert item["forbidden_inferences"] == ["Do not claim absolute immutability."]

            return _Response(
                json.dumps(
                    {
                        "grades": [
                            {
                                "exercise_id": "MB4E-L01-00841",
                                "grade": "PASS",
                                "failure_codes": [],
                                "critical_failure": False,
                                "grader_note": "The answer explicitly conditions alteration on enormous computational effort and is non-absolute.",
                            },
                            {
                                "exercise_id": "MB4E-L01-00843",
                                "grade": "FAIL",
                                "failure_codes": ["factual_error"],
                                "critical_failure": False,
                                "grader_note": "The answer affirmatively says the data cannot be altered or deleted.",
                            },
                            {
                                "exercise_id": "MB4E-L01-00844",
                                "grade": "FAIL",
                                "failure_codes": ["factual_error"],
                                "critical_failure": False,
                                "grader_note": "The answer overstates the benefit as preventing retroactive changes without qualification.",
                            },
                            {
                                "exercise_id": "MB4E-L01-00847",
                                "grade": "PASS",
                                "failure_codes": [],
                                "critical_failure": False,
                                "grader_note": "Extremely difficult to alter is a practical, non-absolute characterization.",
                            },
                        ]
                    }
                )
            )

    model = InitialAnchoringThenQuestionFirstModel()
    grades = grade_batch(model, exercises, answers)
    by_id = {item.exercise_id: item for item in grades}

    assert model.calls == 2
    assert by_id["MB4E-L01-00841"].grade == "PASS"
    assert by_id["MB4E-L01-00847"].grade == "PASS"
    for exercise_id in (
        "MB4E-L01-00843",
        "MB4E-L01-00844",
        "MB4E-L01-00845",
        "MB4E-L01-00848",
        "MB4E-L01-00856",
        "MB4E-L01-00857",
        "MB4E-L01-00858",
    ):
        assert by_id[exercise_id].grade != "PASS"


def test_old_v1_checkpoint_is_regraded_under_v2_semantics(tmp_path):
    exercise = Exercise(
        exercise_id="q1",
        curriculum_id="c1",
        level=1,
        concept="fundamentals",
        question="Question?",
        expected_answer="answer:q1",
        source_refs=("source-1",),
    )
    checkpoint = tmp_path / "level_01_batch_0001.json"
    checkpoint.write_text(
        json.dumps(
            {
                "checkpoint_schema": "roberta-pyramid-checkpoint/v3",
                "grading_semantics": "question-first-adjudication/v1",
                "exercise_ids": ["q1"],
                "grades": [
                    {
                        "exercise_id": "q1",
                        "answer": "stale",
                        "grade": "FAIL",
                        "score": 0.0,
                        "correct": False,
                        "failure_codes": ["factual_error"],
                        "critical_failure": False,
                        "grader_note": "old semantics",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    class PassingModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            if "exercises" in payload:
                return _Response(json.dumps({"answers": [{"exercise_id": "q1", "answer": "answer:q1"}]}))
            return _Response(
                json.dumps(
                    {
                        "grades": [
                            {
                                "exercise_id": "q1",
                                "grade": "PASS",
                                "failure_codes": [],
                                "critical_failure": False,
                                "grader_note": "ok",
                            }
                        ]
                    }
                )
            )

    model = PassingModel()
    outcome = run_exam(
        exercises=(exercise,),
        answer_model=model,
        grader_model=model,
        batch_size=1,
        checkpoint_dir=tmp_path,
        canonical_exam=False,
    )

    assert model.calls == 2
    assert outcome.graded_answers[0].grade == "PASS"
    rewritten = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert rewritten["grading_semantics"] == GRADING_SEMANTICS
    assert GRADING_SEMANTICS == "question-first-adjudication/v2"
