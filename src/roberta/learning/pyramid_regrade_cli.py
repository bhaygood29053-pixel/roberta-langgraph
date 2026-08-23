from __future__ import annotations

import argparse
import json

from roberta.models import create_runtime_model

from .curriculum_io import validate_package
from .pyramid import CANONICAL_LEVEL_QUESTION_COUNT
from .pyramid_regrade import regrade_checkpoints


def _progress(done: int, total: int) -> None:
    percent = (done / total) * 100
    print(f"REGRADE_PROGRESS {done}/{total} ({percent:.1f}%)", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Regrade historical Pyramid checkpoints under current grading semantics "
            "without asking Roberta to answer the exercises again."
        )
    )
    parser.add_argument("--curriculum", required=True, help="Curriculum package directory")
    parser.add_argument("--level", type=int, default=1, help="Pyramid level to regrade (default: 1)")
    parser.add_argument("--seed", required=True, help="Original Pyramid run seed")
    parser.add_argument("--batch-size", type=int, default=10, help="Historical questions per checkpoint batch")
    parser.add_argument(
        "--input-checkpoints",
        required=True,
        help="Historical seed checkpoint directory containing v1 grading state",
    )
    parser.add_argument(
        "--output-checkpoints",
        required=True,
        help="New, separate directory for v2 regraded checkpoints",
    )
    args = parser.parse_args()

    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")

    manifest, bank = validate_package(args.curriculum)
    curriculum_id = str(manifest["curriculum_id"])

    print(f"CURRICULUM {curriculum_id}")
    print(f"LEVEL {args.level}")
    print(f"SEED {args.seed}")
    print(f"QUESTIONS {CANONICAL_LEVEL_QUESTION_COUNT}")
    print(f"INPUT_CHECKPOINTS {args.input_checkpoints}")
    print(f"OUTPUT_CHECKPOINTS {args.output_checkpoints}")

    grader_model = create_runtime_model()
    report = regrade_checkpoints(
        exercise_bank=bank,
        grader_model=grader_model,
        input_dir=args.input_checkpoints,
        output_dir=args.output_checkpoints,
        curriculum_id=curriculum_id,
        level=args.level,
        run_seed=args.seed,
        batch_size=args.batch_size,
        canonical_exam=True,
        progress=_progress,
    )
    payload = report.to_mapping()

    print("\n--- PYRAMID REGRADE RESULT ---")
    print("OLD_GRADE_COUNTS", json.dumps(payload["old_grade_counts"], sort_keys=True))
    print("NEW_GRADE_COUNTS", json.dumps(payload["new_grade_counts"], sort_keys=True))
    print(f"OLD_WEAKNESSES {report.old_weakness_count}")
    print(f"NEW_WEAKNESSES {report.new_weakness_count}")
    print(f"OLD_ACCURACY {report.old_accuracy:.6f}")
    print(f"NEW_ACCURACY {report.new_accuracy:.6f}")
    print(f"OLD_CRITICAL_FAILURES {report.old_critical_failures}")
    print(f"NEW_CRITICAL_FAILURES {report.new_critical_failures}")
    print("GRADE_TRANSITIONS", json.dumps(payload["grade_transitions"], sort_keys=True))
    print("OLD_FAILURE_MODES", json.dumps(payload["old_failure_counts"], sort_keys=True))
    print("NEW_FAILURE_MODES", json.dumps(payload["new_failure_counts"], sort_keys=True))
    print(f"OLD_PASSED {str(report.old_passed).lower()}")
    print(f"NEW_PASSED {str(report.new_passed).lower()}")
    print("ANSWER_MODEL_INVOKED false")
    print("LEDGER_MUTATED false")
    print("RETENTION_AUTHORIZED false")
    print(f"REPORT {args.output_checkpoints}/regrade_report.json")


if __name__ == "__main__":
    main()
