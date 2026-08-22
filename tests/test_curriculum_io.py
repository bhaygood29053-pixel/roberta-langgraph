from __future__ import annotations

import json

import pytest

from roberta.learning.curriculum_io import (
    CurriculumPackageError,
    SOURCE_PROVENANCE_CONTRACT,
    validate_package,
)
from roberta.learning.pyramid import PYRAMID_CONTRACT


def _manifest() -> dict[str, object]:
    return {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": "book001",
        "title": "Example Blockchain Book",
        "source_type": "book",
        "approved_source_refs": ["book001/chapter-1"],
        "levels": [1],
    }


def _manifest_with_provenance() -> dict[str, object]:
    manifest = _manifest()
    manifest["source_provenance"] = {
        "contract": SOURCE_PROVENANCE_CONTRACT,
        "file": "provenance.jsonl",
        "source_key": "book001/chapter-1",
        "source_artifact_sha256": "a" * 64,
        "source_transcript_sha256": "b" * 64,
        "location_scheme": "chapter + named section + printed book page(s)",
    }
    return manifest


def _exercise(source_ref: str = "book001/chapter-1") -> dict[str, object]:
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
    source_key: str = "book001/chapter-1",
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
    (root / "provenance.jsonl").write_text(
        json.dumps(_provenance()) + "\n",
        encoding="utf-8",
    )

    manifest, exercises = validate_package(root)
    assert manifest["source_provenance"]["contract"] == SOURCE_PROVENANCE_CONTRACT
    assert len(exercises) == 1


def test_validate_package_rejects_missing_declared_provenance_file(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())

    with pytest.raises(CurriculumPackageError, match="cannot read source provenance"):
        validate_package(root)


def test_validate_package_rejects_malformed_declared_provenance(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    malformed = _provenance()
    malformed["locations"] = [{"chapter": "Chapter 1", "section": "Blocks", "book_pages": []}]
    (root / "provenance.jsonl").write_text(
        json.dumps(malformed) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CurriculumPackageError, match="positive integer book_pages"):
        validate_package(root)


def test_validate_package_rejects_mismatched_or_incomplete_provenance(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    (root / "provenance.jsonl").write_text(
        json.dumps(_provenance(exercise_id="other-exercise")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CurriculumPackageError, match="cover the exercise bank exactly"):
        validate_package(root)


def test_validate_package_rejects_provenance_source_binding_mismatch(tmp_path) -> None:
    root = tmp_path / "book001"
    _write_package(root, _manifest_with_provenance())
    (root / "provenance.jsonl").write_text(
        json.dumps(_provenance(source_key="other/source")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CurriculumPackageError, match="does not match declared source_key"):
        validate_package(root)
