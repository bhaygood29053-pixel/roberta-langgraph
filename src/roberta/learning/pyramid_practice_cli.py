from __future__ import annotations

import argparse
from pathlib import Path

from roberta.models import create_runtime_model

from .pyramid_answer_recovery import MissingAnswerRetryModel
from .pyramid_practice import prepare_targeted_practice, run_targeted_practice


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run fresh targeted Pyramid practice only after source-grounded remediation, "
            "without mutating the canonical Pyramid training ledger."
        )
    )
    parser.add_argument("--curriculum", required=True, help="Validated Pyramid curriculum package directory")
    parser.add_argument("--practice", required=True, help="Remediation practice_questions.jsonl")
    parser.add_argument("--remediation-plan", required=True, help="Remediation plan JSON that selected the practice set")
    parser.add_argument(
        "--reconstructions",
        required=True,
        help="source_grounded_reconstructions.jsonl covering every original weak item",
    )
    parser.add_argument("--output", required=True, help="Separate targeted-practice output directory")
    parser.add_argument("--batch-size", type=int, default=10, help="Questions per model batch (default: 10)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate curriculum/practice/remediation/reconstruction bindings without model calls",
    )
    return parser


def _progress(done: int, total: int) -> None:
    percent = (done / total) * 100
    print(f"PROGRESS {done}/{total} ({percent:.1f}%)", flush=True)


def main() -> int:
    args = _parser().parse_args()
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    prepared = prepare_targeted_practice(
        curriculum_dir=args.curriculum,
        practice_path=args.practice,
        remediation_plan_path=args.remediation_plan,
        reconstructions_path=args.reconstructions,
    )
    print(f"CURRICULUM {prepared.curriculum_id}")
    print(f"LEVEL {prepared.level}")
    print(f"PRACTICE_QUESTIONS {len(prepared.exercises)}")
    print(f"ORIGINAL_WEAK_ITEMS {len(prepared.original_weak_ids)}")
    print(f"SOURCE_GROUNDED_WEAK_ITEMS {prepared.source_grounded_weak_items}")
    print(f"CRITICAL_WEAKNESS_GROUPS {len(prepared.critical_weakness_keys)}")

    if args.dry_run:
        print("DRY_RUN VALID")
        print("LEDGER_MUTATION_AUTHORIZED false")
        print("RETENTION_AUTHORIZED false")
        print("EXECUTION_AUTHORIZED false")
        return 0

    model = create_runtime_model()
    answer_model = MissingAnswerRetryModel(
        model,
        recover_unexpected_initial_ids=True,
    )
    report = run_targeted_practice(
        prepared=prepared,
        answer_model=answer_model,
        grader_model=model,
        output_dir=args.output,
        batch_size=args.batch_size,
        progress=_progress,
    )
    output = Path(args.output)
    print("\n--- TARGETED PYRAMID PRACTICE RESULT ---")
    print(f"PASS {report.pass_count}")
    print(f"PARTIAL {report.partial_count}")
    print(f"FAIL {report.fail_count}")
    print(f"ACCURACY {report.accuracy:.4f}")
    print(f"REQUIRED_ACCURACY {report.required_accuracy:.4f}")
    print(f"CRITICAL_FAILURES {report.critical_failures}")
    print(f"ALL_WEAKNESSES_PASSED {str(report.all_weaknesses_passed).lower()}")
    print(f"CRITICAL_WEAKNESSES_PASSED {str(report.critical_weaknesses_passed).lower()}")
    print(f"PRACTICE_PASSED {str(report.practice_passed).lower()}")
    print(f"RESULTS {output / 'practice_results.jsonl'}")
    print(f"REPORT {output / 'practice_report.json'}")
    print(f"NEXT_GATE {report.next_gate}")
    print(f"CANONICAL_ATTEMPT_AUTHORIZED {str(report.canonical_attempt_authorized).lower()}")
    print("LEDGER_MUTATION_AUTHORIZED false")
    print("PHASE8_CANDIDATE_CREATION_AUTHORIZED false")
    print("SOURCE_TRUTH_AUTHORIZED false")
    print("LIVE_STATE_AUTHORIZED false")
    print("MEMORY_PROMOTION_AUTHORIZED false")
    print("RETENTION_AUTHORIZED false")
    print("GOVERNANCE_MUTATION_AUTHORIZED false")
    print("EXECUTION_AUTHORIZED false")

    print("\n--- WEAKNESS VERIFICATION ---")
    for item in report.weakness_results:
        label = f"{item.concept}/{item.subconcept or '-'}"
        print(
            f"{label} total={item.total} pass={item.pass_count} partial={item.partial_count} "
            f"fail={item.fail_count} accuracy={item.accuracy:.4f} "
            f"critical_origin={str(item.critical_origin).lower()} passed={str(item.passed).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
