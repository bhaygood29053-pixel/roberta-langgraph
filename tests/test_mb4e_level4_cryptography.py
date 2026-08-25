from __future__ import annotations

from roberta.learning.mb4e_level4_factory import (
    CURRICULUM_ID,
    INTEGRITY_COUNT,
    ORDINARY_COUNT,
    SOURCE_KEY,
    TOTAL_COUNT,
    build_level4_bank,
    level4_provenance_records,
    level4_source_map,
    level4_targets,
)
from roberta.learning.pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    select_level_exercises,
)


def test_level4_bank_is_source_grounded_and_large_enough() -> None:
    targets = level4_targets()
    bank = build_level4_bank()

    assert len(targets) == 28
    assert ORDINARY_COUNT == 28 * 13
    assert TOTAL_COUNT == ORDINARY_COUNT + INTEGRITY_COUNT + 1
    assert len(bank) == TOTAL_COUNT
    assert len(bank) >= CANONICAL_LEVEL_QUESTION_COUNT
    assert sum(item.integrity_question for item in bank) == 50
    assert sum(item.boss_question for item in bank) == 1
    assert all(item.level == 4 for item in bank)
    assert all(item.curriculum_id == CURRICULUM_ID for item in bank)
    assert all(item.source_refs[0] == SOURCE_KEY for item in bank)


def test_level4_source_scope_matches_frozen_stage4_plan() -> None:
    source_map = level4_source_map()
    targets = level4_targets()

    chapters = {target.chapter for target in targets}
    assert chapters == {"Chapter 3", "Chapter 4", "Chapter 18"}
    assert {int(target.chapter.split()[-1]) for target in targets} == {3, 4, 18}
    assert all(target.source_ref in source_map for target in targets)
    assert all(target.pdf_pages for target in targets)


def test_level4_provenance_records_are_canonical() -> None:
    bank = build_level4_bank()
    records = level4_provenance_records(bank)

    assert len(records) == len(bank)
    assert {record["exercise_id"] for record in records} == {
        item.exercise_id for item in bank
    }
    assert all(record["source_key"] == SOURCE_KEY for record in records)
    assert all(record["locations"] for record in records)


def test_level4_canonical_selection_is_300_with_boss_last() -> None:
    bank = build_level4_bank()
    selected = select_level_exercises(
        bank,
        curriculum_id=CURRICULUM_ID,
        level=4,
        run_seed="mb4e-level4-test-selection",
    )

    assert len(selected) == CANONICAL_LEVEL_QUESTION_COUNT == 300
    assert sum(item.integrity_question for item in selected) == CANONICAL_INTEGRITY_QUESTION_COUNT == 50
    assert sum(item.boss_question for item in selected) == 1
    assert selected[-1].boss_question is True
    assert sum(
        not item.integrity_question and not item.boss_question for item in selected
    ) == 249


def test_level4_bank_is_deterministic() -> None:
    assert build_level4_bank() == build_level4_bank()
