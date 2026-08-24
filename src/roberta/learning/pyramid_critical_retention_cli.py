from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pyramid_adjudicator_retry import create_pyramid_runtime_model
from .pyramid_answer_recovery import MissingAnswerRetryModel
from .pyramid_critical_blocker_supplemental import validate_critical_blocker_gate
from .pyramid_critical_retention import (
    CRITICAL_RETENTION_CHECKPOINT_NAMESPACE,
    CRITICAL_RETENTION_CONTRACT,
    CRITICAL_RETENTION_VERSION,
    critical_retention_binding,
    prepare_closed_book_critical_retention,
    validate_grounded_critical_prerequisite,
)
from .pyramid_exam import run_exam
from .pyramid_practice import evaluate_targeted_practice, write_targeted_practice_bundle


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run fresh closed-book retention verification for a validated critical blocker "
            "after perfect source-grounded critical practice."
        )
    )
    parser.add_argument("--curriculum", required=True)
    parser.add_argument("--critical-revalidation-report", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--grounded-report", required=True, help="Perfect grounded critical-blocker practice_report.json")
    parser.add_argument("--grounded-manifest", required=True, help="Grounded critical_blocker_supplemental_manifest.json")
    parser.add_argument(
        "--exclude-checkpoints",
        action="append",
        default=[],
        help="Prior checkpoint directory whose exercise ids must remain fresh; may be repeated",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--questions-per-weakness", type=int, default=10)
    parser.add_argument("--seed", default="critical-retention-r1")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _progress(done: int, total: int) -> None:
    percent = (done / total) * 100
    print(f"PROGRESS {done}/{total} ({percent:.1f}%)", flush=True)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    args = _parser().parse_args()
    if args.questions_per_weakness < 10:
        raise SystemExit("closed-book critical retention requires --questions-per-weakness >= 10")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    try:
        from .curriculum_io import validate_package

        manifest, _ = validate_package(args.curriculum)
        curriculum_id = str(manifest["curriculum_id"])
        gate_evidence = validate_critical_blocker_gate(
            revalidation_report_path=args.critical_revalidation_report,
            ledger_path=args.ledger,
            curriculum_id=curriculum_id,
            level=1,
        )
        prerequisite = validate_grounded_critical_prerequisite(
            grounded_report_path=args.grounded_report,
            grounded_manifest_path=args.grounded_manifest,
            curriculum_id=curriculum_id,
            gate_evidence=gate_evidence,
        )
        prepared, bank_hash = prepare_closed_book_critical_retention(
            curriculum_dir=args.curriculum,
            gate_evidence=gate_evidence,
            exclude_checkpoint_dirs=args.exclude_checkpoints,
            questions_per_weakness=args.questions_per_weakness,
            seed=args.seed,
        )
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    output = Path(args.output)
    if not args.dry_run and output.exists() and any(output.iterdir()):
        raise SystemExit(f"closed-book critical retention output already exists and is not empty: {output}")

    binding = critical_retention_binding(prepared, prerequisite)
    checkpoint_dir = output / CRITICAL_RETENTION_CHECKPOINT_NAMESPACE / binding
    retention_manifest = {
        "contract": CRITICAL_RETENTION_CONTRACT,
        "version": CRITICAL_RETENTION_VERSION,
        "curriculum_id": prepared.curriculum_id,
        "level": prepared.level,
        "critical_gate": gate_evidence,
        "grounded_prerequisite": prerequisite,
        "question_count": len(prepared.exercises),
        "exercise_ids": [item.exercise_id for item in prepared.exercises],
        "retention_bank_sha256": bank_hash,
        "checkpoint_binding": binding,
        "closed_book": True,
        "source_context_injected": False,
        "canonical_exam": False,
        "canonical_attempt_authorized_before_retention": False,
        "ledger_mutation_authorized": False,
        "phase8_candidate_creation_authorized": False,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "retention_authorized": False,
        "governance_mutation_authorized": False,
        "execution_authorized": False,
    }

    print(f"CONTRACT {CRITICAL_RETENTION_CONTRACT}")
    print(f"VERSION {CRITICAL_RETENTION_VERSION}")
    print(f"CURRICULUM {prepared.curriculum_id}")
    print(f"LEVEL {prepared.level}")
    print("CRITICAL_BLOCKER_GATE_VERIFIED true")
    print(f"GATE_REVALIDATED_ACCURACY {float(gate_evidence['revalidated_accuracy']):.4f}")
    print(f"GATE_INTEGRITY_ACCURACY {float(gate_evidence['integrity_accuracy']):.4f}")
    print(f"GATE_BOSS_PASSED {str(gate_evidence['boss_passed']).lower()}")
    print(f"GATE_VALIDATED_CRITICAL_FAILURES {gate_evidence['validated_critical_failures']}")
    print("GROUNDED_PREREQUISITE_VERIFIED true")
    print(f"GROUNDED_QUESTIONS {prerequisite['question_count']}")
    print(f"LEGACY_PREMATURE_AUTHORIZATION_IGNORED {str(prerequisite['legacy_premature_authorization_ignored']).lower()}")
    print(f"RETENTION_QUESTIONS {len(prepared.exercises)}")
    print(f"RETENTION_BANK_SHA256 {bank_hash}")
    print("CLOSED_BOOK true")
    print("SOURCE_CONTEXT_INJECTED false")
    print(f"CHECKPOINT_NAMESPACE {CRITICAL_RETENTION_CHECKPOINT_NAMESPACE}")
    print(f"CHECKPOINT_BINDING {binding}")
    print(f"CHECKPOINTS {checkpoint_dir}")

    if args.dry_run:
        print("DRY_RUN VALID")
        print("CANONICAL_EXAM false")
        print("CANONICAL_ATTEMPT_AUTHORIZED false")
        print("LEDGER_MUTATION_AUTHORIZED false")
        print("PHASE8_CANDIDATE_CREATION_AUTHORIZED false")
        print("SOURCE_TRUTH_AUTHORIZED false")
        print("LIVE_STATE_AUTHORIZED false")
        print("MEMORY_PROMOTION_AUTHORIZED false")
        print("RETENTION_AUTHORIZED false")
        print("GOVERNANCE_MUTATION_AUTHORIZED false")
        print("EXECUTION_AUTHORIZED false")
        return 0

    output.mkdir(parents=True, exist_ok=True)
    _write_json(output / "critical_retention_manifest.json", retention_manifest)

    model = create_pyramid_runtime_model()
    answer_model = MissingAnswerRetryModel(model, recover_unexpected_initial_ids=True)
    outcome = run_exam(
        exercises=prepared.exercises,
        answer_model=answer_model,
        grader_model=model,
        batch_size=args.batch_size,
        checkpoint_dir=checkpoint_dir,
        progress=_progress,
        canonical_exam=False,
    )
    report = evaluate_targeted_practice(prepared, outcome.graded_answers)
    write_targeted_practice_bundle(output, prepared, outcome.graded_answers, report)

    print("\n--- CLOSED-BOOK CRITICAL RETENTION RESULT ---")
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
    print(f"MANIFEST {output / 'critical_retention_manifest.json'}")
    print(f"CHECKPOINTS {checkpoint_dir}")
    print(f"NEXT_GATE {report.next_gate}")
    print(f"CANONICAL_ATTEMPT_AUTHORIZED {str(report.canonical_attempt_authorized).lower()}")
    print("CLOSED_BOOK true")
    print("SOURCE_CONTEXT_INJECTED false")
    print("LEDGER_MUTATION_AUTHORIZED false")
    print("PHASE8_CANDIDATE_CREATION_AUTHORIZED false")
    print("SOURCE_TRUTH_AUTHORIZED false")
    print("LIVE_STATE_AUTHORIZED false")
    print("MEMORY_PROMOTION_AUTHORIZED false")
    print("RETENTION_AUTHORIZED false")
    print("GOVERNANCE_MUTATION_AUTHORIZED false")
    print("EXECUTION_AUTHORIZED false")

    for item in report.weakness_results:
        print(
            f"{item.concept}/{item.subconcept or '-'} total={item.total} pass={item.pass_count} "
            f"partial={item.partial_count} fail={item.fail_count} accuracy={item.accuracy:.4f} "
            f"critical_origin={str(item.critical_origin).lower()} passed={str(item.passed).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
