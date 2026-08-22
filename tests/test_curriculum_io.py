from __future__ import annotations

import json

import pytest

from roberta.learning.curriculum_io import (
    CurriculumPackageError,
    SOURCE_PROVENANCE_CONTRACT,
    TrustedSourceBinding,
    validate_manifest,
    validate_package,
)
from roberta.learning.pyramid import PYRAMID_CONTRACT


SOURCE_REF = "book001/chapter-1"
TRUSTED_ARTIFACT_SHA256 = "a" * 64
TRUSTED_TRANSCRIPT_SHA256 = "b" * 64
TRUSTED_SOURCE_TITLE = "Example Blockchain Book"
TRUSTED_SOURCE_VERSION = "1.0"
TRUSTED_SOURCE_ORIGIN = "test://book001"
TRUSTED_SOURCE_AUTHORITY_CLASS = "secondary"


def _trusted_source_binding() -> TrustedSourceBinding:
    return TrustedSourceBinding(
        source_artifact_sha256=TRUSTED_ARTIFACT_SHA256,
        source_transcript_sha256=TRUSTED_TRANSCRIPT_SHA256,
        source_title=TRUSTED_SOURCE_TITLE,
        source_version=TRUSTED_SOURCE_VERSION,
        source_origin=TRUSTED_SOURCE_ORIGIN,
        source_authority_class=TRUSTED_SOURCE_AUTHORITY_CLASS,
    )


def _trusted_source_resolver(source_key: str) -> TrustedSourceBinding | None:
    if source_key == SOURCE_REF:
        return _trusted_source_binding()
    return None


def _manifest() -> dict[str, object]:
    return {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": "book001",
        "title": "Example Blockchain Book",
        "source_type": "book",
        "approved_source_refs": [SOURCE_REF],
        "levels": [1],
    }


def _manifest_with_provenance() -> dict[str, object]:
    manifest = _manifest()
    manifest.update(
        {
            "source_title": TRUSTED_SOURCE_TITLE,
            "source_author": "Example Author",
            "source_publisher": "Example Publisher",
            "source_edition": "First Edition",
            "publication_date": "2026",
            "source_version": TRUSTED_SOURCE_VERSION,
            "source_origin": TRUSTED_SOURCE_ORIGIN,
            "source_authority_class": TRUSTED_SOURCE_AUTHORITY_CLASS,
            "ingestion_version": "utf8-source/v1",
            "ingestion_timestamp": "2026-08-22T12:00:00Z",
            "ingestion_timestamp_basis": "test fixture",
            "source_status": "approved_static_fixture",
            "source_limitations": ["Static test evidence only."],
            "source_provenance": {
                "contract": SOURCE_PROVENANCE_CONTRACT,
                "file": "provenance.jsonl",
                "source_key": SOURCE_REF,
                "source_artifact_sha256": TRUSTED_ARTIFACT_SHA256,
                "source_transcript_sha256": TRUSTED_TRANSCRIPT_SHA256,
                "location_scheme": "chapter + named section + printed book page(s)",
            },
        }
    )
    return manifest


def _exercise(source_ref: str = SOURCE_REF) -> dict[str, object]:
    return {
        "exercise_id": "book001-l01-00001",
        "curriculum_id": "book001",
        "level": 1,
        "concept": "blocks",
        "question": "What role does a block play?",
        "expected_answer": "It groups accepted transaction/state data under the chain's protocol rules.",
        "source_refs": [source_ref],
    }


def _provenance(
    *,
    exercise_id: str = "book001-l01-00001",
    source_key: str = SOURCE_REF,
) -> dict[str, object]:
    return {
        "exercise_id": exercise_id,
        "source_key": source_key,
        "locations": [
            {
                "chapter": "Chapter 1: Foundations",
                "section": "Blocks",
                "book_pages": [12],
            }
        ],
        "supports": [
            "question",
            "expected_answer",
            "required_reasoning_points",
        ],
    }


def _write_package(root, manifest: dict[str, object]) -> None:
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "exercises.jsonl").write_text(
        json.dumps(_exercise()) + "\n",
        encoding="utf-8",
    )


def _write_valid_provenance(root) -> None:
    (root / "provenance.jsonl").write_text(
        json.dumps(_provenance()) + "\n",
        encoding="utf-8",
    )


def test_validate_package_accepts_manifest_bound_sources(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest())

    manifest, exercises = validate_package(root)
    assert manifest["curriculum_id"] == "book001"
    assert exercises[0].exercise_id == "book001-l01-00001"


def test_validate_package_rejects_unapproved_source_reference(tmp_path) -> None:
    root = tmp_path / "book001"
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    (root / "exercises.jsonl").write_text(
        json.dumps(_exercise("other/source")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CurriculumPackageError, match="outside the approved manifest"):
        validate_package(root)


def test_validate_package_loads_declared_provenance_at_runtime_seam(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    _write_valid_provenance(root)

    manifest, exercises = validate_package(
        root,
        source_resolver=_trusted_source_resolver,
    )
    assert manifest["source_provenance"]["contract"] == SOURCE_PROVENANCE_CONTRACT
    assert len(exercises) == 1


def test_validate_package_rejects_missing_declared_provenance_file(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())

    with pytest.raises(CurriculumPackageError, match="cannot read source provenance"):
        validate_package(root, source_resolver=_trusted_source_resolver)


def test_validate_package_rejects_malformed_declared_provenance(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    malformed = _provenance()
    malformed["locations"] = [
        {"chapter": "Chapter 1", "section": "Blocks", "book_pages": []}
    ]
    (root / "provenance.jsonl").write_text(
        json.dumps(malformed) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CurriculumPackageError, match="positive integer book_pages"):
        validate_package(root, source_resolver=_trusted_source_resolver)


def test_validate_package_rejects_mismatched_or_incomplete_provenance(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    (root / "provenance.jsonl").write_text(
        json.dumps(_provenance(exercise_id="other-exercise")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CurriculumPackageError, match="cover the exercise bank exactly"):
        validate_package(root, source_resolver=_trusted_source_resolver)


def test_validate_package_rejects_provenance_source_binding_mismatch(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    (root / "provenance.jsonl").write_text(
        json.dumps(_provenance(source_key="other/source")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CurriculumPackageError, match="does not match declared source_key"):
        validate_package(root, source_resolver=_trusted_source_resolver)


@pytest.mark.parametrize(
    ("digest_field", "mismatch_message"),
    [
        ("source_artifact_sha256", "artifact digest does not match trusted source"),
        ("source_transcript_sha256", "transcript digest does not match trusted source"),
    ],
)
def test_validate_package_rejects_provenance_digest_not_bound_to_trusted_source(
    tmp_path,
    digest_field: str,
    mismatch_message: str,
) -> None:
    root = tmp_path / "book001"
    manifest = _manifest_with_provenance()
    manifest["source_provenance"][digest_field] = "c" * 64
    _write_package(root, manifest)
    _write_valid_provenance(root)

    with pytest.raises(CurriculumPackageError, match=mismatch_message):
        validate_package(root, source_resolver=_trusted_source_resolver)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("source_title", "Falsified Title"),
        ("source_version", "999.0"),
        ("source_origin", "attacker://substituted-source"),
        ("source_authority_class", "primary"),
    ],
)
def test_validate_package_rejects_identity_or_authority_not_bound_to_trusted_source(
    tmp_path,
    field: str,
    replacement: str,
) -> None:
    root = tmp_path / "book001"
    manifest = _manifest_with_provenance()
    manifest[field] = replacement
    _write_package(root, manifest)
    _write_valid_provenance(root)

    with pytest.raises(CurriculumPackageError, match=f"{field} does not match trusted source"):
        validate_package(root, source_resolver=_trusted_source_resolver)


def test_validate_package_fails_closed_without_trusted_source_binding(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    _write_valid_provenance(root)

    with pytest.raises(CurriculumPackageError, match="no trusted source binding"):
        validate_package(root, source_resolver=lambda _source_key: None)


def test_validate_package_rejects_malformed_trusted_source_binding(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    _write_valid_provenance(root)

    with pytest.raises(CurriculumPackageError, match="trusted source binding.*malformed"):
        validate_package(
            root,
            source_resolver=lambda _source_key: TrustedSourceBinding(
                source_artifact_sha256="a" * 64,
                source_transcript_sha256="not-a-digest",
                source_title=TRUSTED_SOURCE_TITLE,
                source_version=TRUSTED_SOURCE_VERSION,
                source_origin=TRUSTED_SOURCE_ORIGIN,
                source_authority_class=TRUSTED_SOURCE_AUTHORITY_CLASS,
            ),
        )


@pytest.mark.parametrize(
    "field",
    [
        "source_title",
        "source_author",
        "source_edition",
        "publication_date",
        "source_version",
        "source_origin",
        "source_authority_class",
        "ingestion_version",
        "ingestion_timestamp",
        "source_status",
        "source_limitations",
    ],
)
def test_provenance_manifest_requires_source_lifecycle_metadata(field: str) -> None:
    manifest = _manifest_with_provenance()
    del manifest[field]

    with pytest.raises(CurriculumPackageError):
        validate_manifest(manifest)


def test_provenance_manifest_allows_explicit_unknown_edition_and_publication_date() -> None:
    manifest = _manifest_with_provenance()
    manifest["source_edition"] = None
    manifest["publication_date"] = None

    validate_manifest(manifest)


def test_provenance_manifest_rejects_unknown_authority_class() -> None:
    manifest = _manifest_with_provenance()
    manifest["source_authority_class"] = "trusted-because-model-said-so"

    with pytest.raises(CurriculumPackageError, match="source_authority_class"):
        validate_manifest(manifest)


@pytest.mark.parametrize("timestamp", ["not-a-time", "2026-08-22T12:00:00"])
def test_provenance_manifest_requires_timezone_aware_ingestion_timestamp(
    timestamp: str,
) -> None:
    manifest = _manifest_with_provenance()
    manifest["ingestion_timestamp"] = timestamp

    with pytest.raises(CurriculumPackageError, match="timezone-aware ISO-8601"):
        validate_manifest(manifest)


def test_provenance_manifest_requires_explicit_nonempty_limitations() -> None:
    manifest = _manifest_with_provenance()
    manifest["source_limitations"] = []

    with pytest.raises(CurriculumPackageError, match="source_limitations"):
        validate_manifest(manifest)
