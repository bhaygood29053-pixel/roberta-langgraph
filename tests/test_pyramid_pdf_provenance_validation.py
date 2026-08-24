from __future__ import annotations

import json

import pytest

from roberta.learning.curriculum_io import (
    CurriculumPackageError,
    SOURCE_PROVENANCE_CONTRACT,
    TrustedSourceBinding,
    validate_package,
)
from roberta.learning.pyramid import PYRAMID_CONTRACT


SOURCE_KEY = "fixture/source"
ARTIFACT_SHA = "a" * 64
TRANSCRIPT_SHA = "b" * 64


def _binding(
    *,
    original_media_type: str | None = None,
    original_page_count: int | None = None,
) -> TrustedSourceBinding:
    return TrustedSourceBinding(
        source_artifact_sha256=ARTIFACT_SHA,
        source_transcript_sha256=TRANSCRIPT_SHA,
        source_title="Fixture Source",
        source_version="1.0",
        source_origin="test://fixture/source",
        source_authority_class="secondary",
        original_media_type=original_media_type,
        original_page_count=original_page_count,
    )


def _resolver(binding: TrustedSourceBinding):
    def resolve(source_key: str) -> TrustedSourceBinding | None:
        return binding if source_key == SOURCE_KEY else None

    return resolve


def _write_package(tmp_path, *, locator: dict[str, object]):
    root = tmp_path / "curriculum"
    root.mkdir()
    manifest = {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": "fixture-curriculum",
        "title": "Fixture Curriculum",
        "source_type": "book",
        "approved_source_refs": [SOURCE_KEY],
        "levels": [1],
        "source_title": "Fixture Source",
        "source_author": "Fixture Author",
        "source_publisher": "Fixture Publisher",
        "source_edition": "First Edition",
        "publication_date": "2026",
        "source_version": "1.0",
        "source_origin": "test://fixture/source",
        "source_authority_class": "secondary",
        "ingestion_version": "utf8-source/v1",
        "ingestion_timestamp": "2026-08-24T00:00:00Z",
        "source_status": "approved_static_fixture",
        "source_limitations": ["Static fixture only."],
        "source_provenance": {
            "contract": SOURCE_PROVENANCE_CONTRACT,
            "file": "provenance.jsonl",
            "source_key": SOURCE_KEY,
            "source_artifact_sha256": ARTIFACT_SHA,
            "source_transcript_sha256": TRANSCRIPT_SHA,
            "location_scheme": "fixture locator",
        },
    }
    exercise = {
        "exercise_id": "fixture-l01-00001",
        "curriculum_id": "fixture-curriculum",
        "level": 1,
        "concept": "blocks",
        "question": "What role does a block play?",
        "expected_answer": "It groups accepted transaction or state data.",
        "source_refs": [SOURCE_KEY],
    }
    provenance = {
        "exercise_id": "fixture-l01-00001",
        "source_key": SOURCE_KEY,
        "locations": [
            {
                "chapter": "Chapter 1",
                "section": "Blocks",
                **locator,
            }
        ],
        "supports": [
            "question",
            "expected_answer",
            "required_reasoning_points",
        ],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "exercises.jsonl").write_text(json.dumps(exercise) + "\n", encoding="utf-8")
    (root / "provenance.jsonl").write_text(
        json.dumps(provenance) + "\n",
        encoding="utf-8",
    )
    return root


def test_book_pages_remain_backward_compatible_without_media_metadata(tmp_path) -> None:
    root = _write_package(tmp_path, locator={"book_pages": [12]})

    manifest, exercises = validate_package(
        root,
        source_resolver=_resolver(_binding()),
    )

    assert manifest["curriculum_id"] == "fixture-curriculum"
    assert exercises[0].exercise_id == "fixture-l01-00001"


def test_pdf_pages_require_trusted_pdf_media_metadata(tmp_path) -> None:
    root = _write_package(tmp_path, locator={"pdf_pages": [1]})

    with pytest.raises(CurriculumPackageError, match="not a page-counted PDF"):
        validate_package(
            root,
            source_resolver=_resolver(
                _binding(original_media_type="text/plain; charset=utf-8")
            ),
        )


def test_pdf_pages_cannot_exceed_trusted_artifact_page_count(tmp_path) -> None:
    root = _write_package(tmp_path, locator={"pdf_pages": [819, 820]})

    with pytest.raises(CurriculumPackageError, match="exceed trusted source page count 819"):
        validate_package(
            root,
            source_resolver=_resolver(
                _binding(
                    original_media_type="application/pdf",
                    original_page_count=819,
                )
            ),
        )
