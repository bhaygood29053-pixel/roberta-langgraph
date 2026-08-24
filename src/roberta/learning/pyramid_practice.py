from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .curriculum_io import validate_package
from .pyramid import Exercise, get_level_spec
from .pyramid_exam import GradedAnswer, run_exam
from .pyramid_remediation import PYRAMID_REMEDIATION_PRACTICE_BINDING_CONTRACT
from .pyramid_source_reconstruction import (
    PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT,
    PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE,
    PYRAMID_SOURCE_RECONSTRUCTION_VERSION,
)


TARGETED_PRACTICE_CONTRACT = "roberta-pyramid-targeted-practice/v1"
TARGETED_PRACTICE_VERSION = "1.0.0"
TARGETED_PRACTICE_PASS_NEXT_GATE = "new_canonical_level_1_attempt"
TARGETED_PRACTICE_FAIL_NEXT_GATE = "targeted_pyramid_remediation"

_PRACTICE_FIELDS = frozenset(
    {
        "exercise_id",
        "level",
        "concept",
        "subconcept",
        "question",
        "source_refs",
        "integrity_question",
    }
)
_AUTHORITY_FIELDS = (
    "phase8_candidate_creation_authorized",
    "source_truth_authorized",
    "live_state_authorized",
    "memory_promotion_authorized",
    "retention_authorized",
    "governance_mutation_authorized",
    "execution_authorized",
)


class TargetedPyramidPracticeError(RuntimeError):
    """Raised when targeted practice inputs or verification state fail closed."""


WeaknessKey = tuple[str, str | None]


@dataclass(frozen=True, slots=True)
class PreparedTargetedPractice:
    curriculum_id: str
    level: int
    exercises: tuple[Exercise, ...]
    weakness_critical_counts: tuple[tuple[str, str | None, int], ...]
    original_weak_ids: tuple[str, ...]
    source_grounded_weak_items: int

    @property
    def critical_weakness_keys(self) -> frozenset[WeaknessKey]:
        return frozenset(
            (concept, subconcept)
            for concept, subconcept, critical_count in self.weakness_critical_counts
            if critical_count > 0
        )


@dataclass(frozen=True, slots=True)
class WeaknessPracticeResult:
    concept: str
    subconcept: str | None
    total: int
    pass_count: int
    partial_count: int
    fail_count: int
    critical_failures: int
    earned_points: float
    accuracy: float
    critical_origin: bool
    passed: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "concept": self.concept,
            "subconcept": self.subconcept,
            "total": self.total,
            "pass_count": self.pass_count,
            "partial_count": self.partial_count,
            "fail_count": self.fail_count,
            "critical_failures": self.critical_failures,
            "earned_points": self.earned_points,
            "accuracy": self.accuracy,
            "critical_origin": self.critical_origin,
            "passed": self.passed,
        }


@dataclass(frozen=True, slots=True)
class TargetedPracticeReport:
    contract: str
    version: str
    curriculum_id: str
    level: int
    question_count: int
    pass_count: int
    partial_count: int
    fail_count: int
    earned_points: float
    accuracy: float
    required_accuracy: float
    critical_failures: int
    source_grounded_weak_items: int
    weakness_results: tuple[WeaknessPracticeResult, ...]
    all_weaknesses_passed: bool
    critical_weaknesses_passed: bool
    practice_passed: bool
    next_gate: str
    canonical_attempt_authorized: bool
    phase8_candidate_creation_authorized: bool = False
    source_truth_authorized: bool = False
    live_state_authorized: bool = False
    memory_promotion_authorized: bool = False
    retention_authorized: bool = False
    governance_mutation_authorized: bool = False
    execution_authorized: bool = False

    def to_mapping(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "version": self.version,
            "curriculum_id": self.curriculum_id,
            "level": self.level,
            "question_count": self.question_count,
            "pass_count": self.pass_count,
            "partial_count": self.partial_count,
            "fail_count": self.fail_count,
            "earned_points": self.earned_points,
            "accuracy": self.accuracy,
            "required_accuracy": self.required_accuracy,
            "critical_failures": self.critical_failures,
            "source_grounded_weak_items": self.source_grounded_weak_items,
            "weakness_results": [item.to_mapping() for item in self.weakness_results],
            "all_weaknesses_passed": self.all_weaknesses_passed,
            "critical_weaknesses_passed": self.critical_weaknesses_passed,
            "practice_passed": self.practice_passed,
            "next_gate": self.next_gate,
            "canonical_attempt_authorized": self.canonical_attempt_authorized,
            "phase8_candidate_creation_authorized": self.phase8_candidate_creation_authorized,
            "source_truth_authorized": self.source_truth_authorized,
            "live_state_authorized": self.live_state_authorized,
            "memory_promotion_authorized": self.memory_promotion_authorized,
            "retention_authorized": self.retention_authorized,
            "governance_mutation_authorized": self.governance_mutation_authorized,
            "execution_authorized": self.execution_authorized,
        }


def _read_json_object(path: str | Path, *, label: str) -> Mapping[str, object]:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TargetedPyramidPracticeError(f"cannot read {label}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise TargetedPyramidPracticeError(f"{label} must be a JSON object")
    return raw


def _read_jsonl(path: str | Path, *, label: str) -> tuple[Mapping[str, object], ...]:
    source = Path(path)
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise TargetedPyramidPracticeError(f"cannot read {label}: {exc}") from exc
    rows: list[Mapping[str, object]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TargetedPyramidPracticeError(
                f"invalid {label} JSONL at line {line_number}: {exc}"
            ) from exc
        if not isinstance(raw, Mapping):
            raise TargetedPyramidPracticeError(f"{label} row {line_number} must be an object")
        rows.append(raw)
    if not rows:
        raise TargetedPyramidPracticeError(f"{label} must not be empty")
    return tuple(rows)


def _weakness_key(concept: object, subconcept: object) -> WeaknessKey:
    if not isinstance(concept, str) or not concept.strip() or concept != concept.strip():
        raise TargetedPyramidPracticeError("weakness concept must be a normalized non-empty string")
    if subconcept is not None and (
        not isinstance(subconcept, str)
        or not subconcept.strip()
        or subconcept != subconcept.strip()
    ):
        raise TargetedPyramidPracticeError(
            "weakness subconcept must be null or a normalized non-empty string"
        )
    return concept, subconcept


def _parse_remediation_plan(
    plan_path: str | Path,
    *,
    curriculum_id: str,
) -> tuple[
    dict[WeaknessKey, int],
    tuple[str, ...],
    int,
    tuple[str, ...] | None,
    str | None,
]:
    raw = _read_json_object(plan_path, label="remediation plan")
    if raw.get("curriculum_id") != curriculum_id:
        raise TargetedPyramidPracticeError(
            "remediation plan curriculum_id does not match validated curriculum"
        )
    weaknesses = raw.get("weaknesses")
    if not isinstance(weaknesses, list) or not weaknesses:
        raise TargetedPyramidPracticeError(
            "remediation plan weaknesses must be a non-empty array"
        )

    critical_counts: dict[WeaknessKey, int] = {}
    original_ids: list[str] = []
    for item in weaknesses:
        if not isinstance(item, Mapping):
            raise TargetedPyramidPracticeError("remediation weakness entries must be objects")
        key = _weakness_key(item.get("concept"), item.get("subconcept"))
        if key in critical_counts:
            raise TargetedPyramidPracticeError(f"duplicate remediation weakness {key}")
        critical_count = item.get("critical_count")
        if (
            isinstance(critical_count, bool)
            or not isinstance(critical_count, int)
            or critical_count < 0
        ):
            raise TargetedPyramidPracticeError(
                "remediation critical_count must be a non-negative integer"
            )
        ids = item.get("exercise_ids")
        if (
            not isinstance(ids, list)
            or not ids
            or not all(isinstance(value, str) and value for value in ids)
        ):
            raise TargetedPyramidPracticeError(
                "remediation exercise_ids must be a non-empty array of strings"
            )
        critical_counts[key] = critical_count
        original_ids.extend(ids)

    if len(original_ids) != len(set(original_ids)):
        raise TargetedPyramidPracticeError(
            "remediation weak exercise ids must be unique across weaknesses"
        )
    weak_item_count = raw.get("weak_item_count")
    if isinstance(weak_item_count, bool) or not isinstance(weak_item_count, int):
        raise TargetedPyramidPracticeError("remediation weak_item_count must be an integer")
    if weak_item_count != len(original_ids):
        raise TargetedPyramidPracticeError(
            "remediation weak_item_count does not match weakness exercise ids"
        )
    weakness_count = raw.get("weakness_count")
    if isinstance(weakness_count, bool) or not isinstance(weakness_count, int):
        raise TargetedPyramidPracticeError("remediation weakness_count must be an integer")
    if weakness_count != len(critical_counts):
        raise TargetedPyramidPracticeError(
            "remediation weakness_count does not match weakness entries"
        )
    practice_count = raw.get("practice_question_count")
    if (
        isinstance(practice_count, bool)
        or not isinstance(practice_count, int)
        or practice_count <= 0
    ):
        raise TargetedPyramidPracticeError(
            "remediation practice_question_count must be a positive integer"
        )

    binding_markers = (
        "practice_binding_contract",
        "practice_exercise_ids",
        "practice_sha256",
        "excluded_seen_exercise_count",
        "excluded_checkpoint_dirs",
    )
    has_binding_metadata = any(field in raw for field in binding_markers)
    if not has_binding_metadata:
        return critical_counts, tuple(original_ids), practice_count, None, None

    if raw.get("practice_binding_contract") != PYRAMID_REMEDIATION_PRACTICE_BINDING_CONTRACT:
        raise TargetedPyramidPracticeError(
            "remediation plan practice binding contract is missing or unsupported"
        )
    practice_ids = raw.get("practice_exercise_ids")
    if (
        not isinstance(practice_ids, list)
        or len(practice_ids) != practice_count
        or not all(isinstance(value, str) and value for value in practice_ids)
        or len(practice_ids) != len(set(practice_ids))
    ):
        raise TargetedPyramidPracticeError(
            "remediation practice_exercise_ids must be unique strings matching practice_question_count"
        )
    practice_sha256 = raw.get("practice_sha256")
    if (
        not isinstance(practice_sha256, str)
        or len(practice_sha256) != 64
        or any(character not in "0123456789abcdef" for character in practice_sha256)
    ):
        raise TargetedPyramidPracticeError(
            "remediation practice_sha256 must be a lowercase SHA-256 digest"
        )
    return (
        critical_counts,
        tuple(original_ids),
        practice_count,
        tuple(practice_ids),
        practice_sha256,
    )


def _validate_reconstruction_coverage(
    reconstructions_path: str | Path,
    *,
    curriculum_id: str,
    original_weak_ids: Sequence[str],
) -> int:
    rows = _read_jsonl(reconstructions_path, label="source-grounded reconstructions")
    expected_ids = set(original_weak_ids)
    seen: set[str] = set()
    for row in rows:
        exercise_id = row.get("exercise_id")
        if not isinstance(exercise_id, str) or not exercise_id:
            raise TargetedPyramidPracticeError(
                "reconstruction exercise_id must be a non-empty string"
            )
        if exercise_id in seen:
            raise TargetedPyramidPracticeError(f"duplicate reconstruction for {exercise_id}")
        seen.add(exercise_id)
        if row.get("curriculum_id") != curriculum_id:
            raise TargetedPyramidPracticeError(
                "reconstruction curriculum_id does not match validated curriculum"
            )
        if row.get("reconstruction_contract") != PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT:
            raise TargetedPyramidPracticeError("unsupported source reconstruction contract")
        if row.get("reconstruction_version") != PYRAMID_SOURCE_RECONSTRUCTION_VERSION:
            raise TargetedPyramidPracticeError("unsupported source reconstruction version")
        if row.get("source_grounded") is not True:
            raise TargetedPyramidPracticeError(
                f"reconstruction is not source grounded for {exercise_id}"
            )
        if row.get("evidence_packet_status") != "ok":
            raise TargetedPyramidPracticeError(
                f"reconstruction evidence packet is not ok for {exercise_id}"
            )
        anchors = row.get("evidence_anchors")
        if not isinstance(anchors, list) or not anchors:
            raise TargetedPyramidPracticeError(
                f"reconstruction has no evidence anchors for {exercise_id}"
            )
        if row.get("required_next_gate") != PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE:
            raise TargetedPyramidPracticeError(
                f"reconstruction next gate is invalid for {exercise_id}"
            )
        for field in _AUTHORITY_FIELDS:
            if row.get(field) is not False:
                raise TargetedPyramidPracticeError(
                    f"reconstruction cannot authorize {field} for {exercise_id}"
                )

    if seen != expected_ids:
        missing = sorted(expected_ids - seen)
        extra = sorted(seen - expected_ids)
        raise TargetedPyramidPracticeError(
            "reconstruction coverage does not match original weak items; "
            f"missing={missing}, extra={extra}"
        )
    return len(seen)


def _resolve_practice_exercises(
    practice_path: str | Path,
    *,
    bank: Sequence[Exercise],
    weakness_keys: set[WeaknessKey],
    original_weak_ids: set[str],
    expected_count: int,
    expected_practice_ids: tuple[str, ...] | None = None,
    expected_practice_sha256: str | None = None,
) -> tuple[Exercise, ...]:
    if expected_practice_sha256 is not None:
        source = Path(practice_path)
        try:
            actual_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        except OSError as exc:
            raise TargetedPyramidPracticeError(f"cannot read targeted practice: {exc}") from exc
        if actual_sha256 != expected_practice_sha256:
            raise TargetedPyramidPracticeError(
                "targeted practice SHA-256 does not match remediation plan binding"
            )

    rows = _read_jsonl(practice_path, label="targeted practice")
    if len(rows) != expected_count:
        raise TargetedPyramidPracticeError(
            f"targeted practice count does not match remediation plan: {len(rows)} != {expected_count}"
        )
    by_id = {item.exercise_id: item for item in bank}
    if len(by_id) != len(bank):
        raise TargetedPyramidPracticeError(
            "validated curriculum contains duplicate exercise ids"
        )

    selected: list[Exercise] = []
    selected_ids: set[str] = set()
    represented: set[WeaknessKey] = set()
    for row in rows:
        if set(row) != _PRACTICE_FIELDS:
            missing = sorted(_PRACTICE_FIELDS - set(row))
            extra = sorted(set(row) - _PRACTICE_FIELDS)
            raise TargetedPyramidPracticeError(
                "targeted practice row fields do not match contract; "
                f"missing={missing}, extra={extra}"
            )
        exercise_id = row.get("exercise_id")
        if not isinstance(exercise_id, str) or not exercise_id:
            raise TargetedPyramidPracticeError(
                "targeted practice exercise_id must be a non-empty string"
            )
        if exercise_id in selected_ids:
            raise TargetedPyramidPracticeError(
                f"duplicate targeted practice exercise {exercise_id}"
            )
        exercise = by_id.get(exercise_id)
        if exercise is None:
            raise TargetedPyramidPracticeError(
                f"targeted practice exercise {exercise_id} is absent from curriculum"
            )
        if exercise_id in original_weak_ids:
            raise TargetedPyramidPracticeError(
                f"targeted practice exercise {exercise_id} is not fresh"
            )
        if exercise.boss_question:
            raise TargetedPyramidPracticeError(
                f"targeted practice cannot include Boss Question {exercise_id}"
            )
        source_refs = row.get("source_refs")
        if (
            not isinstance(source_refs, list)
            or not all(isinstance(value, str) for value in source_refs)
        ):
            raise TargetedPyramidPracticeError(
                "targeted practice source_refs must be an array of strings"
            )
        expected = (
            exercise.level,
            exercise.concept,
            exercise.subconcept,
            exercise.question,
            exercise.source_refs,
            exercise.integrity_question,
        )
        actual = (
            row.get("level"),
            row.get("concept"),
            row.get("subconcept"),
            row.get("question"),
            tuple(source_refs),
            row.get("integrity_question"),
        )
        if actual != expected:
            raise TargetedPyramidPracticeError(
                "targeted practice row does not match validated curriculum exercise "
                f"{exercise_id}"
            )
        key = (exercise.concept, exercise.subconcept)
        if key not in weakness_keys:
            raise TargetedPyramidPracticeError(
                f"targeted practice exercise {exercise_id} is outside remediation weaknesses"
            )
        represented.add(key)
        selected_ids.add(exercise_id)
        selected.append(exercise)

    if expected_practice_ids is not None:
        actual_ids = tuple(item.exercise_id for item in selected)
        if actual_ids != expected_practice_ids:
            raise TargetedPyramidPracticeError(
                "targeted practice exercise ids do not match remediation plan binding"
            )
    if represented != weakness_keys:
        missing = sorted(
            weakness_keys - represented,
            key=lambda item: (item[0], item[1] or ""),
        )
        raise TargetedPyramidPracticeError(
            f"targeted practice does not cover every remediation weakness: {missing}"
        )
    levels = {item.level for item in selected}
    if len(levels) != 1:
        raise TargetedPyramidPracticeError(
            "targeted practice must cover exactly one Pyramid level"
        )
    return tuple(selected)


def prepare_targeted_practice(
    *,
    curriculum_dir: str | Path,
    practice_path: str | Path,
    remediation_plan_path: str | Path,
    reconstructions_path: str | Path,
) -> PreparedTargetedPractice:
    manifest, bank = validate_package(curriculum_dir)
    curriculum_id = str(manifest["curriculum_id"])
    (
        critical_counts,
        original_weak_ids,
        expected_count,
        expected_practice_ids,
        expected_practice_sha256,
    ) = _parse_remediation_plan(
        remediation_plan_path,
        curriculum_id=curriculum_id,
    )
    grounded_count = _validate_reconstruction_coverage(
        reconstructions_path,
        curriculum_id=curriculum_id,
        original_weak_ids=original_weak_ids,
    )
    exercises = _resolve_practice_exercises(
        practice_path,
        bank=bank,
        weakness_keys=set(critical_counts),
        original_weak_ids=set(original_weak_ids),
        expected_count=expected_count,
        expected_practice_ids=expected_practice_ids,
        expected_practice_sha256=expected_practice_sha256,
    )
    return PreparedTargetedPractice(
        curriculum_id=curriculum_id,
        level=exercises[0].level,
        exercises=exercises,
        weakness_critical_counts=tuple(
            (concept, subconcept, critical_counts[(concept, subconcept)])
            for concept, subconcept in sorted(
                critical_counts,
                key=lambda item: (item[0], item[1] or ""),
            )
        ),
        original_weak_ids=tuple(original_weak_ids),
        source_grounded_weak_items=grounded_count,
    )


def evaluate_targeted_practice(
    prepared: PreparedTargetedPractice,
    grades: Sequence[GradedAnswer],
) -> TargetedPracticeReport:
    if len(grades) != len(prepared.exercises):
        raise TargetedPyramidPracticeError(
            "practice grade count does not match prepared exercises"
        )
    exercise_by_id = {item.exercise_id: item for item in prepared.exercises}
    grade_by_id = {item.exercise_id: item for item in grades}
    if len(grade_by_id) != len(grades) or set(grade_by_id) != set(exercise_by_id):
        raise TargetedPyramidPracticeError(
            "practice grade ids do not match prepared exercises"
        )

    required_accuracy = get_level_spec(prepared.level).pass_accuracy
    critical_keys = prepared.critical_weakness_keys
    grouped: dict[WeaknessKey, list[GradedAnswer]] = {}
    for exercise in prepared.exercises:
        grouped.setdefault((exercise.concept, exercise.subconcept), []).append(
            grade_by_id[exercise.exercise_id]
        )

    weakness_results: list[WeaknessPracticeResult] = []
    for key in sorted(grouped, key=lambda item: (item[0], item[1] or "")):
        items = grouped[key]
        pass_count = sum(1 for item in items if item.grade == "PASS")
        partial_count = sum(1 for item in items if item.grade == "PARTIAL")
        fail_count = sum(1 for item in items if item.grade == "FAIL")
        critical_failures = sum(1 for item in items if item.critical_failure)
        points = sum(item.score for item in items)
        accuracy = points / len(items)
        critical_origin = key in critical_keys
        group_passed = (
            pass_count == len(items) and critical_failures == 0
            if critical_origin
            else accuracy >= required_accuracy and critical_failures == 0
        )
        weakness_results.append(
            WeaknessPracticeResult(
                concept=key[0],
                subconcept=key[1],
                total=len(items),
                pass_count=pass_count,
                partial_count=partial_count,
                fail_count=fail_count,
                critical_failures=critical_failures,
                earned_points=points,
                accuracy=accuracy,
                critical_origin=critical_origin,
                passed=group_passed,
            )
        )

    pass_count = sum(1 for item in grades if item.grade == "PASS")
    partial_count = sum(1 for item in grades if item.grade == "PARTIAL")
    fail_count = sum(1 for item in grades if item.grade == "FAIL")
    critical_failures = sum(1 for item in grades if item.critical_failure)
    earned_points = sum(item.score for item in grades)
    accuracy = earned_points / len(grades)
    all_weaknesses_passed = all(item.passed for item in weakness_results)
    critical_weaknesses_passed = all(
        item.passed for item in weakness_results if item.critical_origin
    )
    practice_passed = (
        accuracy >= required_accuracy
        and critical_failures == 0
        and all_weaknesses_passed
        and critical_weaknesses_passed
    )
    next_gate = (
        TARGETED_PRACTICE_PASS_NEXT_GATE
        if practice_passed
        else TARGETED_PRACTICE_FAIL_NEXT_GATE
    )
    return TargetedPracticeReport(
        contract=TARGETED_PRACTICE_CONTRACT,
        version=TARGETED_PRACTICE_VERSION,
        curriculum_id=prepared.curriculum_id,
        level=prepared.level,
        question_count=len(grades),
        pass_count=pass_count,
        partial_count=partial_count,
        fail_count=fail_count,
        earned_points=earned_points,
        accuracy=accuracy,
        required_accuracy=required_accuracy,
        critical_failures=critical_failures,
        source_grounded_weak_items=prepared.source_grounded_weak_items,
        weakness_results=tuple(weakness_results),
        all_weaknesses_passed=all_weaknesses_passed,
        critical_weaknesses_passed=critical_weaknesses_passed,
        practice_passed=practice_passed,
        next_gate=next_gate,
        canonical_attempt_authorized=practice_passed,
    )


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def write_targeted_practice_bundle(
    output_dir: str | Path,
    prepared: PreparedTargetedPractice,
    grades: Sequence[GradedAnswer],
    report: TargetedPracticeReport,
) -> None:
    output = Path(output_dir)
    exercise_by_id = {item.exercise_id: item for item in prepared.exercises}
    result_lines: list[str] = []
    for grade in grades:
        exercise = exercise_by_id[grade.exercise_id]
        result_lines.append(
            json.dumps(
                {
                    "exercise_id": grade.exercise_id,
                    "concept": exercise.concept,
                    "subconcept": exercise.subconcept,
                    "question": exercise.question,
                    "answer": grade.answer,
                    "grade": grade.grade,
                    "score": grade.score,
                    "correct": grade.correct,
                    "failure_codes": list(grade.failure_codes),
                    "critical_failure": grade.critical_failure,
                    "grader_note": grade.grader_note,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    _atomic_write_text(
        output / "practice_results.jsonl",
        "\n".join(result_lines) + "\n",
    )
    _atomic_write_text(
        output / "practice_report.json",
        json.dumps(report.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def run_targeted_practice(
    *,
    prepared: PreparedTargetedPractice,
    answer_model: Any,
    grader_model: Any,
    output_dir: str | Path,
    batch_size: int = 10,
    progress: Callable[[int, int], None] | None = None,
) -> TargetedPracticeReport:
    if batch_size <= 0:
        raise TargetedPyramidPracticeError("batch_size must be positive")
    output = Path(output_dir)
    outcome = run_exam(
        exercises=prepared.exercises,
        answer_model=answer_model,
        grader_model=grader_model,
        batch_size=batch_size,
        checkpoint_dir=output / "checkpoints",
        progress=progress,
        canonical_exam=False,
    )
    report = evaluate_targeted_practice(prepared, outcome.graded_answers)
    write_targeted_practice_bundle(
        output,
        prepared,
        outcome.graded_answers,
        report,
    )
    return report
