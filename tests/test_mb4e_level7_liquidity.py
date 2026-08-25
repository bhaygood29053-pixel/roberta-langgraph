from __future__ import annotations

import pytest

from roberta.learning.mb4e_level6_factory import build_level6_bank
from roberta.learning.mb4e_level7_builder_cli import Level7BuildError, _assert_required_level6
from roberta.learning.mb4e_level7_factory import (
    CURRICULUM_ID,
    INTEGRITY_COUNT,
    ORDINARY_COUNT,
    TOTAL_COUNT,
    build_level7_bank,
    level7_provenance_records,
    level7_source_map,
    level7_targets,
)
from roberta.learning.pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    select_level_exercises,
)


def test_level7_bank_shape_and_source_scope() -> None:
    bank = build_level7_bank()

    assert len(level7_targets()) == 28
    assert ORDINARY_COUNT == 364
    assert INTEGRITY_COUNT == 50
    assert TOTAL_COUNT == 415
    assert len(bank) == TOTAL_COUNT
    assert sum(item.integrity_question for item in bank) == 50
    assert sum(item.boss_question for item in bank) == 1
    assert len({item.exercise_id for item in bank}) == TOTAL_COUNT
    assert {item.level for item in bank} == {7}

    source_map = level7_source_map()
    assert {value["chapter"] for value in source_map.values()} == {"Chapter 21"}
    pages = {page for value in source_map.values() for page in value["pdf_pages"]}
    assert min(pages) == 728
    assert max(pages) == 746
    assert set(range(734, 741)).isdisjoint(pages)


def test_level7_canonical_selection_is_300_with_integrity_and_boss_last() -> None:
    bank = build_level7_bank()
    selected = select_level_exercises(
        bank,
        curriculum_id=CURRICULUM_ID,
        level=7,
        run_seed="mb4e-level7-test-v1",
    )

    assert len(selected) == CANONICAL_LEVEL_QUESTION_COUNT == 300
    assert sum(item.integrity_question for item in selected) == CANONICAL_INTEGRITY_QUESTION_COUNT == 50
    assert sum(item.boss_question for item in selected) == 1
    assert sum(not item.integrity_question and not item.boss_question for item in selected) == 249
    assert selected[-1].boss_question is True


def test_level7_provenance_covers_every_exercise() -> None:
    bank = build_level7_bank()
    records = level7_provenance_records(bank)

    assert len(records) == len(bank)
    assert {record["exercise_id"] for record in records} == {item.exercise_id for item in bank}
    assert all(record["source_key"] == "mastering_blockchain_4e_2023" for record in records)
    assert all(record["locations"] for record in records)
    assert all(
        all(location["chapter"] == "Chapter 21" for location in record["locations"])
        for record in records
    )


def test_level7_requires_exact_deterministic_level6_bank() -> None:
    expected = build_level6_bank(CURRICULUM_ID)
    _assert_required_level6(expected)

    with pytest.raises(Level7BuildError, match="missing"):
        _assert_required_level6(())

    tampered = list(expected)
    first = tampered[0]
    tampered[0] = type(first)(
        **{**{field: getattr(first, field) for field in first.__dataclass_fields__}, "question": first.question + " tampered"}
    )
    with pytest.raises(Level7BuildError, match="does not exactly match"):
        _assert_required_level6(tuple(tampered))


def test_level7_targets_lock_core_liquidity_boundaries() -> None:
    targets = {(item.concept, item.subconcept): item for item in level7_targets()}

    slippage = targets[("liquidity_depth", "depth_trade_size_slippage")]
    assert "Deeper" in slippage.required_points[0] or "deeper" in slippage.principle

    il = targets[("liquidity_risk", "impermanent_loss")]
    assert "relative" in il.principle.lower()
    assert "withdraw" in il.principle.lower()

    vamm = targets[("amm_innovation", "virtual_amm")]
    assert "collateral" in vamm.principle.lower()
    assert "conventional underlying liquidity pool" in vamm.principle.lower()

    pool = targets[("uniswap_liquidity", "position_management")]
    assert "unclaimed fees" in pool.principle.lower()
    assert "remove liquidity" in pool.principle.lower()


def test_level7_boss_synthesizes_liquidity_without_live_market_claims() -> None:
    boss = next(item for item in build_level7_bank() if item.boss_question)

    assert "impermanent loss" in boss.question.lower()
    assert "slippage" in boss.question.lower()
    assert "capital efficiency" in boss.question.lower()
    assert "uniswap" in boss.question.lower()
    assert "live pool reserves" in " ".join(boss.forbidden_inferences).lower()
