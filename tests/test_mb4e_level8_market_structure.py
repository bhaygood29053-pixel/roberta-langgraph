from __future__ import annotations

import pytest

from roberta.learning.mb4e_level7_factory import build_level7_bank
from roberta.learning.mb4e_level8_builder_cli import Level8BuildError, _assert_required_level7
from roberta.learning.mb4e_level8_factory import (
    CURRICULUM_ID,
    INTEGRITY_COUNT,
    ORDINARY_COUNT,
    TOTAL_COUNT,
    build_level8_bank,
    level8_provenance_records,
    level8_source_map,
    level8_targets,
)
from roberta.learning.pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    select_level_exercises,
)


def test_level8_bank_shape_and_source_scope() -> None:
    bank = build_level8_bank()

    assert len(level8_targets()) == 29
    assert ORDINARY_COUNT == 377
    assert INTEGRITY_COUNT == 50
    assert TOTAL_COUNT == 428
    assert len(bank) == TOTAL_COUNT
    assert sum(item.integrity_question for item in bank) == 50
    assert sum(item.boss_question for item in bank) == 1
    assert len({item.exercise_id for item in bank}) == TOTAL_COUNT
    assert {item.level for item in bank} == {8}

    source_map = level8_source_map()
    assert {value["chapter"] for value in source_map.values()} == {"Chapter 21"}
    pages = {page for value in source_map.values() for page in value["pdf_pages"]}
    assert min(pages) == 713
    assert max(pages) == 734


def test_level8_canonical_selection_is_300_with_integrity_and_boss_last() -> None:
    bank = build_level8_bank()
    selected = select_level_exercises(
        bank,
        curriculum_id=CURRICULUM_ID,
        level=8,
        run_seed="mb4e-level8-test-v1",
    )

    assert len(selected) == CANONICAL_LEVEL_QUESTION_COUNT == 300
    assert sum(item.integrity_question for item in selected) == CANONICAL_INTEGRITY_QUESTION_COUNT == 50
    assert sum(item.boss_question for item in selected) == 1
    assert sum(not item.integrity_question and not item.boss_question for item in selected) == 249
    assert selected[-1].boss_question is True


def test_level8_provenance_covers_every_exercise() -> None:
    bank = build_level8_bank()
    records = level8_provenance_records(bank)

    assert len(records) == len(bank)
    assert {record["exercise_id"] for record in records} == {item.exercise_id for item in bank}
    assert all(record["source_key"] == "mastering_blockchain_4e_2023" for record in records)
    assert all(record["locations"] for record in records)
    assert all(
        all(location["chapter"] == "Chapter 21" for location in record["locations"])
        for record in records
    )


def test_level8_requires_exact_deterministic_level7_bank() -> None:
    expected = build_level7_bank(CURRICULUM_ID)
    _assert_required_level7(expected)

    with pytest.raises(Level8BuildError, match="missing"):
        _assert_required_level7(())

    tampered = list(expected)
    first = tampered[0]
    tampered[0] = type(first)(
        **{**{field: getattr(first, field) for field in first.__dataclass_fields__}, "question": first.question + " tampered"}
    )
    with pytest.raises(Level8BuildError, match="does not exactly match"):
        _assert_required_level7(tuple(tampered))


def test_level8_targets_lock_market_structure_boundaries() -> None:
    targets = {(item.concept, item.subconcept): item for item in level8_targets()}

    order = targets[("orders", "limit_order")]
    assert "specified price or better" in order.principle.lower()

    lifecycle = targets[("trade_lifecycle", "execution_clearing_settlement")]
    assert "execution" in lifecycle.principle.lower()
    assert "clearing" in lifecycle.principle.lower()
    assert "settlement" in lifecycle.principle.lower()

    dex = targets[("dex_structure", "amm_vs_clob")]
    assert "liquidity pools" in dex.principle.lower()
    assert "order book" in dex.principle.lower()

    aggregator = targets[("dex_aggregation", "onchain_offchain_tradeoffs")]
    assert "trusted-third-party" in aggregator.principle.lower()
    assert "scalability" in aggregator.principle.lower()


def test_level8_boss_synthesizes_market_structure_without_live_claims() -> None:
    boss = next(item for item in build_level8_bank() if item.boss_question)

    assert "market/limit/stop" in boss.question.lower()
    assert "clearing and settlement" in boss.question.lower()
    assert "amm" in boss.question.lower()
    assert "clob" in boss.question.lower()
    assert "current order-book depth" in " ".join(boss.forbidden_inferences).lower()
