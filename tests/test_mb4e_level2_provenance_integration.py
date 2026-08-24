from __future__ import annotations

import json

from roberta.learning.curriculum_io import (
    SOURCE_PROVENANCE_CONTRACT,
    TrustedSourceBinding,
    validate_package,
)
from roberta.learning.mb4e_level2_builder_cli import _prepare_stage
from roberta.learning.mb4e_level2_factory import (
    CURRICULUM_ID,
    SOURCE_KEY,
    TOTAL_COUNT,
    build_level2_bank,
    level2_provenance_records,
    level2_source_map,
)
from roberta.learning.pyramid import PYRAMID_CONTRACT, select_level_exercises


ARTIFACT_SHA = "a" * 64
TRANSCRIPT_SHA = "b" * 64


def _binding() -> TrustedSourceBinding:
    return TrustedSourceBinding(
        source_artifact_sha256=ARTIFACT_SHA,
        source_transcript_sha256=TRANSCRIPT_SHA,
        source_title="Mastering Blockchain Fixture",
        source_version="4e-test",
        source_origin="test://mastering-blockchain-4e",
        source_authority_class="secondary",
        original_media_type="application/pdf",
        original_page_count=500,
    )


def _resolver(source_key: str) -> TrustedSourceBinding | None:
    return _binding() if source_key == SOURCE_KEY else None


def _write_level1_base_package(tmp_path):
    root = tmp_path / "curriculum"
    root.mkdir()
    manifest = {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": CURRICULUM_ID,
        "title": "Mastering Blockchain Fixture Curriculum",
        "source_type": "book",
        "approved_source_refs": [SOURCE_KEY],
        "levels": [1],
        "source_title": "Mastering Blockchain Fixture",
        "source_author": "Fixture Author",
        "source_publisher": "Fixture Publisher",
        "source_edition": "Fourth Edition",
        "publication_date": "2023",
        "source_version": "4e-test",
        "source_origin": "test://mastering-blockchain-4e",
        "source_authority_class": "secondary",
        "ingestion_version": "pdf-fixture/v1",
        "ingestion_timestamp": "2026-08-24T00:00:00Z",
        "source_status": "approved_static_fixture",
        "source_limitations": ["Static test fixture only."],
        "source_provenance": {
            "contract": SOURCE_PROVENANCE_CONTRACT,
            "file": "provenance.jsonl",
            "source_key": SOURCE_KEY,
            "source_artifact_sha256": ARTIFACT_SHA,
            "source_transcript_sha256": TRANSCRIPT_SHA,
            "location_scheme": "PDF pages",
        },
    }
    exercise = {
        "exercise_id": "MB4E-L01-FIXTURE-00001",
        "curriculum_id": CURRICULUM_ID,
        "level": 1,
        "concept": "blockchain_basics",
        "question": "What is the fixture's Level 1 source binding?",
        "expected_answer": "The canonical Mastering Blockchain source.",
        "source_refs": [SOURCE_KEY],
    }
    provenance = {
        "exercise_id": "MB4E-L01-FIXTURE-00001",
        "source_key": SOURCE_KEY,
        "supports": [
            "question",
            "expected_answer",
            "required_reasoning_points",
        ],
        "locations": [
            {
                "chapter": "Chapter 1",
                "section": "Fixture",
                "pdf_pages": [1],
            }
        ],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "exercises.jsonl").write_text(json.dumps(exercise) + "\n", encoding="utf-8")
    (root / "provenance.jsonl").write_text(json.dumps(provenance) + "\n", encoding="utf-8")
    return root, manifest


def test_level2_exercises_bind_canonical_and_detailed_sources() -> None:
    bank = build_level2_bank()
    source_map = level2_source_map()

    assert len(bank) == TOTAL_COUNT == 1206
    assert all(SOURCE_KEY in exercise.source_refs for exercise in bank)
    for exercise in bank:
        detailed_refs = tuple(ref for ref in exercise.source_refs if ref != SOURCE_KEY)
        assert detailed_refs
        assert all(ref in source_map for ref in detailed_refs)


def test_level2_provenance_covers_bank_and_uses_only_detailed_locations() -> None:
    bank = build_level2_bank()
    records = level2_provenance_records(bank)
    source_map = level2_source_map()

    assert len(records) == TOTAL_COUNT
    assert {record["exercise_id"] for record in records} == {
        exercise.exercise_id for exercise in bank
    }
    for record in records:
        assert record["source_key"] == SOURCE_KEY
        assert record["locations"]
        assert all(
            location["legacy_source_ref"] in source_map
            for location in record["locations"]
        )
        assert all(
            location["legacy_source_ref"] != SOURCE_KEY
            for location in record["locations"]
        )


def test_complete_staged_level2_package_passes_validate_package(tmp_path) -> None:
    root, manifest = _write_level1_base_package(tmp_path)
    stage = tmp_path / "stage"

    _prepare_stage(root, stage, dict(manifest), "provenance.jsonl")
    staged_manifest, exercises = validate_package(
        stage,
        source_resolver=_resolver,
    )

    level2 = tuple(exercise for exercise in exercises if exercise.level == 2)
    assert staged_manifest["levels"] == [1, 2]
    assert len(level2) == TOTAL_COUNT == 1206
    assert all(SOURCE_KEY in exercise.source_refs for exercise in exercises)

    selected = select_level_exercises(
        exercises,
        curriculum_id=CURRICULUM_ID,
        level=2,
        run_seed="mb4e-level2-provenance-integration",
    )
    assert len(selected) == 1000
    assert sum(
        not exercise.integrity_question and not exercise.boss_question
        for exercise in selected
    ) == 949
    assert sum(exercise.integrity_question for exercise in selected) == 50
    assert sum(exercise.boss_question for exercise in selected) == 1
    assert selected[-1].boss_question is True
