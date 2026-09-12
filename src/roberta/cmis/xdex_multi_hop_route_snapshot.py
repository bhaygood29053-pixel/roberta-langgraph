"""ROBERTA-side validator for accepted CMIS XDEX multi-hop route snapshots.

The CMIS snapshot is already provider-agnostic. This boundary validates that
accepted facts and explicit evidence gaps have not drifted before X1 Scout
projects them into chain-specific interpretation. Raw provider JSON is never
accepted here and execution authority must remain false.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT = "xdex_multi_hop_route_snapshot/v1"
CHAIN = "x1"
EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"


class CMISXDEXMultiHopRouteSnapshotError(ValueError):
    """Raised when a CMIS Smart Route snapshot widens the accepted boundary."""


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CMISXDEXMultiHopRouteSnapshotError(f"{field} must be a mapping")
    return value


def _sequence(value: Any, field: str) -> list[Any]:
    if isinstance(value, (str, bytes, bytearray, Mapping)) or not isinstance(value, Sequence):
        raise CMISXDEXMultiHopRouteSnapshotError(f"{field} must be a list")
    return list(value)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise CMISXDEXMultiHopRouteSnapshotError(f"{field} must be normalized non-empty text")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CMISXDEXMultiHopRouteSnapshotError(f"{field} must be a non-negative integer")
    return value


def _required_true(record: Mapping[str, Any], field: str, label: str) -> None:
    if record.get(field) is not True:
        raise CMISXDEXMultiHopRouteSnapshotError(f"{label}.{field} must remain true")


def _required_false(record: Mapping[str, Any], field: str, label: str) -> None:
    if record.get(field) is not False:
        raise CMISXDEXMultiHopRouteSnapshotError(f"{label}.{field} must remain false")


def _validate_evidence_required(value: Any, field: str, state_field: str) -> dict[str, Any]:
    record = deepcopy(dict(_mapping(value, field)))
    if record.get("status") != EVIDENCE_REQUIRED:
        raise CMISXDEXMultiHopRouteSnapshotError(f"{field}.status must remain EVIDENCE_REQUIRED")
    if record.get(state_field) is not False:
        raise CMISXDEXMultiHopRouteSnapshotError(f"{field}.{state_field} must remain false")
    return record


def validate_xdex_multi_hop_route_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one accepted provider-agnostic CMIS route snapshot fail-closed."""

    if not isinstance(snapshot, Mapping):
        raise CMISXDEXMultiHopRouteSnapshotError("CMIS Smart Route snapshot must be an object")
    safe = deepcopy(dict(snapshot))

    for forbidden in (
        "raw_response",
        "raw_provider_json",
        "provider_json",
        "provider_observation",
        "parsed_quote",
    ):
        if forbidden in safe:
            raise CMISXDEXMultiHopRouteSnapshotError(
                "raw provider material must not cross the CMIS-to-Scout snapshot boundary"
            )

    if safe.get("contract_version") != CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT:
        raise CMISXDEXMultiHopRouteSnapshotError("CMIS Smart Route contract mismatch")
    if safe.get("chain") != CHAIN or safe.get("status") != "ok":
        raise CMISXDEXMultiHopRouteSnapshotError("CMIS Smart Route chain/status mismatch")
    _required_true(safe, "read_only", "snapshot")
    _required_false(safe, "execution_authorized", "snapshot")
    _required_false(safe, "provider_raw_json_exposed", "snapshot")
    _required_false(safe, "route_optimality_verified", "snapshot")
    _required_false(safe, "cross_dex_execution_observed", "snapshot")
    _required_false(safe, "cross_dex_execution_verified", "snapshot")

    if safe.get("cross_dex_configured") not in (None, True, False):
        raise CMISXDEXMultiHopRouteSnapshotError("cross_dex_configured must be boolean or null")
    if safe.get("cross_dex_route_available") not in (True, False):
        raise CMISXDEXMultiHopRouteSnapshotError("cross_dex_route_available must be boolean")

    input_mint = _text(safe.get("input_mint"), "input_mint")
    output_mint = _text(safe.get("output_mint"), "output_mint")
    if input_mint == output_mint:
        raise CMISXDEXMultiHopRouteSnapshotError("input and output mints must differ")
    input_amount_raw = _nonnegative_int(safe.get("input_amount_raw"), "input_amount_raw")
    gross_output_raw = _nonnegative_int(safe.get("gross_output_raw"), "gross_output_raw")
    net_output_raw = _nonnegative_int(safe.get("net_output_raw"), "net_output_raw")
    if input_amount_raw <= 0 or gross_output_raw <= 0 or net_output_raw <= 0:
        raise CMISXDEXMultiHopRouteSnapshotError("route amounts must remain positive")

    hop_count = _nonnegative_int(safe.get("hop_count"), "hop_count")
    if hop_count < 1:
        raise CMISXDEXMultiHopRouteSnapshotError("hop_count must be positive")
    path = _sequence(safe.get("path"), "path")
    hops = _sequence(safe.get("hops"), "hops")
    if len(path) != hop_count + 1 or len(hops) != hop_count:
        raise CMISXDEXMultiHopRouteSnapshotError("path/hops do not match hop_count")
    if path[0] != input_mint or path[-1] != output_mint:
        raise CMISXDEXMultiHopRouteSnapshotError("route path endpoints mismatch")

    previous_output: int | None = None
    normalized_hops: list[dict[str, Any]] = []
    for index, raw_hop in enumerate(hops):
        hop = deepcopy(dict(_mapping(raw_hop, f"hops[{index}]")))
        if hop.get("index") != index:
            raise CMISXDEXMultiHopRouteSnapshotError("hop indexes must be contiguous from zero")
        for field in ("venue", "pool", "token_in_mint", "token_out_mint", "amm_config"):
            _text(hop.get(field), f"hops[{index}].{field}")
        if hop["token_in_mint"] != path[index] or hop["token_out_mint"] != path[index + 1]:
            raise CMISXDEXMultiHopRouteSnapshotError("hop identity does not match route path")
        for field in (
            "pool_identity_verified",
            "pool_state_verified",
            "venue_identity_verified",
            "reserve_math_verified",
            "fee_math_verified",
        ):
            _required_true(hop, field, f"hops[{index}]")
        _required_false(hop, "price_impact_verified", f"hops[{index}]")
        _required_false(hop, "minimum_received_bounded", f"hops[{index}]")
        _required_false(hop, "execution_authorized", f"hops[{index}]")

        amount_in = _nonnegative_int(hop.get("amount_in_raw"), f"hops[{index}].amount_in_raw")
        amount_out = _nonnegative_int(hop.get("expected_output_raw"), f"hops[{index}].expected_output_raw")
        reserve_in = _nonnegative_int(hop.get("active_reserve_in_raw"), f"hops[{index}].active_reserve_in_raw")
        reserve_out = _nonnegative_int(hop.get("active_reserve_out_raw"), f"hops[{index}].active_reserve_out_raw")
        fee_rate = _nonnegative_int(hop.get("trade_fee_rate_ppm"), f"hops[{index}].trade_fee_rate_ppm")
        if amount_in <= 0 or amount_out <= 0 or reserve_in <= 0 or reserve_out <= 0:
            raise CMISXDEXMultiHopRouteSnapshotError("verified hop amounts/reserves must remain positive")
        if fee_rate >= 1_000_000:
            raise CMISXDEXMultiHopRouteSnapshotError("trade_fee_rate_ppm is outside accepted range")
        if index == 0 and amount_in != input_amount_raw:
            raise CMISXDEXMultiHopRouteSnapshotError("first hop input does not match route input")
        if previous_output is not None and amount_in != previous_output:
            raise CMISXDEXMultiHopRouteSnapshotError("hop amounts are not contiguous")
        previous_output = amount_out

        for field in ("pool_context_slot", "config_context_slot"):
            if hop.get(field) is not None:
                _nonnegative_int(hop.get(field), f"hops[{index}].{field}")
        for field in (
            "reconstructed_trade_fee_raw",
            "reconstructed_creator_fee_raw",
            "protocol_fee_rate_ppm_of_trade_fee",
            "fund_fee_rate_ppm_of_trade_fee",
            "creator_fee_rate_ppm",
        ):
            if hop.get(field) is not None:
                _nonnegative_int(hop.get(field), f"hops[{index}].{field}")
        normalized_hops.append(hop)

    if previous_output != gross_output_raw:
        raise CMISXDEXMultiHopRouteSnapshotError("final hop output does not match gross route output")

    window = deepcopy(dict(_mapping(safe.get("observation_window"), "observation_window")))
    slot_min = _nonnegative_int(window.get("slot_min"), "observation_window.slot_min")
    slot_max = _nonnegative_int(window.get("slot_max"), "observation_window.slot_max")
    slot_span = _nonnegative_int(window.get("slot_span"), "observation_window.slot_span")
    max_slot_span = _nonnegative_int(window.get("max_slot_span"), "observation_window.max_slot_span")
    if slot_max < slot_min or slot_max - slot_min != slot_span or slot_span > max_slot_span:
        raise CMISXDEXMultiHopRouteSnapshotError("observation slot window is inconsistent or stale")
    _required_true(window, "current_state_alignment_verified", "observation_window")
    _required_false(window, "provider_fact_time_verified", "observation_window")

    route_output = deepcopy(dict(_mapping(safe.get("route_output"), "route_output")))
    if route_output.get("gross_output_raw") != gross_output_raw:
        raise CMISXDEXMultiHopRouteSnapshotError("route_output gross amount mismatch")
    _required_true(route_output, "aggregate_hop_output_verified", "route_output")

    pool_fees = _sequence(safe.get("pool_fee_evidence"), "pool_fee_evidence")
    if len(pool_fees) != hop_count:
        raise CMISXDEXMultiHopRouteSnapshotError("pool_fee_evidence must cover every hop")
    normalized_fees: list[dict[str, Any]] = []
    for index, raw_fee in enumerate(pool_fees):
        fee = deepcopy(dict(_mapping(raw_fee, f"pool_fee_evidence[{index}]")))
        if fee.get("hop_index") != index or fee.get("input_mint") != normalized_hops[index]["token_in_mint"]:
            raise CMISXDEXMultiHopRouteSnapshotError("pool fee evidence identity mismatch")
        if fee.get("trade_fee_rate_ppm") != normalized_hops[index]["trade_fee_rate_ppm"]:
            raise CMISXDEXMultiHopRouteSnapshotError("pool fee rate does not match verified hop")
        _required_true(fee, "fee_math_verified", f"pool_fee_evidence[{index}]")
        for field in ("reconstructed_trade_fee_raw", "reconstructed_creator_fee_raw"):
            if fee.get(field) is not None:
                _nonnegative_int(fee.get(field), f"pool_fee_evidence[{index}].{field}")
            if fee.get(field) != normalized_hops[index].get(field):
                raise CMISXDEXMultiHopRouteSnapshotError("pool fee evidence does not match verified hop")
        normalized_fees.append(fee)

    routing_fee = deepcopy(dict(_mapping(safe.get("provider_routing_fee_transform"), "provider_routing_fee_transform")))
    fee_bps = _nonnegative_int(routing_fee.get("fee_bps"), "provider_routing_fee_transform.fee_bps")
    fee_amount = _nonnegative_int(routing_fee.get("fee_amount_raw"), "provider_routing_fee_transform.fee_amount_raw")
    routing_net = _nonnegative_int(routing_fee.get("net_output_raw"), "provider_routing_fee_transform.net_output_raw")
    rounding_delta = _nonnegative_int(routing_fee.get("floor_rounding_delta_raw"), "provider_routing_fee_transform.floor_rounding_delta_raw")
    if fee_bps >= 10_000:
        raise CMISXDEXMultiHopRouteSnapshotError("provider routing fee bps is outside accepted range")
    if routing_net != net_output_raw or gross_output_raw - fee_amount - routing_net != rounding_delta:
        raise CMISXDEXMultiHopRouteSnapshotError("provider routing-fee arithmetic no longer balances")
    _required_true(routing_fee, "arithmetic_transform_verified", "provider_routing_fee_transform")
    _required_false(routing_fee, "business_semantics_verified", "provider_routing_fee_transform")

    safe["price_impact"] = _validate_evidence_required(safe.get("price_impact"), "price_impact", "verified")
    safe["minimum_received"] = _validate_evidence_required(safe.get("minimum_received"), "minimum_received", "bounded")
    safe["network_fee"] = _validate_evidence_required(safe.get("network_fee"), "network_fee", "verified")
    safe["hops"] = normalized_hops
    safe["pool_fee_evidence"] = normalized_fees
    safe["observation_window"] = window
    safe["route_output"] = route_output
    safe["provider_routing_fee_transform"] = routing_fee
    return safe


__all__ = [
    "CHAIN",
    "CMIS_XDEX_MULTI_HOP_ROUTE_SNAPSHOT_CONTRACT",
    "CMISXDEXMultiHopRouteSnapshotError",
    "EVIDENCE_REQUIRED",
    "validate_xdex_multi_hop_route_snapshot",
]
