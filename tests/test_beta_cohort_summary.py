from __future__ import annotations

import json

import pytest

from roberta.beta_cohort_summary import (
    BETA_COHORT_SUMMARY_VERSION,
    BetaCohortSummaryError,
    load_beta_jsonl,
    summarize_beta_records,
)
from roberta.beta_product_proof import build_automatic_outcome, build_user_feedback


def _telemetry(*, workflow: str, unknowns: list[str] | None = None):
    return {
        "evaluation_evidence": {
            "human_response_decision": {
                "workflow": workflow,
                "response_depth": "normal",
                "evidence_quality": "MEDIUM",
                "important_unknowns": list(unknowns or []),
                "execution_authorized": False,
            }
        },
        "claims": [{"name": "bounded_claim"}],
        "evidence_provenance": {"source_contracts": ["bounded_contract/v1"]},
        "execution_authorized": False,
    }


def test_summary_is_aggregate_only_and_ranks_product_signals():
    first_id = "1" * 32
    second_id = "2" * 32
    records = [
        build_automatic_outcome(
            _telemetry(workflow="token_investigation"),
            duration_ms=1_500,
            response_id=first_id,
        ),
        build_user_feedback(
            response_id=first_id,
            helpful=True,
            clarity="clear",
            evidence_drill_down=True,
            would_use_again=True,
            willingness_to_pay="yes",
            interest_surface="end_user",
        ),
        build_automatic_outcome(
            _telemetry(workflow="pre_trade", unknowns=["network_fee"]),
            duration_ms=8_000,
            response_id=second_id,
        ),
        build_user_feedback(
            response_id=second_id,
            helpful=False,
            clarity="too_technical",
            evidence_drill_down=False,
            would_use_again=False,
            willingness_to_pay="no",
            interest_surface="both",
        ),
    ]

    summary = summarize_beta_records(records)

    assert summary["contract_version"] == BETA_COHORT_SUMMARY_VERSION
    assert summary["cohort_size"] == 2
    assert summary["feedback_count"] == 2
    assert summary["outcomes"] == {"evidence_required": 1, "success": 1}
    assert summary["rates"]["helpful"] == {
        "numerator": 1,
        "denominator": 2,
        "rate": 0.5,
    }
    assert summary["rates"]["too_technical_or_confusing"]["rate"] == 0.5
    assert summary["rates"]["would_use_again"]["rate"] == 0.5
    assert summary["targets"]["evidence_required_names_unknowns"] is True

    ranked = summary["ranked_product_signals"]
    assert ranked[0] == {
        "workflow": "pre_trade",
        "signal": "not_helpful",
        "count": 1,
        "impact_weight": 4,
        "priority_score": 4,
    }

    encoded = json.dumps(summary, sort_keys=True)
    assert first_id not in encoded
    assert second_id not in encoded
    assert summary["privacy"] == {
        "contains_response_ids": False,
        "contains_prompt_or_response_text": False,
        "contains_cross_session_identity": False,
    }
    assert summary["execution_authorized"] is False


def test_duplicate_automatic_response_id_fails_closed():
    response_id = "a" * 32
    automatic = build_automatic_outcome(
        _telemetry(workflow="pre_trade"),
        duration_ms=500,
        response_id=response_id,
    )

    with pytest.raises(BetaCohortSummaryError, match="duplicate automatic"):
        summarize_beta_records([automatic, automatic])


def test_duplicate_feedback_is_ignored_and_orphans_are_reported():
    response_id = "b" * 32
    orphan_id = "c" * 32
    automatic = build_automatic_outcome(
        _telemetry(workflow="wallet_relationship"),
        duration_ms=2_500,
        response_id=response_id,
    )
    feedback = build_user_feedback(
        response_id=response_id,
        helpful=True,
        clarity="clear",
    )
    duplicate = build_user_feedback(
        response_id=response_id,
        helpful=False,
        clarity="confusing",
    )
    orphan = build_user_feedback(
        response_id=orphan_id,
        helpful=True,
        clarity="clear",
    )

    summary = summarize_beta_records([automatic, feedback, duplicate, orphan])

    assert summary["feedback_count"] == 1
    assert summary["duplicate_feedback_ignored"] == 1
    assert summary["orphan_feedback_count"] == 1
    assert summary["rates"]["helpful"]["rate"] == 1.0


def test_jsonl_loader_rejects_schema_drift_and_content_fields(tmp_path):
    source = tmp_path / "bad.jsonl"
    source.write_text(
        json.dumps(
            {
                "contract_version": "roberta_beta_product_proof/v1",
                "record_type": "automatic_response_outcome",
                "response_id": "d" * 32,
                "prompt": "content must never enter beta records",
                "execution_authorized": False,
                "content_persisted": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(BetaCohortSummaryError, match="invalid beta record"):
        load_beta_jsonl(source)


def test_empty_summary_does_not_claim_targets_pass():
    summary = summarize_beta_records([])

    assert summary["cohort_size"] == 0
    assert summary["targets"]["helpful_gte_70pct"] is None
    assert summary["targets"]["too_technical_or_confusing_lte_20pct"] is None
    assert summary["targets"]["supported_workflow_unavailable_lte_10pct"] is None
    assert summary["targets"]["would_use_again_gte_60pct"] is None
