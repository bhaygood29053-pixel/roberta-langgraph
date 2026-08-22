from __future__ import annotations

from pathlib import Path

from roberta.learning.curriculum_io import validate_package
from roberta.learning.pyramid import select_level_exercises
from roberta.learning.user_source_batch import get_user_source_spec


CURRICULUM_ROOT = (
    Path(__file__).resolve().parents[1]
    / "curricula"
    / "mastering_blockchain_4e_2023_smoke_l1"
)
CURRICULUM_ID = "mastering_blockchain_4e_2023_smoke_l1"
SOURCE_REF = "mastering_blockchain_4e_2023"


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
    assert {item.exercise_id for item in selected} == {item.exercise_id for item in exercises}
    assert sum(item.integrity_question for item in selected) == 5
    assert sum(item.boss_question for item in selected) == 1


def test_level1_smoke_source_ref_is_an_accepted_static_external_reference() -> None:
    spec = get_user_source_spec(SOURCE_REF)

    assert spec.authority_class == "secondary"
    assert spec.storage_mode == "external_exact_transcript"
    assert spec.live_state_authorized is False
