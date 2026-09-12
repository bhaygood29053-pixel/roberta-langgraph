"""Typed X1 Scout projection for accepted CMIS Smart Route snapshots.

Scout may interpret the accepted X1 route facts, but it may not re-parse XDEX
provider JSON, upgrade evidence gaps, claim global optimality, or authorize
execution. All route arithmetic and evidence states remain owned by CMIS.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Literal, TypedDict

from roberta.cmis.xdex_multi_hop_route_snapshot import (
    CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT,
    CMISXDEXMultiHopRouteSnapshotError,
    validate_xdex_multi_hop_route_snapshot,
)

X1_SMART_ROUTE_CONTRACT = "x1_smart_route_intelligence/v1"


class X1SmartRouteContractError(ValueError):
    """Raised when CMIS route evidence cannot satisfy the X1 Scout boundary."""


class X1SmartRouteProjection(TypedDict):
    contract_version: str
    product: str
    chain: Literal["x1"]
    status: Literal["ok"]
    cmis_contract_version: str
    input_mint: str
    output_mint: str
    input_amount_raw: int
    gross_output_raw: int
    net_output_raw: int
    hop_count: int
    path: list[str]
    hops: list[dict[str, object]]
    observation_window: dict[str, object]
    route_output: dict[str, object]
    pool_fee_evidence: list[dict[str, object]]
    provider_routing_fee_transform: dict[str, object]
    price_impact: dict[str, object]
    minimum_received: dict[str, object]
    network_fee: dict[str, object]
    cross_dex_configured: bool | None
    cross_dex_route_available: bool
    cross_dex_execution_observed: bool
    cross_dex_execution_verified: bool
    route_optimality_verified: bool
    evidence_state_semantics_preserved: bool
    pool_fee_units_preserved_per_hop: bool
    provider_fee_business_semantics_inference_authorized: bool
    provider_fact_time_inference_authorized: bool
    quoted_output_is_executed_output: bool
    minimum_received_is_guaranteed_fill: bool
    global_route_optimality_claimed: bool
    direct_vs_multi_hop_exhaustive_comparison_claimed: bool
    provider_raw_json_exposed: bool
    read_only: bool
    execution_authorized: bool


def build_x1_smart_route_intelligence(snapshot: Mapping[str, Any]) -> X1SmartRouteProjection:
    """Project one accepted CMIS route snapshot without strengthening its claims."""

    try:
        safe = validate_xdex_multi_hop_route_snapshot(snapshot)
    except CMISXDEXMultiHopRouteSnapshotError as exc:
        raise X1SmartRouteContractError(str(exc)) from exc

    product: X1SmartRouteProjection = {
        "contract_version": X1_SMART_ROUTE_CONTRACT,
        "product": "x1_smart_route_intelligence",
        "chain": "x1",
        "status": "ok",
        "cmis_contract_version": CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT,
        "input_mint": safe["input_mint"],
        "output_mint": safe["output_mint"],
        "input_amount_raw": safe["input_amount_raw"],
        "gross_output_raw": safe["gross_output_raw"],
        "net_output_raw": safe["net_output_raw"],
        "hop_count": safe["hop_count"],
        "path": deepcopy(safe["path"]),
        "hops": deepcopy(safe["hops"]),
        "observation_window": deepcopy(safe["observation_window"]),
        "route_output": deepcopy(safe["route_output"]),
        "pool_fee_evidence": deepcopy(safe["pool_fee_evidence"]),
        "provider_routing_fee_transform": deepcopy(safe["provider_routing_fee_transform"]),
        "price_impact": deepcopy(safe["price_impact"]),
        "minimum_received": deepcopy(safe["minimum_received"]),
        "network_fee": deepcopy(safe["network_fee"]),
        "cross_dex_configured": safe["cross_dex_configured"],
        "cross_dex_route_available": safe["cross_dex_route_available"],
        "cross_dex_execution_observed": safe["cross_dex_execution_observed"],
        "cross_dex_execution_verified": safe["cross_dex_execution_verified"],
        "route_optimality_verified": safe["route_optimality_verified"],
        "evidence_state_semantics_preserved": True,
        "pool_fee_units_preserved_per_hop": True,
        "provider_fee_business_semantics_inference_authorized": False,
        "provider_fact_time_inference_authorized": False,
        "quoted_output_is_executed_output": False,
        "minimum_received_is_guaranteed_fill": False,
        "global_route_optimality_claimed": False,
        "direct_vs_multi_hop_exhaustive_comparison_claimed": False,
        "provider_raw_json_exposed": False,
        "read_only": True,
        "execution_authorized": False,
    }
    return product


__all__ = [
    "X1_SMART_ROUTE_CONTRACT",
    "X1SmartRouteContractError",
    "X1SmartRouteProjection",
    "build_x1_smart_route_intelligence",
]
