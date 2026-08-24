from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from roberta.learning.pyramid import Exercise, select_level_exercises
from roberta.learning.pyramid_critical_revalidation import revalidate_critical_checkpoints
from roberta.learning.pyramid_exam import (
    CHECKPOINT_SCHEMA,
    GRADING_SEMANTICS,
    PREVIOUS_GRADING_SEMANTICS,
    PyramidExamError,
    grade_batch,
)


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


def _exercise(
    exercise_id: str,
    *,
    forbidden_inferences: tuple[str, ...] = (),
    integrity: bool = False,
    boss: bool = False,
) -> Exercise:
    return Exercise(
        exercise_id=exercise_id,
        curriculum_id="mastering_blockchain_4e_2023_book01",
        level=1,
        concept="benefits" if "immut" in exercise_id else "blockchain_definition",
        subconcept="immutability" if "immut" in exercise_id else "append_only",
        question="What does the chapter say about this property?",
        expected_answer="The property is practical rather than absolute.",
        source_refs=("MB4E-TEST-SOURCE",),
        required_reasoning_points=("practical rather than absolute",),
        forbidden_inferences=forbidden_inferences,
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
        integrity_question=integrity,
        boss_question=boss,
    )


def _row(
    exercise_id: str,
    *,
    grade: str = "FAIL",
    codes: list[str] | None = None,
    critical: bool,
    note: str,
) -> dict[str, object]:
    return {
        "exercise_id": exercise_id,
        "grade": grade,
        "failure_codes": codes if codes is not None else ["factual_error"],
        "critical_failure": critical,
        "grader_note": note,
    }


def test_explicit_absolute_immutability_can_remain_critical_after_bounded_validation() -> None:
    exercise = _exercise(
        "immut-absolute",
        forbidden_inferences=("Do not claim absolute immutability.",),
    )
    answers = {exercise.exercise_id: "Once recorded, data cannot be altered or deleted."}

    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls == 1:
                return _Response(json.dumps({"grades": [
                    _row(item["exercise_id"], critical=True, note="Absolute claim proposed critical.")
                ]}))
            assert self.calls == 2
            assert item["initial_critical_failure"] is True
            assert item["critical_deterministic_basis"] is True
            return _Response(json.dumps({"grades": [
                _row(item["exercise_id"], critical=True, note="Affirmative absolute claim confirmed.")
            ]}))

    model = Model()
    grades = grade_batch(model, (exercise,), answers)

    assert model.calls == 2
    assert grades[0].grade == "FAIL"
    assert grades[0].critical_failure is True


def test_qualified_immutability_cannot_remain_critical_even_if_validator_repeats_proposal() -> None:
    exercise = _exercise(
        "immut-qualified",
        forbidden_inferences=("Do not claim absolute immutability.",),
    )
    answers = {
        exercise.exercise_id: (
            "Accepted data cannot be easily altered or deleted, so the ledger is tamper-evident."
        )
    }

    class OverStrictModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls == 2:
                assert item["initial_critical_failure"] is True
                assert item["critical_deterministic_basis"] is False
                assert "cannot be easily altered" in item["roberta_answer"]
            return _Response(json.dumps({"grades": [
                _row(item["exercise_id"], critical=True, note="Over-strict absolute-immutability claim.")
            ]}))

    model = OverStrictModel()
    grades = grade_batch(model, (exercise,), answers)

    assert model.calls == 2
    assert grades[0].grade == "FAIL"
    assert grades[0].critical_failure is False


def test_append_only_without_forbidden_inference_is_ordinary_fail_not_critical() -> None:
    exercise = _exercise("append-only")
    answers = {
        exercise.exercise_id: "Existing blocks are never modified or removed."
    }

    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls == 2:
                assert item["initial_critical_failure"] is True
                assert item["critical_deterministic_basis"] is False
            return _Response(json.dumps({"grades": [
                _row(item["exercise_id"], critical=True, note="Normal factual error.")
            ]}))

    model = Model()
    grades = grade_batch(model, (exercise,), answers)

    assert model.calls == 2
    assert grades[0].grade == "FAIL"
    assert grades[0].failure_codes == ("factual_error",)
    assert grades[0].critical_failure is False


def test_first_pass_critical_proposal_receives_bounded_validation() -> None:
    exercise = _exercise(
        "immut-bounded",
        forbidden_inferences=("Do not claim absolute immutability.",),
    )
    answers = {exercise.exercise_id: "Data cannot be altered."}

    class Model:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls == 1:
                assert "initial_grade" not in item
                return _Response(json.dumps({"grades": [
                    _row(item["exercise_id"], critical=True, note="Proposal.")
                ]}))
            assert self.calls == 2
            assert item["initial_grade"] == "FAIL"
            assert item["initial_critical_failure"] is True
            return _Response(json.dumps({"grades": [
                _row(item["exercise_id"], critical=True, note="Validated.")
            ]}))

    model = Model()
    grades = grade_batch(model, (exercise,), answers)

    assert model.calls == 2
    assert grades[0].critical_failure is True


def test_second_pass_can_clear_critical_but_cannot_create_new_critical() -> None:
    proposed = _exercise(
        "immut-clear",
        forbidden_inferences=("Do not claim absolute immutability.",),
    )
    answers = {proposed.exercise_id: "The data is extremely difficult to alter."}

    class ClearingModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls == 1:
                return _Response(json.dumps({"grades": [
                    _row(item["exercise_id"], critical=True, note="Mistaken proposal.")
                ]}))
            return _Response(json.dumps({"grades": [
                _row(item["exercise_id"], grade="PASS", codes=[], critical=False, note="Qualified wording is valid.")
            ]}))

    cleared = grade_batch(ClearingModel(), (proposed,), answers)
    assert cleared[0].critical_failure is False
    assert cleared[0].grade == "PASS"

    ordinary = _exercise("ordinary-factual")
    ordinary_answers = {ordinary.exercise_id: "A wrong answer."}

    class IntroducingModel:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            if self.calls == 1:
                return _Response(json.dumps({"grades": [
                    _row(item["exercise_id"], critical=False, note="Send factual error to MB4E adjudication.")
                ]}))
            return _Response(json.dumps({"grades": [
                _row(item["exercise_id"], critical=True, note="Improperly introduced critical.")
            ]}))

    with pytest.raises(PyramidExamError, match="cannot introduce a critical failure"):
        grade_batch(IntroducingModel(), (ordinary,), ordinary_answers)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_revalidation_writes_separate_namespace_and_never_mutates_inputs_or_ledger(tmp_path: Path) -> None:
    bank = (
        _exercise(
            "immut-audit",
            forbidden_inferences=("Do not claim absolute immutability.",),
        ),
        _exercise("append-audit", boss=True),
    )
    seed = "audit-seed"
    selected = select_level_exercises(
        bank,
        curriculum_id="mastering_blockchain_4e_2023_book01",
        level=1,
        run_seed=seed,
        count=2,
    )
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    checkpoint = input_dir / "level_01_batch_0001.json"
    rows = []
    for item in selected:
        if item.exercise_id == "immut-audit":
            answer = "Accepted data cannot be easily altered or deleted."
            row = {
                "exercise_id": item.exercise_id,
                "answer": answer,
                "grade": "FAIL",
                "score": 0.0,
                "correct": False,
                "failure_codes": ["factual_error"],
                "critical_failure": True,
                "grader_note": "Historical over-strict critical proposal.",
            }
        else:
            row = {
                "exercise_id": item.exercise_id,
                "answer": "A wrong but noncritical answer.",
                "grade": "FAIL",
                "score": 0.0,
                "correct": False,
                "failure_codes": ["factual_error"],
                "critical_failure": False,
                "grader_note": "Historical ordinary failure.",
            }
        rows.append(row)
    checkpoint.write_text(json.dumps({
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "grading_semantics": PREVIOUS_GRADING_SEMANTICS,
        "exercise_ids": [item.exercise_id for item in selected],
        "grades": rows,
    }, indent=2), encoding="utf-8")

    ledger = tmp_path / "pyramid_training.sqlite3"
    ledger.write_bytes(b"ledger-sentinel-must-not-change")
    input_sha = _sha(checkpoint)
    ledger_sha = _sha(ledger)

    class Validator:
        def __init__(self) -> None:
            self.calls = 0

        def invoke(self, messages):
            self.calls += 1
            payload = json.loads(messages[-1].content)
            item = payload["items"][0]
            assert item["exercise_id"] == "immut-audit"
            assert item["initial_critical_failure"] is True
            assert item["critical_deterministic_basis"] is False
            return _Response(json.dumps({"grades": [
                _row(item["exercise_id"], critical=False, note="Qualified wording is non-absolute.")
            ]}))

    validator = Validator()
    report = revalidate_critical_checkpoints(
        exercise_bank=bank,
        grader_model=validator,
        input_dir=input_dir,
        output_dir=output_dir,
        curriculum_id="mastering_blockchain_4e_2023_book01",
        level=1,
        run_seed=seed,
        batch_size=2,
        canonical_exam=False,
        question_count=2,
    )

    assert validator.calls == 1
    assert report.old_critical_failures == 1
    assert report.new_critical_failures == 0
    assert _sha(checkpoint) == input_sha
    assert _sha(ledger) == ledger_sha
    assert (output_dir / "level_01_batch_0001.json").is_file()
    assert (output_dir / "critical_revalidation_report.json").is_file()
    output = json.loads((output_dir / "level_01_batch_0001.json").read_text(encoding="utf-8"))
    assert output["grading_semantics"] == GRADING_SEMANTICS


def test_revalidation_refuses_same_or_nested_output_namespace(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    exercise = _exercise("append-safe")

    class UnusedModel:
        def invoke(self, messages):
            raise AssertionError("unsafe paths must fail before model invocation")

    with pytest.raises(Exception, match="separate|nested"):
        revalidate_critical_checkpoints(
            exercise_bank=(exercise,),
            grader_model=UnusedModel(),
            input_dir=input_dir,
            output_dir=input_dir,
            curriculum_id="mastering_blockchain_4e_2023_book01",
            level=1,
            run_seed="seed",
            batch_size=1,
            canonical_exam=False,
            question_count=1,
        )
