from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable, Mapping, Sequence

from .pyramid import CANONICAL_LEVEL_QUESTION_COUNT, Exercise, select_level_exercises
from .pyramid_exam import (
    CHECKPOINT_SCHEMA,
    GRADING_SEMANTICS,
    GRADE_SCORES,
    GradedAnswer,
    grade_batch,
    summarize_exam,
)


PYRAMID_REGRADE_CONTRACT = "roberta-pyramid-regrade/v1"
PYRAMID_REGRADE_VERSION = "1.0.0"
HISTORICAL_GRADING_SEMANTICS = "question-first-adjudication/v1"


class PyramidRegradeError(RuntimeError):
    """Raised when historical Pyramid checkpoint state cannot be safely regraded."""


@dataclass(frozen=True, slots=True)
class RegradeReport:
    contract: str
    version: str
    curriculum_id: str
    level: int
    run_seed: str
    checkpoint_schema: str
    input_grading_semantics: str
    output_grading_semantics: str
    batch_size: int
    total_questions: int
    input_checkpoint_sha256: tuple[tuple[str, str], ...]
    old_grade_counts: tuple[tuple[str, int], ...]
    new_grade_counts: tuple[tuple[str, int], ...]
    old_weakness_count: int
    new_weakness_count: int
    old_accuracy: float
    new_accuracy: float
    old_critical_failures: int
    new_critical_failures: int
    old_passed: bool
    new_passed: bool
    old_failure_counts: tuple[tuple[str, int], ...]
    new_failure_counts: tuple[tuple[str, int], ...]
    grade_transitions: tuple[tuple[str, int], ...]
    answer_model_invoked: bool = False
    training_ledger_mutated: bool = False
    retention_authorized: bool = False
    source_truth_authorized: bool = False
    execution_authorized: bool = False

    def to_mapping(self) -> dict[str, object]:
        value = asdict(self)
        for name in (
            "input_checkpoint_sha256",
            "old_grade_counts",
            "new_grade_counts",
            "old_failure_counts",
            "new_failure_counts",
            "grade_transitions",
        ):
            value[name] = dict(value[name])
        return value


def _chunks(items: Sequence[Exercise], size: int) -> tuple[tuple[Exercise, ...], ...]:
    if size <= 0:
        raise PyramidRegradeError("batch_size must be positive")
    return tuple(tuple(items[index : index + size]) for index in range(0, len(items), size))


def _checkpoint_name(level: int, batch_index: int) -> str:
    return f"level_{level:02d}_batch_{batch_index:04d}.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_distinct_roots(input_dir: str | Path, output_dir: str | Path) -> tuple[Path, Path]:
    input_root = Path(input_dir).resolve()
    output_root = Path(output_dir).resolve()
    if input_root == output_root or input_root in output_root.parents or output_root in input_root.parents:
        raise PyramidRegradeError("input and output checkpoint directories must be separate non-nested paths")
    if not input_root.is_dir():
        raise PyramidRegradeError(f"input checkpoint directory does not exist: {input_root}")
    if output_root.exists():
        raise PyramidRegradeError(f"output checkpoint directory already exists: {output_root}")
    return input_root, output_root


def _historical_grade(raw: object, *, exercise_id: str, path: Path) -> GradedAnswer:
    if not isinstance(raw, Mapping):
        raise PyramidRegradeError(f"historical checkpoint grade must be an object: {path}")
    if raw.get("exercise_id") != exercise_id:
        raise PyramidRegradeError(f"historical checkpoint grade order/id mismatch for {exercise_id}: {path}")
    answer = raw.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise PyramidRegradeError(f"historical checkpoint answer must be a non-empty string for {exercise_id}: {path}")
    grade_name = str(raw.get("grade", "")).strip().upper()
    if grade_name not in GRADE_SCORES:
        raise PyramidRegradeError(f"invalid historical grade for {exercise_id}: {path}")
    try:
        score = float(raw.get("score", GRADE_SCORES[grade_name]))
    except (TypeError, ValueError) as exc:
        raise PyramidRegradeError(f"invalid historical score for {exercise_id}: {path}") from exc
    if not math.isfinite(score) or score != GRADE_SCORES[grade_name]:
        raise PyramidRegradeError(f"historical score does not match grade semantics for {exercise_id}: {path}")
    correct = raw.get("correct", grade_name == "PASS")
    if not isinstance(correct, bool) or correct != (grade_name == "PASS"):
        raise PyramidRegradeError(f"historical correct flag does not match grade for {exercise_id}: {path}")
    raw_codes = raw.get("failure_codes", [])
    if not isinstance(raw_codes, list) or not all(isinstance(code, str) for code in raw_codes):
        raise PyramidRegradeError(f"historical failure_codes must be strings for {exercise_id}: {path}")
    codes = tuple(sorted({code.strip() for code in raw_codes if code.strip()}))
    note = raw.get("grader_note", "")
    if not isinstance(note, str):
        raise PyramidRegradeError(f"historical grader_note must be a string for {exercise_id}: {path}")
    critical = raw.get("critical_failure", False)
    if not isinstance(critical, bool):
        raise PyramidRegradeError(f"historical critical_failure must be boolean for {exercise_id}: {path}")
    return GradedAnswer(
        exercise_id=exercise_id,
        answer=answer,
        grade=grade_name,
        score=score,
        correct=correct,
        failure_codes=codes,
        critical_failure=critical,
        grader_note=note,
    )


def _load_historical_batch(
    path: Path,
    exercises: Sequence[Exercise],
) -> tuple[bytes, tuple[GradedAnswer, ...]]:
    try:
        data = path.read_bytes()
        raw = json.loads(data.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PyramidRegradeError(f"invalid historical checkpoint {path}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise PyramidRegradeError(f"historical checkpoint must be an object: {path}")
    if raw.get("checkpoint_schema") != CHECKPOINT_SCHEMA:
        raise PyramidRegradeError(
            f"historical checkpoint schema must equal {CHECKPOINT_SCHEMA}: {path}"
        )
    if raw.get("grading_semantics") != HISTORICAL_GRADING_SEMANTICS:
        raise PyramidRegradeError(
            "historical checkpoint grading semantics must equal "
            f"{HISTORICAL_GRADING_SEMANTICS}: {path}"
        )
    expected_ids = [item.exercise_id for item in exercises]
    if raw.get("exercise_ids") != expected_ids:
        raise PyramidRegradeError(f"historical checkpoint exercise ids do not match seed-selected exam: {path}")
    grades_raw = raw.get("grades")
    if not isinstance(grades_raw, list) or len(grades_raw) != len(exercises):
        raise PyramidRegradeError(f"historical checkpoint grade count is invalid: {path}")
    grades = tuple(
        _historical_grade(row, exercise_id=exercise.exercise_id, path=path)
        for exercise, row in zip(exercises, grades_raw, strict=True)
    )
    grade_ids = [item.exercise_id for item in grades]
    if len(set(grade_ids)) != len(grade_ids):
        raise PyramidRegradeError(f"historical checkpoint contains duplicate grade ids: {path}")
    return data, grades


def _grade_counts(grades: Sequence[GradedAnswer]) -> tuple[tuple[str, int], ...]:
    counts = Counter(item.grade for item in grades)
    return tuple((name, counts.get(name, 0)) for name in ("PASS", "PARTIAL", "FAIL"))


def _failure_counts(grades: Sequence[GradedAnswer]) -> tuple[tuple[str, int], ...]:
    counts: Counter[str] = Counter()
    for item in grades:
        counts.update(item.failure_codes)
    return tuple(sorted(counts.items()))


def _weakness_count(grades: Sequence[GradedAnswer]) -> int:
    return sum(item.grade != "PASS" or item.critical_failure for item in grades)


def _checkpoint_payload(
    exercises: Sequence[Exercise],
    grades: Sequence[GradedAnswer],
    *,
    input_file: str,
    input_sha256: str,
) -> dict[str, object]:
    return {
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "grading_semantics": GRADING_SEMANTICS,
        "regrade_provenance": {
            "contract": PYRAMID_REGRADE_CONTRACT,
            "version": PYRAMID_REGRADE_VERSION,
            "input_checkpoint_file": input_file,
            "input_checkpoint_sha256": input_sha256,
            "input_grading_semantics": HISTORICAL_GRADING_SEMANTICS,
        },
        "exercise_ids": [item.exercise_id for item in exercises],
        "grades": [
            {
                "exercise_id": item.exercise_id,
                "answer": item.answer,
                "grade": item.grade,
                "score": item.score,
                "correct": item.correct,
                "failure_codes": list(item.failure_codes),
                "critical_failure": item.critical_failure,
                "grader_note": item.grader_note,
            }
            for item in grades
        ],
    }


def regrade_checkpoints(
    *,
    exercise_bank: Sequence[Exercise],
    grader_model: Any,
    input_dir: str | Path,
    output_dir: str | Path,
    curriculum_id: str,
    level: int,
    run_seed: str,
    batch_size: int = 10,
    question_count: int = CANONICAL_LEVEL_QUESTION_COUNT,
    canonical_exam: bool = True,
    progress: Callable[[int, int], None] | None = None,
) -> RegradeReport:
    expected_curriculum = str(curriculum_id).strip()
    if not expected_curriculum:
        raise PyramidRegradeError("curriculum_id is required")
    if question_count <= 0:
        raise PyramidRegradeError("question_count must be positive")
    if canonical_exam and question_count != CANONICAL_LEVEL_QUESTION_COUNT:
        raise PyramidRegradeError(
            f"canonical regrade requires exactly {CANONICAL_LEVEL_QUESTION_COUNT} questions"
        )
    try:
        exercises = select_level_exercises(
            exercise_bank,
            curriculum_id=expected_curriculum,
            level=level,
            run_seed=run_seed,
            count=question_count,
        )
    except ValueError as exc:
        raise PyramidRegradeError(f"cannot reconstruct seed-selected Pyramid exam: {exc}") from exc

    input_root, output_root = _resolve_distinct_roots(input_dir, output_dir)
    batches = _chunks(exercises, batch_size)
    expected_names = tuple(_checkpoint_name(level, index) for index in range(1, len(batches) + 1))
    actual_names = tuple(sorted(path.name for path in input_root.glob(f"level_{level:02d}_batch_*.json")))
    if actual_names != tuple(sorted(expected_names)):
        missing = sorted(set(expected_names) - set(actual_names))
        extra = sorted(set(actual_names) - set(expected_names))
        raise PyramidRegradeError(
            f"historical checkpoint batch set mismatch; missing={missing}, extra={extra}"
        )

    # Validate every historical batch and capture its exact bytes before making
    # any model call or writing any output artifact.
    historical_batches: list[tuple[tuple[Exercise, ...], str, bytes, tuple[GradedAnswer, ...]]] = []
    for batch, filename in zip(batches, expected_names, strict=True):
        data, grades = _load_historical_batch(input_root / filename, batch)
        historical_batches.append((batch, filename, data, grades))

    old_grades = tuple(grade for _, _, _, grades in historical_batches for grade in grades)
    new_batches: list[tuple[tuple[Exercise, ...], str, str, tuple[GradedAnswer, ...]]] = []
    done = 0
    for batch, filename, data, historical in historical_batches:
        answers = {item.exercise_id: item.answer for item in historical}
        regraded = grade_batch(grader_model, batch, answers)
        if tuple(item.exercise_id for item in regraded) != tuple(item.exercise_id for item in batch):
            raise PyramidRegradeError(f"regraded exercise order changed for {filename}")
        for old, new in zip(historical, regraded, strict=True):
            if new.answer != old.answer:
                raise PyramidRegradeError(
                    f"regrade changed Roberta's historical answer for {old.exercise_id}"
                )
        input_digest = _sha256(data)
        new_batches.append((batch, filename, input_digest, regraded))
        done += len(batch)
        if progress is not None:
            progress(done, len(exercises))

    new_grades = tuple(grade for _, _, _, grades in new_batches for grade in grades)
    old_outcome = summarize_exam(exercises, old_grades, canonical_exam=canonical_exam)
    new_outcome = summarize_exam(exercises, new_grades, canonical_exam=canonical_exam)
    transitions = Counter(
        f"{old.grade}->{new.grade}" for old, new in zip(old_grades, new_grades, strict=True)
    )
    input_hashes = tuple((filename, _sha256(data)) for _, filename, data, _ in historical_batches)
    report = RegradeReport(
        contract=PYRAMID_REGRADE_CONTRACT,
        version=PYRAMID_REGRADE_VERSION,
        curriculum_id=expected_curriculum,
        level=level,
        run_seed=str(run_seed),
        checkpoint_schema=CHECKPOINT_SCHEMA,
        input_grading_semantics=HISTORICAL_GRADING_SEMANTICS,
        output_grading_semantics=GRADING_SEMANTICS,
        batch_size=batch_size,
        total_questions=len(exercises),
        input_checkpoint_sha256=input_hashes,
        old_grade_counts=_grade_counts(old_grades),
        new_grade_counts=_grade_counts(new_grades),
        old_weakness_count=_weakness_count(old_grades),
        new_weakness_count=_weakness_count(new_grades),
        old_accuracy=old_outcome.level_result.accuracy,
        new_accuracy=new_outcome.level_result.accuracy,
        old_critical_failures=old_outcome.level_result.critical_failures,
        new_critical_failures=new_outcome.level_result.critical_failures,
        old_passed=old_outcome.level_result.passed,
        new_passed=new_outcome.level_result.passed,
        old_failure_counts=_failure_counts(old_grades),
        new_failure_counts=_failure_counts(new_grades),
        grade_transitions=tuple(sorted(transitions.items())),
    )

    output_root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.tmp-", dir=output_root.parent))
    try:
        for batch, filename, input_digest, regraded in new_batches:
            payload = _checkpoint_payload(
                batch,
                regraded,
                input_file=filename,
                input_sha256=input_digest,
            )
            (stage / filename).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        (stage / "regrade_report.json").write_text(
            json.dumps(report.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(stage, output_root)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return report
