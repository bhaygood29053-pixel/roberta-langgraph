from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from roberta.learning.mb4e_level2_builder_cli import Level2BuildError, _assert_existing_level2
from roberta.learning.mb4e_level2_factory import (
    CURRICULUM_ID,
    INTEGRITY_COUNT,
    ORDINARY_COUNT,
    TOTAL_COUNT,
    build_level2_bank,
    level2_provenance_records,
    level2_source_map,
    level2_targets,
)
from roberta.learning.pyramid import select_level_exercises


def test_level2_bank_has_production_shape_and_stable_ids() -> None:
    bank = build_level2_bank()
    assert len(level2_targets()) == 55
    assert len(bank) == TOTAL_COUNT == 1206
    assert ORDINARY_COUNT == 1155
    assert sum(item.integrity_question for item in bank) == INTEGRITY_COUNT == 50
    assert sum(item.boss_question for item in bank) == 1
    assert bank[0].exercise_id == "MB4E-L02-00001"
    assert bank[ORDINARY_COUNT - 1].exercise_id == "MB4E-L02-01155"
    assert bank[-1].exercise_id == "MB4E-L02-01206"
    assert bank[-1].boss_question is True
    assert len({item.exercise_id for item in bank}) == TOTAL_COUNT
    assert all(item.level == 2 for item in bank)
    assert all(item.curriculum_id == CURRICULUM_ID for item in bank)


def test_level2_canonical_selection_is_949_plus_50_plus_boss() -> None:
    selected = select_level_exercises(
        build_level2_bank(),
        curriculum_id=CURRICULUM_ID,
        level=2,
        run_seed="level2-selection-test",
    )
    assert len(selected) == 1000
    assert sum(item.integrity_question for item in selected) == 50
    assert sum(item.boss_question for item in selected) == 1
    assert selected[-1].boss_question is True
    assert sum(not item.integrity_question and not item.boss_question for item in selected) == 949


def test_level2_source_map_stays_within_declared_chapters_and_pdf_pages() -> None:
    source_map = level2_source_map()
    assert source_map
    assert {str(item["chapter"]) for item in source_map.values()} == {"Chapter 1", "Chapter 2", "Chapter 5"}
    pages = {page for item in source_map.values() for page in item["pdf_pages"]}
    assert min(pages) == 37
    assert max(pages) == 189
    assert {62, 63, 64, 65, 66, 67, 68, 69, 70}.issubset(pages)
    assert set(range(152, 190)).issubset(pages)


def test_level2_provenance_covers_bank_exactly_without_source_text() -> None:
    bank = build_level2_bank()
    records = level2_provenance_records(bank)
    assert len(records) == len(bank)
    assert {item["exercise_id"] for item in records} == {item.exercise_id for item in bank}
    for record in records:
        assert record["source_key"] == "mastering_blockchain_4e_2023"
        assert set(record["supports"]) >= {"question", "expected_answer", "required_reasoning_points"}
        assert record["locations"]
        serialized = repr(record)
        assert "excerpt" not in serialized
        assert "text" not in serialized
        for location in record["locations"]:
            assert location["chapter"] in {"Chapter 1", "Chapter 2", "Chapter 5"}
            assert location["pdf_pages"]
            assert location["legacy_source_ref"] in level2_source_map()


def test_level2_encodes_material_consensus_misconception_guards() -> None:
    by_key = {(item.concept, item.subconcept): item for item in level2_targets()}
    assert "distributed and decentralized as synonyms" in " ".join(by_key[("decentralization", "distributed_vs_decentralized")].forbidden_inferences)
    assert "all consensus is impossible" in " ".join(by_key[("consensus", "flp_impossibility")].forbidden_inferences)
    assert "Byzantine" in " ".join(by_key[("fault_tolerance", "cft_vs_bft")].forbidden_inferences)
    assert "2f+1" in " ".join(by_key[("fault_tolerance", "bft_lower_bound")].forbidden_inferences)
    assert "hash puzzle alone" in " ".join(by_key[("nakamoto", "pow_role")].forbidden_inferences)
    assert "deterministic finality" in " ".join(by_key[("nakamoto", "probabilistic_consensus")].forbidden_inferences)


def test_existing_level2_is_idempotent_only_when_exact() -> None:
    generated = build_level2_bank()
    assert _assert_existing_level2(generated, generated) is True
    assert _assert_existing_level2((), generated) is False

    changed = (replace(generated[0], question="different question"), *generated[1:])
    with pytest.raises(Level2BuildError, match="does not exactly match"):
        _assert_existing_level2(changed, generated)

    with pytest.raises(Level2BuildError, match="does not exactly match"):
        _assert_existing_level2(generated[:10], generated)
