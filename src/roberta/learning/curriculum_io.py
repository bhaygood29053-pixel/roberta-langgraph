from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import re
from pathlib import Path
from typing import Callable, Iterable, Mapping

from .pyramid import Exercise, PYRAMID_CONTRACT, validate_curriculum


MANIFEST_CONTRACT = "roberta-pyramid-manifest/v1"
SOURCE_PROVENANCE_CONTRACT = "roberta-pyramid-source-provenance/v1"
_REQUIRED_PROVENANCE_SUPPORTS = frozenset(
    {"question", "expected_answer", "required_reasoning_points"}
)
_SOURCE_AUTHORITY_CLASSES = frozenset({"primary", "secondary", "internal", "unknown"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class TrustedSourceBinding:
    """Canonical source identity supplied independently of a curriculum package."""

    source_artifact_sha256: str
    source_transcript_sha256: str
    source_title: str
    source_version: str
    source_origin: str
    source_authority_class: str


TrustedSourceResolver = Callable[[str], TrustedSourceBinding | None]


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


def _require_nonempty_string(value: Mapping[str, object], field: str) -> str:
    candidate = value.get(field)
    if not isinstance(candidate, str) or not candidate.strip():
        raise CurriculumPackageError(f"{field} is required")
    return candidate


def _require_explicit_optional_string(value: Mapping[str, object], field: str) -> None:
    if field not in value:
        raise CurriculumPackageError(f"{field} must be explicitly preserved")
    candidate = value[field]
    if candidate is not None and (
        not isinstance(candidate, str) or not candidate.strip()
    ):
        raise CurriculumPackageError(f"{field} must be null or a non-empty string")


def _validate_source_manifest_metadata(value: Mapping[str, object]) -> None:
    """Validate the source-manifest fields required by provenance-bearing packages."""

    for field in (
        "source_title",
        "source_version",
        "source_origin",
        "ingestion_version",
        "ingestion_timestamp",
        "source_status",
    ):
        _require_nonempty_string(value, field)

    author = value.get("source_author")
    valid_author = isinstance(author, str) and bool(author.strip())
    if isinstance(author, list):
        valid_author = bool(author) and all(
            isinstance(item, str) and bool(item.strip()) for item in author
        )
    if not valid_author:
        raise CurriculumPackageError(
            "source_author must be a non-empty string or non-empty array of strings"
        )

    _require_explicit_optional_string(value, "source_edition")
    _require_explicit_optional_string(value, "publication_date")

    authority_class = value.get("source_authority_class")
    if authority_class not in _SOURCE_AUTHORITY_CLASSES:
        raise CurriculumPackageError(
            "source_authority_class must be one of "
            f"{sorted(_SOURCE_AUTHORITY_CLASSES)}"
        )

    limitations = value.get("source_limitations")
    if (
        not isinstance(limitations, list)
        or not limitations
        or not all(isinstance(item, str) and item.strip() for item in limitations)
    ):
        raise CurriculumPackageError(
            "source_limitations must be a non-empty array of non-empty strings"
        )

    ingestion_timestamp = str(value["ingestion_timestamp"])
    try:
        parsed_timestamp = datetime.fromisoformat(
            ingestion_timestamp.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise CurriculumPackageError(
            "ingestion_timestamp must be a valid timezone-aware ISO-8601 timestamp"
        ) from exc
    if parsed_timestamp.tzinfo is None or parsed_timestamp.utcoffset() is None:
        raise CurriculumPackageError(
            "ingestion_timestamp must be a valid timezone-aware ISO-8601 timestamp"
        )

    for optional_field in ("source_publisher", "ingestion_timestamp_basis"):
        if optional_field in value:
            _require_nonempty_string(value, optional_field)


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
        _validate_source_manifest_metadata(value)
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


def _default_trusted_source_resolver(source_key: str) -> TrustedSourceBinding | None:
    """Resolve accepted Learning System source identity without trusting a package."""

    from .source_ingestion import SourceIngestionError
    from .user_source_batch import get_user_source_spec

    try:
        spec = get_user_source_spec(source_key)
    except SourceIngestionError:
        return None
    return TrustedSourceBinding(
        source_artifact_sha256=spec.original_sha256,
        source_transcript_sha256=spec.transcript_sha256,
        source_title=spec.title,
        source_version=spec.version,
        source_origin=spec.origin,
        source_authority_class=spec.authority_class,
    )


def _validate_trusted_source_binding(
    source_key: str,
    binding: object,
) -> TrustedSourceBinding:
    if not isinstance(binding, TrustedSourceBinding):
        raise CurriculumPackageError(
            f"trusted source binding for {source_key} is malformed"
        )
    if any(
        _SHA256_RE.fullmatch(digest) is None
        for digest in (
            binding.source_artifact_sha256,
            binding.source_transcript_sha256,
        )
    ):
        raise CurriculumPackageError(
            f"trusted source binding for {source_key} is malformed"
        )
    if any(
        not isinstance(candidate, str) or not candidate.strip()
        for candidate in (
            binding.source_title,
            binding.source_version,
            binding.source_origin,
        )
    ):
        raise CurriculumPackageError(
            f"trusted source binding for {source_key} is malformed"
        )
    if binding.source_authority_class not in _SOURCE_AUTHORITY_CLASSES:
        raise CurriculumPackageError(
            f"trusted source binding for {source_key} is malformed"
        )
    return binding


def _lookup_trusted_source_binding(
    source_key: str,
    resolver: TrustedSourceResolver,
    *,
    required: bool,
) -> TrustedSourceBinding | None:
    try:
        binding = resolver(source_key)
    except Exception as exc:
        raise CurriculumPackageError(
            f"trusted source resolution failed for {source_key}"
        ) from exc
    if binding is None:
        if required:
            raise CurriculumPackageError(
                f"no trusted source binding is registered for {source_key}"
            )
        return None
    return _validate_trusted_source_binding(source_key, binding)


def _resolve_trusted_source_binding(
    source_key: str,
    resolver: TrustedSourceResolver,
) -> TrustedSourceBinding:
    binding = _lookup_trusted_source_binding(
        source_key,
        resolver,
        required=True,
    )
    assert binding is not None
    return binding


def _validate_manifest_against_trusted_source(
    manifest: Mapping[str, object],
    declaration: Mapping[str, object],
    trusted: TrustedSourceBinding,
    *,
    source_key: str,
) -> None:
    expected_fields = {
        "source_artifact_sha256": trusted.source_artifact_sha256,
        "source_transcript_sha256": trusted.source_transcript_sha256,
    }
    for field, expected in expected_fields.items():
        if declaration[field] != expected:
            label = "artifact" if field == "source_artifact_sha256" else "transcript"
            raise CurriculumPackageError(
                f"source_provenance {label} digest does not match trusted source {source_key}"
            )

    canonical_metadata = {
        "source_title": trusted.source_title,
        "source_version": trusted.source_version,
        "source_origin": trusted.source_origin,
        "source_authority_class": trusted.source_authority_class,
    }
    for field, expected in canonical_metadata.items():
        if manifest[field] != expected:
            raise CurriculumPackageError(
                f"{field} does not match trusted source {source_key}"
            )


def validate_package(
    directory: str | Path,
    *,
    source_resolver: TrustedSourceResolver | None = None,
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

    resolver = source_resolver or _default_trusted_source_resolver
    trusted_approved: dict[str, TrustedSourceBinding] = {}
    for source_key in sorted(approved):
        trusted = _lookup_trusted_source_binding(
            source_key,
            resolver,
            required=False,
        )
        if trusted is not None:
            trusted_approved[source_key] = trusted

    if trusted_approved and "source_provenance" not in manifest:
        raise CurriculumPackageError(
            "registered approved source refs require source_provenance; "
            f"registered={sorted(trusted_approved)}"
        )

    if "source_provenance" in manifest:
        declaration = _validate_source_provenance_declaration(
            manifest["source_provenance"],
            approved_source_refs=approved,
        )
        source_key = str(declaration["source_key"])
        trusted = trusted_approved.get(source_key)
        if trusted is None:
            trusted = _resolve_trusted_source_binding(source_key, resolver)
        _validate_manifest_against_trusted_source(
            manifest,
            declaration,
            trusted,
            source_key=source_key,
        )

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
