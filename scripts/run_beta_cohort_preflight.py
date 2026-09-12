#!/usr/bin/env python3
"""Deterministic privacy/collection preflight for the ROBERTA beta cohort.

The configured production beta JSONL is never modified by this script. The
preflight writes a sibling ``*.preflight.jsonl`` file using synthetic, content-
free records and proves that the aggregate summary contains no response ids or
execution authority.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from roberta.beta_cohort_summary import summarize_beta_jsonl
from roberta.beta_product_proof import (
    BETA_PATH_ENV,
    append_beta_record,
    build_automatic_outcome,
    build_user_feedback,
)


def _synthetic_telemetry() -> dict[str, object]:
    return {
        "evaluation_evidence": {
            "human_response_decision": {
                "workflow": "pre_trade",
                "response_depth": "normal",
                "evidence_quality": "MEDIUM",
                "important_unknowns": ["bounded_missing_evidence"],
                "execution_authorized": False,
            }
        },
        "claims": [{"name": "bounded_claim"}],
        "evidence_provenance": {
            "source_contracts": ["bounded_contract/v1"],
        },
        "execution_authorized": False,
    }


def main() -> None:
    configured = os.getenv(BETA_PATH_ENV, "").strip()
    if not configured:
        raise SystemExit(
            f"{BETA_PATH_ENV} must be explicitly configured before cohort preflight"
        )

    live_path = Path(configured).expanduser()
    suffix = live_path.suffix or ".jsonl"
    preflight_path = live_path.with_name(
        f"{live_path.stem}.preflight{suffix}"
    )
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    if preflight_path.exists():
        preflight_path.unlink()

    automatic = build_automatic_outcome(
        _synthetic_telemetry(),
        duration_ms=4_200,
        response_id="1" * 32,
        timestamp="2026-09-12T12:00:00Z",
    )
    feedback = build_user_feedback(
        response_id="1" * 32,
        helpful=True,
        clarity="clear",
        evidence_drill_down=True,
        would_use_again=True,
        willingness_to_pay="maybe",
        interest_surface="end_user",
        timestamp="2026-09-12T12:01:00Z",
    )

    assert append_beta_record(automatic, path=preflight_path)
    assert append_beta_record(feedback, path=preflight_path)

    summary = summarize_beta_jsonl(preflight_path)
    encoded = json.dumps(summary, sort_keys=True, allow_nan=False)

    assert summary["cohort_size"] == 1
    assert summary["feedback_count"] == 1
    assert summary["execution_authorized"] is False
    assert summary["privacy"]["contains_response_ids"] is False
    assert summary["privacy"]["contains_prompt_or_response_text"] is False
    assert "11111111111111111111111111111111" not in encoded
    assert "prompt" not in encoded.lower()
    assert "reply" not in encoded.lower()

    print(
        json.dumps(
            {
                "status": "PASS",
                "configured_live_path": str(live_path),
                "preflight_path": str(preflight_path),
                "cohort_summary_contract": summary["contract_version"],
                "execution_authorized": False,
                "content_persisted": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
