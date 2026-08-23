from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_exam import CHECKPOINT_SCHEMA, GRADING_SEMANTICS
from roberta.learning.pyramid_regrade import (
    HISTORICAL_GRADING_SEMANTICS,
    PyramidRegradeError,
    regrade_checkpoints,
)


CURRICULUM = "test-curriculum"
SEED = "original-seed"


def _exercise(index: int) -> Exercise:
    return Exercise(
        exercise_id=f"E-{index:03d}",
        curriculum_id=CURRICULUM,
        level=1,
        concept="fundamentals",
        question=f"Question {index}?",
        expected_answer=f"Expected {index}",
        source_refs=("SRC-1",),
    )


def _row(
    exercise: Exercise,
    *,
    answer: str,
    grade: str = "FAIL",
    failure_codes: list[str] | None = None,
    critical_failure: bool = False,
) -> dict[str, object]:
    scores = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}
    return {
        "exercise_id": exercise.exercise_id,
        "answer": answer,
        "grade": grade,
        "score": scores[grade],
        "correct": grade == "PASS",
        "failure_codes": failure_codes if failure_codes is not None else ([] if grade == "PASS" else ["factual_error"]),
        "critical_failure": critical_failure,
        "grader_note": f"historical {grade}",
    }


def _write_checkpoint(
    path: Path,
    exercises: tuple[Exercise, ...],
    rows: list[dict[str, object]],
    *,
    semantics: str = HISTORICAL_GRADING_SEMANTICS,
    exercise_ids: list[str] | None = None,
) -> bytes:
    payload = {
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "grading_semantics": semantics,
        "exercise_ids": exercise_ids if exercise_ids is not None else [item.exercise_id for item in exercises],
        "grades": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    path.write_bytes(data)
    return data


class GraderOnlyModel:
    def __init__(self, grades: dict[str, str] | None = None, *, fail_on_call: int | None = None):
        self.grades = grades or {}
        self.fail_on_call = fail_on_call
        self.calls = 0
        self.answers_seen: dict[str, str] = {}

    def invoke(self, messages):
        self.calls += 1
        if self.fail_on_call == self.calls:
            raise RuntimeError("simulated grader failure")
        system = str(messages[0].content)
        assert "taking a closed-book blockchain reasoning examination" not in system
        assert "evaluator for Roberta's Pyramid examination" in system
        payload = json.loads(messages[1].content)
        rows = []
        for item in payload["items"]:
            exercise_id = item["exercise_id"]
            answer = item["roberta_answer"]
            self.answers_seen[exercise_id] = answer
            grade = self.grades.get(exercise_id, "PASS")
            rows.append(
                {
                    "exercise_id": exercise_id,
                    "grade": grade,
                    "failure_codes": [] if grade == "PASS" else ["factual_error"],
                    "critical_failure": False,
                    "grader_note": f"regraded {grade}",
                }
            )
        return SimpleNamespace(content=json.dumps({"grades": rows}))


def test_regrade_has_no_answer_model_seam_and_preserves_exact_historical_answers(tmp_path: Path) -> None:
    assert "answer_model" not in inspect.signature(regrade_checkpoints).parameters

    exercises = (_exercise(1), _exercise(2))
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    answers = ("  exact historical answer one  ", "Exact historical answer two")
    original = _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        exercises,
        [
            _row(exercises[0], answer=answers[0], grade="FAIL"),
            _row(exercises[1], answer=answers[1], grade="PARTIAL", failure_codes=["incomplete_reasoning"]),
        ],
    )
    original_hash = hashlib.sha256(original).hexdigest()
    model = GraderOnlyModel()

    report = regrade_checkpoints(
        exercises=exercises,
        grader_model=model,
        input_dir=input_dir,
        output_dir=output_dir,
        curriculum_id=CURRICULUM,
        run_seed=SEED,
        batch_size=2,
        canonical_exam=False,
    )

    assert model.calls == 1
    assert model.answers_seen == {exercises[0].exercise_id: answers[0], exercises[1].exercise_id: answers[1]}
    assert (input_dir / "level_01_batch_0001.json").read_bytes() == original
    output = json.loads((output_dir / "level_01_batch_0001.json").read_text(encoding="utf-8"))
    assert output["checkpoint_schema"] == CHECKPOINT_SCHEMA
    assert output["grading_semantics"] == GRADING_SEMANTICS
    assert [item["answer"] for item in output["grades"]] == list(answers)
    assert output["regrade_provenance"] == {
        "contract": "roberta-pyramid-regrade/v1",
        "version": "1.0.0",
        "input_checkpoint_file": "level_01_batch_0001.json",
        "input_checkpoint_sha256": original_hash,
        "input_grading_semantics": HISTORICAL_GRADING_SEMANTICS,
    }
    assert dict(report.old_grade_counts) == {"PASS": 0, "PARTIAL": 1, "FAIL": 1}
    assert dict(report.new_grade_counts) == {"PASS": 2, "PARTIAL": 0, "FAIL": 0}
    assert dict(report.grade_transitions) == {"FAIL->PASS": 1, "PARTIAL->PASS": 1}
    assert report.old_weakness_count == 2
    assert report.new_weakness_count == 0
    assert report.answer_model_invoked is False
    assert report.training_ledger_mutated is False
    assert report.retention_authorized is False
    assert report.source_truth_authorized is False
    assert report.execution_authorized is False


@pytest.mark.parametrize("semantics", [GRADING_SEMANTICS, "unknown-grading/v99"])
def test_regrade_rejects_nonhistorical_semantics_before_model_or_output(
    tmp_path: Path, semantics: str
) -> None:
    exercise = _exercise(1)
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        (exercise,),
        [_row(exercise, answer="Original")],
        semantics=semantics,
    )
    model = GraderOnlyModel()

    with pytest.raises(PyramidRegradeError, match="grading semantics"):
        regrade_checkpoints(
            exercises=(exercise,),
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            curriculum_id=CURRICULUM,
            run_seed=SEED,
            batch_size=1,
            canonical_exam=False,
        )

    assert model.calls == 0
    assert not output_dir.exists()


def test_regrade_requires_exact_complete_batch_set_before_model_call(tmp_path: Path) -> None:
    exercises = (_exercise(1), _exercise(2))
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        (exercises[0],),
        [_row(exercises[0], answer="First")],
    )
    model = GraderOnlyModel()

    with pytest.raises(PyramidRegradeError, match="batch set mismatch"):
        regrade_checkpoints(
            exercises=exercises,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            curriculum_id=CURRICULUM,
            run_seed=SEED,
            batch_size=1,
            canonical_exam=False,
        )

    assert model.calls == 0
    assert not output_dir.exists()


@pytest.mark.parametrize(
    "mutator,match",
    [
        (lambda payload: payload.update({"exercise_ids": ["WRONG", "E-002"]}), "exercise ids"),
        (
            lambda payload: payload["grades"].__setitem__(1, {**payload["grades"][1], "exercise_id": "E-001"}),
            "order/id mismatch",
        ),
        (lambda payload: payload["grades"][0].update({"answer": ""}), "non-empty string"),
    ],
)
def test_regrade_fails_closed_on_mismatched_duplicate_or_malformed_historical_data(
    tmp_path: Path, mutator, match: str
) -> None:
    exercises = (_exercise(1), _exercise(2))
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    path = input_dir / "level_01_batch_0001.json"
    _write_checkpoint(
        path,
        exercises,
        [_row(exercises[0], answer="First"), _row(exercises[1], answer="Second")],
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutator(payload)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    model = GraderOnlyModel()

    with pytest.raises(PyramidRegradeError, match=match):
        regrade_checkpoints(
            exercises=exercises,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            curriculum_id=CURRICULUM,
            run_seed=SEED,
            batch_size=2,
            canonical_exam=False,
        )

    assert model.calls == 0
    assert not output_dir.exists()


def test_regrade_model_failure_leaves_no_partial_output(tmp_path: Path) -> None:
    exercises = (_exercise(1), _exercise(2))
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    for index, exercise in enumerate(exercises, start=1):
        _write_checkpoint(
            input_dir / f"level_01_batch_{index:04d}.json",
            (exercise,),
            [_row(exercise, answer=f"Original {index}")],
        )
    model = GraderOnlyModel(fail_on_call=2)

    with pytest.raises(RuntimeError, match="simulated grader failure"):
        regrade_checkpoints(
            exercises=exercises,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            curriculum_id=CURRICULUM,
            run_seed=SEED,
            batch_size=1,
            canonical_exam=False,
        )

    assert model.calls == 2
    assert not output_dir.exists()


@pytest.mark.parametrize("mode", ["same", "nested", "existing"])
def test_regrade_requires_new_separate_output_directory(tmp_path: Path, mode: str) -> None:
    exercise = _exercise(1)
    input_dir = tmp_path / "historical"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        (exercise,),
        [_row(exercise, answer="Original")],
    )
    if mode == "same":
        output_dir = input_dir
    elif mode == "nested":
        output_dir = input_dir / "regraded"
    else:
        output_dir = tmp_path / "regraded"
        output_dir.mkdir()
    model = GraderOnlyModel()

    with pytest.raises(PyramidRegradeError):
        regrade_checkpoints(
            exercises=(exercise,),
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            curriculum_id=CURRICULUM,
            run_seed=SEED,
            batch_size=1,
            canonical_exam=False,
        )

    assert model.calls == 0


def test_regrade_report_and_written_artifacts_are_deterministic(tmp_path: Path) -> None:
    exercises = (_exercise(1), _exercise(2))
    input_dir = tmp_path / "historical"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        exercises,
        [
            _row(exercises[0], answer="First", grade="FAIL"),
            _row(exercises[1], answer="Second", grade="PASS"),
        ],
    )
    output_a = tmp_path / "regraded-a"
    output_b = tmp_path / "regraded-b"

    report_a = regrade_checkpoints(
        exercises=exercises,
        grader_model=GraderOnlyModel({exercises[0].exercise_id: "PARTIAL", exercises[1].exercise_id: "PASS"}),
        input_dir=input_dir,
        output_dir=output_a,
        curriculum_id=CURRICULUM,
        run_seed=SEED,
        batch_size=2,
        canonical_exam=False,
    )
    report_b = regrade_checkpoints(
        exercises=exercises,
        grader_model=GraderOnlyModel({exercises[0].exercise_id: "PARTIAL", exercises[1].exercise_id: "PASS"}),
        input_dir=input_dir,
        output_dir=output_b,
        curriculum_id=CURRICULUM,
        run_seed=SEED,
        batch_size=2,
        canonical_exam=False,
    )

    assert report_a.to_mapping() == report_b.to_mapping()
    assert (output_a / "regrade_report.json").read_bytes() == (output_b / "regrade_report.json").read_bytes()
    assert (output_a / "level_01_batch_0001.json").read_bytes() == (
        output_b / "level_01_batch_0001.json"
    ).read_bytes()
    assert dict(report_a.grade_transitions) == {"FAIL->PARTIAL": 1, "PASS->PASS": 1}
