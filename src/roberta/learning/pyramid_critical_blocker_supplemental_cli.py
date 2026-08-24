from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .curriculum_io import validate_package
from .pyramid_adjudicator_retry import create_pyramid_runtime_model
from .pyramid_answer_recovery import MissingAnswerRetryModel
from .pyramid_critical_blocker_supplemental import (
    CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT,
    CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION,
    build_critical_checkpoint_view,
    mb4e_immutability_critical_blocker_bank,
    validate_critical_blocker_gate,
)
from .pyramid_critical_retention import (
    CRITICAL_GROUNDED_PASS_NEXT_GATE,
    demote_grounded_canonical_authority,
)
from .pyramid_grounded_practice import (
    GROUNDED_PRACTICE_CHECKPOINT_NAMESPACE,
    grounded_practice_binding,
    grounded_practice_checkpoint_dir,
    load_grounded_practice_contexts,
    run_grounded_targeted_practice,
)
from .pyramid_supplemental_practice import (
    prepare_supplemental_targeted_practice,
    supplemental_manifest,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run source-grounded fresh supplemental verification for validated critical blockers "
            "after canonical accuracy/integrity/Boss gates have already been met."
        )
    )
    parser.add_argument("--curriculum", required=True)
    parser.add_argument("--checkpoints", required=True, help="Current V3 critical-revalidated checkpoint directory")
    parser.add_argument("--critical-revalidation-report", required=True, help="V3 critical_revalidation_report.json")
    parser.add_argument("--ledger", required=True, help="Read-only Pyramid training ledger")
    parser.add_argument("--reconstructions", required=True, help="Source-grounded reconstructions for current critical blockers")
    parser.add_argument(
        "--inherit-remediation-plan",
        action="append",
        default=[],
        help="Prior remediation plan whose critical-origin status must be inherited; may be repeated",
    )
    parser.add_argument(
        "--exclude-checkpoints",
        action="append",
        default=[],
        help="Prior supplemental checkpoint directory whose synthetic ids must remain fresh; may be repeated",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--questions-per-weakness", type=int, default=10)
    parser.add_argument("--seed", default="critical-blocker-supplemental-r1")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _progress(done: int, total: int) -> None:
    percent = (done / total) * 100
    print(f"PROGRESS {done}/{total} ({percent:.1f}%)", flush=True)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def main() -> int:
    args = _parser().parse_args()
    if args.questions_per_weakness < 10:
        raise SystemExit("critical-blocker verification requires --questions-per-weakness >= 10")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    try:
        manifest, _ = validate_package(args.curriculum)
        curriculum_id = str(manifest["curriculum_id"])
        gate_evidence = validate_critical_blocker_gate(
            revalidation_report_path=args.critical_revalidation_report,
            ledger_path=args.ledger,
            curriculum_id=curriculum_id,
            level=1,
        )
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc

    output = Path(args.output)
    if not args.dry_run and output.exists() and any(output.iterdir()):
        raise SystemExit(f"critical-blocker supplemental output already exists and is not empty: {output}")

    with TemporaryDirectory(prefix="roberta-critical-blocker-view-") as temp_root:
        critical_view = Path(temp_root) / "critical_checkpoints"
        try:
            critical_manifest = build_critical_checkpoint_view(
                source_dir=args.checkpoints,
                output_dir=critical_view,
            )
            if critical_manifest.get("critical_exercise_ids") != gate_evidence.get("critical_ids"):
                raise RuntimeError(
                    "critical revalidation report critical ids do not match current V3 checkpoint blockers"
                )
            preparation = prepare_supplemental_targeted_practice(
                curriculum_dir=args.curriculum,
                checkpoint_dir=critical_view,
                reconstructions_path=args.reconstructions,
                inherited_remediation_plan_paths=args.inherit_remediation_plan,
                exclude_checkpoint_dirs=args.exclude_checkpoints,
                questions_per_weakness=args.questions_per_weakness,
                seed=args.seed,
                supplemental_bank=mb4e_immutability_critical_blocker_bank(curriculum_id),
            )
            prepared = preparation.prepared
            contexts = load_grounded_practice_contexts(
                curriculum_dir=args.curriculum,
                reconstructions_path=args.reconstructions,
                prepared=prepared,
            )
        except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
            raise SystemExit(str(exc)) from exc

    if preparation.current_weakness_keys != (("benefits", "immutability"),):
        raise SystemExit(
            "critical-blocker supplemental bank currently supports only benefits/immutability; "
            f"found {preparation.current_weakness_keys}"
        )
    if len(prepared.critical_weakness_keys) != 1 or ("benefits", "immutability") not in prepared.critical_weakness_keys:
        raise SystemExit("benefits/immutability must remain a critical-origin weakness")

    checkpoint_binding = grounded_practice_binding(prepared, contexts)
    checkpoint_dir = grounded_practice_checkpoint_dir(output, prepared, contexts)
    manifest_payload = supplemental_manifest(preparation, checkpoint_binding=checkpoint_binding)
    manifest_payload.update(
        {
            "critical_blocker_contract": CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT,
            "critical_blocker_version": CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION,
            "critical_blocker_mode": True,
            "critical_blocker_gate": gate_evidence,
            "critical_checkpoint_source": critical_manifest,
            "minimum_questions_per_weakness": 10,
            "canonical_attempt_authorized_before_practice": False,
            "canonical_attempt_authorized_after_grounded_practice": False,
            "grounded_success_next_gate": CRITICAL_GROUNDED_PASS_NEXT_GATE,
        }
    )

    print(f"CONTRACT {CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT}")
    print(f"VERSION {CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION}")
    print(f"CURRICULUM {prepared.curriculum_id}")
    print(f"LEVEL {prepared.level}")
    print("CRITICAL_BLOCKER_GATE_VERIFIED true")
    print(f"GATE_REVALIDATED_ACCURACY {float(gate_evidence['revalidated_accuracy']):.4f}")
    print(f"GATE_INTEGRITY_ACCURACY {float(gate_evidence['integrity_accuracy']):.4f}")
    print(f"GATE_BOSS_PASSED {str(gate_evidence['boss_passed']).lower()}")
    print(f"GATE_VALIDATED_CRITICAL_FAILURES {gate_evidence['validated_critical_failures']}")
    print(f"CURRENT_CRITICAL_ITEMS {len(preparation.current_weak_ids)}")
    print(f"ACTIVE_CRITICAL_WEAKNESSES {len(preparation.current_weakness_keys)}")
    print(f"SUPPLEMENTAL_QUESTIONS {len(prepared.exercises)}")
    print(f"SOURCE_GROUNDED_WEAK_ITEMS {prepared.source_grounded_weak_items}")
    print(f"GROUNDED_CONTEXT_GROUPS {len(contexts)}")
    print(f"SUPPLEMENTAL_BANK_SHA256 {preparation.selected_bank_sha256}")
    print(f"CANONICAL_BANK_OVERLAP {str(preparation.canonical_bank_overlap).lower()}")
    print(f"CHECKPOINT_NAMESPACE {GROUNDED_PRACTICE_CHECKPOINT_NAMESPACE}")
    print(f"CHECKPOINT_BINDING {checkpoint_binding}")
    print(f"CHECKPOINTS {checkpoint_dir}")
    print("CRITICAL_BLOCKER_MODE true")

    if args.dry_run:
        print("DRY_RUN VALID")
        print("SUPPLEMENTAL_NONCANONICAL true")
        print("GROUNDED_REMEDIATION_CONTEXT true")
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
    _write_json(output / "critical_blocker_supplemental_manifest.json", manifest_payload)

    model = create_pyramid_runtime_model()
    answer_model = MissingAnswerRetryModel(model, recover_unexpected_initial_ids=True)
    report = run_grounded_targeted_practice(
        prepared=prepared,
        contexts=contexts,
        answer_model=answer_model,
        grader_model=model,
        output_dir=output,
        batch_size=args.batch_size,
        progress=_progress,
    )
    report = demote_grounded_canonical_authority(report)
    _write_json(output / "practice_report.json", report.to_mapping())

    print("\n--- CRITICAL BLOCKER SUPPLEMENTAL RESULT ---")
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
    print(f"MANIFEST {output / 'critical_blocker_supplemental_manifest.json'}")
    print(f"CHECKPOINTS {checkpoint_dir}")
    print(f"NEXT_GATE {report.next_gate}")
    print(f"CANONICAL_ATTEMPT_AUTHORIZED {str(report.canonical_attempt_authorized).lower()}")
    print("SUPPLEMENTAL_NONCANONICAL true")
    print("GROUNDED_REMEDIATION_CONTEXT true")
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
