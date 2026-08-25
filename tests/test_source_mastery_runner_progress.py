from __future__ import annotations

from roberta.learning.mb4e_source_mastery_plan_cli import build_mb4e_source_mastery_plan
from roberta.learning.pyramid import evaluate_level, get_level_spec
from roberta.learning.source_mastery import SourceMasteryStage, make_source_mastery_plan
from roberta.learning.training_ledger import PyramidTrainingLedger


def _pass(level: int, *, total_questions: int = 300):
    return evaluate_level(
        level=level,
        total_questions=total_questions,
        correct_questions=int(total_questions * 0.96),
        integrity_total=50,
        integrity_correct=49,
        boss_passed=True,
    )


def _stage(stage: int, capability_level: int) -> SourceMasteryStage:
    spec = get_level_spec(capability_level)
    return SourceMasteryStage(
        stage=stage,
        capability_level=capability_level,
        capability_name=spec.name,
        domain=spec.domain,
        source_chapters=(stage,),
        rationale=f"test coverage for capability {capability_level}",
    )


def test_binding_maps_existing_level1_and_level2_without_rewriting_history(tmp_path) -> None:
    ledger = PyramidTrainingLedger(tmp_path / "pyramid.sqlite3")
    run_id = ledger.start_run(
        "mastering_blockchain_4e_2023_book01",
        "legacy-seed",
        run_id="rp_existing_mb4e",
    )
    ledger.record_level_result(run_id, _pass(1, total_questions=1000))
    ledger.record_level_result(run_id, _pass(2, total_questions=1000))

    plan = build_mb4e_source_mastery_plan(
        source_title="Mastering Blockchain, Fourth Edition"
    )
    assert ledger.preview_source_mastery_completed_stages(run_id, plan) == 2

    before = ledger.run_history(plan.curriculum_id)[0].copy()
    binding = ledger.bind_source_mastery_plan(run_id, plan)
    after = ledger.run_history(plan.curriculum_id)[0]
    progress = ledger.source_mastery_progress(run_id)

    assert binding["completed_stage_count"] == 2
    assert progress is not None
    assert progress["plan_hash"] == plan.plan_hash
    assert [row["capability_level"] for row in progress["stages"]] == [1, 2]
    assert all(row["historical_mapped"] == 1 for row in progress["stages"])
    assert before["highest_level_passed"] == after["highest_level_passed"] == 2
    assert before["status"] == after["status"] == "active"


def test_source_stage_progression_allows_noncontiguous_capability_levels(tmp_path) -> None:
    ledger = PyramidTrainingLedger(tmp_path / "pyramid.sqlite3")
    plan = make_source_mastery_plan(
        curriculum_id="book-gap",
        source_key="book-gap-source",
        source_title="Gap Test",
        planner="test/v1",
        planner_basis="prove source stages can skip unrelated capability numbers",
        stages=(_stage(1, 1), _stage(2, 3)),
        source_capstone_required=False,
    )
    run_id = ledger.start_run(plan.curriculum_id, "seed-gap")
    ledger.bind_source_mastery_plan(run_id, plan)

    first = ledger.record_source_stage_result(run_id, plan, 1, _pass(1))
    assert first["completed_stage_count"] == 1
    assert first["status"] == "active"

    second = ledger.record_source_stage_result(run_id, plan, 2, _pass(3))
    progress = ledger.source_mastery_progress(run_id)
    run = ledger.run_history(plan.curriculum_id)[0]

    assert second["completed_stage_count"] == 2
    assert second["status"] == "mastered"
    assert progress is not None
    assert [row["capability_level"] for row in progress["stages"]] == [1, 3]
    # Global capability progress remains the highest contiguous prefix. Capability 2
    # was not passed, so the source-specific capability-3 stage must not imply it was.
    assert run["highest_level_passed"] == 1
    assert run["status"] == "mastered"


def test_source_stage_completion_waits_for_required_capstone(tmp_path) -> None:
    ledger = PyramidTrainingLedger(tmp_path / "pyramid.sqlite3")
    plan = make_source_mastery_plan(
        curriculum_id="book-capstone",
        source_key="book-capstone-source",
        source_title="Capstone Test",
        planner="test/v1",
        planner_basis="prove stages complete before source mastery",
        stages=(_stage(1, 1),),
        source_capstone_required=True,
    )
    run_id = ledger.start_run(plan.curriculum_id, "seed-capstone")
    ledger.bind_source_mastery_plan(run_id, plan)
    state = ledger.record_source_stage_result(run_id, plan, 1, _pass(1))

    assert state["status"] == "stages_complete"
    assert state["capstone_passed"] == 0
    assert ledger.run_history(plan.curriculum_id)[0]["status"] == "active"

    ledger.mark_source_capstone_passed(run_id, plan.plan_hash)
    final = ledger.source_mastery_progress(run_id)
    assert final is not None
    assert final["status"] == "mastered"
    assert final["capstone_passed"] == 1
    assert ledger.run_history(plan.curriculum_id)[0]["status"] == "mastered"


def test_bound_plan_hash_is_immutable(tmp_path) -> None:
    ledger = PyramidTrainingLedger(tmp_path / "pyramid.sqlite3")
    plan_a = make_source_mastery_plan(
        curriculum_id="book-hash",
        source_key="book-hash-source",
        source_title="Hash Test",
        planner="test/v1",
        planner_basis="first frozen plan",
        stages=(_stage(1, 1),),
    )
    plan_b = make_source_mastery_plan(
        curriculum_id="book-hash",
        source_key="book-hash-source",
        source_title="Hash Test",
        planner="test/v1",
        planner_basis="different frozen plan",
        stages=(_stage(1, 1),),
    )
    run_id = ledger.start_run(plan_a.curriculum_id, "seed-hash")
    ledger.bind_source_mastery_plan(run_id, plan_a)

    try:
        ledger.bind_source_mastery_plan(run_id, plan_b)
    except ValueError as exc:
        assert "different source mastery plan" in str(exc)
    else:
        raise AssertionError("a bound source mastery plan hash must be immutable")
