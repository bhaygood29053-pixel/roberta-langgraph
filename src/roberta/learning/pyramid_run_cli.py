from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import secrets

from .curriculum_io import validate_package
from .pyramid import CANONICAL_LEVEL_QUESTION_COUNT, select_level_exercises
from .pyramid_adjudicator_retry import create_pyramid_runtime_model
from .pyramid_answer_recovery import MissingAnswerRetryModel
from .pyramid_exam import run_exam
from .pyramid_learned_concept_answer import PyramidLearnedConceptAnswerModel
from .pyramid_learned_concepts import PyramidLearnedConceptError, load_learned_concepts
from .source_mastery import SourceMasteryPlan, SourceMasteryPlanError, load_source_mastery_plan
from .training_ledger import PyramidTrainingLedger


MB4E_CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
SOURCE_MASTERY_PLAN_FILENAME = "source_mastery_plan.json"


def _active_run(ledger: PyramidTrainingLedger, curriculum_id: str) -> dict[str, object] | None:
    for run in ledger.run_history(curriculum_id):
        if run["status"] == "active":
            return run
    return None


def _progress(done: int, total: int) -> None:
    percent = (done / total) * 100
    print(f"PROGRESS {done}/{total} ({percent:.1f}%)", flush=True)


def _checkpoint_run_dir(
    root: str | Path,
    *,
    curriculum_id: str,
    seed: str,
    question_count: int,
) -> Path:
    """Namespace restart checkpoints by selected exam size.

    Pre-migration 1,000-question checkpoints remain in the legacy seed root and are
    never consumed by new 300-question runs. New and future canonical attempts use
    an explicit q<count> subdirectory so changing an exam contract cannot silently
    collide with historical batch identities.
    """
    return Path(root) / curriculum_id / str(seed) / f"q{question_count}"


def _load_learned_memory(
    *,
    supplied_path: str | None,
    disabled: bool,
    curriculum_id: str,
    level: int,
) -> tuple[Path | None, tuple]:
    if disabled:
        if supplied_path is not None:
            raise PyramidLearnedConceptError("--learned-concepts cannot be combined with --without-learned-concepts")
        return None, ()

    path = Path(supplied_path) if supplied_path is not None else Path(f".roberta/pyramid_learned_concepts/{curriculum_id}.json")
    if not path.exists():
        if supplied_path is not None:
            raise PyramidLearnedConceptError(f"Pyramid learned-concepts store does not exist: {path}")
        return path, ()
    learned = load_learned_concepts(path, curriculum_id=curriculum_id, level=level)
    return path, learned


def _build_answer_model(model: object, learned: tuple) -> MissingAnswerRetryModel:
    """Build the canonical answer path with one bounded ID-substitution recovery."""
    answer_base = PyramidLearnedConceptAnswerModel(model, learned) if learned else model
    return MissingAnswerRetryModel(answer_base, recover_unexpected_initial_ids=True)


def _load_source_mastery_plan(
    *,
    curriculum_path: str,
    curriculum_id: str,
    supplied_path: str | None,
    disabled: bool,
) -> tuple[Path | None, SourceMasteryPlan | None]:
    if disabled:
        if supplied_path is not None:
            raise SourceMasteryPlanError(
                "--source-mastery-plan cannot be combined with --without-source-mastery-plan"
            )
        return None, None

    path = Path(supplied_path) if supplied_path is not None else Path(curriculum_path) / SOURCE_MASTERY_PLAN_FILENAME
    if not path.exists():
        if supplied_path is not None:
            raise SourceMasteryPlanError(f"source mastery plan does not exist: {path}")
        if curriculum_id == MB4E_CURRICULUM_ID:
            raise SourceMasteryPlanError(
                "Mastering Blockchain requires its frozen source mastery plan before the next canonical run. "
                f'Run: roberta-pyramid-plan-mb4e-source --curriculum "{curriculum_path}"'
            )
        return path, None

    plan = load_source_mastery_plan(path)
    if plan.curriculum_id != curriculum_id:
        raise SourceMasteryPlanError(
            f"source mastery plan belongs to {plan.curriculum_id}, expected {curriculum_id}"
        )
    return path, plan


def _select_or_exit(
    bank: tuple,
    *,
    curriculum_id: str,
    level: int,
    seed: str,
    curriculum_path: str,
    count: int = CANONICAL_LEVEL_QUESTION_COUNT,
) -> tuple:
    try:
        return select_level_exercises(
            bank,
            curriculum_id=curriculum_id,
            level=level,
            run_seed=seed,
            count=count,
        )
    except ValueError as exc:
        eligible = sum(1 for item in bank if item.curriculum_id == curriculum_id and item.level == level)
        if eligible < count:
            lines = [
                "CURRICULUM_LEVEL_BANK_MISSING",
                f"CURRICULUM {curriculum_id}",
                f"LEVEL {level}",
                f"ELIGIBLE {eligible}",
                f"REQUIRED {count}",
                f"DETAIL {exc}",
            ]
            if curriculum_id == MB4E_CURRICULUM_ID:
                if level == 2:
                    lines.append(f'BUILD_COMMAND roberta-pyramid-build-mb4e-level2 --curriculum "{curriculum_path}"')
                elif level == 3:
                    lines.append(f'BUILD_COMMAND roberta-pyramid-build-mb4e-level3 --curriculum "{curriculum_path}"')
            lines.append(f"NEXT_GATE build_level_{level}_curriculum")
            raise SystemExit("\n".join(lines)) from exc
        raise


def _source_stage_selection(
    *,
    parser: argparse.ArgumentParser,
    ledger: PyramidTrainingLedger,
    plan: SourceMasteryPlan,
    active: dict[str, object] | None,
    requested_stage: int | None,
    requested_level: int | None,
    requested_seed: str | None,
) -> tuple[int, int, str, str | None]:
    if active is not None:
        run_id = str(active["run_id"])
        completed = ledger.preview_source_mastery_completed_stages(run_id, plan)
        expected_stage = completed + 1
        if expected_stage > plan.required_stage_count:
            progress = ledger.source_mastery_progress(run_id)
            if progress is not None and str(progress["status"]) == "stages_complete":
                raise SystemExit("SOURCE_STAGES_COMPLETE\nNEXT_GATE source_capstone")
            raise SystemExit("SOURCE_MASTERY_STAGES_ALREADY_COMPLETE")
        stage_number = requested_stage or expected_stage
        if stage_number != expected_stage:
            parser.error(
                f"active source mastery run expects stage {expected_stage}, not stage {stage_number}"
            )
        active_seed = str(active["run_seed"])
        if requested_seed is not None and str(requested_seed) != active_seed:
            parser.error("--seed does not match the active Pyramid run")
        seed = active_seed
    else:
        run_id = None
        stage_number = requested_stage or 1
        if stage_number != 1:
            parser.error("a new source mastery run must begin at source stage 1")
        seed = requested_seed or secrets.token_hex(8)

    stage = plan.stages[stage_number - 1]
    level = stage.capability_level
    if requested_level is not None and requested_level != level:
        parser.error(
            f"source stage {stage_number} maps to capability level {level}, not level {requested_level}"
        )
    return stage_number, level, seed, run_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a scored Roberta Pyramid level against a validated curriculum package.")
    parser.add_argument("--curriculum", required=True, help="Curriculum package directory")
    parser.add_argument("--db", default=".roberta/pyramid_training.sqlite3", help="Pyramid SQLite training ledger")
    parser.add_argument("--level", type=int, help="Capability level to run. With a source mastery plan this must match the current source stage.")
    parser.add_argument("--stage", type=int, help="Source mastery stage to run; defaults to the next required stage when a frozen plan is present")
    parser.add_argument("--seed", help="Run seed. A new random seed is generated for a new run when omitted.")
    parser.add_argument("--batch-size", type=int, default=10, help="Questions per model batch (default: 10)")
    parser.add_argument("--checkpoint-dir", default=".roberta/pyramid_checkpoints", help="Root directory for restart-safe batch checkpoints")
    parser.add_argument("--learned-concepts", help="Verified Pyramid learned-concepts store. When omitted, .roberta/pyramid_learned_concepts/<curriculum_id>.json is used if present.")
    parser.add_argument("--without-learned-concepts", action="store_true", help="Explicitly disable verified Pyramid learned-concept retrieval for this run.")
    parser.add_argument("--source-mastery-plan", help="Frozen source mastery plan. Defaults to <curriculum>/source_mastery_plan.json when present.")
    parser.add_argument("--without-source-mastery-plan", action="store_true", help="Explicitly use the legacy fixed 20-level ladder instead of a source-specific plan.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and select the exam without making model calls or writing a run")
    parser.add_argument("--smoke-count", type=int, help="Run a non-canonical sample for model/evaluator testing; results are not written to the ledger")
    args = parser.parse_args()

    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.smoke_count is not None and not 1 <= args.smoke_count < CANONICAL_LEVEL_QUESTION_COUNT:
        parser.error(f"--smoke-count must be between 1 and {CANONICAL_LEVEL_QUESTION_COUNT - 1}")

    manifest, bank = validate_package(args.curriculum)
    curriculum_id = str(manifest["curriculum_id"])
    ledger = PyramidTrainingLedger(args.db)
    active = _active_run(ledger, curriculum_id)
    try:
        source_plan_path, source_plan = _load_source_mastery_plan(
            curriculum_path=args.curriculum,
            curriculum_id=curriculum_id,
            supplied_path=args.source_mastery_plan,
            disabled=args.without_source_mastery_plan,
        )
    except SourceMasteryPlanError as exc:
        parser.error(str(exc))
    if args.stage is not None and source_plan is None:
        parser.error("--stage requires a frozen source mastery plan")

    source_stage: int | None = None
    if args.smoke_count is not None:
        if source_plan is not None:
            if active is not None:
                completed = ledger.preview_source_mastery_completed_stages(str(active["run_id"]), source_plan)
                source_stage = args.stage or min(completed + 1, source_plan.required_stage_count)
            else:
                source_stage = args.stage or 1
            if not 1 <= source_stage <= source_plan.required_stage_count:
                parser.error("source mastery stage is outside the frozen plan")
            level = source_plan.stages[source_stage - 1].capability_level
            if args.level is not None and args.level != level:
                parser.error(
                    f"source stage {source_stage} maps to capability level {level}, not level {args.level}"
                )
        else:
            level = args.level or 1
        seed = args.seed or "smoke"
        selected = _select_or_exit(
            bank,
            curriculum_id=curriculum_id,
            level=level,
            seed=seed,
            curriculum_path=args.curriculum,
            count=args.smoke_count,
        )
        canonical = False
        run_id = None
    else:
        if source_plan is not None:
            source_stage, level, seed, run_id = _source_stage_selection(
                parser=parser,
                ledger=ledger,
                plan=source_plan,
                active=active,
                requested_stage=args.stage,
                requested_level=args.level,
                requested_seed=args.seed,
            )
        elif active is not None:
            expected_level = int(active["highest_level_passed"]) + 1
            level = args.level or expected_level
            if level != expected_level:
                parser.error(f"active run expects level {expected_level}, not level {level}")
            active_seed = str(active["run_seed"])
            if args.seed is not None and str(args.seed) != active_seed:
                parser.error("--seed does not match the active Pyramid run")
            seed = active_seed
            run_id = str(active["run_id"])
        else:
            level = args.level or 1
            if level != 1:
                parser.error("a new Pyramid run must begin at level 1")
            seed = args.seed or secrets.token_hex(8)
            run_id = None
        selected = _select_or_exit(
            bank,
            curriculum_id=curriculum_id,
            level=level,
            seed=seed,
            curriculum_path=args.curriculum,
        )
        canonical = True

    try:
        learned_path, learned = _load_learned_memory(
            supplied_path=args.learned_concepts,
            disabled=args.without_learned_concepts,
            curriculum_id=curriculum_id,
            level=level,
        )
    except PyramidLearnedConceptError as exc:
        parser.error(str(exc))

    print(f"CURRICULUM {curriculum_id}")
    if source_plan is not None:
        assert source_stage is not None
        stage_spec = source_plan.stages[source_stage - 1]
        print(f"SOURCE_MASTERY_PLAN {source_plan_path}")
        print(f"SOURCE_PLAN_HASH {source_plan.plan_hash}")
        print(f"SOURCE_STAGE {source_stage}/{source_plan.required_stage_count}")
        print(f"SOURCE_CAPABILITY {stage_spec.capability_level}")
        print(f"SOURCE_CAPABILITY_NAME {json.dumps(stage_spec.capability_name)}")
        print("SOURCE_CHAPTERS " + ",".join(str(value) for value in stage_spec.source_chapters))
    print(f"LEVEL {level}")
    print(f"SEED {seed}")
    print(f"QUESTIONS {len(selected)}")
    print(f"INTEGRITY {sum(item.integrity_question for item in selected)}")
    print(f"BOSS {sum(item.boss_question for item in selected)}")
    print(f"PYRAMID_LEARNED_MEMORY {str(bool(learned)).lower()}")
    print(f"LEARNED_CONCEPTS {len(learned)}")
    if learned_path is not None:
        print(f"LEARNED_CONCEPTS_STORE {learned_path}")

    if args.dry_run:
        if source_plan is not None and active is not None:
            completed = ledger.preview_source_mastery_completed_stages(str(active["run_id"]), source_plan)
            print(f"SOURCE_COMPLETED_STAGES {completed}")
            print("SOURCE_PLAN_BOUND false")
        print("DRY_RUN VALID")
        return

    if canonical and run_id is None:
        run_id = ledger.start_run(curriculum_id, seed)
        print(f"RUN_ID {run_id}")
    elif canonical:
        print(f"RESUME_RUN_ID {run_id}")

    if canonical and source_plan is not None:
        assert run_id is not None
        assert source_stage is not None
        binding = ledger.bind_source_mastery_plan(run_id, source_plan)
        expected_completed = source_stage - 1
        if int(binding["completed_stage_count"]) != expected_completed:
            raise SystemExit(
                "source mastery binding changed the expected stage; refusing to run against inconsistent progress"
            )
        print("SOURCE_PLAN_BOUND true")
        print(f"SOURCE_COMPLETED_STAGES {binding['completed_stage_count']}")

    model = create_pyramid_runtime_model()
    answer_model = _build_answer_model(model, learned)
    checkpoint_dir = _checkpoint_run_dir(
        args.checkpoint_dir,
        curriculum_id=curriculum_id,
        seed=str(seed),
        question_count=len(selected),
    )
    outcome = run_exam(
        exercises=selected,
        answer_model=answer_model,
        grader_model=model,
        batch_size=args.batch_size,
        checkpoint_dir=checkpoint_dir,
        progress=_progress,
        canonical_exam=canonical,
    )

    result = outcome.level_result
    print("\n--- PYRAMID LEVEL RESULT ---")
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    print("FAILURE_MODES", json.dumps(outcome.failure_counts, sort_keys=True))

    if canonical:
        assert run_id is not None
        if source_plan is not None:
            assert source_stage is not None
            source_state = ledger.record_source_stage_result(
                run_id,
                source_plan,
                source_stage,
                result,
            )
        else:
            source_state = None
            ledger.record_level_result(run_id, result)
        ledger.record_failures(run_id, level, outcome.failure_counts)
        print(f"LEDGER_RECORDED {args.db}")

        if source_plan is not None:
            if result.passed and source_stage < source_plan.required_stage_count:
                next_stage = source_plan.stages[source_stage]
                print(f"SOURCE_STAGE_PASSED {source_stage}")
                print(f"SOURCE_COMPLETED_STAGES {source_state['completed_stage_count']}")
                print(f"NEXT_SOURCE_STAGE {next_stage.stage}")
                print(f"NEXT_CAPABILITY {next_stage.capability_level}")
                print(f"NEXT_CAPABILITY_NAME {json.dumps(next_stage.capability_name)}")
            elif result.passed and source_plan.source_capstone_required:
                print("SOURCE_STAGES_COMPLETE")
                print("SOURCE_CAPSTONE_REQUIRED true")
                print("NEXT_GATE source_capstone")
            elif result.passed:
                print("SOURCE_MASTERED")
            else:
                print("SOURCE_MASTERY_RUN_FAILED — next attempt starts at source stage 1 with a new seed")
        elif result.passed and level < 20:
            print(f"UNLOCKED_LEVEL {level + 1}")
        elif result.passed:
            print("PYRAMID_MASTERED")
        else:
            print("PYRAMID_RUN_FAILED — next attempt starts at Level 1 with a new seed")
    else:
        print("SMOKE_RUN_NOT_RECORDED")


if __name__ == "__main__":
    main()
