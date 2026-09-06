from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    TRADE_PRICE_IMPACT_CONTRACT_VERSION,
    TRADE_PRICE_IMPACT_MIN_CMIS_CONTRACT_VERSION,
    TRADE_PRICE_IMPACT_REQUIRED_LIMITATIONS,
    TRADE_PRICE_IMPACT_REQUIRED_REQUIREMENTS,
    require_trade_price_impact_capability,
    validate_capability_manifest,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.trade_price_impact import (
    CMISTradePriceImpactContractError,
    normalize_trade_price_impact_request,
    validate_trade_price_impact_response,
)
from roberta.x1_scout.trade_price_impact import (
    TRADE_PRICE_IMPACT_CONTRACT,
    build_x1_trade_price_impact_intelligence,
)
from tests.test_cmis_http_client import _Server, _capabilities


ASSET = "AssetMint1111111111111111111111111111111111"
EVIDENCE = "trade-evidence-001"
WALLET = "Wallet11111111111111111111111111111111111"
POOL = "Pool111111111111111111111111111111111111"
TARGET = "TargetSig111111111111111111111111111111111"
NEXT = "NextSig2222222222222222222222222222222222"


def _promoted_capabilities():
    value = deepcopy(_capabilities())
    value["contract_version"] = "1.24.0"
    value["supported_services"].append("trade_price_impact_intelligence")
    x1 = value["chains"]["x1"]
    x1["services"]["trade_price_impact_intelligence"] = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": TRADE_PRICE_IMPACT_CONTRACT_VERSION,
        "requirements": list(TRADE_PRICE_IMPACT_REQUIRED_REQUIREMENTS),
        "limitations": list(TRADE_PRICE_IMPACT_REQUIRED_LIMITATIONS),
        "execution_authorized": False,
    }
    x1["callable_services"].append("trade_price_impact_intelligence")
    solana = value["chains"]["solana"]
    solana["services"]["trade_price_impact_intelligence"] = {
        "state": "unavailable",
        "callable": False,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "service_contract_version": TRADE_PRICE_IMPACT_CONTRACT_VERSION,
        "requirements": [],
        "limitations": [
            "trade_price_impact_intelligence_not_available_for_chain"
        ],
        "execution_authorized": False,
    }
    return value


def _request():
    return normalize_trade_price_impact_request(
        evidence_id=EVIDENCE,
        asset_mint=ASSET,
    )


def _envelope():
    return {
        "service": "trade_price_impact_intelligence",
        "chain": "x1",
        "status": "ok",
        "asset": {"canonical_id": ASSET, "mint": ASSET},
        "data": {
            "contract_version": TRADE_PRICE_IMPACT_CONTRACT_VERSION,
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "read_only": True,
            "wallet_trade": {
                "wallet_address": WALLET,
                "real_world_identity_verified": False,
                "transaction_signature": TARGET,
                "slot": 100,
                "fact_time": "2026-09-06T12:00:00Z",
                "requested_asset_mint": ASSET,
                "direction": "BUY",
                "wallet_trade_amount_attribution_verified": True,
                "asset_amount": "4200000",
                "quote_amount": "218.4",
                "amount_basis": (
                    "single_recognized_amm_transaction_plus_exact_selected_pool_vault_deltas"
                ),
            },
            "pool": {
                "pool_address": POOL,
                "transaction_pool_membership_verified": True,
                "single_recognized_amm_attribution_verified": True,
                "pre_trade_asset_reserve": "10000000",
                "pre_trade_quote_reserve": "480",
                "post_trade_asset_reserve": "5800000",
                "post_trade_quote_reserve": "698.4",
                "pre_trade_spot_price_native": "0.000048",
                "average_execution_price_native": "0.000052",
                "post_trade_spot_price_native": "0.0001204137931034482758620689655",
                "spot_price_change_percent": "150.8620689655172413793103448",
                "execution_price_impact_percent_vs_pre_spot": "8.333333333333333333333333333",
                "pool_local_state_transition_verified": True,
            },
            "next_verified_trade": {
                "verified": True,
                "reason": "strictly_next_verified_exact_pool_swap_by_rpc_slot",
                "signature": NEXT,
                "slot": 101,
                "block_time": 1788696011,
                "execution_price_native": "0.0001200",
            },
            "measured_window": {
                "scope": "exact_selected_pool_rolling_24h",
                "requested_window": {
                    "start_epoch": "1788609600",
                    "end_epoch": "1788696000",
                    "duration_seconds": "86400",
                },
                "trade_usd_notional": "18400",
                "verified_window_volume_usd": "59354.83870967741935483870968",
                "trade_volume_contribution_percent": "31.0",
                "numerator_denominator_same_verified_usd_basis": True,
                "window_coverage_verified": True,
            },
            "evidence_boundaries": {
                "wallet_owner_identity_inference_authorized": False,
                "whale_insider_manipulator_label_authorized": False,
                "intent_inference_authorized": False,
                "coordinated_wallet_inference_authorized": False,
                "whole_market_price_impact_claim_authorized": False,
                "volume_causality_claim_authorized": False,
                "automatic_risk_conclusion_authorized": False,
                "trade_recommendation_authorized": False,
                "pool_local_causal_state_transition_authorized": True,
                "source_independence_verified": False,
            },
            "execution_authorized": False,
        },
        "risk": None,
        "confidence": {
            "wallet_transaction_direction_verified": True,
            "single_pool_amount_attribution_verified": True,
            "pool_state_transition_verified": True,
            "measured_window_volume_contribution_verified": True,
            "next_trade_execution_price_verified": True,
        },
        "sources": [{
            "source": "X1 RPC + accepted XDEX/X1.Ninja CMIS evidence",
            "scope": "single_exact_x1_pool_transaction_and_verified_pool_window",
            "transaction_signature": TARGET,
            "pool_address": POOL,
        }],
        "observed_at": "2026-09-06T12:00:00Z",
        "warnings": [{
            "code": "pool_local_scope_only",
            "message": "Exact selected pool only.",
        }],
        "errors": [],
        "execution_authorized": False,
    }


def test_cmis_124_trade_price_impact_capability_is_exact_and_bounded():
    manifest = validate_capability_manifest(_promoted_capabilities())
    capability = require_trade_price_impact_capability(manifest)

    assert TRADE_PRICE_IMPACT_MIN_CMIS_CONTRACT_VERSION == "1.24.0"
    assert capability["service_contract_version"] == (
        "trade_price_impact_intelligence/v1"
    )
    assert capability["state"] == "bounded"
    assert capability["read_only"] is True
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["execution_authorized"] is False


def test_trade_price_impact_capability_rejects_causality_guardrail_drift():
    raw = _promoted_capabilities()
    raw["chains"]["x1"]["services"]["trade_price_impact_intelligence"][
        "limitations"
    ].remove("pool_local_price_impact_is_not_whole_market_price_impact")
    manifest = validate_capability_manifest(raw)

    with pytest.raises(
        CMISCapabilityContractError,
        match="missing accepted limitations",
    ):
        require_trade_price_impact_capability(manifest)


def test_trade_price_impact_response_preserves_verified_facts_and_boundaries():
    accepted = validate_trade_price_impact_response(
        _envelope(),
        expected_request=_request(),
    )
    data = accepted["data"]

    assert data["wallet_trade"]["wallet_address"] == WALLET
    assert data["wallet_trade"]["transaction_signature"] == TARGET
    assert data["wallet_trade"]["direction"] == "BUY"
    assert data["wallet_trade"]["asset_amount"] == "4200000"
    assert data["pool"]["pre_trade_spot_price_native"] == "0.000048"
    assert data["pool"]["average_execution_price_native"] == "0.000052"
    assert data["pool"]["post_trade_spot_price_native"] == (
        "0.0001204137931034482758620689655"
    )
    assert data["next_verified_trade"]["execution_price_native"] == "0.0001200"
    assert data["measured_window"]["trade_volume_contribution_percent"] == "31.0"
    assert data["evidence_boundaries"][
        "pool_local_causal_state_transition_authorized"
    ] is True
    assert data["evidence_boundaries"][
        "whole_market_price_impact_claim_authorized"
    ] is False
    assert accepted["risk"] is None
    assert accepted["execution_authorized"] is False


@pytest.mark.parametrize(
    ("path", "value", "match"),
    [
        (
            ("data", "wallet_trade", "real_world_identity_verified"),
            True,
            "real-world identity",
        ),
        (
            (
                "data",
                "evidence_boundaries",
                "whole_market_price_impact_claim_authorized",
            ),
            True,
            "boundary drift",
        ),
        (
            (
                "data",
                "evidence_boundaries",
                "trade_recommendation_authorized",
            ),
            True,
            "boundary drift",
        ),
    ],
)
def test_trade_price_impact_response_fails_closed_on_identity_or_scope_drift(
    path,
    value,
    match,
):
    bad = _envelope()
    target = bad
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    with pytest.raises(CMISTradePriceImpactContractError, match=match):
        validate_trade_price_impact_response(
            bad,
            expected_request=_request(),
        )


def test_http_client_posts_only_cmis_selector_and_exact_mint():
    expected = _envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).trade_price_impact_intelligence(
            chain="x1",
            evidence_id=EVIDENCE,
            asset_mint=ASSET,
        )

    assert result == expected
    assert running.requests == [{
        "service": "trade_price_impact_intelligence",
        "chain": "x1",
        "asset": ASSET,
        "params": _request(),
    }]


def test_http_client_blocks_trade_price_impact_before_cmis_124_without_post():
    capabilities = _promoted_capabilities()
    capabilities["contract_version"] = "1.23.0"

    with _Server(_envelope(), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).trade_price_impact_intelligence(
            chain="x1",
            evidence_id=EVIDENCE,
            asset_mint=ASSET,
        )

    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == (
        "cmis_trade_price_impact_contract_unavailable"
    )
    assert running.requests == []


def test_x1_scout_product_preserves_cmis_projection_without_recomputation():
    product = build_x1_trade_price_impact_intelligence(
        _envelope(),
        expected_request=_request(),
    )

    assert product["contract_version"] == TRADE_PRICE_IMPACT_CONTRACT
    assert product["trade_price_impact"] == _envelope()["data"]
    assert product["wallet_address_is_real_world_identity"] is False
    assert product["whale_insider_manipulator_label_authorized"] is False
    assert product["whole_market_price_impact_claim_authorized"] is False
    assert product["volume_causality_claim_authorized"] is False
    assert product["automatic_risk_conclusion_authorized"] is False
    assert product["trade_recommendation_authorized"] is False
    assert product["pool_local_state_transition_authorized"] is True
    assert product["risk_interpretation"] is None
    assert product["execution_authorized"] is False


def test_public_x1_scout_wiring_preserves_explicit_cmis_124_operation():
    graph = Path("src/roberta/x1_scout/graph.py").read_text()
    tool = Path("src/roberta/x1_scout/tool.py").read_text()
    state = Path("src/roberta/x1_scout/state.py").read_text()
    client = Path("src/roberta/cmis/client.py").read_text()

    assert 'if operation == "trade_price_impact_intelligence":' in graph
    assert "require_trade_price_impact_capability(" in graph
    assert "cmis_client.trade_price_impact_intelligence(" in graph
    assert '"trade_price_impact_intelligence" not in operations' in graph
    assert 'report["x1_trade_price_impact_intelligence"]' in graph
    assert "build_x1_trade_price_impact_intelligence(" in graph

    assert '"trade_price_impact_intelligence",' in tool
    assert "trade_price_impact_evidence_id: str | None = None" in tool
    assert "trade_price_impact_asset_mint: str | None = None" in tool
    assert "trade price-impact asset must equal the exact X1 asset mint" in tool
    assert "Never infer real-world wallet identity" in tool
    assert "whole-market price impact" in tool

    assert "trade_price_impact_evidence_id: NotRequired[str]" in state
    assert "trade_price_impact_asset_mint: NotRequired[str]" in state
    assert "x1_trade_price_impact_intelligence: NotRequired" in state

    assert "def trade_price_impact_intelligence(" in client
    assert "evidence_id: str" in client
    assert "asset_mint: str" in client

