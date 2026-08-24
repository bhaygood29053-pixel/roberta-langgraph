from __future__ import annotations

import ctypes
from dataclasses import dataclass
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any, Mapping

from .curriculum_io import SOURCE_PROVENANCE_CONTRACT, validate_package
from .user_source_batch import get_user_source_spec


MIGRATION_CONTRACT = "roberta-pyramid-legacy-provenance-migration/v1"
MIGRATION_VERSION = "1.0.0"
MB4E_SOURCE_KEY = "mastering_blockchain_4e_2023"
MB4E_LEGACY_CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"

_LEGACY_REF_RE = re.compile(
    r"^MB4E-CH(?P<chapter>[1-9][0-9]*)-P(?P<start>[1-9][0-9]*)-(?P<end>[1-9][0-9]*)-(?P<label>[A-Z0-9-]+)$"
)
_SOURCE_MAP_RE = re.compile(
    r"^PDF pages (?P<start>[1-9][0-9]*)-(?P<end>[1-9][0-9]*):\s*(?P<section>.+)$"
)
_SNAPSHOT_FILES = ("manifest.json", "exercises.jsonl", "source_map.json")
_AT_FDCWD = -100
_RENAME_NOREPLACE = 1


class PyramidProvenanceMigrationError(RuntimeError):
    """Raised when a legacy Pyramid package cannot be migrated without guessing provenance."""


@dataclass(frozen=True, slots=True)
class PyramidProvenanceMigrationReport:
    curriculum_id: str
    source_key: str
    input_dir: str
    output_dir: str
    exercise_count_before: int
    exercise_count_after: int
    provenance_count: int
    exercise_ids_identical: bool
    question_text_identical: bool
    semantic_fields_identical: bool
    checkpoint_compatible: bool | None
    checkpoint_exercise_count: int | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "migration_contract": MIGRATION_CONTRACT,
            "migration_version": MIGRATION_VERSION,
            "curriculum_id": self.curriculum_id,
            "source_key": self.source_key,
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "exercise_count_before": self.exercise_count_before,
            "exercise_count_after": self.exercise_count_after,
            "provenance_count": self.provenance_count,
            "exercise_ids_identical": self.exercise_ids_identical,
            "question_text_identical": self.question_text_identical,
            "semantic_fields_identical": self.semantic_fields_identical,
            "checkpoint_compatible": self.checkpoint_compatible,
            "checkpoint_exercise_count": self.checkpoint_exercise_count,
        }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_bytes(path: Path, *, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PyramidProvenanceMigrationError(f"cannot read {label}: {exc}") from exc


def _read_json_object_bytes(value: bytes, *, label: str) -> dict[str, object]:
    try:
        text = value.decode("utf-8")
        parsed = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PyramidProvenanceMigrationError(f"cannot read {label}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PyramidProvenanceMigrationError(f"{label} must be a JSON object")
    return parsed


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    return _read_json_object_bytes(_read_bytes(path, label=label), label=label)


def _read_raw_exercises_bytes(value: bytes) -> list[dict[str, object]]:
    try:
        lines = value.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise PyramidProvenanceMigrationError(f"cannot read legacy exercise bank: {exc}") from exc
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PyramidProvenanceMigrationError(
                f"invalid legacy exercise JSONL at line {line_number}: {exc}"
            ) from exc
        if not isinstance(raw, dict):
            raise PyramidProvenanceMigrationError(
                f"legacy exercise at line {line_number} must be an object"
            )
        exercise_id = raw.get("exercise_id")
        if not isinstance(exercise_id, str) or not exercise_id.strip():
            raise PyramidProvenanceMigrationError(
                f"legacy exercise at line {line_number} requires exercise_id"
            )
        if exercise_id in seen:
            raise PyramidProvenanceMigrationError(f"duplicate legacy exercise_id: {exercise_id}")
        seen.add(exercise_id)
        rows.append(raw)
    if not rows:
        raise PyramidProvenanceMigrationError("legacy exercise bank is empty")
    return rows


def _capture_input_snapshot(input_root: Path) -> dict[str, bytes]:
    snapshot = {
        name: _read_bytes(input_root / name, label=f"legacy {name}")
        for name in _SNAPSHOT_FILES
    }
    _assert_input_snapshot_unchanged(input_root, snapshot)
    return snapshot


def _assert_input_snapshot_unchanged(input_root: Path, snapshot: Mapping[str, bytes]) -> None:
    for name in _SNAPSHOT_FILES:
        expected = snapshot.get(name)
        if not isinstance(expected, bytes):
            raise PyramidProvenanceMigrationError(f"legacy input snapshot is missing {name}")
        current = _read_bytes(input_root / name, label=f"legacy {name}")
        if current != expected:
            raise PyramidProvenanceMigrationError(
                f"legacy input changed during migration: {name}"
            )


def _validate_legacy_snapshot(snapshot: Mapping[str, bytes]) -> tuple[dict[str, object], list[Any]]:
    with tempfile.TemporaryDirectory(prefix=".mb4e-legacy-validate-") as temp_dir:
        root = Path(temp_dir)
        for name in _SNAPSHOT_FILES:
            value = snapshot.get(name)
            if not isinstance(value, bytes):
                raise PyramidProvenanceMigrationError(f"legacy input snapshot is missing {name}")
            (root / name).write_bytes(value)
        return validate_package(root)


def _legacy_location(
    source_ref: str,
    source_map: Mapping[str, object],
    *,
    max_pdf_page: int,
) -> dict[str, object]:
    ref_match = _LEGACY_REF_RE.fullmatch(source_ref)
    if ref_match is None:
        raise PyramidProvenanceMigrationError(
            f"unsupported legacy source ref {source_ref!r}; refusing to guess provenance"
        )
    mapped = source_map.get(source_ref)
    if not isinstance(mapped, str) or not mapped.strip():
        raise PyramidProvenanceMigrationError(
            f"legacy source ref {source_ref!r} is missing from source_map.json"
        )
    map_match = _SOURCE_MAP_RE.fullmatch(mapped.strip())
    if map_match is None:
        raise PyramidProvenanceMigrationError(
            f"legacy source map for {source_ref!r} must explicitly declare a PDF page range"
        )

    ref_start = int(ref_match.group("start"))
    ref_end = int(ref_match.group("end"))
    map_start = int(map_match.group("start"))
    map_end = int(map_match.group("end"))
    if ref_start > ref_end or (ref_start, ref_end) != (map_start, map_end):
        raise PyramidProvenanceMigrationError(
            f"legacy source ref/page-map mismatch for {source_ref!r}"
        )
    if ref_end > max_pdf_page:
        raise PyramidProvenanceMigrationError(
            f"legacy source ref {source_ref!r} exceeds registered source PDF page count {max_pdf_page}"
        )

    return {
        "chapter": f"Chapter {int(ref_match.group('chapter'))}",
        "section": map_match.group("section").strip(),
        "pdf_pages": list(range(ref_start, ref_end + 1)),
        "legacy_source_ref": source_ref,
    }


def _semantic_projection(raw: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in raw.items() if key != "source_refs"}


def _migrate_exercises(
    rows: list[dict[str, object]],
    source_map: Mapping[str, object],
    *,
    source_key: str,
    max_pdf_page: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    migrated: list[dict[str, object]] = []
    provenance: list[dict[str, object]] = []
    for raw in rows:
        exercise_id = str(raw["exercise_id"])
        source_refs = raw.get("source_refs")
        if (
            not isinstance(source_refs, list)
            or not source_refs
            or not all(isinstance(item, str) and item.strip() for item in source_refs)
        ):
            raise PyramidProvenanceMigrationError(
                f"legacy exercise {exercise_id} has malformed source_refs"
            )
        if source_key in source_refs:
            raise PyramidProvenanceMigrationError(
                f"legacy exercise {exercise_id} already references canonical source key; package is not an unmigrated legacy input"
            )
        legacy_refs = tuple(source_refs)
        locations = [
            _legacy_location(ref, source_map, max_pdf_page=max_pdf_page)
            for ref in legacy_refs
        ]

        migrated_row = json.loads(json.dumps(raw, ensure_ascii=False))
        migrated_row["source_refs"] = [*legacy_refs, source_key]
        if _semantic_projection(migrated_row) != _semantic_projection(raw):
            raise PyramidProvenanceMigrationError(
                f"semantic drift detected while migrating exercise {exercise_id}"
            )
        migrated.append(migrated_row)
        provenance.append(
            {
                "exercise_id": exercise_id,
                "source_key": source_key,
                "locations": locations,
                "supports": [
                    "question",
                    "expected_answer",
                    "required_reasoning_points",
                ],
            }
        )
    return migrated, provenance


def _migrated_manifest(
    legacy: Mapping[str, object],
    *,
    source_key: str,
    exercise_count: int,
    input_hashes: Mapping[str, str],
) -> dict[str, object]:
    if legacy.get("curriculum_id") != MB4E_LEGACY_CURRICULUM_ID:
        raise PyramidProvenanceMigrationError(
            f"migration only supports curriculum_id {MB4E_LEGACY_CURRICULUM_ID!r}"
        )
    if "source_provenance" in legacy:
        raise PyramidProvenanceMigrationError("legacy input already declares source_provenance")
    if source_key != MB4E_SOURCE_KEY:
        raise PyramidProvenanceMigrationError(
            f"migration only supports canonical source key {MB4E_SOURCE_KEY!r}"
        )
    spec = get_user_source_spec(source_key)

    approved = legacy.get("approved_source_refs")
    if (
        not isinstance(approved, list)
        or not approved
        or not all(isinstance(item, str) and item.strip() for item in approved)
    ):
        raise PyramidProvenanceMigrationError("legacy manifest approved_source_refs are malformed")

    manifest = json.loads(json.dumps(legacy, ensure_ascii=False))
    manifest.update(
        {
            "source_title": spec.title,
            "source_author": "Imran Bashir",
            "source_publisher": "Packt",
            "source_edition": "Fourth Edition",
            "publication_date": "2023",
            "source_version": spec.version,
            "source_origin": spec.origin,
            "source_authority_class": spec.authority_class,
            "ingestion_version": "utf8-source/v1",
            "ingestion_timestamp": "2026-08-22T15:30:21Z",
            "ingestion_timestamp_basis": (
                "Accepted Learning System source-registration merge time for PR #147; "
                "the copyrighted external transcript is not repository-materialized at runtime."
            ),
            "source_status": "approved_static_external_exact_transcript",
            "source_limitations": [
                "User-supplied copyrighted secondary educational reference.",
                "The repository stores provenance and integrity metadata but does not republish the full book transcript.",
                "Runtime source ingestion requires exact external transcript bytes matching the pinned transcript SHA-256.",
                "Legacy Level 1 provenance preserves PDF page coordinates explicitly; they are not asserted to be printed-book page numbers.",
                "This static source is not authoritative for current market, chain, wallet, tokenomics, validator, authority, or risk state.",
            ],
            "approved_source_refs": [*approved, source_key],
            "source_provenance": {
                "contract": SOURCE_PROVENANCE_CONTRACT,
                "file": "provenance.jsonl",
                "source_key": source_key,
                "source_artifact_sha256": spec.original_sha256,
                "source_transcript_sha256": spec.transcript_sha256,
                "location_scheme": "chapter + named section + explicit PDF page(s) preserved from legacy source aliases",
            },
            "exercise_count": exercise_count,
            "provenance_migration": {
                "contract": MIGRATION_CONTRACT,
                "version": MIGRATION_VERSION,
                "input_manifest_sha256": input_hashes["manifest.json"],
                "input_exercises_sha256": input_hashes["exercises.jsonl"],
                "input_source_map_sha256": input_hashes["source_map.json"],
                "historical_semantics_preserved": True,
                "legacy_pdf_page_basis_preserved": True,
            },
        }
    )
    return manifest


def _checkpoint_compatibility(
    checkpoints: str | Path | None,
    exercise_ids: set[str],
) -> tuple[bool | None, int | None]:
    if checkpoints is None:
        return None, None
    root = Path(checkpoints)
    if not root.is_dir():
        raise PyramidProvenanceMigrationError("checkpoint directory does not exist")
    selected: list[str] = []
    paths = sorted(root.glob("level_*_batch_*.json"))
    if not paths:
        raise PyramidProvenanceMigrationError("checkpoint directory contains no Pyramid batch checkpoints")
    for path in paths:
        raw = _read_json_object(path, label=f"checkpoint {path.name}")
        ids = raw.get("exercise_ids")
        if not isinstance(ids, list) or not all(isinstance(item, str) and item for item in ids):
            raise PyramidProvenanceMigrationError(f"checkpoint {path.name} has malformed exercise_ids")
        selected.extend(ids)
    unknown = sorted(set(selected) - exercise_ids)
    if unknown:
        raise PyramidProvenanceMigrationError(
            f"checkpoint exercise ids are absent from migrated bank: {unknown}"
        )
    return True, len(selected)


def _publish_directory_noreplace(stage: Path, output_root: Path) -> None:
    """Atomically publish one staged directory without replacing an existing path."""

    if sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = getattr(libc, "renameat2", None)
        if renameat2 is None:
            raise PyramidProvenanceMigrationError(
                "atomic no-replace publication is unavailable on this Linux runtime"
            )
        renameat2.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameat2.restype = ctypes.c_int
        result = renameat2(
            _AT_FDCWD,
            os.fsencode(str(stage)),
            _AT_FDCWD,
            os.fsencode(str(output_root)),
            _RENAME_NOREPLACE,
        )
        if result == 0:
            return
        error_number = ctypes.get_errno()
        if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
            raise PyramidProvenanceMigrationError(
                f"output directory already exists at publication: {output_root}"
            )
        raise OSError(error_number, os.strerror(error_number), str(output_root))

    if os.name == "nt":
        try:
            os.rename(stage, output_root)
        except FileExistsError as exc:
            raise PyramidProvenanceMigrationError(
                f"output directory already exists at publication: {output_root}"
            ) from exc
        return

    raise PyramidProvenanceMigrationError(
        "atomic no-replace publication is unsupported on this platform"
    )


def migrate_legacy_mb4e_curriculum(
    *,
    curriculum_dir: str | Path,
    output_dir: str | Path,
    checkpoints_dir: str | Path | None = None,
    source_key: str = MB4E_SOURCE_KEY,
) -> PyramidProvenanceMigrationReport:
    input_root = Path(curriculum_dir).resolve()
    output_root = Path(output_dir).resolve()
    if not input_root.is_dir():
        raise PyramidProvenanceMigrationError("legacy curriculum directory does not exist")
    if output_root == input_root or input_root in output_root.parents:
        raise PyramidProvenanceMigrationError(
            "output directory must be outside the legacy curriculum tree"
        )
    if output_root.exists():
        raise PyramidProvenanceMigrationError(f"output directory already exists: {output_root}")
    if source_key != MB4E_SOURCE_KEY:
        raise PyramidProvenanceMigrationError(
            f"migration only supports canonical source key {MB4E_SOURCE_KEY!r}"
        )

    snapshot = _capture_input_snapshot(input_root)
    input_hashes = {name: _sha256_bytes(value) for name, value in snapshot.items()}

    # Validate and derive from the exact same immutable byte snapshot.
    legacy_manifest, legacy_exercises = _validate_legacy_snapshot(snapshot)
    raw_rows = _read_raw_exercises_bytes(snapshot["exercises.jsonl"])
    if len(raw_rows) != len(legacy_exercises):
        raise PyramidProvenanceMigrationError("raw/validated legacy exercise counts disagree")
    source_map = _read_json_object_bytes(
        snapshot["source_map.json"],
        label="legacy source_map.json",
    )

    source_spec = get_user_source_spec(source_key)
    max_pdf_page = source_spec.original_page_count
    if not isinstance(max_pdf_page, int) or max_pdf_page < 1:
        raise PyramidProvenanceMigrationError(
            "registered source does not declare a valid original PDF page count"
        )

    migrated_rows, provenance_rows = _migrate_exercises(
        raw_rows,
        source_map,
        source_key=source_key,
        max_pdf_page=max_pdf_page,
    )
    manifest = _migrated_manifest(
        legacy_manifest,
        source_key=source_key,
        exercise_count=len(migrated_rows),
        input_hashes=input_hashes,
    )

    before_ids = [str(item["exercise_id"]) for item in raw_rows]
    after_ids = [str(item["exercise_id"]) for item in migrated_rows]
    before_questions = [item.get("question") for item in raw_rows]
    after_questions = [item.get("question") for item in migrated_rows]
    semantics_identical = all(
        _semantic_projection(before) == _semantic_projection(after)
        for before, after in zip(raw_rows, migrated_rows, strict=True)
    )
    if before_ids != after_ids or before_questions != after_questions or not semantics_identical:
        raise PyramidProvenanceMigrationError("historical exercise identity/semantics changed during migration")

    checkpoint_compatible, checkpoint_exercise_count = _checkpoint_compatibility(
        checkpoints_dir,
        set(after_ids),
    )
    report = PyramidProvenanceMigrationReport(
        curriculum_id=str(legacy_manifest["curriculum_id"]),
        source_key=source_key,
        input_dir=str(input_root),
        output_dir=str(output_root),
        exercise_count_before=len(raw_rows),
        exercise_count_after=len(migrated_rows),
        provenance_count=len(provenance_rows),
        exercise_ids_identical=before_ids == after_ids,
        question_text_identical=before_questions == after_questions,
        semantic_fields_identical=semantics_identical,
        checkpoint_compatible=checkpoint_compatible,
        checkpoint_exercise_count=checkpoint_exercise_count,
    )

    output_root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.tmp-", dir=output_root.parent))
    try:
        for child in input_root.iterdir():
            if child.name in {
                "manifest.json",
                "exercises.jsonl",
                "source_map.json",
                "provenance.jsonl",
            }:
                continue
            target = stage / child.name
            if child.is_dir():
                shutil.copytree(child, target)
            else:
                shutil.copy2(child, target)

        (stage / "source_map.json").write_bytes(snapshot["source_map.json"])
        (stage / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        with (stage / "exercises.jsonl").open("w", encoding="utf-8") as handle:
            for row in migrated_rows:
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        with (stage / "provenance.jsonl").open("w", encoding="utf-8") as handle:
            for row in provenance_rows:
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        (stage / "migration_report.json").write_text(
            json.dumps(report.to_mapping(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        migrated_manifest, migrated_exercises = validate_package(stage)
        if str(migrated_manifest["curriculum_id"]) != str(legacy_manifest["curriculum_id"]):
            raise PyramidProvenanceMigrationError("curriculum_id changed during migration")
        if [item.exercise_id for item in migrated_exercises] != before_ids:
            raise PyramidProvenanceMigrationError("validated migrated exercise ordering/identity changed")

        # Refuse publication if the historical source package changed after capture.
        _assert_input_snapshot_unchanged(input_root, snapshot)
        _publish_directory_noreplace(stage, output_root)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    return report
