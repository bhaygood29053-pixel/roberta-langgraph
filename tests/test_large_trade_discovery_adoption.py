from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    LARGE_TRADE_DISCOVERY_CONTRACT_VERSION,
    LARGE_TRADE_DISCOVERY_MIN_CMIS_CONTRACT_VERSION,
    LARGE_TRADE_DISCOVERY_REQUIRED_LIMITATIONS,
    LARGE_TRADE_DISCOVERY_REQUIRED_REQUIREMENTS,
    require_large_trade_discovery_capability,
    validate_capability_manifest,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.large_trade_discovery import (
    CMISLargeTradeDiscoveryContractError,
    RANKING_SCOPE,
    normalize_large_trade_discovery_request,
    validate_large_trade_discovery_response,
)
from roberta.x1_scout.large_trade_discovery import (
    LARGE_TRADE_DISCOVERY_CONTRACT,
    build_x1_large_trade_discovery,
)
from tests.test_cmis_http_client import _Server, _capabilities


ASSET = "AssetMint1111111111111111111111111111111111"
POOL_A = "Pool111111111111111111111111111111111111"
POOL_B = "Pool222222222222222222222222222222222222"
QUOTE = "QuoteMint111111111111111111111111111111111"
END = "1788696000"
START = "1788609600"


def _promoted_capabilities():
    value = deepcopy(_capabilities())
    value["contract_version"] = "1.25.0"
    value["supported_services"].append("large_trade_discovery")
    x1 = value["chains"]["x1"]
    x1["services"]["large_trade_discovery"] = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": LARGE_TRADE_DISCOVERY_CONTRACT_VERSION,
        "requirements": list(LARGE_TRADE_DISCOVERY_REQUIRED_REQUIREMENTS),
        "limitations": list(LARGE_TRADE_DISCOVERY_REQUIRED_LIMITATIONS),
        "execution_authorized": False,
    }
    x1["callable_services"].append("large_trade_discovery")
    solana = value["chains"]["solana"]
    solana["services"]["large_trade_discovery"] = {
        "state": "unavailable",
        "callable": False,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "service_contract_version": LARGE_TRADE_DISCOVERY_CONTRACT_VERSION,
        "requirements": [],
        "limitations": ["large_trade_discovery_not_available_for_chain"],
        "execution_authorized": False,
    }
    return value


def _request():
    return normalize_large_trade_discovery_request(
        asset_mint=ASSET,
        direction="BUY",
        limit=2,
    )


def _row(
    rank,
    signature,
    slot,
    pool,
    usd,
    *,
    wallet=None,
    evidence_id=None,
):
    wallet_verified = wallet is not None
    handoff_ready = wallet_verified and evidence_id is not None
    return {
        "rank": rank,
        "transaction_signature": signature,
        "slot": slot,
        "block_time": str(1788609600 + slot),
        "pool_address": pool,
        "direction": "BUY",
        "asset_mint": ASSET,
        "asset_amount": str(1000 * rank),
        "quote_mint": QUOTE,
        "quote_amount": str(100 * rank),
        "verified_usd_notional": str(usd),
        "usd_notional_verified": True,
        "wallet_address": wallet,
        "wallet_attribution_verified": wallet_verified,
        "real_world_wallet_owner_verified": False,
        "wallet_fact_time": (
            "2026-09-06T12:00:00Z" if wallet_verified else None
        ),
        "trade_price_impact_evidence_id": evidence_id,
        "trade_price_impact_handoff_ready": handoff_ready,
    }


def _envelope():
    return {
        "service": "large_trade_discovery",
        "chain": "x1",
        "status": "ok",
        "asset": {"canonical_id": ASSET, "mint": ASSET},
        "data": {
            "contract_version": LARGE_TRADE_DISCOVERY_CONTRACT_VERSION,
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "read_only": True,
            "ranking_metric": "verified_historical_usd_notional",
            "ranking_order": (
                "usd_notional_desc_then_slot_asc_then_signature_then_pool"
            ),
            "ranking_scope": RANKING_SCOPE,
            "requested_direction": "BUY",
            "requested_limit": 2,
            "requested_window": {
                "start_epoch": START,
                "end_epoch": END,
                "duration_seconds": "86400",
            },
            "evaluated_at": END,
            "pool_scope": {
                "contract_version": "x1_ninja_current_pool_scope/v1",
                "pool_addresses": [POOL_A, POOL_B],
                "pool_count": 2,
                "provider_scoped_pool_universe_verified": True,
                "global_xdex_pool_universe_verified": False,
            },
            "exact_swap_count_examined": 4,
            "eligible_trade_count": 3,
            "result_count": 2,
            "ranking_complete_for_scope": True,
            "results": [
                _row(
                    1,
                    "buy-big",
                    20,
                    POOL_A,
                    500,
                    wallet="Wallet11111111111111111111111111111111111",
                    evidence_id="tpi:buy-big",
                ),
                _row(
                    2,
                    "buy-mid",
                    40,
                    POOL_B,
                    300,
                    evidence_id="tpi:buy-mid",
                ),
            ],
            "evidence_boundaries": {
                "global_x1_dex_trade_ranking_authorized": False,
                "wallet_owner_identity_inference_authorized": False,
                "whale_insider_manipulator_label_authorized": False,
                "intent_inference_authorized": False,
                "coordinated_wallet_inference_authorized": False,
                "whole_market_price_impact_claim_authorized": False,
                "volume_causality_claim_authorized": False,
                "automatic_risk_conclusion_authorized": False,
                "trade_recommendation_authorized": False,
                "source_independence_verified": False,
            },
            "execution_authorized": False,
        },
        "risk": None,
        "confidence": {
            "ranking_complete_for_scope": True,
            "pool_scope_verified": True,
            "window_coverage_verified": True,
            "usd_notional_basis_verified": True,
            "wallet_attribution_complete_for_results": False,
            "source_independence_verified": False,
        },
        "sources": [{
            "source": "CMIS verified X1 pool-scope + exact pool 24h windows",
            "scope": RANKING_SCOPE,
            "pool_count": 2,
        }],
        "observed_at": END,
        "warnings": [{
            "code": "provider_scoped_pool_universe_only",
            "message": "Not every X1 DEX.",
        }],
        "errors": [],
    }


def test_cmis_125_large_trade_capability_is_exact_and_scout_promoted():
    manifest = validate_capability_manifest(_promoted_capabilities())
    capability = require_large_trade_discovery_capability(manifest)

    assert LARGE_TRADE_DISCOVERY_MIN_CMIS_CONTRACT_VERSION == "1.25.0"
    assert capability["service_contract_version"] == (
        "large_trade_discovery/v1"
    )
    assert capability["state"] == "bounded"
    assert capability["read_only"] is True
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["execution_authorized"] is False


def test_capability_rejects_missing_not_global_guardrail():
    raw = _promoted_capabilities()
    raw["chains"]["x1"]["services"]["large_trade_discovery"][
        "limitations"
    ].remove("global_x1_dex_trade_ranking_not_authorized")
    manifest = validate_capability_manifest(raw)

    with pytest.raises(
        CMISCapabilityContractError,
        match="missing accepted limitations",
    ):
        require_large_trade_discovery_capability(manifest)


def test_response_preserves_ranked_transactions_and_handoff_without_recompute():
    accepted = validate_large_trade_discovery_response(
        _envelope(),
        expected_request=_request(),
    )
    data = accepted["data"]

    assert data["ranking_scope"] == RANKING_SCOPE
    assert [row["rank"] for row in data["results"]] == [1, 2]
    assert [
        row["transaction_signature"] for row in data["results"]
    ] == ["buy-big", "buy-mid"]
    assert [
        row["verified_usd_notional"] for row in data["results"]
    ] == ["500", "300"]
    assert data["results"][0]["wallet_attribution_verified"] is True
    assert data["results"][0]["real_world_wallet_owner_verified"] is False
    assert data["results"][0]["trade_price_impact_evidence_id"] == (
        "tpi:buy-big"
    )
    assert data["results"][0]["trade_price_impact_handoff_ready"] is True
    assert data["results"][1]["wallet_address"] is None
    assert data["results"][1]["trade_price_impact_evidence_id"] == "tpi:buy-mid"
    assert data["results"][1]["trade_price_impact_handoff_ready"] is False
    assert data["evidence_boundaries"][
        "global_x1_dex_trade_ranking_authorized"
    ] is False
    assert accepted["risk"] is None


def test_response_rejects_noncanonical_order_instead_of_resorting():
    bad = _envelope()
    bad["data"]["results"][0]["verified_usd_notional"] = "250"
    bad["data"]["results"][1]["verified_usd_notional"] = "300"

    with pytest.raises(
        CMISLargeTradeDiscoveryContractError,
        match="rank/order is not canonical",
    ):
        validate_large_trade_discovery_response(
            bad,
            expected_request=_request(),
        )


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda value: value["data"]["pool_scope"].__setitem__(
                "global_xdex_pool_universe_verified",
                True,
            ),
            "global XDEX pool universe",
        ),
        (
            lambda value: value["data"]["evidence_boundaries"].__setitem__(
                "global_x1_dex_trade_ranking_authorized",
                True,
            ),
            "evidence boundary drift",
        ),
        (
            lambda value: value["data"]["results"][0].__setitem__(
                "real_world_wallet_owner_verified",
                True,
            ),
            "real-world owner identity",
        ),
        (
            lambda value: value.__setitem__(
                "risk",
                {"level": "LOW"},
            ),
            "risk conclusion",
        ),
    ],
)
def test_response_fails_closed_on_scope_identity_or_risk_drift(
    mutator,
    match,
):
    bad = _envelope()
    mutator(bad)
    with pytest.raises(CMISLargeTradeDiscoveryContractError, match=match):
        validate_large_trade_discovery_response(
            bad,
            expected_request=_request(),
        )


def test_http_client_posts_only_exact_mint_direction_and_limit():
    expected = _envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).large_trade_discovery(
            chain="x1",
            asset_mint=ASSET,
            direction="BUY",
            limit=2,
        )

    assert result == expected
    assert running.requests == [{
        "service": "large_trade_discovery",
        "chain": "x1",
        "asset": ASSET,
        "params": _request(),
    }]


def test_http_client_blocks_before_cmis_125_without_post():
    capabilities = _promoted_capabilities()
    capabilities["contract_version"] = "1.24.0"

    with _Server(_envelope(), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).large_trade_discovery(
            chain="x1",
            asset_mint=ASSET,
            direction="BUY",
            limit=2,
        )

    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == (
        "cmis_large_trade_discovery_contract_unavailable"
    )
    assert running.requests == []


def test_x1_scout_product_preserves_cmis_ranking_verbatim():
    source = _envelope()
    product = build_x1_large_trade_discovery(
        source,
        expected_request=_request(),
    )

    assert product["contract_version"] == LARGE_TRADE_DISCOVERY_CONTRACT
    assert product["large_trade_discovery"] == source["data"]
    assert product["provider_scoped_ranking_is_global_x1_dex_ranking"] is False
    assert product["wallet_address_is_real_world_identity"] is False
    assert product["whale_insider_manipulator_label_authorized"] is False
    assert product["whole_market_price_impact_claim_authorized"] is False
    assert product["automatic_risk_conclusion_authorized"] is False
    assert product["trade_recommendation_authorized"] is False
    assert product["risk_interpretation"] is None
    assert product["execution_authorized"] is False


def test_public_x1_scout_wiring_preserves_cmis_rank_and_exact_selectors():
    graph = Path("src/roberta/x1_scout/graph.py").read_text()
    tool = Path("src/roberta/x1_scout/tool.py").read_text()
    state = Path("src/roberta/x1_scout/state.py").read_text()
    client = Path("src/roberta/cmis/client.py").read_text()

    assert 'if operation == "large_trade_discovery":' in graph
    assert "require_large_trade_discovery_capability(" in graph
    assert "cmis_client.large_trade_discovery(" in graph
    assert '"large_trade_discovery" not in operations' in graph
    assert 'report["x1_large_trade_discovery"]' in graph
    assert "build_x1_large_trade_discovery(" in graph

    assert '"large_trade_discovery",' in tool
    assert "large_trade_asset_mint: str | None = None" in tool
    assert "large_trade_direction: str | None = None" in tool
    assert "large_trade_limit: int | None = None" in tool
    assert "large-trade discovery asset must equal the exact X1 asset mint" in tool
    assert "Preserve " in tool
    assert "CMIS ranking order" in tool
    assert "whale/insider/manipulator labels" in tool

    assert "large_trade_asset_mint: NotRequired[str]" in state
    assert "large_trade_direction: NotRequired[str]" in state
    assert "large_trade_limit: NotRequired[int]" in state
    assert "x1_large_trade_discovery: NotRequired" in state

    assert "def large_trade_discovery(" in client
    assert "asset_mint: str" in client
    assert 'direction: str = "ANY"' in client
    assert "limit: int = 5" in client
