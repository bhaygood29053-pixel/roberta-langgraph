from __future__ import annotations

import pytest

from roberta.learning.mb4e_level5_factory import build_level5_bank
from roberta.learning.mb4e_level6_builder_cli import Level6BuildError, _assert_required_level5
from roberta.learning.mb4e_level6_factory import (
    CURRICULUM_ID,
    INTEGRITY_COUNT,
    ORDINARY_COUNT,
    TOTAL_COUNT,
    build_level6_bank,
    level6_provenance_records,
    level6_source_map,
    level6_targets,
)
from roberta.learning.pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    select_level_exercises,
)


def test_level6_bank_is_deterministic_and_has_expected_counts() -> None:
    first = build_level6_bank()
    second = build_level6_bank()
    assert first == second
    assert len(level6_targets()) == 34
    assert ORDINARY_COUNT == 442
    assert INTEGRITY_COUNT == 50
    assert TOTAL_COUNT == 493
    assert len(first) == TOTAL_COUNT
    assert sum(item.integrity_question for item in first) == 50
    assert sum(item.boss_question for item in first) == 1
    assert len({item.exercise_id for item in first}) == TOTAL_COUNT
    assert all(item.level == 6 for item in first)


def test_level6_is_grounded_only_in_chapter15_source_ranges() -> None:
    source_map = level6_source_map()
    assert len(source_map) == 6
    assert {entry["chapter"] for entry in source_map.values()} == {"Chapter 15"}
    all_pages = {page for entry in source_map.values() for page in entry["pdf_pages"]}
    assert min(all_pages) == 502
    assert max(all_pages) == 529
    assert all(502 <= page <= 529 for page in all_pages)


def test_every_level6_exercise_has_canonical_source_provenance() -> None:
    bank = build_level6_bank()
    records = level6_provenance_records(bank)
    assert len(records) == TOTAL_COUNT
    assert {record["exercise_id"] for record in records} == {
        exercise.exercise_id for exercise in bank
    }
    for exercise, record in zip(bank, records, strict=True):
        assert exercise.source_refs[0] == "mastering_blockchain_4e_2023"
        assert record["source_key"] == "mastering_blockchain_4e_2023"
        assert record["locations"]
        assert all(location["chapter"] == "Chapter 15" for location in record["locations"])


def test_level6_canonical_selection_is_300_with_integrity_and_boss_last() -> None:
    selected = select_level_exercises(
        build_level6_bank(),
        curriculum_id=CURRICULUM_ID,
        level=6,
        run_seed="level6-canonical-test",
    )
    assert len(selected) == CANONICAL_LEVEL_QUESTION_COUNT == 300
    assert sum(item.integrity_question for item in selected) == CANONICAL_INTEGRITY_QUESTION_COUNT == 50
    assert sum(item.boss_question for item in selected) == 1
    assert selected[-1].boss_question
    assert sum(
        not item.integrity_question and not item.boss_question for item in selected
    ) == 249


def test_level6_builder_requires_exact_level5_bank() -> None:
    level5 = build_level5_bank(CURRICULUM_ID)
    _assert_required_level5(level5)
    with pytest.raises(Level6BuildError, match="does not exactly match"):
        _assert_required_level5(level5[:-1])
    with pytest.raises(Level6BuildError, match="missing"):
        _assert_required_level5(())


def test_level6_boss_synthesizes_tokenization_and_economics_boundaries() -> None:
    boss = next(item for item in build_level6_bank() if item.boss_question)
    text = (boss.question + " " + boss.expected_answer).lower()
    for term in (
        "fungible",
        "stable",
        "security",
        "erc-20",
        "erc-721",
        "offering",
        "tokenomics",
        "cryptoeconomics",
        "token engineering",
        "taxonomy",
    ):
        assert term in text
    assert any("liquidity" in item.lower() for item in boss.forbidden_inferences)
    assert any("supply" in item.lower() for item in boss.forbidden_inferences)
