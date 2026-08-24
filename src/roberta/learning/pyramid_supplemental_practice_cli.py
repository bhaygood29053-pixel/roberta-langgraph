from __future__ import annotations

import argparse
import json
from pathlib import Path

from roberta.models import create_runtime_model

from .pyramid_answer_recovery import MissingAnswerRetryModel
from .pyramid_grounded_practice import (
    GROUNDED_PRACTICE_CHECKPOINT_NAMESPACE,
    grounded_practice_binding,
    grounded_practice_checkpoint_dir,
    load_grounded_practice_contexts,
    run_grounded_targeted_practice,
)
from .pyramid_supplemental_practice import (
    SUPPLEMENTAL_PRACTICE_CONTRACT,
    SUPPLEMENTAL_PRACTICE_VERSION,
    prepare_supplemental_targeted_practice,
    supplemental_manifest,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run source-grounded supplemental Pyramid practice when the canonical remediation "
            "question pool is exhausted. Supplemental questions remain outside the canonical "
            "curriculum and never mutate the canonical Pyramid ledger."
        )
    )
    parser.add_argument("--curriculum", required=True)
    parser.add_argument(
        "--checkpoints",
        required=True,
        help="Current failed targeted-practice checkpoint directory used to identify active weaknesses",
    )
    parser.add_argument(
        "--inherit-remediation-plan",
        action="append",
        default=[],
        help="Prior remediation plan whose critical-origin status must be inherited; may be repeated",
    )
    parser.add_argument(
        "--reconstructions",
        required=True,
        help="Validated source_grounded_reconstructions.jsonl used as remediation evidence",
    )
    parser.add_argument(
        "--exclude-checkpoints",
        action="append",
        default=[],
        help="Prior supplemental checkpoint directory whose synthetic ids must remain fresh; may be repeated",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--questions-per-weakness", type=int, default=5)
    parser.add_argument("--seed", default="supplemental-r3")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _progress(done: int, total: int) -> None:
    percent = (done / total) * 100
    print(f"PROGRESS {done}/{total} ({percent:.1f}%)", flush=True)


def _write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def main() -> int:
    args = _parser().parse_args()
    if args.questions_per_weakness <= 0:
        raise SystemExit("--questions-per-weakness must be positive")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    try:
        preparation = prepare_supplemental_targeted_practice(
            curriculum_dir=args.curriculum,
            checkpoint_dir=args.checkpoints,
            reconstructions_path=args.reconstructions,
            inherited_remediation_plan_paths=args.inherit_remediation_plan,
            exclude_checkpoint_dirs=args.exclude_checkpoints,
            questions_per_weakness=args.questions_per_weakness,
            seed=args.seed,
        )
        prepared = preparation.prepared
        contexts = load_grounded_practice_contexts(
            curriculum_dir=args.curriculum,
            reconstructions_path=args.reconstructions,
            prepared=prepared,
        )
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc

    output = Path(args.output)
    checkpoint_binding = grounded_practice_binding(prepared, contexts)
    checkpoint_dir = grounded_practice_checkpoint_dir(output, prepared, contexts)
    manifest_payload = supplemental_manifest(preparation, checkpoint_binding=checkpoint_binding)

    print(f"CONTRACT {SUPPLEMENTAL_PRACTICE_CONTRACT}")
    print(f"VERSION {SUPPLEMENTAL_PRACTICE_VERSION}")
    print(f"CURRICULUM {prepared.curriculum_id}")
    print(f"LEVEL {prepared.level}")
    print(f"CURRENT_WEAK_ITEMS {len(preparation.current_weak_ids)}")
    print(f"ACTIVE_WEAKNESSES {len(preparation.current_weakness_keys)}")
    print(f"SUPPLEMENTAL_QUESTIONS {len(prepared.exercises)}")
    print(f"SOURCE_GROUNDED_WEAK_ITEMS {prepared.source_grounded_weak_items}")
    print(f"GROUNDED_CONTEXT_GROUPS {len(contexts)}")
    print(f"CRITICAL_WEAKNESS_GROUPS {len(prepared.critical_weakness_keys)}")
    print(f"SUPPLEMENTAL_BANK_SHA256 {preparation.selected_bank_sha256}")
    print(f"CANONICAL_BANK_OVERLAP {str(preparation.canonical_bank_overlap).lower()}")
    print(f"CHECKPOINT_NAMESPACE {GROUNDED_PRACTICE_CHECKPOINT_NAMESPACE}")
    print(f"CHECKPOINT_BINDING {checkpoint_binding}")
    print(f"CHECKPOINTS {checkpoint_dir}")

    print("\n--- ACTIVE WEAKNESSES ---")
    for concept, subconcept in preparation.current_weakness_keys:
        critical = (concept, subconcept) in prepared.critical_weakness_keys
        print(f"{concept}/{subconcept or '-'} critical_origin={str(critical).lower()}")

    if args.dry_run:
        print("\nDRY_RUN VALID")
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

    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"supplemental practice output already exists and is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    _write_manifest(output / "supplemental_manifest.json", manifest_payload)

    model = create_runtime_model()
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

    print("\n--- SUPPLEMENTAL TARGETED PRACTICE RESULT ---")
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
    print(f"MANIFEST {output / 'supplemental_manifest.json'}")
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
