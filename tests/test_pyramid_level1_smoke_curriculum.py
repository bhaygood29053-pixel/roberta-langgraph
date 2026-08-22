from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from roberta.learning.curriculum_io import CurriculumPackageError, validate_package
from roberta.learning.pyramid import select_level_exercises
from roberta.learning.user_source_batch import get_user_source_spec


CURRICULUM_ROOT = (
    Path(__file__).resolve().parents[1]
    / "curricula"
    / "mastering_blockchain_4e_2023_smoke_l1"
)
CURRICULUM_ID = "mastering_blockchain_4e_2023_smoke_l1"
SOURCE_REF = "mastering_blockchain_4e_2023"
PROVENANCE_CONTRACT = "roberta-pyramid-source-provenance/v1"


def _provenance_records() -> tuple[dict[str, object], ...]:
    path = CURRICULUM_ROOT / "provenance.jsonl"
    return tuple(
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def test_level1_smoke_package_is_valid_and_source_bound() -> None:
    manifest, exercises = validate_package(CURRICULUM_ROOT)

    assert manifest["curriculum_id"] == CURRICULUM_ID
    assert manifest["approved_source_refs"] == [SOURCE_REF]
    assert manifest["exercise_count"] == 50
    assert len(exercises) == 50
    assert {item.level for item in exercises} == {1}
    assert all(item.curriculum_id == CURRICULUM_ID for item in exercises)
    assert all(item.source_refs == (SOURCE_REF,) for item in exercises)
    assert all(item.requires_live_data is False for item in exercises)


def test_registered_smoke_source_cannot_strip_provenance(tmp_path) -> None:
    copied_root = tmp_path / CURRICULUM_ID
    shutil.copytree(CURRICULUM_ROOT, copied_root)
    manifest_path = copied_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["source_provenance"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(
        CurriculumPackageError,
        match="registered approved source refs require source_provenance",
    ):
        validate_package(copied_root)


def test_level1_smoke_exercises_cover_training_gates_and_core_fundamentals() -> None:
    _, exercises = validate_package(CURRICULUM_ROOT)

    integrity = [item for item in exercises if item.integrity_question]
    bosses = [item for item in exercises if item.boss_question]
    concepts = {item.concept for item in exercises}

    assert len(integrity) == 5
    assert len(bosses) == 1
    assert bosses[0].exercise_id == "mb4e-l1-smoke-050"
    assert {
        "distributed_consensus",
        "fault_tolerance",
        "cap_theorem",
        "ledger_models",
        "generic_elements",
        "block_linking",
        "architecture_layers",
        "business_blockchain",
        "integrity",
        "synthesis",
    }.issubset(concepts)


def test_level1_smoke_selection_contains_all_50_including_integrity_and_boss() -> None:
    _, exercises = validate_package(CURRICULUM_ROOT)

    selected = select_level_exercises(
        exercises,
        curriculum_id=CURRICULUM_ID,
        level=1,
        run_seed="training-start-2026-08-22",
        count=50,
    )

    assert len(selected) == 50
    assert {item.exercise_id for item in selected} == {
        item.exercise_id for item in exercises
    }
    assert sum(item.integrity_question for item in selected) == 5
    assert sum(item.boss_question for item in selected) == 1


def test_level1_smoke_source_ref_is_an_accepted_static_external_reference() -> None:
    manifest, _ = validate_package(CURRICULUM_ROOT)
    spec = get_user_source_spec(SOURCE_REF)
    provenance = manifest["source_provenance"]

    assert spec.authority_class == "secondary"
    assert spec.storage_mode == "external_exact_transcript"
    assert spec.live_state_authorized is False
    assert provenance["contract"] == PROVENANCE_CONTRACT
    assert provenance["file"] == "provenance.jsonl"
    assert provenance["source_key"] == SOURCE_REF
    assert provenance["source_artifact_sha256"] == spec.original_sha256
    assert provenance["source_transcript_sha256"] == spec.transcript_sha256


def test_level1_smoke_manifest_preserves_required_source_metadata() -> None:
    manifest, _ = validate_package(CURRICULUM_ROOT)
    spec = get_user_source_spec(SOURCE_REF)

    assert manifest["source_title"] == spec.title
    assert manifest["source_author"] == "Imran Bashir"
    assert manifest["source_publisher"] == "Packt"
    assert manifest["source_edition"] == "Fourth Edition"
    assert manifest["publication_date"] == "2023"
    assert manifest["source_version"] == spec.version
    assert manifest["source_origin"] == spec.origin
    assert manifest["source_authority_class"] == spec.authority_class
    assert manifest["ingestion_version"] == "utf8-source/v1"
    assert manifest["ingestion_timestamp"] == "2026-08-22T15:30:21Z"
    assert "source-registration merge time" in manifest["ingestion_timestamp_basis"]
    assert manifest["source_status"] == "approved_static_external_exact_transcript"

    limitations = manifest["source_limitations"]
    assert isinstance(limitations, list) and len(limitations) >= 4
    joined = " ".join(str(item) for item in limitations)
    assert "copyrighted secondary educational reference" in joined
    assert "does not republish the full book transcript" in joined
    assert "exact external transcript bytes" in joined
    assert "not authoritative for current" in joined


def test_every_smoke_exercise_has_auditable_granular_source_location() -> None:
    _, exercises = validate_package(CURRICULUM_ROOT)
    records = _provenance_records()
    exercise_ids = {item.exercise_id for item in exercises}

    assert len(records) == 50
    assert {record["exercise_id"] for record in records} == exercise_ids

    for record in records:
        assert record["source_key"] == SOURCE_REF
        assert set(record["supports"]) >= {
            "question",
            "expected_answer",
            "required_reasoning_points",
        }
        locations = record["locations"]
        assert isinstance(locations, list) and locations
        for location in locations:
            assert isinstance(location["chapter"], str)
            assert location["chapter"].startswith("Chapter ")
            assert isinstance(location["section"], str) and location["section"].strip()
            pages = location["book_pages"]
            assert isinstance(pages, list) and pages
            assert all(isinstance(page, int) and page > 0 for page in pages)

        # Provenance is an auditable locator only; copyrighted source text stays out of the repo.
        assert "text" not in record
        assert "excerpt" not in record


def test_boss_provenance_spans_all_required_synthesis_regions() -> None:
    by_id = {record["exercise_id"]: record for record in _provenance_records()}
    boss = by_id["mb4e-l1-smoke-050"]

    assert len(boss["locations"]) == 5
    chapters = {location["chapter"] for location in boss["locations"]}
    assert chapters == {
        "Chapter 1: Blockchain 101",
        "Chapter 5: Consensus Algorithms",
        "Chapter 6: Bitcoin Architecture",
    }
