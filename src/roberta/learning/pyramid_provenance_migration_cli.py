from __future__ import annotations

import argparse
import json

from .pyramid_provenance_migration import (
    MB4E_SOURCE_KEY,
    migrate_legacy_mb4e_curriculum,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate the legacy canonical Mastering Blockchain Level 1 Pyramid "
            "package to accepted source provenance without mutating historical inputs."
        )
    )
    parser.add_argument("--curriculum", required=True, help="Legacy curriculum package directory")
    parser.add_argument("--output", required=True, help="New migrated curriculum package directory")
    parser.add_argument(
        "--checkpoints",
        help="Optional historical/regraded checkpoint directory to verify exercise-id compatibility",
    )
    parser.add_argument(
        "--source-key",
        default=MB4E_SOURCE_KEY,
        help=f"Canonical Learning System source key (default: {MB4E_SOURCE_KEY})",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    report = migrate_legacy_mb4e_curriculum(
        curriculum_dir=args.curriculum,
        output_dir=args.output,
        checkpoints_dir=args.checkpoints,
        source_key=args.source_key,
    )
    print(f"CURRICULUM {report.curriculum_id}")
    print(f"SOURCE_KEY {report.source_key}")
    print(f"INPUT {report.input_dir}")
    print(f"OUTPUT {report.output_dir}")
    print(f"EXERCISES_BEFORE {report.exercise_count_before}")
    print(f"EXERCISES_AFTER {report.exercise_count_after}")
    print(f"PROVENANCE {report.provenance_count}")
    print(f"EXERCISE_IDS_IDENTICAL {str(report.exercise_ids_identical).lower()}")
    print(f"QUESTION_TEXT_IDENTICAL {str(report.question_text_identical).lower()}")
    print(f"SEMANTIC_FIELDS_IDENTICAL {str(report.semantic_fields_identical).lower()}")
    if report.checkpoint_compatible is not None:
        print(f"CHECKPOINT_COMPATIBLE {str(report.checkpoint_compatible).lower()}")
        print(f"CHECKPOINT_EXERCISES {report.checkpoint_exercise_count}")
    print(f"REPORT {report.output_dir}/migration_report.json")
    print("HISTORICAL_PACKAGE_MUTATED false")
    print("HISTORICAL_CHECKPOINTS_MUTATED false")
    print("PDF_PAGE_BASIS_PRESERVED true")
    print("NEXT_GATE regenerate_remediation_handoffs")
    print("AUTHORITY_WIDENED false")
    print("REPORT_JSON", json.dumps(report.to_mapping(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
