from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable, Mapping, Sequence

from .pyramid import (
    CANONICAL_LEVEL_QUESTION_COUNT,
    Exercise,
    SUPPORTED_CANONICAL_LEVEL_QUESTION_COUNTS,
    select_level_exercises,
)
from .pyramid_exam import (
    CHECKPOINT_SCHEMA,
    GRADING_SEMANTICS,
    GRADE_SCORES,
    PREVIOUS_GRADING_SEMANTICS,
    GradedAnswer,
    _write_checkpoint,
    summarize_exam,
    validate_critical_proposals,
)


CRITICAL_REVALIDATION_CONTRACT = "roberta-pyramid-critical-revalidation/v1"
CRITICAL_REVALIDATION_VERSION = "1.0.0"


class CriticalRevalidationError(RuntimeError):
    """Raised when saved Pyramid grades cannot be revalidated safely."""


@dataclass(frozen=True, slots=True)
class CriticalRevalidationReport:
    contract: str
    version: str
    curriculum_id: str
    level: int
    run_seed: str
    checkpoint_schema: str
    input_grading_semantics: str
    output_grading_semantics: str
    total_questions: int
    old_accuracy: float
    new_accuracy: float
    old_critical_failures: int
    new_critical_failures: int
    old_passed: bool
    new_passed: bool
    critical_ids_before: tuple[str, ...]
    critical_ids_after: tuple[str, ...]
    input_checkpoint_sha256: tuple[tuple[str, str], ...]

    def to_mapping(self) -> dict[str, object]:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _chunked(items: Sequence[Exercise], size: int) -> tuple[tuple[Exercise, ...], ...]:
    if size <= 0:
        raise ValueError("batch_size must be positive")
    return tuple(tuple(items[index : index + size]) for index in range(0, len(items), size))


def _load_saved_batch(path: Path, exercises: Sequence[Exercise]) -> tuple[GradedAnswer, ...]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CriticalRevalidationError(f"invalid checkpoint {path}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise CriticalRevalidationError(f"invalid checkpoint structure: {path}")
    if raw.get("checkpoint_schema") != CHECKPOINT_SCHEMA:
        raise CriticalRevalidationError(
            f"checkpoint schema must equal {CHECKPOINT_SCHEMA}: {path}"
        )
    if raw.get("grading_semantics") != PREVIOUS_GRADING_SEMANTICS:
        raise CriticalRevalidationError(
            "checkpoint grading semantics must equal "
            f"{PREVIOUS_GRADING_SEMANTICS}: {path}"
        )
    rows = raw.get("grades")
    if not isinstance(rows, list):
        raise CriticalRevalidationError(f"checkpoint grades must be an array: {path}")
    expected_ids = [item.exercise_id for item in exercises]
    if raw.get("exercise_ids") != expected_ids:
        raise CriticalRevalidationError(f"checkpoint exercise ids do not match selected exam: {path}")

    result: list[GradedAnswer] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise CriticalRevalidationError(f"invalid checkpoint grade entry: {path}")

        exercise_id_raw = row.get("exercise_id")
        answer_raw = row.get("answer")
        grade_raw = row.get("grade")
        score_raw = row.get("score")
        correct_raw = row.get("correct")
        critical_raw = row.get("critical_failure")
        grader_note_raw = row.get("grader_note")

        if not isinstance(exercise_id_raw, str) or not exercise_id_raw.strip():
            raise CriticalRevalidationError(f"checkpoint exercise_id must be a non-empty string: {path}")
        exercise_id = exercise_id_raw.strip()
        if exercise_id != exercise_id_raw:
            raise CriticalRevalidationError(f"checkpoint exercise_id must be normalized: {path}")
        if not isinstance(answer_raw, str) or not answer_raw.strip():
            raise CriticalRevalidationError(f"checkpoint answer must be a non-empty string: {path}")
        if not isinstance(grade_raw, str) or grade_raw not in GRADE_SCORES:
            raise CriticalRevalidationError(f"invalid checkpoint grade value: {path}")
        grade_name = grade_raw
        if isinstance(score_raw, bool) or not isinstance(score_raw, (int, float)):
            raise CriticalRevalidationError(f"checkpoint score must be numeric: {path}")
        score = float(score_raw)
        if not math.isfinite(score) or score != GRADE_SCORES[grade_name]:
            raise CriticalRevalidationError(f"checkpoint score does not match grade semantics: {path}")
        if not isinstance(correct_raw, bool) or correct_raw is not (grade_name == "PASS"):
            raise CriticalRevalidationError(f"checkpoint correct flag does not match grade semantics: {path}")
        if not isinstance(critical_raw, bool):
            raise CriticalRevalidationError(f"checkpoint critical_failure must be boolean: {path}")
        if not isinstance(grader_note_raw, str):
            raise CriticalRevalidationError(f"checkpoint grader_note must be a string: {path}")

        raw_codes = row.get("failure_codes")
        if not isinstance(raw_codes, list) or not all(isinstance(code, str) for code in raw_codes):
            raise CriticalRevalidationError(f"invalid checkpoint failure codes: {path}")
        normalized_codes = tuple(sorted({code.strip() for code in raw_codes if code.strip()}))
        if list(normalized_codes) != sorted(set(raw_codes)):
            raise CriticalRevalidationError(f"checkpoint failure codes must be normalized and unique: {path}")

        result.append(
            GradedAnswer(
                exercise_id=exercise_id,
                answer=answer_raw,
                grade=grade_name,
                score=score,
                correct=correct_raw,
                failure_codes=normalized_codes,
                critical_failure=critical_raw,
                grader_note=grader_note_raw,
            )
        )
    if [item.exercise_id for item in result] != expected_ids:
        raise CriticalRevalidationError(f"checkpoint grade order does not match selected exam: {path}")
    return tuple(result)


def _reject_unsafe_output(input_root: Path, output_root: Path) -> None:
    input_resolved = input_root.resolve()
    output_resolved = output_root.resolve()
    if input_resolved == output_resolved:
        raise CriticalRevalidationError("output checkpoints must be separate from input checkpoints")
    if input_resolved in output_resolved.parents or output_resolved in input_resolved.parents:
        raise CriticalRevalidationError("input and output checkpoint directories must not be nested")
    if output_root.exists():
        raise CriticalRevalidationError(f"output checkpoint directory already exists: {output_root}")


def revalidate_critical_checkpoints(
    *,
    exercise_bank: Sequence[Exercise],
    grader_model: Any,
    input_dir: str | Path,
    output_dir: str | Path,
    curriculum_id: str,
    level: int,
    run_seed: str,
    batch_size: int = 10,
    canonical_exam: bool = True,
    question_count: int = CANONICAL_LEVEL_QUESTION_COUNT,
    progress: Callable[[int, int], None] | None = None,
) -> CriticalRevalidationReport:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if canonical_exam and question_count not in SUPPORTED_CANONICAL_LEVEL_QUESTION_COUNTS:
        supported = ", ".join(str(value) for value in SUPPORTED_CANONICAL_LEVEL_QUESTION_COUNTS)
        raise ValueError(
            f"canonical critical revalidation requires a supported question count: {supported}"
        )

    input_root = Path(input_dir)
    output_root = Path(output_dir)
    if not input_root.is_dir():
        raise CriticalRevalidationError(f"input checkpoint directory does not exist: {input_root}")
    _reject_unsafe_output(input_root, output_root)

    selected = select_level_exercises(
        exercise_bank,
        curriculum_id=curriculum_id,
        level=level,
        run_seed=run_seed,
        count=question_count,
    )
    batches = _chunked(selected, batch_size)
    expected_paths = tuple(
        input_root / f"level_{level:02d}_batch_{index:04d}.json"
        for index in range(1, len(batches) + 1)
    )
    missing = [str(path) for path in expected_paths if not path.is_file()]
    if missing:
        raise CriticalRevalidationError(f"missing input checkpoints: {missing[:5]}")

    input_hashes_before = tuple((path.name, _sha256(path)) for path in expected_paths)
    old_all: list[GradedAnswer] = []
    new_all: list[GradedAnswer] = []

    output_root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{output_root.name}.tmp-",
            dir=str(output_root.parent),
        )
    )
    try:
        done = 0
        for index, (batch, input_path) in enumerate(zip(batches, expected_paths), start=1):
            old_batch = _load_saved_batch(input_path, batch)
            new_batch = validate_critical_proposals(grader_model, batch, old_batch)
            old_all.extend(old_batch)
            new_all.extend(new_batch)
            _write_checkpoint(
                temporary / f"level_{level:02d}_batch_{index:04d}.json",
                batch,
                new_batch,
            )
            done += len(batch)
            if progress is not None:
                progress(done, len(selected))

        input_hashes_after = tuple((path.name, _sha256(path)) for path in expected_paths)
        if input_hashes_after != input_hashes_before:
            raise CriticalRevalidationError("input checkpoints changed during read-only revalidation")

        strict_current_contract = canonical_exam and question_count == CANONICAL_LEVEL_QUESTION_COUNT
        old_outcome = summarize_exam(selected, old_all, canonical_exam=strict_current_contract)
        new_outcome = summarize_exam(selected, new_all, canonical_exam=strict_current_contract)
        old_critical = tuple(item.exercise_id for item in old_all if item.critical_failure)
        new_critical = tuple(item.exercise_id for item in new_all if item.critical_failure)
        report = CriticalRevalidationReport(
            contract=CRITICAL_REVALIDATION_CONTRACT,
            version=CRITICAL_REVALIDATION_VERSION,
            curriculum_id=curriculum_id,
            level=level,
            run_seed=str(run_seed),
            checkpoint_schema=CHECKPOINT_SCHEMA,
            input_grading_semantics=PREVIOUS_GRADING_SEMANTICS,
            output_grading_semantics=GRADING_SEMANTICS,
            total_questions=len(selected),
            old_accuracy=old_outcome.level_result.accuracy,
            new_accuracy=new_outcome.level_result.accuracy,
            old_critical_failures=old_outcome.level_result.critical_failures,
            new_critical_failures=new_outcome.level_result.critical_failures,
            old_passed=old_outcome.level_result.passed,
            new_passed=new_outcome.level_result.passed,
            critical_ids_before=old_critical,
            critical_ids_after=new_critical,
            input_checkpoint_sha256=input_hashes_before,
        )
        (temporary / "critical_revalidation_report.json").write_text(
            json.dumps(report.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(output_root)
        return report
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
