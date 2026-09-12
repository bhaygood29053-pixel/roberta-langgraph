from __future__ import annotations

from copy import deepcopy

import pytest

from roberta.cmis.xdex_multi_hop_route_snapshot import (
    CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT,
    CMISXDEXMultiHopRouteSnapshotError,
    validate_xdex_multi_hop_route_snapshot,
)
from roberta.x1_scout.smart_route_intelligence import (
    X1_SMART_ROUTE_CONTRACT,
    X1SmartRouteContractError,
    build_x1_smart_route_intelligence,
)

MINT_A = "So11111111111111111111111111111111111111112"
MINT_B = "33kzreZb3DnzBrcbdeiWhGtdc8aU1uxqb2mMTii2hNGq"
MINT_C = "GdgA3rcAzWsrtt8QkyNXNTrrvfRPeAYiJPyyxSku8pzk"


def _hop(
    index: int,
    token_in: str,
    token_out: str,
    amount_in: int,
    amount_out: int,
    *,
    pool: str,
    config: str,
    slot: int,
    trade_fee: int,
) -> dict[str, object]:
    return {
        "index": index,
        "venue": "xdex",
        "pool": pool,
        "token_in_mint": token_in,
        "token_out_mint": token_out,
        "amm_config": config,
        "pool_context_slot": slot,
        "config_context_slot": slot + 1,
        "amount_in_raw": amount_in,
        "expected_output_raw": amount_out,
        "active_reserve_in_raw": 100_000_000 + index,
        "active_reserve_out_raw": 200_000_000 + index,
        "trade_fee_rate_ppm": 2_800,
        "reconstructed_trade_fee_raw": trade_fee,
        "reconstructed_creator_fee_raw": 0,
        "protocol_fee_rate_ppm_of_trade_fee": 120_000,
        "fund_fee_rate_ppm_of_trade_fee": 40_000,
        "creator_fee_rate_ppm": 0,
        "pool_identity_verified": True,
        "pool_state_verified": True,
        "venue_identity_verified": True,
        "reserve_math_verified": True,
        "fee_math_verified": True,
        "price_impact_verified": False,
        "minimum_received_bounded": False,
        "execution_authorized": False,
    }


def _snapshot() -> dict[str, object]:
    hops = [
        _hop(
            0,
            MINT_A,
            MINT_B,
            1_000_000,
            900_000,
            pool="pool-one",
            config="config-one",
            slot=100,
            trade_fee=2_800,
        ),
        _hop(
            1,
            MINT_B,
            MINT_C,
            900_000,
            800_000,
            pool="pool-two",
            config="config-two",
            slot=102,
            trade_fee=2_520,
        ),
    ]
    return {
        "contract_version": CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT,
        "chain": "x1",
        "status": "ok",
        "input_mint": MINT_A,
        "output_mint": MINT_C,
        "input_amount_raw": 1_000_000,
        "gross_output_raw": 800_000,
        "net_output_raw": 796_000,
        "hop_count": 2,
        "path": [MINT_A, MINT_B, MINT_C],
        "hops": hops,
        "observation_window": {
            "slot_min": 100,
            "slot_max": 104,
            "slot_span": 4,
            "max_slot_span": 8,
            "current_state_alignment_verified": True,
            "provider_fact_time_verified": False,
        },
        "route_output": {
            "gross_output_raw": 800_000,
            "aggregate_hop_output_verified": True,
        },
        "pool_fee_evidence": [
            {
                "hop_index": 0,
                "input_mint": MINT_A,
                "trade_fee_rate_ppm": 2_800,
                "reconstructed_trade_fee_raw": 2_800,
                "reconstructed_creator_fee_raw": 0,
                "fee_math_verified": True,
            },
            {
                "hop_index": 1,
                "input_mint": MINT_B,
                "trade_fee_rate_ppm": 2_800,
                "reconstructed_trade_fee_raw": 2_520,
                "reconstructed_creator_fee_raw": 0,
                "fee_math_verified": True,
            },
        ],
        "provider_routing_fee_transform": {
            "fee_bps": 50,
            "fee_amount_raw": 4_000,
            "net_output_raw": 796_000,
            "floor_rounding_delta_raw": 0,
            "arithmetic_transform_verified": True,
            "business_semantics_verified": False,
        },
        "price_impact": {"status": "EVIDENCE_REQUIRED", "verified": False},
        "minimum_received": {"status": "EVIDENCE_REQUIRED", "bounded": False},
        "network_fee": {"status": "EVIDENCE_REQUIRED", "verified": False},
        "cross_dex_configured": None,
        "cross_dex_route_available": False,
        "cross_dex_execution_observed": False,
        "cross_dex_execution_verified": False,
        "route_optimality_verified": False,
        "provider_raw_json_exposed": False,
        "read_only": True,
        "execution_authorized": False,
    }


def test_valid_cmis_snapshot_and_scout_projection_preserve_truth_boundary():
    source = _snapshot()
    safe = validate_xdex_multi_hop_route_snapshot(source)
    product = build_x1_smart_route_intelligence(source)

    assert safe["contract_version"] == CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT
    assert product["contract_version"] == X1_SMART_ROUTE_CONTRACT
    assert product["cmis_contract_version"] == CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT
    assert product["path"] == [MINT_A, MINT_B, MINT_C]
    assert product["hop_count"] == 2
    assert product["gross_output_raw"] == 800_000
    assert product["net_output_raw"] == 796_000
    assert product["route_output"]["aggregate_hop_output_verified"] is True
    assert product["observation_window"]["slot_span"] == 4
    assert product["observation_window"]["provider_fact_time_verified"] is False
    assert product["price_impact"] == {"status": "EVIDENCE_REQUIRED", "verified": False}
    assert product["minimum_received"] == {"status": "EVIDENCE_REQUIRED", "bounded": False}
    assert product["network_fee"] == {"status": "EVIDENCE_REQUIRED", "verified": False}
    assert product["provider_routing_fee_transform"]["arithmetic_transform_verified"] is True
    assert product["provider_routing_fee_transform"]["business_semantics_verified"] is False
    assert product["pool_fee_units_preserved_per_hop"] is True
    assert product["provider_fee_business_semantics_inference_authorized"] is False
    assert product["provider_fact_time_inference_authorized"] is False
    assert product["quoted_output_is_executed_output"] is False
    assert product["minimum_received_is_guaranteed_fill"] is False
    assert product["route_optimality_verified"] is False
    assert product["global_route_optimality_claimed"] is False
    assert product["direct_vs_multi_hop_exhaustive_comparison_claimed"] is False
    assert product["cross_dex_execution_observed"] is False
    assert product["cross_dex_execution_verified"] is False
    assert product["provider_raw_json_exposed"] is False
    assert product["read_only"] is True
    assert product["execution_authorized"] is False


def test_projection_deep_copies_cmis_material():
    source = _snapshot()
    product = build_x1_smart_route_intelligence(source)
    source["hops"][0]["active_reserve_in_raw"] = 1
    source["pool_fee_evidence"][0]["reconstructed_trade_fee_raw"] = 1
    source["price_impact"]["status"] = "VERIFIED"
    assert product["hops"][0]["active_reserve_in_raw"] == 100_000_000
    assert product["pool_fee_evidence"][0]["reconstructed_trade_fee_raw"] == 2_800
    assert product["price_impact"]["status"] == "EVIDENCE_REQUIRED"


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (lambda s: s.update(contract_version="xdex_multi_hop_route_snapshot/v999"), "contract mismatch"),
        (lambda s: s.update(provider_raw_json_exposed=True), "provider_raw_json_exposed"),
        (lambda s: s.update(route_optimality_verified=True), "route_optimality_verified"),
        (lambda s: s.update(cross_dex_execution_observed=True), "cross_dex_execution_observed"),
        (lambda s: s.update(cross_dex_execution_verified=True), "cross_dex_execution_verified"),
        (lambda s: s.update(execution_authorized=True), "execution_authorized"),
        (lambda s: s["observation_window"].update(provider_fact_time_verified=True), "provider_fact_time_verified"),
        (lambda s: s["observation_window"].update(slot_span=9), "slot window"),
        (lambda s: s["price_impact"].update(status="VERIFIED", verified=True), "price_impact.status"),
        (lambda s: s["minimum_received"].update(status="VERIFIED", bounded=True), "minimum_received.status"),
        (lambda s: s["network_fee"].update(status="VERIFIED", verified=True), "network_fee.status"),
        (lambda s: s["provider_routing_fee_transform"].update(business_semantics_verified=True), "business_semantics_verified"),
        (lambda s: s["provider_routing_fee_transform"].update(fee_amount_raw=3_999), "arithmetic"),
        (lambda s: s["hops"][1].update(token_in_mint=MINT_A), "route path"),
        (lambda s: s["hops"][1].update(amount_in_raw=899_999), "not contiguous"),
        (lambda s: s["hops"][0].update(pool_state_verified=False), "pool_state_verified"),
        (lambda s: s["pool_fee_evidence"][1].update(input_mint=MINT_A), "fee evidence identity"),
        (lambda s: s["pool_fee_evidence"][0].update(reconstructed_trade_fee_raw=2_799), "does not match verified hop"),
    ],
)
def test_cmis_snapshot_rejects_semantic_or_evidence_drift(mutator, match: str):
    source = _snapshot()
    mutator(source)
    with pytest.raises(CMISXDEXMultiHopRouteSnapshotError, match=match):
        validate_xdex_multi_hop_route_snapshot(source)


def test_snapshot_rejects_raw_provider_response_even_if_hidden_in_extra_field():
    source = _snapshot()
    source["raw_response"] = {"provider": "xdex"}
    # A normalized CMIS snapshot may evolve additively, but provider JSON itself
    # must never be accepted as Scout evidence. The explicit boundary flag alone
    # is not enough when the raw object is physically present.
    with pytest.raises(CMISXDEXMultiHopRouteSnapshotError, match="raw provider"):
        validate_xdex_multi_hop_route_snapshot(source)


def test_scout_wraps_cmis_contract_errors_without_strengthening():
    source = _snapshot()
    source["route_optimality_verified"] = True
    with pytest.raises(X1SmartRouteContractError, match="route_optimality_verified"):
        build_x1_smart_route_intelligence(source)
