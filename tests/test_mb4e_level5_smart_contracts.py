from __future__ import annotations

import pytest

from roberta.learning.mb4e_level4_factory import build_level4_bank
from roberta.learning.mb4e_level5_builder_cli import Level5BuildError, _assert_required_level4
from roberta.learning.mb4e_level5_factory import (
    CURRICULUM_ID,
    INTEGRITY_COUNT,
    ORDINARY_COUNT,
    SOURCE_KEY,
    TOTAL_COUNT,
    build_level5_bank,
    level5_provenance_records,
    level5_source_map,
    level5_targets,
)
from roberta.learning.pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    select_level_exercises,
)


def test_level5_bank_is_source_grounded_and_large_enough_for_300_question_exam() -> None:
    targets = level5_targets()
    bank = build_level5_bank()
    source_map = level5_source_map()

    assert len(targets) == 34
    assert ORDINARY_COUNT == 442
    assert INTEGRITY_COUNT == 50
    assert TOTAL_COUNT == 493
    assert len(bank) == TOTAL_COUNT
    assert len(bank) >= CANONICAL_LEVEL_QUESTION_COUNT
    assert sum(item.integrity_question for item in bank) == 50
    assert sum(item.boss_question for item in bank) == 1
    assert all(SOURCE_KEY in item.source_refs for item in bank)
    assert {value["chapter"] for value in source_map.values()} == {
        "Chapter 8",
        "Chapter 11",
        "Chapter 12",
    }
    for item in bank:
        detailed = [ref for ref in item.source_refs if ref != SOURCE_KEY]
        assert detailed
        assert all(ref in source_map for ref in detailed)


def test_level5_source_map_matches_frozen_stage5_chapters() -> None:
    source_map = level5_source_map()
    assert set(source_map) == {
        "MB4E-CH8-P254-258-SMART-CONTRACT-FOUNDATIONS",
        "MB4E-CH8-P258-263-RICARDIAN-TEMPLATES",
        "MB4E-CH8-P264-272-ORACLES",
        "MB4E-CH8-P273-278-DEPLOYMENT-DAO-ADVANCES",
        "MB4E-CH11-P376-387-COMPILER-TOOLS",
        "MB4E-CH11-P387-392-SOLIDITY-FUNCTIONS",
        "MB4E-CH11-P392-398-SOLIDITY-DATA",
        "MB4E-CH11-P398-402-SOLIDITY-STRUCTURES",
        "MB4E-CH12-P404-414-WEB3-DEPLOYMENT",
        "MB4E-CH12-P414-424-WEB3-FRONTENDS",
        "MB4E-CH12-P424-437-TRUFFLE-WORKFLOW",
        "MB4E-CH12-P437-439-IPFS-DAPP",
    }


def test_level5_provenance_covers_every_exercise() -> None:
    bank = build_level5_bank()
    records = level5_provenance_records(bank)
    source_map = level5_source_map()

    assert len(records) == len(bank)
    assert {record["exercise_id"] for record in records} == {item.exercise_id for item in bank}
    for record in records:
        assert record["source_key"] == SOURCE_KEY
        assert record["locations"]
        assert all(location["legacy_source_ref"] in source_map for location in record["locations"])


def test_level5_canonical_selection_is_249_ordinary_50_integrity_1_boss() -> None:
    selected = select_level_exercises(
        build_level5_bank(),
        curriculum_id=CURRICULUM_ID,
        level=5,
        run_seed="mb4e-level5-300-contract",
    )

    assert len(selected) == CANONICAL_LEVEL_QUESTION_COUNT == 300
    assert sum(item.integrity_question for item in selected) == CANONICAL_INTEGRITY_QUESTION_COUNT == 50
    assert sum(item.boss_question for item in selected) == 1
    assert sum(not item.integrity_question and not item.boss_question for item in selected) == 249
    assert selected[-1].boss_question is True


def test_level5_builder_requires_exact_level4_bank_not_manifest_claim() -> None:
    with pytest.raises(Level5BuildError, match="Level 4 exercise bank is missing"):
        _assert_required_level4(())

    exact = build_level4_bank(CURRICULUM_ID)
    _assert_required_level4(exact)

    with pytest.raises(Level5BuildError, match="does not exactly match"):
        _assert_required_level4(exact[:-1])


def test_level5_boss_synthesizes_contract_toolchain_web3_and_dapp_boundaries() -> None:
    boss = [item for item in build_level5_bank() if item.boss_question]
    assert len(boss) == 1
    item = boss[0]
    text = (item.question + " " + item.expected_answer).lower()
    for required in ("oracle", "solidity", "abi", "web3", "truffle", "ipfs", "reentrancy"):
        assert required in text
