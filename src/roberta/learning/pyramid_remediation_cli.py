from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .curriculum_io import validate_package
from .pyramid_critical_blocker_supplemental import validate_critical_blocker_gate
from .pyramid_critical_origin import inherit_critical_origins
from .pyramid_exam import GRADING_SEMANTICS
from .pyramid_learning_handoff import (
    build_pyramid_learning_handoffs,
    write_pyramid_learning_handoffs_jsonl,
)
from .pyramid_remediation import (
    PYRAMID_REMEDIATION_PRACTICE_BINDING_CONTRACT,
    build_remediation_plan,
    load_seen_exercise_ids,
    load_weak_items,
    select_fresh_practice,
    write_practice_jsonl,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a targeted Pyramid remediation plan from checkpoint results.")
    parser.add_argument("--curriculum", default="curricula/mastering_blockchain_4e_2023")
    parser.add_argument("--checkpoints", default=".roberta/pyramid_checkpoints/mastering_blockchain_4e_2023_book01/smoke")
    parser.add_argument(
        "--critical-blockers-only",
        action="store_true",
        help=(
            "Explicitly remediate only validated critical_failure=true items. Requires current "
            "question-first-adjudication/v3 checkpoint semantics plus canonical gate evidence."
        ),
    )
    parser.add_argument(
        "--critical-revalidation-report",
        help="V3 critical_revalidation_report.json proving corrected accuracy and remaining critical ids",
    )
    parser.add_argument(
        "--ledger",
        help="Read-only Pyramid training ledger used to prove integrity and Boss gates",
    )
    parser.add_argument(
        "--exclude-checkpoints",
        action="append",
        default=[],
        help=(
            "Additional checkpoint directory whose exercise ids must be excluded from fresh practice. "
            "May be supplied more than once."
        ),
    )
    parser.add_argument(
        "--inherit-remediation-plan",
        action="append",
        default=[],
        help=(
            "Earlier remediation_plan.json whose critical-origin weakness status must be inherited. "
            "May be supplied more than once; unrelated historical weaknesses are ignored."
        ),
    )
    parser.add_argument("--output", default=".roberta/pyramid_remediation/mastering_blockchain_4e_2023_book01")
    parser.add_argument("--practice-per-weakness", type=int, default=5)
    parser.add_argument("--seed", default="remediation-001")
    return parser


def _load_inherited_plans(
    paths: list[str],
) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    plans: list[dict[str, object]] = []
    records: list[dict[str, str]] = []
    for raw_path in paths:
        path = Path(raw_path)
        try:
            raw_bytes = path.read_bytes()
            raw = json.loads(raw_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Cannot read inherited remediation plan {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise SystemExit(f"Inherited remediation plan must be a JSON object: {path}")
        plans.append(raw)
        records.append(
            {
                "path": str(path),
                "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            }
        )
    return plans, records


def main() -> int:
    args = _parser().parse_args()
    manifest, exercises = validate_package(args.curriculum)
    curriculum_id = str(manifest["curriculum_id"])
    try:
        weak_items = load_weak_items(
            args.checkpoints,
            critical_only=args.critical_blockers_only,
            required_grading_semantics=(GRADING_SEMANTICS if args.critical_blockers_only else None),
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not weak_items:
        if args.critical_blockers_only:
            raise SystemExit("No validated critical blockers found; critical-blocker remediation is not applicable.")
        raise SystemExit("No PARTIAL/FAIL/critical checkpoint items found; nothing to remediate.")

    gate_evidence: dict[str, object] | None = None
    if args.critical_blockers_only:
        if not args.critical_revalidation_report or not args.ledger:
            raise SystemExit(
                "critical-blocker remediation requires --critical-revalidation-report and --ledger"
            )
        try:
            gate_evidence = validate_critical_blocker_gate(
                revalidation_report_path=args.critical_revalidation_report,
                ledger_path=args.ledger,
                curriculum_id=curriculum_id,
                level=1,
            )
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc
        current_critical_ids = sorted(item.exercise_id for item in weak_items)
        if gate_evidence.get("critical_ids") != current_critical_ids:
            raise SystemExit(
                "critical revalidation report critical ids do not match current V3 checkpoint blockers"
            )

    plan = build_remediation_plan(exercises, weak_items)
    inherited_plans, inherited_plan_records = _load_inherited_plans(
        list(args.inherit_remediation_plan)
    )
    if inherited_plans:
        try:
            plan = inherit_critical_origins(
                plan,
                inherited_plans,
                curriculum_id=curriculum_id,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc

    exclusion_dirs = [args.checkpoints, *args.exclude_checkpoints]
    try:
        excluded_seen_ids = load_seen_exercise_ids(exclusion_dirs)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    canonical_practice_exhausted = False
    canonical_practice_exhaustion_reason = ""
    try:
        practice = select_fresh_practice(
            exercises,
            weak_items,
            per_weakness=args.practice_per_weakness,
            seed=args.seed,
            excluded_exercise_ids=excluded_seen_ids,
        )
    except ValueError as exc:
        if args.critical_blockers_only and str(exc).startswith(
            "cumulative checkpoint history exhausted fresh practice for remediation weaknesses:"
        ):
            practice = ()
            canonical_practice_exhausted = True
            canonical_practice_exhaustion_reason = str(exc)
        else:
            raise SystemExit(str(exc)) from exc

    approved_source_refs = manifest.get("approved_source_refs")
    if not isinstance(approved_source_refs, list):
        raise SystemExit("Validated curriculum manifest is missing approved_source_refs.")
    handoffs = build_pyramid_learning_handoffs(
        exercises,
        weak_items,
        curriculum_id=curriculum_id,
        approved_source_refs=tuple(str(item) for item in approved_source_refs),
    )

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / "remediation_plan.json"
    practice_path = output / "practice_questions.jsonl"
    handoff_path = output / "learning_handoffs.jsonl"

    write_practice_jsonl(practice_path, practice)
    practice_sha256 = hashlib.sha256(practice_path.read_bytes()).hexdigest()
    practice_exercise_ids = [item.exercise_id for item in practice]
    plan_payload = {
        "curriculum_id": manifest["curriculum_id"],
        "seed": args.seed,
        "critical_blocker_mode": args.critical_blockers_only,
        "critical_blocker_gate": gate_evidence,
        "required_grading_semantics": GRADING_SEMANTICS if args.critical_blockers_only else None,
        "canonical_practice_exhausted": canonical_practice_exhausted,
        "canonical_practice_exhaustion_reason": canonical_practice_exhaustion_reason,
        "supplemental_fallback_required": bool(args.critical_blockers_only and canonical_practice_exhausted),
        "practice_question_count": len(practice),
        "learning_handoff_count": len(handoffs),
        "excluded_seen_exercise_count": len(excluded_seen_ids),
        "excluded_checkpoint_dirs": [str(Path(item)) for item in exclusion_dirs],
        "inherited_remediation_plans": inherited_plan_records,
        "practice_binding_contract": PYRAMID_REMEDIATION_PRACTICE_BINDING_CONTRACT,
        "practice_exercise_ids": practice_exercise_ids,
        "practice_sha256": practice_sha256,
        **plan,
    }
    plan_path.write_text(json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_pyramid_learning_handoffs_jsonl(handoff_path, handoffs)

    print(f"CURRICULUM {manifest['curriculum_id']}")
    print(f"CRITICAL_BLOCKER_MODE {str(args.critical_blockers_only).lower()}")
    if gate_evidence is not None:
        print(f"CRITICAL_BLOCKER_GATE_VERIFIED true")
        print(f"GATE_REVALIDATED_ACCURACY {float(gate_evidence['revalidated_accuracy']):.4f}")
        print(f"GATE_INTEGRITY_ACCURACY {float(gate_evidence['integrity_accuracy']):.4f}")
        print(f"GATE_BOSS_PASSED {str(gate_evidence['boss_passed']).lower()}")
        print(f"GATE_VALIDATED_CRITICAL_FAILURES {gate_evidence['validated_critical_failures']}")
    print(f"WEAK_ITEMS {plan['weak_item_count']}")
    print(f"WEAKNESSES {plan['weakness_count']}")
    print(f"EXCLUDED_SEEN_EXERCISES {len(excluded_seen_ids)}")
    print(f"FRESH_PRACTICE {len(practice)}")
    print(f"CANONICAL_PRACTICE_EXHAUSTED {str(canonical_practice_exhausted).lower()}")
    print(f"SUPPLEMENTAL_FALLBACK_REQUIRED {str(args.critical_blockers_only and canonical_practice_exhausted).lower()}")
    if canonical_practice_exhaustion_reason:
        print(f"CANONICAL_PRACTICE_EXHAUSTION_REASON {canonical_practice_exhaustion_reason}")
    print(f"PRACTICE_SHA256 {practice_sha256}")
    print(f"LEARNING_HANDOFFS {len(handoffs)}")
    if inherited_plan_records:
        inherited_critical = plan.get("inherited_critical_weaknesses", [])
        print(f"INHERITED_REMEDIATION_PLANS {len(inherited_plan_records)}")
        print(f"INHERITED_CRITICAL_WEAKNESSES {len(inherited_critical)}")
    print(f"PLAN {plan_path}")
    print(f"PRACTICE {practice_path}")
    print(f"HANDOFFS {handoff_path}")
    if handoffs:
        if args.critical_blockers_only and canonical_practice_exhausted:
            print("NEXT_GATE source_grounded_phase7_reconstruction_for_supplemental")
        else:
            print("NEXT_GATE source_grounded_phase7_reconstruction")
        print("CANONICAL_ATTEMPT_AUTHORIZED false")
        print("RETENTION_AUTHORIZED false")

    print("\n--- TOP REMEDIATION TARGETS ---")
    for item in plan["weaknesses"][:10]:
        print(
            f"{item['concept']}/{item['subconcept']} "
            f"priority={item['priority']} fail={item['fail_count']} "
            f"partial={item['partial_count']} critical={item['critical_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
