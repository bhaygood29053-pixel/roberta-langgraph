from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from roberta.learning.pyramid import Exercise, select_level_exercises
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


def _selected(
    bank: tuple[Exercise, ...],
    *,
    seed: str = SEED,
    count: int | None = None,
) -> tuple[Exercise, ...]:
    return select_level_exercises(
        bank,
        curriculum_id=CURRICULUM,
        level=1,
        run_seed=seed,
        count=len(bank) if count is None else count,
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


def _regrade(
    *,
    bank: tuple[Exercise, ...],
    grader_model,
    input_dir: Path,
    output_dir: Path,
    batch_size: int,
    seed: str = SEED,
    question_count: int | None = None,
):
    return regrade_checkpoints(
        exercise_bank=bank,
        grader_model=grader_model,
        input_dir=input_dir,
        output_dir=output_dir,
        curriculum_id=CURRICULUM,
        level=1,
        run_seed=seed,
        batch_size=batch_size,
        question_count=len(bank) if question_count is None else question_count,
        canonical_exam=False,
    )


def test_regrade_has_no_answer_model_seam_and_preserves_exact_historical_answers(tmp_path: Path) -> None:
    parameters = inspect.signature(regrade_checkpoints).parameters
    assert "answer_model" not in parameters
    assert "exercises" not in parameters
    assert "exercise_bank" in parameters

    bank = (_exercise(1), _exercise(2))
    selected = _selected(bank)
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    answers = ("  exact historical answer one  ", "Exact historical answer two")
    original = _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        selected,
        [
            _row(selected[0], answer=answers[0], grade="FAIL"),
            _row(selected[1], answer=answers[1], grade="PARTIAL", failure_codes=["incomplete_reasoning"]),
        ],
    )
    original_hash = hashlib.sha256(original).hexdigest()
    model = GraderOnlyModel()

    report = _regrade(
        bank=bank,
        grader_model=model,
        input_dir=input_dir,
        output_dir=output_dir,
        batch_size=2,
    )

    assert model.calls == 1
    assert model.answers_seen == {selected[0].exercise_id: answers[0], selected[1].exercise_id: answers[1]}
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
    assert report.run_seed == SEED
    assert report.answer_model_invoked is False
    assert report.training_ledger_mutated is False
    assert report.retention_authorized is False
    assert report.source_truth_authorized is False
    assert report.execution_authorized is False


@pytest.mark.parametrize("semantics", [GRADING_SEMANTICS, "unknown-grading/v99"])
def test_regrade_rejects_nonhistorical_semantics_before_model_or_output(
    tmp_path: Path, semantics: str
) -> None:
    bank = (_exercise(1),)
    selected = _selected(bank)
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        selected,
        [_row(selected[0], answer="Original")],
        semantics=semantics,
    )
    model = GraderOnlyModel()

    with pytest.raises(PyramidRegradeError, match="grading semantics"):
        _regrade(
            bank=bank,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            batch_size=1,
        )

    assert model.calls == 0
    assert not output_dir.exists()


def test_regrade_requires_exact_complete_batch_set_before_model_call(tmp_path: Path) -> None:
    bank = (_exercise(1), _exercise(2))
    selected = _selected(bank)
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        (selected[0],),
        [_row(selected[0], answer="First")],
    )
    model = GraderOnlyModel()

    with pytest.raises(PyramidRegradeError, match="batch set mismatch"):
        _regrade(
            bank=bank,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            batch_size=1,
        )

    assert model.calls == 0
    assert not output_dir.exists()


@pytest.mark.parametrize(
    "mode,match",
    [
        ("exercise_ids", "exercise ids"),
        ("duplicate_grade", "order/id mismatch"),
        ("empty_answer", "non-empty string"),
    ],
)
def test_regrade_fails_closed_on_mismatched_duplicate_or_malformed_historical_data(
    tmp_path: Path, mode: str, match: str
) -> None:
    bank = (_exercise(1), _exercise(2))
    selected = _selected(bank)
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    path = input_dir / "level_01_batch_0001.json"
    _write_checkpoint(
        path,
        selected,
        [_row(selected[0], answer="First"), _row(selected[1], answer="Second")],
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if mode == "exercise_ids":
        payload["exercise_ids"] = ["WRONG", selected[1].exercise_id]
    elif mode == "duplicate_grade":
        payload["grades"][1]["exercise_id"] = selected[0].exercise_id
    else:
        payload["grades"][0]["answer"] = ""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    model = GraderOnlyModel()

    with pytest.raises(PyramidRegradeError, match=match):
        _regrade(
            bank=bank,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            batch_size=2,
        )

    assert model.calls == 0
    assert not output_dir.exists()


def test_regrade_reconstructs_exact_seed_selected_identity_before_model(tmp_path: Path) -> None:
    bank = tuple(_exercise(index) for index in range(1, 7))
    original = _selected(bank, count=3)
    alternate_seed = None
    for index in range(100):
        candidate = f"alternate-{index}"
        if _selected(bank, seed=candidate, count=3) != original:
            alternate_seed = candidate
            break
    assert alternate_seed is not None

    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        original,
        [_row(item, answer=f"Original {item.exercise_id}") for item in original],
    )
    model = GraderOnlyModel()

    with pytest.raises(PyramidRegradeError, match="seed-selected exam"):
        _regrade(
            bank=bank,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            batch_size=3,
            seed=alternate_seed,
            question_count=3,
        )

    assert model.calls == 0
    assert not output_dir.exists()


def test_regrade_model_failure_leaves_no_partial_output(tmp_path: Path) -> None:
    bank = (_exercise(1), _exercise(2))
    selected = _selected(bank)
    input_dir = tmp_path / "historical"
    output_dir = tmp_path / "regraded"
    for index, exercise in enumerate(selected, start=1):
        _write_checkpoint(
            input_dir / f"level_01_batch_{index:04d}.json",
            (exercise,),
            [_row(exercise, answer=f"Original {index}")],
        )
    model = GraderOnlyModel(fail_on_call=2)

    with pytest.raises(RuntimeError, match="simulated grader failure"):
        _regrade(
            bank=bank,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            batch_size=1,
        )

    assert model.calls == 2
    assert not output_dir.exists()


@pytest.mark.parametrize("mode", ["same", "nested", "existing"])
def test_regrade_requires_new_separate_output_directory(tmp_path: Path, mode: str) -> None:
    bank = (_exercise(1),)
    selected = _selected(bank)
    input_dir = tmp_path / "historical"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        selected,
        [_row(selected[0], answer="Original")],
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
        _regrade(
            bank=bank,
            grader_model=model,
            input_dir=input_dir,
            output_dir=output_dir,
            batch_size=1,
        )

    assert model.calls == 0


def test_regrade_report_and_written_artifacts_are_deterministic(tmp_path: Path) -> None:
    bank = (_exercise(1), _exercise(2))
    selected = _selected(bank)
    input_dir = tmp_path / "historical"
    _write_checkpoint(
        input_dir / "level_01_batch_0001.json",
        selected,
        [
            _row(selected[0], answer="First", grade="FAIL"),
            _row(selected[1], answer="Second", grade="PASS"),
        ],
    )
    output_a = tmp_path / "regraded-a"
    output_b = tmp_path / "regraded-b"
    grades = {selected[0].exercise_id: "PARTIAL", selected[1].exercise_id: "PASS"}

    report_a = _regrade(
        bank=bank,
        grader_model=GraderOnlyModel(grades),
        input_dir=input_dir,
        output_dir=output_a,
        batch_size=2,
    )
    report_b = _regrade(
        bank=bank,
        grader_model=GraderOnlyModel(grades),
        input_dir=input_dir,
        output_dir=output_b,
        batch_size=2,
    )

    assert report_a.to_mapping() == report_b.to_mapping()
    assert (output_a / "regrade_report.json").read_bytes() == (output_b / "regrade_report.json").read_bytes()
    assert (output_a / "level_01_batch_0001.json").read_bytes() == (
        output_b / "level_01_batch_0001.json"
    ).read_bytes()
    assert dict(report_a.grade_transitions) == {"FAIL->PARTIAL": 1, "PASS->PASS": 1}
