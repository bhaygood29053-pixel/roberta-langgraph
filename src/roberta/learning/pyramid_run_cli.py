from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import secrets

from roberta.models import create_runtime_model

from .curriculum_io import validate_package
from .pyramid import CANONICAL_LEVEL_QUESTION_COUNT, select_level_exercises
from .pyramid_exam import run_exam
from .training_ledger import PyramidTrainingLedger


def _active_run(ledger: PyramidTrainingLedger, curriculum_id: str) -> dict[str, object] | None:
    for run in ledger.run_history(curriculum_id):
        if run["status"] == "active":
            return run
    return None


def _progress(done: int, total: int) -> None:
    percent = (done / total) * 100
    print(f"PROGRESS {done}/{total} ({percent:.1f}%)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a scored Roberta Pyramid level against a validated curriculum package."
    )
    parser.add_argument("--curriculum", required=True, help="Curriculum package directory")
    parser.add_argument(
        "--db",
        default=".roberta/pyramid_training.sqlite3",
        help="Pyramid SQLite training ledger",
    )
    parser.add_argument("--level", type=int, help="Level to run; defaults to the active run's next level or 1")
    parser.add_argument("--seed", help="Run seed. A new random seed is generated for a new run when omitted.")
    parser.add_argument("--batch-size", type=int, default=10, help="Questions per model batch (default: 10)")
    parser.add_argument(
        "--checkpoint-dir",
        default=".roberta/pyramid_checkpoints",
        help="Root directory for restart-safe batch checkpoints",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and select the exam without making model calls or writing a run",
    )
    parser.add_argument(
        "--smoke-count",
        type=int,
        help="Run a non-canonical sample for model/evaluator testing; results are not written to the ledger",
    )
    args = parser.parse_args()

    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.smoke_count is not None and not 1 <= args.smoke_count < CANONICAL_LEVEL_QUESTION_COUNT:
        parser.error(f"--smoke-count must be between 1 and {CANONICAL_LEVEL_QUESTION_COUNT - 1}")

    manifest, bank = validate_package(args.curriculum)
    curriculum_id = str(manifest["curriculum_id"])
    ledger = PyramidTrainingLedger(args.db)
    active = _active_run(ledger, curriculum_id)

    if args.smoke_count is not None:
        level = args.level or 1
        seed = args.seed or "smoke"
        selected = select_level_exercises(
            bank,
            curriculum_id=curriculum_id,
            level=level,
            run_seed=seed,
            count=args.smoke_count,
        )
        canonical = False
        run_id = None
    else:
        if active is not None:
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
        selected = select_level_exercises(
            bank,
            curriculum_id=curriculum_id,
            level=level,
            run_seed=seed,
        )
        canonical = True

    print(f"CURRICULUM {curriculum_id}")
    print(f"LEVEL {level}")
    print(f"SEED {seed}")
    print(f"QUESTIONS {len(selected)}")
    print(f"INTEGRITY {sum(item.integrity_question for item in selected)}")
    print(f"BOSS {sum(item.boss_question for item in selected)}")

    if args.dry_run:
        print("DRY_RUN VALID")
        return

    if canonical and run_id is None:
        run_id = ledger.start_run(curriculum_id, seed)
        print(f"RUN_ID {run_id}")
    elif canonical:
        print(f"RESUME_RUN_ID {run_id}")

    model = create_runtime_model()
    checkpoint_dir = Path(args.checkpoint_dir) / curriculum_id / str(seed)
    outcome = run_exam(
        exercises=selected,
        answer_model=model,
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
        ledger.record_failures(run_id, level, outcome.failure_counts)
        ledger.record_level_result(run_id, result)
        print(f"LEDGER_RECORDED {args.db}")
        if result.passed and level < 20:
            print(f"UNLOCKED_LEVEL {level + 1}")
        elif result.passed:
            print("PYRAMID_MASTERED")
        else:
            print("PYRAMID_RUN_FAILED — next attempt starts at Level 1 with a new seed")
    else:
        print("SMOKE_RUN_NOT_RECORDED")


if __name__ == "__main__":
    main()
