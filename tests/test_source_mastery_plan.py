from __future__ import annotations

import json

import pytest

from roberta.learning.mb4e_source_mastery_plan_cli import build_mb4e_source_mastery_plan
from roberta.learning.source_mastery import (
    SourceMasteryPlanError,
    load_source_mastery_plan,
    write_source_mastery_plan,
)


def test_mb4e_plan_selects_only_capabilities_supported_by_source() -> None:
    plan = build_mb4e_source_mastery_plan(source_title="Mastering Blockchain, Fourth Edition")

    assert plan.planner == "roberta-mb4e-source-mastery-planner/v2"
    assert plan.required_stage_count == 14
    assert plan.required_capability_levels == (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 17)
    assert plan.excluded_capability_levels == (12, 15, 16, 18, 19, 20)
    assert plan.exam_questions_per_stage == 300
    assert plan.coverage_complete is True
    assert plan.source_capstone_required is True
    assert [stage.stage for stage in plan.stages] == list(range(1, 15))
    assert plan.stages[0].capability_level == 1
    assert plan.stages[1].capability_level == 2
    assert plan.stages[2].capability_level == 3
    assert plan.stages[2].source_chapters == (6, 9, 13, 14)


def test_mb4e_plan_preserves_completed_level_1_and_2_as_first_two_stages() -> None:
    plan = build_mb4e_source_mastery_plan(source_title="Mastering Blockchain, Fourth Edition")

    completed_capabilities = (1, 2)
    assert plan.required_capability_levels[: len(completed_capabilities)] == completed_capabilities
    assert plan.stages[2].capability_name == "Transactions"


def test_source_mastery_plan_round_trips_and_hash_is_stable(tmp_path) -> None:
    plan = build_mb4e_source_mastery_plan(source_title="Mastering Blockchain, Fourth Edition")
    path = tmp_path / "source_mastery_plan.json"

    write_source_mastery_plan(path, plan)
    loaded = load_source_mastery_plan(path)

    assert loaded == plan
    assert len(plan.plan_hash) == 64
    assert loaded.plan_hash == plan.plan_hash
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["required_stage_count"] == 14
    assert payload["required_capability_levels"] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 17]


def test_source_mastery_plan_rejects_tampering(tmp_path) -> None:
    plan = build_mb4e_source_mastery_plan(source_title="Mastering Blockchain, Fourth Edition")
    path = tmp_path / "source_mastery_plan.json"
    write_source_mastery_plan(path, plan)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["stages"][2]["source_chapters"] = [999]
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SourceMasteryPlanError, match="plan_hash"):
        load_source_mastery_plan(path)
