from __future__ import annotations

import argparse
import json

from .curriculum_io import validate_package
from .pyramid import (
    LEGACY_CANONICAL_LEVEL_QUESTION_COUNT,
    SUPPORTED_CANONICAL_LEVEL_QUESTION_COUNTS,
)
from .pyramid_adjudicator_retry import create_pyramid_runtime_model
from .pyramid_critical_revalidation import revalidate_critical_checkpoints


def _progress(done: int, total: int) -> None:
    percent = (done / total) * 100
    print(f"CRITICAL_REVALIDATION_PROGRESS {done}/{total} ({percent:.1f}%)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Revalidate model-proposed critical failures in saved Pyramid v2-semantic checkpoints "
            "without re-answering questions or mutating the original checkpoints/ledger."
        )
    )
    parser.add_argument("--curriculum", required=True, help="Curriculum package directory")
    parser.add_argument("--level", type=int, default=1, help="Pyramid level to revalidate (default: 1)")
    parser.add_argument("--seed", required=True, help="Original Pyramid run seed")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument(
        "--question-count",
        type=int,
        choices=SUPPORTED_CANONICAL_LEVEL_QUESTION_COUNTS,
        default=LEGACY_CANONICAL_LEVEL_QUESTION_COUNT,
        help="Historical canonical question count (default: 1000 for pre-migration checkpoints)",
    )
    parser.add_argument("--input-checkpoints", required=True)
    parser.add_argument("--output-checkpoints", required=True)
    args = parser.parse_args()

    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")

    manifest, bank = validate_package(args.curriculum)
    curriculum_id = str(manifest["curriculum_id"])

    print(f"CURRICULUM {curriculum_id}")
    print(f"LEVEL {args.level}")
    print(f"SEED {args.seed}")
    print(f"QUESTIONS {args.question_count}")
    print(f"INPUT_CHECKPOINTS {args.input_checkpoints}")
    print(f"OUTPUT_CHECKPOINTS {args.output_checkpoints}")

    report = revalidate_critical_checkpoints(
        exercise_bank=bank,
        grader_model=create_pyramid_runtime_model(),
        input_dir=args.input_checkpoints,
        output_dir=args.output_checkpoints,
        curriculum_id=curriculum_id,
        level=args.level,
        run_seed=args.seed,
        batch_size=args.batch_size,
        question_count=args.question_count,
        canonical_exam=True,
        progress=_progress,
    )

    print("\n--- PYRAMID CRITICAL REVALIDATION RESULT ---")
    print(f"INPUT_GRADING_SEMANTICS {report.input_grading_semantics}")
    print(f"OUTPUT_GRADING_SEMANTICS {report.output_grading_semantics}")
    print(f"OLD_ACCURACY {report.old_accuracy:.6f}")
    print(f"NEW_ACCURACY {report.new_accuracy:.6f}")
    print(f"OLD_CRITICAL_FAILURES {report.old_critical_failures}")
    print(f"NEW_CRITICAL_FAILURES {report.new_critical_failures}")
    print("CRITICAL_IDS_BEFORE", json.dumps(report.critical_ids_before))
    print("CRITICAL_IDS_AFTER", json.dumps(report.critical_ids_after))
    print(f"OLD_PASSED {str(report.old_passed).lower()}")
    print(f"NEW_PASSED {str(report.new_passed).lower()}")
    print("ANSWER_MODEL_INVOKED false")
    print("LEDGER_MUTATED false")
    print("ORIGINAL_CHECKPOINTS_MUTATED false")
    print("CANONICAL_ATTEMPT_AUTHORIZED false")
    print("PHASE8_CANDIDATE_CREATION_AUTHORIZED false")
    print("SOURCE_TRUTH_AUTHORIZED false")
    print("LIVE_STATE_AUTHORIZED false")
    print("MEMORY_PROMOTION_AUTHORIZED false")
    print("RETENTION_AUTHORIZED false")
    print("GOVERNANCE_MUTATION_AUTHORIZED false")
    print("EXECUTION_AUTHORIZED false")
    print(f"REPORT {args.output_checkpoints}/critical_revalidation_report.json")


if __name__ == "__main__":
    main()
