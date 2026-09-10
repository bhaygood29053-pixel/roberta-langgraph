from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    WALLET_RELATIONSHIP_CONTRACT_VERSION,
    WALLET_RELATIONSHIP_MIN_CMIS_CONTRACT_VERSION,
    WALLET_RELATIONSHIP_REQUIRED_LIMITATIONS,
    WALLET_RELATIONSHIP_REQUIRED_REQUIREMENTS,
    require_wallet_relationship_capability,
    validate_capability_manifest,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.wallet_relationship import (
    CMISWalletRelationshipContractError,
    normalize_wallet_relationship_request,
    validate_wallet_relationship_response,
)
from roberta.x1_scout.wallet_relationship_intelligence import (
    X1_WALLET_RELATIONSHIP_CONTRACT,
    build_x1_wallet_relationship_intelligence,
    render_x1_wallet_relationship_text,
)
from tests.test_cmis_http_client import _Server, _capabilities


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58(data: bytes) -> str:
    number = int.from_bytes(data, "big")
    encoded = ""
    while number:
        number, rem = divmod(number, 58)
        encoded = ALPHABET[rem] + encoded
    leading = len(data) - len(data.lstrip(b"\x00"))
    return "1" * leading + (encoded or "")


SIGNATURE = _b58(bytes(range(64)))
ASSET = _b58(bytes([7]) * 32)
SENDER = _b58(bytes([8]) * 32)
RECIPIENT = _b58(bytes([9]) * 32)
SOURCE_ACCOUNT = _b58(bytes([10]) * 32)
DEST_ACCOUNT = _b58(bytes([11]) * 32)
OBSERVED_AT = "2026-09-10T13:00:00Z"


def _promoted_capabilities():
    value = deepcopy(_capabilities())
    value["contract_version"] = "1.28.0"
    value["response_freshness"] = {
        "contract_version": "cmis_response_freshness/v1",
        "required_on_every_public_response": True,
        "observation_time_alone_never_proves_provider_fact_freshness": True,
        "missing_service_specific_freshness_fails_closed": True,
    }
    value["supported_services"].append("wallet_relationship_intelligence")
    capability = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": WALLET_RELATIONSHIP_CONTRACT_VERSION,
        "request_contract_version": "wallet_relationship_intelligence_request/v1",
        "materialization_contract_version": "x1_direct_wallet_transfer_materialization/v1",
        "requirements": list(WALLET_RELATIONSHIP_REQUIRED_REQUIREMENTS),
        "limitations": list(WALLET_RELATIONSHIP_REQUIRED_LIMITATIONS),
        "observed_relationships_only": True,
        "ownership_inference_authorized": False,
        "beneficial_ownership_inference_authorized": False,
        "behavior_or_intent_inference_authorized": False,
        "risk_inference_authorized": False,
        "complete_history_claim_authorized": False,
        "complete_graph_coverage_claim_authorized": False,
        "evidence_receipt_binding_available": False,
        "proof_score_binding_available": False,
        "proof_score_separate_from_risk": True,
        "execution_authorized": False,
    }
    x1 = value["chains"]["x1"]
    x1["services"]["wallet_relationship_intelligence"] = capability
    x1["callable_services"].append("wallet_relationship_intelligence")
    solana = value["chains"]["solana"]
    solana["services"]["wallet_relationship_intelligence"] = {
        "state": "unavailable",
        "callable": False,
        "requirements": [],
        "limitations": ["wallet_relationship_intelligence_not_available_for_chain"],
    }
    return value


def _request():
    return normalize_wallet_relationship_request(
        chain="x1",
        transaction_signature=SIGNATURE,
        asset_mint=ASSET,
        sender_wallet=SENDER,
        recipient_wallet=RECIPIENT,
    )


def _envelope():
    return {
        "service": "wallet_relationship_intelligence",
        "chain": "x1",
        "status": "ok",
        "asset": {"id": ASSET, "id_kind": "mint"},
        "data": {
            "contract_version": "wallet_relationship_intelligence/v1",
            "relationship_kind": "observed_direct_interaction",
            "interaction_type": "verified_token_transfer",
            "asset_mint": ASSET,
            "sender_wallet": SENDER,
            "recipient_wallet": RECIPIENT,
            "transaction_signature": SIGNATURE,
            "observed_at": OBSERVED_AT,
            "block_slot": 123456,
            "amount_raw": "1250000",
            "decimals": 6,
            "source_token_account": SOURCE_ACCOUNT,
            "destination_token_account": DEST_ACCOUNT,
            "relationship_evidence_id": "wr_" + "a" * 64,
            "wallet_activity_observation_id": "wa_" + "b" * 64,
            "evidence_scope": "exact_finalized_x1_transaction",
            "evidence_receipt_binding_available": False,
            "proof_score_binding_available": False,
            "proof_strength_separate_from_risk": True,
            "ownership_inference_added": False,
            "beneficial_ownership_inference_added": False,
            "behavioral_interpretation_added": False,
            "intent_interpretation_added": False,
            "risk_interpretation": None,
            "complete_history_claimed": False,
            "complete_graph_coverage_claimed": False,
            "execution_authorized": False,
            "limitations": [
                "observed_direct_interaction_only",
                "ownership_not_inferred",
                "beneficial_ownership_not_inferred",
                "behavior_intent_and_risk_not_inferred",
                "complete_wallet_history_not_proven",
                "complete_relationship_graph_not_proven",
                "missing_amounts_are_not_zero_filled",
            ],
        },
        "risk": None,
        "confidence": {
            "proof_score_available": False,
            "proof_score_separate_from_risk": True,
            "basis": "deterministically_revalidated_direct_transfer_evidence",
        },
        "sources": [{"source": "X1 RPC", "transaction_signature": SIGNATURE}],
        "observed_at": OBSERVED_AT,
        "freshness": {
            "contract_version": "cmis_response_freshness/v1",
            "scope": "wallet_relationship_intelligence.response",
            "state": "NOT_APPLICABLE",
            "freshness_verified": None,
            "observed_at": OBSERVED_AT,
            "details": {},
            "reason": "historical_finalized_transaction_fact",
        },
        "warnings": ["observed_direct_interaction_only"],
        "errors": [],
        "execution_authorized": False,
    }


def test_capability_requires_exact_cmis_128_wallet_relationship_promotion():
    manifest = validate_capability_manifest(_promoted_capabilities())
    capability = require_wallet_relationship_capability(manifest)
    assert WALLET_RELATIONSHIP_MIN_CMIS_CONTRACT_VERSION == "1.28.0"
    assert capability["state"] == "bounded"
    assert capability["read_only"] is True
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["observed_relationships_only"] is True
    assert capability["ownership_inference_authorized"] is False
    assert capability["risk_inference_authorized"] is False
    assert capability["execution_authorized"] is False


def test_capability_rejects_missing_complete_history_guardrail():
    raw = _promoted_capabilities()
    raw["chains"]["x1"]["services"]["wallet_relationship_intelligence"]["limitations"].remove(
        "relationship_is_transaction_scoped_not_complete_history"
    )
    manifest = validate_capability_manifest(raw)
    with pytest.raises(CMISCapabilityContractError, match="missing accepted limitations"):
        require_wallet_relationship_capability(manifest)


def test_request_normalization_is_exact_and_rejects_same_wallet():
    request = _request()
    assert request == {
        "contract_version": "wallet_relationship_intelligence_request/v1",
        "chain": "x1",
        "transaction_signature": SIGNATURE,
        "asset_mint": ASSET,
        "sender_wallet": SENDER,
        "recipient_wallet": RECIPIENT,
    }
    with pytest.raises(CMISWalletRelationshipContractError, match="distinct"):
        normalize_wallet_relationship_request(
            chain="x1",
            transaction_signature=SIGNATURE,
            asset_mint=ASSET,
            sender_wallet=SENDER,
            recipient_wallet=SENDER,
        )


def test_response_preserves_one_exact_transfer_and_rejects_authority_drift():
    accepted = validate_wallet_relationship_response(_envelope(), expected_request=_request())
    data = accepted["data"]
    assert data["transaction_signature"] == SIGNATURE
    assert data["sender_wallet"] == SENDER
    assert data["recipient_wallet"] == RECIPIENT
    assert data["amount_raw"] == "1250000"
    assert data["ownership_inference_added"] is False
    assert data["complete_history_claimed"] is False
    assert accepted["risk"] is None
    for field, value in (
        ("ownership_inference_added", True),
        ("complete_history_claimed", True),
        ("execution_authorized", True),
    ):
        bad = _envelope()
        bad["data"][field] = value
        with pytest.raises(CMISWalletRelationshipContractError):
            validate_wallet_relationship_response(bad, expected_request=_request())
    bad_risk = _envelope()
    bad_risk["risk"] = {"level": "HIGH"}
    with pytest.raises(CMISWalletRelationshipContractError, match="must not add risk"):
        validate_wallet_relationship_response(bad_risk, expected_request=_request())


def test_http_posts_selector_only_shape_without_outer_asset_or_caller_facts():
    expected = _envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        result = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2).wallet_relationship_intelligence(
            chain="x1",
            transaction_signature=SIGNATURE,
            asset_mint=ASSET,
            sender_wallet=SENDER,
            recipient_wallet=RECIPIENT,
        )
    assert result == expected
    assert running.requests == [{
        "service": "wallet_relationship_intelligence",
        "chain": "x1",
        "params": {
            "contract_version": "wallet_relationship_intelligence_request/v1",
            "transaction_signature": SIGNATURE,
            "asset_mint": ASSET,
            "sender_wallet": SENDER,
            "recipient_wallet": RECIPIENT,
        },
    }]
    assert "asset" not in running.requests[0]
    assert "amount_raw" not in running.requests[0]["params"]
    assert "risk" not in running.requests[0]["params"]


def test_http_fails_closed_before_cmis_128_without_post():
    capabilities = _promoted_capabilities()
    capabilities["contract_version"] = "1.27.0"
    with _Server(_envelope(), capabilities=capabilities) as running:
        result = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2).wallet_relationship_intelligence(
            chain="x1",
            transaction_signature=SIGNATURE,
            asset_mint=ASSET,
            sender_wallet=SENDER,
            recipient_wallet=RECIPIENT,
        )
    assert result["status"] == "unavailable"
    assert running.requests == []


def test_x1_scout_projection_and_human_text_do_not_widen_one_transfer():
    source = _envelope()
    product = build_x1_wallet_relationship_intelligence(source, expected_request=_request())
    assert product["contract_version"] == X1_WALLET_RELATIONSHIP_CONTRACT
    assert product["wallet_relationship_intelligence"] == source["data"]
    assert product["relationship_scope_is_one_selected_finalized_transaction"] is True
    assert product["common_ownership_claim_authorized"] is False
    assert product["whale_insider_bot_market_maker_claim_authorized"] is False
    assert product["causality_claim_authorized"] is False
    assert product["risk_severity_claim_authorized"] is False
    assert product["complete_wallet_history_claim_authorized"] is False
    assert product["execution_authorized"] is False
    text = render_x1_wallet_relationship_text(product)
    assert "CMIS verified a direct X1 token transfer" in text
    assert "selected finalized transfer only" in text
    assert "does not prove common ownership" in text
    assert "complete wallet history" in text


def test_public_scout_wiring_is_explicit_and_skips_identity_side_call():
    graph = Path("src/roberta/x1_scout/graph.py").read_text()
    tool = Path("src/roberta/x1_scout/tool.py").read_text()
    state = Path("src/roberta/x1_scout/state.py").read_text()
    client = Path("src/roberta/cmis/client.py").read_text()
    contracts = Path("src/roberta/cmis/contracts.py").read_text()
    assert 'if operation == "wallet_relationship_intelligence":' in graph
    assert "require_wallet_relationship_capability(" in graph
    assert "cmis_client.wallet_relationship_intelligence(" in graph
    assert '"wallet_relationship_intelligence" not in operations' in graph
    assert 'report["x1_wallet_relationship_intelligence"]' in graph
    assert 'report["x1_wallet_relationship_text"]' in graph
    assert '"wallet_relationship_intelligence",' in tool
    assert "wallet_relationship_transaction_signature: str | None = None" in tool
    assert "wallet relationship asset must equal the exact X1 asset mint" in tool
    assert "must not turn it into" in tool
    assert "wallet_relationship_transaction_signature: NotRequired[str]" in state
    assert "x1_wallet_relationship_intelligence: NotRequired" in state
    assert "def wallet_relationship_intelligence(" in client
    assert '"wallet_relationship_intelligence",' in contracts
