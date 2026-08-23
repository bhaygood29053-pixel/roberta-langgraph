from __future__ import annotations

import argparse
from pathlib import Path

from .pyramid_source_reconstruction import (
    build_source_grounded_reconstructions,
    write_source_grounded_reconstruction_bundle,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Ground current-semantics Pyramid learning handoffs in exact approved "
            "Learning System source evidence without authorizing retention or Phase 8 promotion."
        )
    )
    parser.add_argument("--curriculum", required=True, help="Validated Pyramid curriculum package directory")
    parser.add_argument("--handoffs", required=True, help="Current-semantics learning_handoffs.jsonl")
    parser.add_argument("--checkpoints", required=True, help="v2 checkpoint directory bound by the handoffs")
    parser.add_argument("--output", required=True, help="New output directory for reconstruction artifacts")
    parser.add_argument(
        "--source-transcript",
        help=(
            "Exact external UTF-8 transcript for an external-only approved source. "
            "The pinned source contract validates its byte count and SHA-256."
        ),
    )
    parser.add_argument("--top-k", type=int, default=5, help="Canonical source evidence anchors per handoff")
    return parser


def main() -> int:
    args = _parser().parse_args()
    reconstructions = build_source_grounded_reconstructions(
        curriculum_dir=args.curriculum,
        handoffs_path=args.handoffs,
        checkpoints_dir=args.checkpoints,
        source_transcript_path=args.source_transcript,
        top_k=args.top_k,
    )
    report = write_source_grounded_reconstruction_bundle(args.output, reconstructions)
    output = Path(args.output)
    print(f"CURRICULUM {report.curriculum_id}")
    print(f"SOURCE_KEY {report.source_key}")
    print(f"RECONSTRUCTIONS {report.reconstruction_count}")
    print(f"EVIDENCE_ANCHORS {report.evidence_anchor_count}")
    print(f"SOURCE_GROUNDED {report.source_grounded_count}")
    print(f"PACKET_STATUS_COUNTS {dict(report.packet_status_counts)}")
    print(f"RECONSTRUCTIONS_FILE {output / 'source_grounded_reconstructions.jsonl'}")
    print(f"REPORT {output / 'reconstruction_report.json'}")
    print("NEXT_GATE targeted_pyramid_practice")
    print("PHASE8_CANDIDATE_CREATION_AUTHORIZED false")
    print("SOURCE_TRUTH_AUTHORIZED false")
    print("LIVE_STATE_AUTHORIZED false")
    print("MEMORY_PROMOTION_AUTHORIZED false")
    print("RETENTION_AUTHORIZED false")
    print("GOVERNANCE_MUTATION_AUTHORIZED false")
    print("EXECUTION_AUTHORIZED false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
