from __future__ import annotations

from copy import deepcopy

import pytest

from roberta.x1_scout.tokenized_equity_claim_integrity import (
    ROBERTA_TOKENIZED_EQUITY_CLAIM_INTEGRITY_CONTRACT,
    TokenizedEquityClaimIntegrityError,
    build_tokenized_equity_claim_integrity,
)

MINT = "1" * 32
OTHER_MINT = "2" * 32
SECURITY_ID = "US0378331005"


def _right(state: str, summary: str) -> dict[str, object]:
    return {
        "dimension": "set-by-fixture",
        "state": state,
        "summary": summary,
        "conditions": ["subject to terms"] if state == "CONDITIONAL" else [],
        "evidence": [] if state == "UNKNOWN" else [{"evidence_id": "ev-1"}],
        "evidence_binding_verified": state != "UNKNOWN",
        "legal_effect_adjudicated": False,
    }


def _rights() -> dict[str, object]:
    dimensions = {
        "underlying_ownership": _right("VERIFIED", "Economic exposure is through a tokenized security representation."),
        "voting_rights": _right("DENIED", "No voting right is established for the token holder."),
        "dividend_treatment": _right("CONDITIONAL", "Distribution treatment is conditional on governing terms."),
        "redemption_rights": _right("UNKNOWN", "Redemption evidence is incomplete."),
        "backing_collateral": _right("VERIFIED", "Backing structure is described in authoritative evidence."),
        "issuer_counterparty": _right("VERIFIED", "Issuer and material counterparty are evidence-bound."),
        "jurisdiction_scope": _right("VERIFIED", "Governing jurisdiction is evidence-bound."),
        "transfer_restrictions": _right("CONDITIONAL", "Transfer eligibility is conditional."),
        "custody_structure": _right("VERIFIED", "Custody dependency is evidence-bound."),
    }
    for name, row in dimensions.items():
        row["dimension"] = name
    return {
        "contract": "tokenized_equity_rights/v1",
        "state_semantics": "evidence_bound_claim_status_not_legal_adjudication",
        "dimensions": dimensions,
        "verification": {
            "accepted_tokenized_equity_provenance_bound": True,
            "all_non_unknown_states_authoritatively_evidence_bound": True,
            "legal_effect_independently_adjudicated": False,
            "shareholder_status_independently_verified": False,
            "backing_sufficiency_verified": False,
            "custody_safety_verified": False,
        },
        "execution_authorized": False,
    }


def _metric(
    state: str,
    semantic: str,
    value: object = None,
    *,
    unit: str = "count",
) -> dict[str, object]:
    return {
        "state": state,
        "semantic": semantic,
        "value": value,
        "unit": unit,
        "fact_time": "2026-09-11T03:00:00Z" if state == "OBSERVED" else None,
        "window": None,
        "freshness": {"state": "FRESH", "age_seconds": 5, "max_age_seconds": 300},
        "bounded_zero_observed": False,
    }


def _market() -> dict[str, object]:
    return {
        "contract": "tokenized_equity_market_activity/v1",
        "scope": {
            "scope_kind": "asset",
            "chain": "x1",
            "scope_id": MINT,
            "scope_id_kind": "mint",
            "program_id": None,
            "coverage_complete_for_scope": False,
            "coverage_basis": "bounded accepted source scope",
        },
        "metrics": {
            "liquidity_usd": _metric("OBSERVED", "liquidity_snapshot", "125000.00", unit="usd"),
            "trade_volume_usd": _metric("OBSERVED", "executed_trade_volume", "7500.00", unit="usd"),
            "trade_count": _metric("OBSERVED", "executed_trade_count", 12),
            "transfer_count": _metric("OBSERVED", "token_transfer_count", 21),
            "holder_count": _metric("UNKNOWN", "holder_snapshot"),
            "price_usd": _metric("OBSERVED", "reference_price", "184.25", unit="usd_per_token"),
            "bridge_inflow_units": _metric("UNKNOWN", "bridge_inflow", unit="token_units"),
            "bridge_outflow_units": _metric("UNKNOWN", "bridge_outflow", unit="token_units"),
        },
        "verification": {
            "accepted_tokenized_equity_provenance_bound": True,
            "exact_scope_identity_bound": True,
            "metric_semantics_kept_separate": True,
            "global_market_coverage_verified": False,
            "live_x1_equity_deployment_verified": False,
            "live_robinhood_x1_route_verified": False,
        },
        "execution_authorized": False,
    }


def _provenance() -> dict[str, object]:
    return {
        "contract": "tokenized_equity_provenance/v1",
        "token": {"chain": "x1", "asset_id": MINT, "asset_id_kind": "mint"},
        "underlying_security": {
            "security_id": SECURITY_ID,
            "security_id_kind": "isin",
        },
        "representation": {
            "type": "tokenized_security_representation",
            "issuer": {"name": "Example Issuer"},
            "backing_model": "custodial",
            "custody_model": "qualified custodian",
            "wrapper_layers": [
                {
                    "layer_index": 0,
                    "layer_type": "destination_wrapper",
                    "token": {"chain": "x1", "asset_id": MINT, "asset_id_kind": "mint"},
                }
            ],
        },
        "verification": {
            "exact_token_identity_structurally_bound": True,
            "exact_underlying_security_id_structurally_bound": True,
            "representation_classification_verified": False,
            "issuer_identity_verified": False,
            "underlying_equity_ownership_verified": False,
            "backing_verified": False,
            "custody_verified": False,
            "holder_rights_verified": False,
            "live_deployment_verified": False,
            "live_bridge_route_verified": False,
        },
        "execution_authorized": False,
    }


def _cross_chain() -> dict[str, object]:
    return {
        "contract": "cross_chain_equity_provenance/v1",
        "origin": {"chain": "source", "asset_id": "security-root", "asset_id_kind": "registry"},
        "current": {"chain": "x1", "asset_id": MINT, "asset_id_kind": "mint"},
        "lineage": [
            {
                "source": {"chain": "source", "asset_id": "security-root", "asset_id_kind": "registry"},
                "destination": {"chain": "x1", "asset_id": MINT, "asset_id_kind": "mint"},
                "bridge": "Example Bridge",
                "bridge_route_id": "route-1",
            }
        ],
        "route_evidence": [{"evidence_id": "route-evidence-1", "qualified": True}],
        "verification": {
            "tokenized_equity_binding_verified": True,
            "structural_lineage_continuity_verified": True,
            "all_route_evidence_qualified": True,
            "robinhood_x1_route_verified": False,
            "observed_asset_movement_verified": False,
            "adoption_verified": False,
            "legal_or_economic_equivalence_verified": False,
        },
        "execution_authorized": False,
    }


def _quality() -> dict[str, object]:
    return {
        "contract": "tokenized_equity_evidence_quality/v1",
        "freshness": {
            "policy": {"retrieval_time_alone_proves_freshness": False},
            "fresh_receipt_count": 2,
            "stale_receipt_count": 0,
            "unknown_receipt_count": 4,
        },
        "conflict_evidence": {
            "state": "UNKNOWN",
            "conflicts": [],
            "conflict_detection_complete": False,
            "absence_of_recorded_conflict_proves_agreement": False,
        },
        "unresolved_fields": ["rights.redemption_rights", "market.holder_count"],
        "confidence_inputs": {
            "exact_subject_identity_verified": True,
            "accepted_component_binding_verified": True,
            "source_independence_verified": False,
            "same_fact_agreement_verified": False,
            "proof_score": None,
            "proof_score_owned_by_protected_runtime": True,
            "risk_considered": False,
            "legal_effect_adjudicated": False,
        },
        "verification": {
            "missing_evidence_zero_filled": False,
            "global_agreement_inferred": False,
            "source_independence_inferred_from_distinct_labels": False,
        },
        "execution_authorized": False,
    }


def _projection() -> dict[str, object]:
    return {
        "contract_version": "x1_tokenized_equity_intelligence/v1",
        "product": "x1_tokenized_equity_intelligence",
        "chain": "x1",
        "status": "ok",
        "cmis_contract_version": "tokenized_equity_intelligence/v1",
        "subject_resolution_state": "RESOLVED",
        "selected_subject": {
            "chain": "x1",
            "asset_mint": MINT,
            "asset_id_kind": "mint",
            "security_id": SECURITY_ID,
            "security_id_kind": "isin",
        },
        "resolved_subject": {
            "chain": "x1",
            "asset_mint": MINT,
            "asset_id_kind": "mint",
            "security_id": SECURITY_ID,
            "security_id_kind": "isin",
        },
        "requested_components": ["provenance", "cross_chain", "rights", "market_activity"],
        "component_states": {
            "provenance": "AVAILABLE",
            "cross_chain": "AVAILABLE",
            "rights": "AVAILABLE",
            "market_activity": "AVAILABLE",
        },
        "components": {
            "provenance": _provenance(),
            "cross_chain": _cross_chain(),
            "rights": _rights(),
            "market_activity": _market(),
        },
        "evidence_quality": _quality(),
        "observed_at": "2026-09-11T03:05:00Z",
        "freshness": {"contract_version": "cmis_response_freshness/v1", "state": "UNKNOWN"},
        "confidence": {"proof_score_separate_from_risk": True},
        "sources": [],
        "warnings": [],
        "errors": [],
        "evidence_receipt": {"receipt_id": "receipt-1"},
        "proof_score": {"contract_version": "cmis_proof_score/v1", "score": 87},
        "missing_evidence_zero_filled": False,
        "component_state_semantics_preserved": True,
        "beneficial_ownership_inference_authorized": False,
        "shareholder_status_inference_authorized": False,
        "legal_or_economic_equivalence_inference_authorized": False,
        "live_deployment_inference_authorized": False,
        "bridge_route_inference_authorized": False,
        "adoption_inference_authorized": False,
        "liquidity_volume_equivalence_authorized": False,
        "transfer_trade_equivalence_authorized": False,
        "reference_executed_price_equivalence_authorized": False,
        "proof_score_as_risk_authorized": False,
        "causality_inference_authorized": False,
        "automatic_risk_conclusion_authorized": False,
        "investment_recommendation_authorized": False,
        "legal_advice_authorized": False,
        "read_only": True,
        "execution_authorized": False,
    }


def _wallet(*, mint: str = MINT) -> dict[str, object]:
    data = {
        "relationship_kind": "observed_direct_interaction",
        "interaction_type": "verified_token_transfer",
        "asset_mint": mint,
        "sender_wallet": "3" * 32,
        "recipient_wallet": "4" * 32,
        "transaction_signature": "sig-1",
        "observed_at": "2026-09-11T03:01:00Z",
        "amount_raw": "1000000",
        "decimals": 6,
        "ownership_inference_added": False,
        "beneficial_ownership_inference_added": False,
        "behavioral_interpretation_added": False,
        "intent_interpretation_added": False,
        "risk_interpretation": None,
        "complete_history_claimed": False,
        "complete_graph_coverage_claimed": False,
        "execution_authorized": False,
    }
    return {
        "contract_version": "x1_wallet_relationship_intelligence/v1",
        "product": "x1_wallet_relationship_intelligence",
        "chain": "x1",
        "status": "ok",
        "wallet_relationship_intelligence": data,
        "relationship_scope_is_one_selected_finalized_transaction": True,
        "common_ownership_claim_authorized": False,
        "beneficial_ownership_claim_authorized": False,
        "real_world_identity_claim_authorized": False,
        "whale_insider_bot_market_maker_claim_authorized": False,
        "behavior_or_intent_claim_authorized": False,
        "coordination_manipulation_fraud_claim_authorized": False,
        "causality_claim_authorized": False,
        "risk_severity_claim_authorized": False,
        "complete_wallet_history_claim_authorized": False,
        "complete_relationship_graph_claim_authorized": False,
        "execution_authorized": False,
    }


def test_claim_integrity_authorizes_only_bounded_tokenized_equity_claims():
    result = build_tokenized_equity_claim_integrity(_projection())
    assert result["contract_version"] == ROBERTA_TOKENIZED_EQUITY_CLAIM_INTEGRITY_CONTRACT
    assert result["status"] == "PASS"
    assert result["facts_authority"] == "chain_scout_cmis"
    assert result["judgment_authority"] == "roberta"
    assert result["claims"]["identity_representation"]["state"] == "AUTHORIZED"
    assert result["claims"]["issuer_counterparty"]["state"] == "AUTHORIZED"
    assert result["claims"]["backing_collateral"]["state"] == "AUTHORIZED"
    assert result["claims"]["custody_wrapper"]["state"] == "AUTHORIZED"
    assert result["claims"]["cross_chain_lineage"]["claim_mode"] == "QUALIFIED_ROUTE_CONFIGURATION_ONLY"
    assert result["claims"]["cross_chain_lineage"]["data"]["observed_asset_movement_verified"] is False
    assert result["claims"]["market_activity"]["state"] == "AUTHORIZED"
    assert result["claims"]["proof_score"]["claim_mode"] == "EVIDENCE_STRENGTH_ONLY"
    assert result["claims"]["observed_wallet_relationships"]["state"] == "NOT_APPLICABLE"
    assert result["automatic_risk_conclusion_authorized"] is False
    assert result["investment_recommendation_authorized"] is False
    assert result["legal_advice_authorized"] is False
    assert result["execution_authorized"] is False


def test_unknown_rights_remain_evidence_required_not_false():
    source = _projection()
    rights = source["components"]["rights"]
    rights["dimensions"]["issuer_counterparty"] = _right("UNKNOWN", "Issuer evidence incomplete.")
    rights["dimensions"]["issuer_counterparty"]["dimension"] = "issuer_counterparty"
    result = build_tokenized_equity_claim_integrity(source)
    issuer = result["claims"]["issuer_counterparty"]
    assert issuer["state"] == "EVIDENCE_REQUIRED"
    assert issuer["data"]["state"] == "UNKNOWN"
    assert result["claims"]["holder_rights"]["data"]["evidence_required_dimensions"] == [
        "redemption_rights",
        "issuer_counterparty",
    ]


def test_decisive_right_without_evidence_binding_fails_closed():
    source = _projection()
    source["components"]["rights"]["dimensions"]["voting_rights"]["evidence_binding_verified"] = False
    with pytest.raises(TokenizedEquityClaimIntegrityError, match="evidence_binding_verified"):
        build_tokenized_equity_claim_integrity(source)


def test_market_metric_and_price_semantics_are_not_widened():
    result = build_tokenized_equity_claim_integrity(_projection())
    market = result["claims"]["market_activity"]["data"]["observed_metrics"]
    assert market["liquidity_usd"]["semantic"] == "liquidity_snapshot"
    assert market["trade_volume_usd"]["semantic"] == "executed_trade_volume"
    assert market["transfer_count"]["semantic"] == "token_transfer_count"
    assert market["price_usd"]["semantic"] == "reference_price"
    assert "holder_count" in result["claims"]["market_activity"]["data"]["evidence_required_metrics"]
    assert result["checks"]["liquidity_not_volume"] is True
    assert result["checks"]["transfer_not_trade"] is True
    assert result["checks"]["price_semantics_not_widened"] is True


@pytest.mark.parametrize("field", ["observed_asset_movement_verified", "adoption_verified"])
def test_cross_chain_route_cannot_be_upgraded_to_movement_or_adoption(field):
    source = _projection()
    source["components"]["cross_chain"]["verification"][field] = True
    with pytest.raises(TokenizedEquityClaimIntegrityError):
        build_tokenized_equity_claim_integrity(source)


def test_evidence_quality_keeps_unknown_conflict_and_proof_score_separate_from_risk():
    result = build_tokenized_equity_claim_integrity(_projection())
    quality = result["claims"]["evidence_quality"]
    assert quality["state"] == "AUTHORIZED"
    assert quality["data"]["conflict_evidence"]["state"] == "UNKNOWN"
    assert quality["data"]["conflict_evidence"]["absence_of_recorded_conflict_proves_agreement"] is False
    assert result["claims"]["proof_score"]["data"]["score"] == 87
    assert result["checks"]["proof_score_separate_from_risk"] is True
    assert result["automatic_risk_conclusion_authorized"] is False


def test_observed_wallet_relationship_can_be_attached_without_ownership_or_intent():
    result = build_tokenized_equity_claim_integrity(_projection(), wallet_relationship=_wallet())
    wallet = result["claims"]["observed_wallet_relationships"]
    assert wallet["state"] == "AUTHORIZED"
    assert wallet["claim_mode"] == "ONE_OBSERVED_DIRECT_TRANSFER_ONLY"
    assert wallet["data"]["asset_mint"] == MINT
    assert wallet["data"]["sender_wallet"] == "3" * 32
    assert result["checks"]["wallet_observation_not_identity_intent_or_causality"] is True


def test_wallet_relationship_for_different_asset_fails_closed():
    with pytest.raises(TokenizedEquityClaimIntegrityError, match="asset_mint"):
        build_tokenized_equity_claim_integrity(_projection(), wallet_relationship=_wallet(mint=OTHER_MINT))


@pytest.mark.parametrize(
    "field",
    [
        "beneficial_ownership_inference_authorized",
        "shareholder_status_inference_authorized",
        "legal_or_economic_equivalence_inference_authorized",
        "live_deployment_inference_authorized",
        "adoption_inference_authorized",
        "proof_score_as_risk_authorized",
        "execution_authorized",
    ],
)
def test_scout_authority_drift_fails_closed(field):
    source = _projection()
    source[field] = True
    with pytest.raises(TokenizedEquityClaimIntegrityError, match=field):
        build_tokenized_equity_claim_integrity(source)


def test_unresolved_subject_preserves_evidence_required_without_zero_fill():
    source = _projection()
    source["status"] = "partial"
    source["subject_resolution_state"] = "EVIDENCE_REQUIRED"
    source["resolved_subject"] = None
    source["component_states"] = {
        "provenance": "EVIDENCE_REQUIRED",
        "cross_chain": "EVIDENCE_REQUIRED",
        "rights": "EVIDENCE_REQUIRED",
        "market_activity": "EVIDENCE_REQUIRED",
    }
    source["components"] = {}
    source["evidence_quality"] = None
    source.pop("proof_score")
    result = build_tokenized_equity_claim_integrity(source)
    assert result["status"] == "PASS"
    assert result["claims"]["identity_representation"]["state"] == "EVIDENCE_REQUIRED"
    assert result["claims"]["issuer_counterparty"]["state"] == "EVIDENCE_REQUIRED"
    assert result["claims"]["market_activity"]["state"] == "EVIDENCE_REQUIRED"
    assert result["claims"]["proof_score"]["state"] == "EVIDENCE_REQUIRED"
    assert result["checks"]["unknown_remains_unknown"] is True
    assert result["execution_authorized"] is False
