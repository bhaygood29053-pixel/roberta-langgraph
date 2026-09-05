"""ROBERTA-side validation for promoted CMIS Bridge-to-XDEX Utilization v1.

This module validates and preserves the CMIS public projection. It never
recalculates bridge flow, supply, XDEX liquidity/volume, value basis,
utilization, adoption, causality, or risk.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

SERVICE = "bridge_to_xdex_utilization"
SERVICE_CONTRACT_VERSION = "bridge_to_xdex_utilization/v1"
PROMOTED_SCOPE = "verified_xdex_program_family"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CMISBridgeToXdexContractError(ValueError):
    """Raised when the promoted CMIS response/request violates #482."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CMISBridgeToXdexContractError(f"{field} must be normalized text")
    return value


def _positive_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise CMISBridgeToXdexContractError(f"{field} must be positive")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CMISBridgeToXdexContractError(f"{field} must be positive") from exc
    if parsed <= 0:
        raise CMISBridgeToXdexContractError(f"{field} must be positive")
    return parsed


def normalize_bridge_to_xdex_request(
    *,
    evidence_sha256: Any,
    route_id: Any,
    source_mint: Any,
    destination_mint: Any,
    evaluated_at: Any,
    max_evidence_age_seconds: Any,
) -> dict[str, object]:
    evidence = _text(evidence_sha256, "evidence_sha256")
    if not _SHA256_RE.fullmatch(evidence):
        raise CMISBridgeToXdexContractError(
            "evidence_sha256 must be a lowercase 64-character SHA-256 hex digest"
        )
    route = _text(route_id, "route_id")
    source = _text(source_mint, "source_mint")
    destination = _text(destination_mint, "destination_mint")
    evaluated = _positive_number(evaluated_at, "evaluated_at")
    max_age = _positive_number(
        max_evidence_age_seconds,
        "max_evidence_age_seconds",
    )
    return {
        "evidence_sha256": evidence,
        "route_id": route,
        "source_mint": source,
        "destination_mint": destination,
        "evaluated_at": evaluated,
        "max_evidence_age_seconds": max_age,
    }


def _mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise CMISBridgeToXdexContractError(
            f"required Bridge-to-XDEX object missing: {key}"
        )
    return value


def _sequence(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, Mapping)):
        raise CMISBridgeToXdexContractError(
            f"required Bridge-to-XDEX list malformed: {key}"
        )
    return list(value)


def validate_bridge_to_xdex_response(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CMISBridgeToXdexContractError(
            "CMIS Bridge-to-XDEX response must be an object"
        )
    safe = deepcopy(dict(response))
    if safe.get("service") != SERVICE:
        raise CMISBridgeToXdexContractError("Bridge-to-XDEX service mismatch")
    if safe.get("chain") != "x1":
        raise CMISBridgeToXdexContractError("Bridge-to-XDEX chain must remain x1")
    if safe.get("status") != "ok":
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX promoted product requires CMIS ok status"
        )
    if safe.get("risk") is not None:
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX response must not promote an automatic risk conclusion"
        )
    if safe.get("execution_authorized") not in (None, False):
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX response must preserve execution_authorized=false"
        )

    data = _mapping(safe, "data")
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX service contract mismatch"
        )
    for field, expected in (
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("read_only", True),
        ("causal_bridge_to_xdex_claim_authorized", False),
        ("adoption_claim_authorized", False),
        ("risk_promotion_authorized", False),
        ("execution_authorized", False),
    ):
        if data.get(field) is not expected:
            raise CMISBridgeToXdexContractError(
                f"Bridge-to-XDEX {field} must be {str(expected).lower()}"
            )

    route = _mapping(data, "route")
    for field in ("route_id", "source_mint", "destination_mint"):
        if route.get(field) != expected_request.get(field):
            raise CMISBridgeToXdexContractError(
                f"Bridge-to-XDEX {field} must match the exact request identity"
            )
    if route.get("source_chain") != "solana":
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX source_chain must remain solana"
        )
    if route.get("destination_chain") != "x1":
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX destination_chain must remain x1"
        )

    scope = _mapping(data, "scope")
    if scope.get("xdex_pool_universe_scope") != PROMOTED_SCOPE:
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX scope must remain verified XDEX program-family"
        )
    if scope.get("recognized_program_registry_globally_exhaustive") is not False:
        raise CMISBridgeToXdexContractError(
            "recognized XDEX program registry must not become globally exhaustive"
        )
    if scope.get("global_onchain_pool_discovery_proven") is not False:
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX must not claim global X1 DEX discovery"
        )

    bridge = _mapping(data, "bridge")
    flow = _mapping(bridge, "flow_24h")
    if flow.get("value_unit") != "USD":
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX bridge flow must preserve USD value semantics"
        )

    market = _mapping(data, "xdex_market")
    if market.get("value_unit") != "USD":
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX XDEX market values must remain USD"
        )
    if market.get("volume_24h_window_coverage_verified") is not True:
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX 24h volume coverage must remain verified"
        )
    pool_addresses = _sequence(market, "pool_addresses")
    if market.get("verified_zero_pool_set") is True:
        if pool_addresses or market.get("pool_count") != 0:
            raise CMISBridgeToXdexContractError(
                "verified zero pool set cannot contain pool addresses"
            )
        if market.get("current_liquidity_zero_verified") is not True:
            raise CMISBridgeToXdexContractError(
                "verified zero pool set requires current zero-liquidity proof"
            )
        if market.get("liquidity_value") != "0":
            raise CMISBridgeToXdexContractError(
                "verified zero pool set must preserve zero liquidity"
            )

    _mapping(data, "utilization")
    freshness = _mapping(data, "freshness")
    if freshness.get("freshness_verified") is not True:
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX public freshness must remain verified"
        )
    if float(freshness.get("evaluated_at")) != float(expected_request["evaluated_at"]):
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX evaluated_at must match the request"
        )
    if float(freshness.get("max_evidence_age_seconds")) != float(
        expected_request["max_evidence_age_seconds"]
    ):
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX freshness bound must match the request"
        )

    evidence = _mapping(data, "evidence")
    if evidence.get("evidence_sha256") != expected_request.get("evidence_sha256"):
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX evidence selector mismatch"
        )
    if evidence.get("comparable_value_basis_verified") is not True:
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX comparable value basis must remain verified"
        )
    if evidence.get("issue_410_acceptance_verified") is not True:
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX #410 acceptance must remain verified"
        )
    if not isinstance(evidence.get("source_independence_verified"), bool):
        raise CMISBridgeToXdexContractError(
            "Bridge-to-XDEX source independence must remain explicit"
        )

    canonical = _mapping(data, "canonical_utilization")
    if canonical.get("evidence_sha256") != expected_request.get("evidence_sha256"):
        raise CMISBridgeToXdexContractError(
            "canonical Bridge-to-XDEX evidence selector mismatch"
        )
    if canonical.get("route_id") != expected_request.get("route_id"):
        raise CMISBridgeToXdexContractError(
            "canonical Bridge-to-XDEX route mismatch"
        )
    if canonical.get("source_mint") != expected_request.get("source_mint"):
        raise CMISBridgeToXdexContractError(
            "canonical Bridge-to-XDEX source mint mismatch"
        )
    if canonical.get("destination_mint") != expected_request.get("destination_mint"):
        raise CMISBridgeToXdexContractError(
            "canonical Bridge-to-XDEX destination mint mismatch"
        )
    if canonical.get("xdex_pool_universe_scope") != PROMOTED_SCOPE:
        raise CMISBridgeToXdexContractError(
            "canonical Bridge-to-XDEX scope widened"
        )
    for field in (
        "causal_bridge_to_xdex_claim_authorized",
        "adoption_claim_authorized",
        "risk_promotion_authorized",
        "public_service_promoted",
        "scout_reliance_promoted",
        "execution_authorized",
    ):
        if canonical.get(field) is not False:
            raise CMISBridgeToXdexContractError(
                f"canonical Bridge-to-XDEX {field} must remain false"
            )

    _mapping(safe, "confidence")
    _sequence(safe, "sources")
    _sequence(safe, "warnings")
    _sequence(safe, "errors")
    return safe


__all__ = [
    "CMISBridgeToXdexContractError",
    "PROMOTED_SCOPE",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "normalize_bridge_to_xdex_request",
    "validate_bridge_to_xdex_response",
]
