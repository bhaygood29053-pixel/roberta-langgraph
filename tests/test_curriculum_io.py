from __future__ import annotations

import json

import pytest

from roberta.learning.curriculum_io import CurriculumPackageError, validate_package
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


def test_validate_package_accepts_manifest_bound_sources(tmp_path) -> None:
    root = tmp_path / "book001"
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    (root / "exercises.jsonl").write_text(json.dumps(_exercise()) + "\n", encoding="utf-8")

    manifest, exercises = validate_package(root)
    assert manifest["curriculum_id"] == "book001"
    assert exercises[0].exercise_id == "book001-l01-00001"


def test_validate_package_rejects_unapproved_source_reference(tmp_path) -> None:
    root = tmp_path / "book001"
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    (root / "exercises.jsonl").write_text(json.dumps(_exercise("other/source")) + "\n", encoding="utf-8")

    with pytest.raises(CurriculumPackageError, match="outside the approved manifest"):
        validate_package(root)
