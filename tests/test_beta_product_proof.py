from __future__ import annotations

import json

import pytest

from roberta.beta_product_proof import (
    BETA_PRODUCT_PROOF_VERSION,
    BetaProductProofError,
    append_beta_record,
    build_automatic_outcome,
    build_user_feedback,
    validate_beta_record,
)

RESPONSE_ID = "a" * 32


def telemetry(*, unknowns: int = 0, execution_authorized: bool = False):
    return {
        "evaluation_telemetry_version": "roberta_evaluation_telemetry/v2",
        "evaluation_evidence": {
            "human_response_decision": {
                "workflow": "x1_smart_route_pretrade",
                "response_depth": "normal",
                "evidence_quality": "MEDIUM",
                "important_unknowns": [
                    {"source_value": f"unknown-{index}"} for index in range(unknowns)
                ],
                "execution_authorized": execution_authorized,
            }
        },
        "claims": [{"name": "recommendation"}, {"name": "primary_driver"}],
        "evidence_provenance": {
            "source_contracts": ["contract-a", "contract-b"],
        },
        "execution_authorized": execution_authorized,
    }


def factual_telemetry(
    *,
    available: bool = True,
    verification_status: str = "VERIFIED",
    freshness_verified: bool = False,
    coverage: float = 80.0,
    projection_execution_authorized: bool = False,
):
    return {
        "evaluation_telemetry_version": "roberta_evaluation_telemetry/v2",
        "evaluation_evidence": {
            "factual_response": {
                "specialist": "x1_scout",
                "chain": "x1",
                "requested_asset": "sensitive-exact-token-identifier",
                "source": {
                    "service": "cmis",
                    "operation": "instant_x1_scan",
                },
                "cmis_status": "partial",
                "confidence": {},
                "evidence_context": {
                    "available": available,
                    "verification_status": verification_status,
                    "freshness_verified": freshness_verified,
                    "category_coverage_percent": coverage,
                },
            },
            "evaluation_projection_integrity": {
                "contract_version": "roberta_evaluation_projection_integrity/v1",
                "status": "PASS",
                "execution_authorized": projection_execution_authorized,
            },
        },
        "claims": [
            {
                "name": "asset_symbol",
                "evidence_path": "factual_response.asset.symbol",
                "value": "PEPE",
            },
            {
                "name": "market_liquidity_usd",
                "evidence_path": "factual_response.findings.data.sections.market.liquidity_usd",
                "value": 2283.0,
            },
        ],
        "evidence_provenance": {
            "source_contracts": ["instant_x1_scan/v6"],
        },
        "execution_authorized": False,
    }


def test_automatic_outcome_is_coarse_and_content_free():
    record = build_automatic_outcome(
        telemetry(unknowns=3),
        duration_ms=7_500,
        response_id=RESPONSE_ID,
        timestamp="2026-09-12T12:00:00Z",
    )
    assert record == {
        "contract_version": BETA_PRODUCT_PROOF_VERSION,
        "record_type": "automatic_response_outcome",
        "response_id": RESPONSE_ID,
        "timestamp": "2026-09-12T12:00:00Z",
        "workflow": "x1_smart_route_pretrade",
        "outcome": "evidence_required",
        "response_depth": "normal",
        "evidence_quality": "MEDIUM",
        "explicit_unknown_count": 3,
        "claim_count": 2,
        "source_contract_count": 2,
        "duration_bucket": "5_15s",
        "execution_authorized": False,
        "content_persisted": False,
    }
    encoded = json.dumps(record).lower()
    for forbidden in ("wallet", "token_address", "message", "prompt", "reply", "raw_evidence"):
        assert forbidden not in encoded


def test_automatic_outcome_uses_v2_factual_projection_when_human_decision_is_absent():
    record = build_automatic_outcome(
        factual_telemetry(),
        duration_ms=12_000,
        response_id=RESPONSE_ID,
        timestamp="2026-09-12T18:58:55Z",
    )
    assert record["workflow"] == "x1_scout:instant_x1_scan"
    assert record["outcome"] == "evidence_required"
    assert record["response_depth"] == "unknown"
    assert record["evidence_quality"] == "MEDIUM"
    assert record["explicit_unknown_count"] == 2
    assert record["claim_count"] == 2
    assert record["source_contract_count"] == 1
    assert record["execution_authorized"] is False
    assert record["content_persisted"] is False
    encoded = json.dumps(record)
    assert "sensitive-exact-token-identifier" not in encoded
    assert "PEPE" not in encoded


def test_factual_projection_can_report_success_when_structured_evidence_has_no_gap():
    record = build_automatic_outcome(
        factual_telemetry(
            freshness_verified=True,
            coverage=100.0,
        ),
        duration_ms=2_500,
        response_id=RESPONSE_ID,
    )
    assert record["workflow"] == "x1_scout:instant_x1_scan"
    assert record["outcome"] == "success"
    assert record["evidence_quality"] == "HIGH"
    assert record["explicit_unknown_count"] == 0


def test_factual_projection_unavailable_remains_unavailable():
    record = build_automatic_outcome(
        factual_telemetry(available=False),
        duration_ms=500,
        response_id=RESPONSE_ID,
    )
    assert record["workflow"] == "x1_scout:instant_x1_scan"
    assert record["outcome"] == "unavailable"
    assert record["evidence_quality"] == "UNAVAILABLE"
    assert record["explicit_unknown_count"] == 1


def test_v1_factual_shape_is_not_promoted_without_accepted_v2_projection():
    value = factual_telemetry()
    value["evaluation_telemetry_version"] = "roberta_evaluation_telemetry/v1"
    record = build_automatic_outcome(
        value,
        duration_ms=500,
        response_id=RESPONSE_ID,
    )
    assert record["outcome"] == "unavailable"
    assert record["workflow"] == "unknown"
    assert record["evidence_quality"] == "UNAVAILABLE"


def test_automatic_outcome_marks_missing_final_structure_unavailable():
    record = build_automatic_outcome(
        {"execution_authorized": False},
        duration_ms=500,
        response_id=RESPONSE_ID,
    )
    assert record["outcome"] == "unavailable"
    assert record["workflow"] == "unknown"
    assert record["evidence_quality"] == "UNAVAILABLE"


def test_execution_authority_widening_fails_closed():
    with pytest.raises(BetaProductProofError, match="execution_authorized"):
        build_automatic_outcome(
            telemetry(execution_authorized=True),
            duration_ms=1_000,
            response_id=RESPONSE_ID,
        )


def test_factual_projection_execution_authority_widening_fails_closed():
    with pytest.raises(BetaProductProofError, match="execution_authorized"):
        build_automatic_outcome(
            factual_telemetry(projection_execution_authorized=True),
            duration_ms=1_000,
            response_id=RESPONSE_ID,
        )


def test_explicit_feedback_is_bounded_and_opt_in():
    record = build_user_feedback(
        response_id=RESPONSE_ID,
        helpful=True,
        clarity="too_technical",
        evidence_drill_down=True,
        would_use_again=True,
        willingness_to_pay="maybe",
        interest_surface="both",
        timestamp="2026-09-12T12:01:00Z",
    )
    assert record["helpful"] is True
    assert record["clarity"] == "too_technical"
    assert record["willingness_to_pay"] == "maybe"
    assert record["content_persisted"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("clarity", "freeform explanation"),
        ("willingness_to_pay", "$20/month"),
        ("interest_surface", "my wallet is 0x123"),
    ],
)
def test_feedback_freeform_values_fail_closed(field, value):
    kwargs = {
        "response_id": RESPONSE_ID,
        "helpful": True,
        "clarity": "clear",
        "willingness_to_pay": None,
        "interest_surface": None,
    }
    kwargs[field] = value
    with pytest.raises(BetaProductProofError):
        build_user_feedback(**kwargs)


def test_forbidden_content_fields_are_rejected():
    record = build_user_feedback(
        response_id=RESPONSE_ID,
        helpful=True,
        clarity="clear",
    )
    for key in ("prompt", "message", "wallet_address", "token_address", "reply"):
        widened = dict(record)
        widened[key] = "sensitive content"
        with pytest.raises(BetaProductProofError):
            validate_beta_record(widened)


def test_collection_is_disabled_without_configured_path(monkeypatch, tmp_path):
    monkeypatch.delenv("ROBERTA_BETA_PRODUCT_PROOF_PATH", raising=False)
    record = build_user_feedback(
        response_id=RESPONSE_ID,
        helpful=True,
        clarity="clear",
    )
    assert append_beta_record(record) is False
    assert not list(tmp_path.iterdir())


def test_append_only_jsonl_collector_writes_validated_record(tmp_path):
    destination = tmp_path / "beta" / "events.jsonl"
    record = build_user_feedback(
        response_id=RESPONSE_ID,
        helpful=False,
        clarity="missing_evidence",
        evidence_drill_down=True,
        would_use_again=False,
        willingness_to_pay="no",
        interest_surface="end_user",
    )
    assert append_beta_record(record, path=destination) is True
    lines = destination.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == record


def test_duration_is_persisted_only_as_bucket():
    record = build_automatic_outcome(
        telemetry(),
        duration_ms=31_234,
        response_id=RESPONSE_ID,
    )
    assert record["duration_bucket"] == "gte_30s"
    assert "duration_ms" not in record
