from __future__ import annotations

import argparse

from roberta.learning.mb4e_source_mastery_plan_cli import build_mb4e_source_mastery_plan
from roberta.learning.pyramid import evaluate_level
from roberta.learning.pyramid_run_cli import (
    _load_source_mastery_plan,
    _source_stage_selection,
)
from roberta.learning.source_mastery import SourceMasteryPlanError, write_source_mastery_plan
from roberta.learning.training_ledger import PyramidTrainingLedger


def _legacy_pass(level: int):
    return evaluate_level(
        level=level,
        total_questions=1000,
        correct_questions=960,
        integrity_total=50,
        integrity_correct=48,
        boss_passed=True,
    )


def test_runner_selects_stage3_from_existing_level1_level2_history(tmp_path) -> None:
    plan = build_mb4e_source_mastery_plan(
        source_title="Mastering Blockchain, Fourth Edition"
    )
    ledger = PyramidTrainingLedger(tmp_path / "pyramid.sqlite3")
    run_id = ledger.start_run(plan.curriculum_id, "existing-seed", run_id="rp_mb4e")
    ledger.record_level_result(run_id, _legacy_pass(1))
    ledger.record_level_result(run_id, _legacy_pass(2))
    active = ledger.run_history(plan.curriculum_id)[0]

    stage, level, seed, selected_run_id = _source_stage_selection(
        parser=argparse.ArgumentParser(),
        ledger=ledger,
        plan=plan,
        active=active,
        requested_stage=None,
        requested_level=None,
        requested_seed=None,
    )

    assert stage == 3
    assert level == 3
    assert seed == "existing-seed"
    assert selected_run_id == run_id


def test_mb4e_runner_requires_frozen_plan_by_default(tmp_path) -> None:
    curriculum = tmp_path / "curriculum"
    curriculum.mkdir()
    try:
        _load_source_mastery_plan(
            curriculum_path=str(curriculum),
            curriculum_id="mastering_blockchain_4e_2023_book01",
            supplied_path=None,
            disabled=False,
        )
    except SourceMasteryPlanError as exc:
        assert "roberta-pyramid-plan-mb4e-source" in str(exc)
    else:
        raise AssertionError("MB4E canonical runs must require a frozen source plan")


def test_runner_loads_hash_validated_plan_from_curriculum(tmp_path) -> None:
    curriculum = tmp_path / "curriculum"
    curriculum.mkdir()
    plan = build_mb4e_source_mastery_plan(
        source_title="Mastering Blockchain, Fourth Edition"
    )
    target = curriculum / "source_mastery_plan.json"
    write_source_mastery_plan(target, plan)

    path, loaded = _load_source_mastery_plan(
        curriculum_path=str(curriculum),
        curriculum_id=plan.curriculum_id,
        supplied_path=None,
        disabled=False,
    )

    assert path == target
    assert loaded == plan
