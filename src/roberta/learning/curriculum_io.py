from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Mapping

from .pyramid import Exercise, PYRAMID_CONTRACT, validate_curriculum


MANIFEST_CONTRACT = "roberta-pyramid-manifest/v1"
SOURCE_PROVENANCE_CONTRACT = "roberta-pyramid-source-provenance/v1"
_REQUIRED_PROVENANCE_SUPPORTS = frozenset(
    {"question", "expected_answer", "required_reasoning_points"}
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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


def _validate_source_provenance_declaration(
    value: object,
    *,
    approved_source_refs: set[str],
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CurriculumPackageError("source_provenance must be a JSON object")
    if value.get("contract") != SOURCE_PROVENANCE_CONTRACT:
        raise CurriculumPackageError(
            f"source_provenance.contract must equal {SOURCE_PROVENANCE_CONTRACT}"
        )

    file_name = value.get("file")
    if (
        not isinstance(file_name, str)
        or not file_name.strip()
        or "/" in file_name
        or "\\" in file_name
        or Path(file_name).name != file_name
    ):
        raise CurriculumPackageError(
            "source_provenance.file must be a local package filename"
        )

    source_key = value.get("source_key")
    if not isinstance(source_key, str) or not source_key.strip():
        raise CurriculumPackageError("source_provenance.source_key is required")
    if source_key not in approved_source_refs:
        raise CurriculumPackageError(
            "source_provenance.source_key must be present in approved_source_refs"
        )

    for field in ("source_artifact_sha256", "source_transcript_sha256"):
        digest = value.get(field)
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise CurriculumPackageError(
                f"source_provenance.{field} must be a lowercase SHA-256 digest"
            )

    location_scheme = value.get("location_scheme")
    if not isinstance(location_scheme, str) or not location_scheme.strip():
        raise CurriculumPackageError("source_provenance.location_scheme is required")
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
    if (
        not isinstance(source_refs, list)
        or not source_refs
        or not all(isinstance(item, str) and item.strip() for item in source_refs)
    ):
        raise CurriculumPackageError(
            "approved_source_refs must be a non-empty array of strings"
        )
    approved_source_refs = set(source_refs)
    if "source_provenance" in value:
        _validate_source_provenance_declaration(
            value["source_provenance"],
            approved_source_refs=approved_source_refs,
        )
    levels = value.get("levels")
    if levels is not None:
        if not isinstance(levels, list) or not all(
            isinstance(item, int) and not isinstance(item, bool) and 1 <= item <= 20
            for item in levels
        ):
            raise CurriculumPackageError("levels must contain only integers 1..20")


def load_exercises_jsonl(
    path: str | Path,
    *,
    expected_curriculum_id: str | None = None,
) -> tuple[Exercise, ...]:
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
            raise CurriculumPackageError(
                f"invalid JSONL at line {line_number}: {exc}"
            ) from exc
        if not isinstance(raw, dict):
            raise CurriculumPackageError(
                f"exercise at line {line_number} must be an object"
            )
        try:
            exercise = Exercise.from_mapping(raw)
        except (TypeError, ValueError) as exc:
            raise CurriculumPackageError(
                f"invalid exercise at line {line_number}: {exc}"
            ) from exc
        if (
            expected_curriculum_id is not None
            and exercise.curriculum_id != expected_curriculum_id
        ):
            raise CurriculumPackageError(
                f"exercise {exercise.exercise_id} belongs to {exercise.curriculum_id}, "
                f"expected {expected_curriculum_id}"
            )
        exercises.append(exercise)

    if not exercises:
        raise CurriculumPackageError("exercise bank is empty")
    try:
        validate_curriculum(exercises)
    except ValueError as exc:
        raise CurriculumPackageError(str(exc)) from exc
    return tuple(exercises)


def load_source_provenance_jsonl(
    path: str | Path,
    *,
    expected_source_key: str,
    expected_exercise_ids: set[str],
) -> tuple[dict[str, object], ...]:
    source = Path(path)
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CurriculumPackageError(f"cannot read source provenance: {exc}") from exc

    records: list[dict[str, object]] = []
    seen_exercise_ids: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CurriculumPackageError(
                f"invalid source provenance JSONL at line {line_number}: {exc}"
            ) from exc
        if not isinstance(raw, dict):
            raise CurriculumPackageError(
                f"source provenance at line {line_number} must be an object"
            )
        if "text" in raw or "excerpt" in raw:
            raise CurriculumPackageError(
                f"source provenance at line {line_number} must contain locators, not source text"
            )

        exercise_id = raw.get("exercise_id")
        if not isinstance(exercise_id, str) or not exercise_id.strip():
            raise CurriculumPackageError(
                f"source provenance at line {line_number} requires exercise_id"
            )
        if exercise_id in seen_exercise_ids:
            raise CurriculumPackageError(
                f"duplicate source provenance for exercise {exercise_id}"
            )
        seen_exercise_ids.add(exercise_id)

        if raw.get("source_key") != expected_source_key:
            raise CurriculumPackageError(
                f"source provenance for {exercise_id} does not match declared source_key"
            )

        supports = raw.get("supports")
        if (
            not isinstance(supports, list)
            or not supports
            or not all(isinstance(item, str) and item.strip() for item in supports)
            or len(set(supports)) != len(supports)
            or not _REQUIRED_PROVENANCE_SUPPORTS.issubset(set(supports))
        ):
            raise CurriculumPackageError(
                f"source provenance for {exercise_id} must cover question, "
                "expected_answer, and required_reasoning_points"
            )

        locations = raw.get("locations")
        if not isinstance(locations, list) or not locations:
            raise CurriculumPackageError(
                f"source provenance for {exercise_id} requires at least one location"
            )
        for location_number, location in enumerate(locations, start=1):
            if not isinstance(location, Mapping):
                raise CurriculumPackageError(
                    f"source provenance location {location_number} for {exercise_id} "
                    "must be an object"
                )
            if "text" in location or "excerpt" in location:
                raise CurriculumPackageError(
                    f"source provenance location {location_number} for {exercise_id} "
                    "must contain locators, not source text"
                )
            chapter = location.get("chapter")
            section = location.get("section")
            pages = location.get("book_pages")
            if not isinstance(chapter, str) or not chapter.strip():
                raise CurriculumPackageError(
                    f"source provenance location {location_number} for {exercise_id} "
                    "requires chapter"
                )
            if not isinstance(section, str) or not section.strip():
                raise CurriculumPackageError(
                    f"source provenance location {location_number} for {exercise_id} "
                    "requires section"
                )
            if (
                not isinstance(pages, list)
                or not pages
                or not all(
                    isinstance(page, int) and not isinstance(page, bool) and page > 0
                    for page in pages
                )
            ):
                raise CurriculumPackageError(
                    f"source provenance location {location_number} for {exercise_id} "
                    "requires positive integer book_pages"
                )
        records.append(raw)

    if not records:
        raise CurriculumPackageError("source provenance is empty")
    if seen_exercise_ids != expected_exercise_ids:
        missing = sorted(expected_exercise_ids - seen_exercise_ids)
        extra = sorted(seen_exercise_ids - expected_exercise_ids)
        raise CurriculumPackageError(
            "source provenance must cover the exercise bank exactly; "
            f"missing={missing}, extra={extra}"
        )
    return tuple(records)


def validate_package(
    directory: str | Path,
) -> tuple[dict[str, object], tuple[Exercise, ...]]:
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
                f"exercise {exercise.exercise_id} references sources outside "
                f"the approved manifest: {unknown}"
            )

    if "source_provenance" in manifest:
        declaration = _validate_source_provenance_declaration(
            manifest["source_provenance"],
            approved_source_refs=approved,
        )
        source_key = str(declaration["source_key"])
        missing_source_binding = sorted(
            exercise.exercise_id
            for exercise in exercises
            if source_key not in exercise.source_refs
        )
        if missing_source_binding:
            raise CurriculumPackageError(
                "declared provenance source_key must be referenced by every exercise; "
                f"missing={missing_source_binding}"
            )
        load_source_provenance_jsonl(
            root / str(declaration["file"]),
            expected_source_key=source_key,
            expected_exercise_ids={exercise.exercise_id for exercise in exercises},
        )

    return manifest, exercises


def iter_level_counts(exercises: Iterable[Exercise]) -> dict[int, int]:
    counts = {level: 0 for level in range(1, 21)}
    for exercise in exercises:
        counts[exercise.level] += 1
    return counts
