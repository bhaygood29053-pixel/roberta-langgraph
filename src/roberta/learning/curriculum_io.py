from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from .pyramid import Exercise, PYRAMID_CONTRACT, validate_curriculum


MANIFEST_CONTRACT = "roberta-pyramid-manifest/v1"


class CurriculumPackageError(ValueError):
    pass


def load_manifest(path: str | Path) -> dict[str, object]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CurriculumPackageError(f"invalid curriculum manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise CurriculumPackageError("manifest must be a JSON object")
    validate_manifest(value)
    return value


def validate_manifest(value: Mapping[str, object]) -> None:
    if value.get("manifest_contract") != MANIFEST_CONTRACT:
        raise CurriculumPackageError(f"manifest_contract must equal {MANIFEST_CONTRACT}")
    if value.get("curriculum_contract") != PYRAMID_CONTRACT:
        raise CurriculumPackageError(f"curriculum_contract must equal {PYRAMID_CONTRACT}")
    for field in ("curriculum_id", "title", "source_type"):
        if not isinstance(value.get(field), str) or not str(value[field]).strip():
            raise CurriculumPackageError(f"{field} is required")
    source_refs = value.get("approved_source_refs")
    if not isinstance(source_refs, list) or not source_refs or not all(isinstance(item, str) and item.strip() for item in source_refs):
        raise CurriculumPackageError("approved_source_refs must be a non-empty array of strings")
    levels = value.get("levels")
    if levels is not None:
        if not isinstance(levels, list) or not all(isinstance(item, int) and 1 <= item <= 20 for item in levels):
            raise CurriculumPackageError("levels must contain only integers 1..20")


def load_exercises_jsonl(path: str | Path, *, expected_curriculum_id: str | None = None) -> tuple[Exercise, ...]:
    source = Path(path)
    exercises: list[Exercise] = []
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CurriculumPackageError(f"cannot read exercise bank: {exc}") from exc

    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CurriculumPackageError(f"invalid JSONL at line {line_number}: {exc}") from exc
        if not isinstance(raw, dict):
            raise CurriculumPackageError(f"exercise at line {line_number} must be an object")
        try:
            exercise = Exercise.from_mapping(raw)
        except (TypeError, ValueError) as exc:
            raise CurriculumPackageError(f"invalid exercise at line {line_number}: {exc}") from exc
        if expected_curriculum_id is not None and exercise.curriculum_id != expected_curriculum_id:
            raise CurriculumPackageError(
                f"exercise {exercise.exercise_id} belongs to {exercise.curriculum_id}, expected {expected_curriculum_id}"
            )
        exercises.append(exercise)

    if not exercises:
        raise CurriculumPackageError("exercise bank is empty")
    try:
        validate_curriculum(exercises)
    except ValueError as exc:
        raise CurriculumPackageError(str(exc)) from exc
    return tuple(exercises)


def validate_package(directory: str | Path) -> tuple[dict[str, object], tuple[Exercise, ...]]:
    root = Path(directory)
    manifest = load_manifest(root / "manifest.json")
    exercises = load_exercises_jsonl(
        root / "exercises.jsonl",
        expected_curriculum_id=str(manifest["curriculum_id"]),
    )
    approved = set(str(item) for item in manifest["approved_source_refs"])
    for exercise in exercises:
        if not set(exercise.source_refs).issubset(approved):
            unknown = sorted(set(exercise.source_refs) - approved)
            raise CurriculumPackageError(
                f"exercise {exercise.exercise_id} references sources outside the approved manifest: {unknown}"
            )
    return manifest, exercises


def iter_level_counts(exercises: Iterable[Exercise]) -> dict[int, int]:
    counts = {level: 0 for level in range(1, 21)}
    for exercise in exercises:
        counts[exercise.level] += 1
    return counts
