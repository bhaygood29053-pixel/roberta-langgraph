from __future__ import annotations

import json

import pytest

from roberta.learning.curriculum_io import (
    SOURCE_PROVENANCE_CONTRACT,
    TrustedSourceBinding,
    validate_package,
)
from roberta.learning.mb4e_level2_builder_cli import _prepare_stage as _prepare_level2_stage
from roberta.learning.mb4e_level2_factory import build_level2_bank
from roberta.learning.mb4e_level3_builder_cli import (
    Level3BuildError,
    _assert_required_level2,
    _prepare_stage as _prepare_level3_stage,
)
from roberta.learning.mb4e_level3_factory import (
    CURRICULUM_ID,
    INTEGRITY_COUNT,
    ORDINARY_COUNT,
    SOURCE_KEY,
    TOTAL_COUNT,
    build_level3_bank,
    level3_provenance_records,
    level3_source_map,
    level3_targets,
)
from roberta.learning.pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    PYRAMID_CONTRACT,
    select_level_exercises,
)


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
        original_page_count=817,
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
        "source_author": "Imran Bashir",
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
        "exercise_id": exercise["exercise_id"],
        "source_key": SOURCE_KEY,
        "supports": ["question", "expected_answer", "required_reasoning_points"],
        "locations": [{"chapter": "Chapter 1", "section": "Fixture", "pdf_pages": [1]}],
    }
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "exercises.jsonl").write_text(json.dumps(exercise) + "\n", encoding="utf-8")
    (root / "provenance.jsonl").write_text(json.dumps(provenance) + "\n", encoding="utf-8")
    return root, manifest


def test_level3_bank_is_source_grounded_and_large_enough_for_300_question_exam() -> None:
    targets = level3_targets()
    bank = build_level3_bank()
    source_map = level3_source_map()

    assert len(targets) == 25
    assert ORDINARY_COUNT == 325
    assert INTEGRITY_COUNT == 50
    assert TOTAL_COUNT == 376
    assert len(bank) == TOTAL_COUNT
    assert len(bank) >= CANONICAL_LEVEL_QUESTION_COUNT
    assert sum(item.integrity_question for item in bank) == 50
    assert sum(item.boss_question for item in bank) == 1
    assert all(SOURCE_KEY in item.source_refs for item in bank)
    assert {value["chapter"] for value in source_map.values()} == {
        "Chapter 6",
        "Chapter 9",
        "Chapter 13",
        "Chapter 14",
    }
    for item in bank:
        detailed = [ref for ref in item.source_refs if ref != SOURCE_KEY]
        assert detailed
        assert all(ref in source_map for ref in detailed)


def test_level3_provenance_covers_every_exercise() -> None:
    bank = build_level3_bank()
    records = level3_provenance_records(bank)
    source_map = level3_source_map()

    assert len(records) == len(bank)
    assert {record["exercise_id"] for record in records} == {item.exercise_id for item in bank}
    for record in records:
        assert record["source_key"] == SOURCE_KEY
        assert record["locations"]
        assert all(location["legacy_source_ref"] in source_map for location in record["locations"])


def test_level3_canonical_selection_is_249_ordinary_50_integrity_1_boss() -> None:
    selected = select_level_exercises(
        build_level3_bank(),
        curriculum_id=CURRICULUM_ID,
        level=3,
        run_seed="mb4e-level3-300-contract",
    )

    assert len(selected) == CANONICAL_LEVEL_QUESTION_COUNT == 300
    assert sum(item.integrity_question for item in selected) == CANONICAL_INTEGRITY_QUESTION_COUNT == 50
    assert sum(item.boss_question for item in selected) == 1
    assert sum(not item.integrity_question and not item.boss_question for item in selected) == 249
    assert selected[-1].boss_question is True


def test_level3_builder_requires_exact_level2_bank_not_manifest_claim() -> None:
    with pytest.raises(Level3BuildError, match="Level 2 exercise bank is missing"):
        _assert_required_level2(())

    exact = build_level2_bank(CURRICULUM_ID)
    _assert_required_level2(exact)

    with pytest.raises(Level3BuildError, match="does not exactly match"):
        _assert_required_level2(exact[:-1])


def test_staging_level3_preserves_existing_level1_and_level2_content(tmp_path) -> None:
    root, manifest = _write_level1_base_package(tmp_path)
    level2_stage = tmp_path / "level2-stage"
    _prepare_level2_stage(root, level2_stage, dict(manifest), "provenance.jsonl")
    level2_manifest, before = validate_package(level2_stage, source_resolver=_resolver)
    prior = tuple(item for item in before if item.level in {1, 2})
    _assert_required_level2(before)

    level3_stage = tmp_path / "level3-stage"
    _prepare_level3_stage(
        level2_stage,
        level3_stage,
        dict(level2_manifest),
        "provenance.jsonl",
    )
    staged_manifest, after = validate_package(level3_stage, source_resolver=_resolver)

    assert staged_manifest["levels"] == [1, 2, 3]
    assert tuple(item for item in after if item.level in {1, 2}) == prior
    level3 = tuple(item for item in after if item.level == 3)
    assert len(level3) == TOTAL_COUNT

    selected = select_level_exercises(
        after,
        curriculum_id=CURRICULUM_ID,
        level=3,
        run_seed="mb4e-level3-stage-integration",
    )
    assert len(selected) == 300
    assert sum(item.integrity_question for item in selected) == 50
    assert sum(item.boss_question for item in selected) == 1
    assert selected[-1].boss_question
