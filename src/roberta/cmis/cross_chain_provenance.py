"""ROBERTA-side validation for promoted CMIS cross-chain provenance v1.

The validator preserves CMIS-owned structural lineage exactly. It never infers
identity from symbols/names, reconstructs hops, recalculates representation
depth, or turns bridge/custody dependencies into backing, safety, adoption,
causality, current bridge-state, or risk conclusions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

SERVICE = "cross_chain_asset_provenance"
SERVICE_CONTRACT_VERSION = "cross_chain_asset_provenance/v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DISALLOWED_ID_KINDS = frozenset({"symbol", "ticker", "name", "label"})


class CMISCrossChainProvenanceContractError(ValueError):
    """Promoted CMIS provenance request/response violates the accepted contract."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CMISCrossChainProvenanceContractError(
            f"{field} must be normalized text"
        )
    return value


def _mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise CMISCrossChainProvenanceContractError(
            f"required provenance object missing: {key}"
        )
    return value


def _sequence(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, Sequence) or isinstance(
        value,
        (str, bytes, Mapping),
    ):
        raise CMISCrossChainProvenanceContractError(
            f"required provenance list malformed: {key}"
        )
    return list(value)


def _endpoint(value: Any, field: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise CMISCrossChainProvenanceContractError(
            f"{field} must be an object"
        )
    chain = _text(value.get("chain"), f"{field}.chain").casefold()
    asset_id = _text(value.get("asset_id"), f"{field}.asset_id")
    asset_id_kind = _text(
        value.get("asset_id_kind"),
        f"{field}.asset_id_kind",
    ).casefold()
    if asset_id_kind in _DISALLOWED_ID_KINDS:
        raise CMISCrossChainProvenanceContractError(
            f"{field}.asset_id_kind cannot use symbol/name labels as identity"
        )
    return {
        "chain": chain,
        "asset_id": asset_id,
        "asset_id_kind": asset_id_kind,
    }


def normalize_cross_chain_provenance_request(
    *,
    evidence_sha256: Any,
    current_asset_id: Any,
    current_asset_id_kind: Any,
) -> dict[str, str]:
    evidence = _text(evidence_sha256, "evidence_sha256")
    if not _SHA256_RE.fullmatch(evidence):
        raise CMISCrossChainProvenanceContractError(
            "evidence_sha256 must be a lowercase 64-character SHA-256 hex digest"
        )
    current = _text(current_asset_id, "current_asset_id")
    kind = _text(current_asset_id_kind, "current_asset_id_kind").casefold()
    if kind in _DISALLOWED_ID_KINDS:
        raise CMISCrossChainProvenanceContractError(
            "current_asset_id_kind cannot use symbol/name labels as identity"
        )
    return {
        "evidence_sha256": evidence,
        "current_asset_id": current,
        "current_asset_id_kind": kind,
    }


def _validate_lineage(
    lineage: list[Any],
    *,
    origin: Mapping[str, str],
    current: Mapping[str, str],
) -> None:
    if not lineage:
        raise CMISCrossChainProvenanceContractError(
            "promoted cross-chain provenance requires at least one hop"
        )
    previous_destination: dict[str, str] | None = None
    for index, raw in enumerate(lineage):
        if not isinstance(raw, Mapping):
            raise CMISCrossChainProvenanceContractError(
                f"lineage[{index}] must be an object"
            )
        source = _endpoint(raw.get("source"), f"lineage[{index}].source")
        destination = _endpoint(
            raw.get("destination"),
            f"lineage[{index}].destination",
        )
        _text(raw.get("bridge"), f"lineage[{index}].bridge")
        _text(
            raw.get("representation_type"),
            f"lineage[{index}].representation_type",
        )
        if source["chain"] == destination["chain"]:
            raise CMISCrossChainProvenanceContractError(
                f"lineage[{index}] must cross chains"
            )
        if index == 0 and source != dict(origin):
            raise CMISCrossChainProvenanceContractError(
                "first lineage source must equal origin"
            )
        if previous_destination is not None and source != previous_destination:
            raise CMISCrossChainProvenanceContractError(
                f"lineage[{index}] source must equal prior destination"
            )
        previous_destination = destination
    if previous_destination != dict(current):
        raise CMISCrossChainProvenanceContractError(
            "final lineage destination must equal current representation"
        )


def validate_cross_chain_provenance_response(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CMISCrossChainProvenanceContractError(
            "CMIS cross-chain provenance response must be an object"
        )
    safe = deepcopy(dict(response))
    if safe.get("service") != SERVICE:
        raise CMISCrossChainProvenanceContractError(
            "cross-chain provenance service mismatch"
        )
    if safe.get("chain") != "x1":
        raise CMISCrossChainProvenanceContractError(
            "cross-chain provenance chain must remain x1"
        )
    if safe.get("status") != "ok":
        raise CMISCrossChainProvenanceContractError(
            "promoted cross-chain provenance requires CMIS ok status"
        )
    if safe.get("risk") is not None:
        raise CMISCrossChainProvenanceContractError(
            "cross-chain provenance must not promote a risk conclusion"
        )
    if safe.get("execution_authorized") not in (None, False):
        raise CMISCrossChainProvenanceContractError(
            "cross-chain provenance must preserve execution_authorized=false"
        )

    data = _mapping(safe, "data")
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISCrossChainProvenanceContractError(
            "cross-chain provenance service contract mismatch"
        )
    for field, expected in (
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("read_only", True),
        ("symbol_or_name_identity_inference_authorized", False),
        ("bridge_dependency_is_risk", False),
        ("custody_dependency_is_risk", False),
        ("backing_claim_authorized", False),
        ("solvency_claim_authorized", False),
        ("safety_claim_authorized", False),
        ("adoption_claim_authorized", False),
        ("causal_inference_authorized", False),
        ("current_bridge_state_claim_authorized", False),
        ("risk_promotion_authorized", False),
        ("execution_authorized", False),
    ):
        if data.get(field) is not expected:
            raise CMISCrossChainProvenanceContractError(
                f"cross-chain provenance {field} must be "
                f"{str(expected).lower()}"
            )

    origin = _endpoint(data.get("origin"), "origin")
    current = _endpoint(data.get("current"), "current")
    if current["chain"] != "x1":
        raise CMISCrossChainProvenanceContractError(
            "current provenance representation must remain on X1"
        )
    if current["asset_id"] != expected_request.get("current_asset_id"):
        raise CMISCrossChainProvenanceContractError(
            "current provenance asset id must match the exact request identity"
        )
    if current["asset_id_kind"] != expected_request.get("current_asset_id_kind"):
        raise CMISCrossChainProvenanceContractError(
            "current provenance asset id kind must match the exact request identity"
        )

    depth = data.get("representation_depth")
    if isinstance(depth, bool) or not isinstance(depth, int) or depth <= 0:
        raise CMISCrossChainProvenanceContractError(
            "representation_depth must be a positive integer"
        )
    lineage = _sequence(data, "lineage")
    if depth != len(lineage):
        raise CMISCrossChainProvenanceContractError(
            "representation_depth must equal ordered lineage length"
        )
    _validate_lineage(lineage, origin=origin, current=current)
    dependencies = _sequence(data, "dependencies")

    verification = _mapping(data, "verification")
    expected_verification = {
        "structural_continuity_verified": True,
        "exact_chain_scoped_identifiers_required": True,
        "symbol_equivalence_authorized": False,
        "live_bridge_state_verified": False,
        "backing_verified": False,
        "custody_verified": False,
        "source_independence_verified": False,
    }
    if dict(verification) != expected_verification:
        raise CMISCrossChainProvenanceContractError(
            "cross-chain provenance verification boundary drift"
        )

    evidence = _mapping(data, "evidence")
    if evidence.get("evidence_sha256") != expected_request.get("evidence_sha256"):
        raise CMISCrossChainProvenanceContractError(
            "cross-chain provenance evidence selector mismatch"
        )
    if evidence.get("source_independence_verified") is not False:
        raise CMISCrossChainProvenanceContractError(
            "source independence must remain explicitly unverified"
        )

    canonical = _mapping(data, "canonical_provenance")
    if canonical.get("contract") != SERVICE_CONTRACT_VERSION:
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance contract mismatch"
        )
    if canonical.get("canonical_asset_id") != data.get("canonical_asset_id"):
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance asset identity diverged from public projection"
        )
    if canonical.get("origin") != data.get("origin"):
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance origin diverged from public projection"
        )
    if canonical.get("current") != data.get("current"):
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance current representation diverged from public projection"
        )
    if canonical.get("representation_depth") != depth:
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance representation depth diverged from public projection"
        )
    if canonical.get("lineage") != lineage:
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance lineage diverged from public projection"
        )
    if canonical.get("dependencies") != dependencies:
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance dependencies diverged from public projection"
        )
    if canonical.get("verification") != dict(verification):
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance verification diverged from public projection"
        )
    if canonical.get("read_only") is not True:
        raise CMISCrossChainProvenanceContractError(
            "canonical provenance must remain read-only"
        )
    for field in (
        "public_service_promoted",
        "scout_reliance_promoted",
        "execution_authorized",
    ):
        if canonical.get(field) is not False:
            raise CMISCrossChainProvenanceContractError(
                f"canonical provenance {field} must remain false"
            )

    asset = _mapping(safe, "asset")
    if asset.get("asset_id") != current["asset_id"]:
        raise CMISCrossChainProvenanceContractError(
            "response asset identity must match current provenance representation"
        )
    if asset.get("asset_id_kind") != current["asset_id_kind"]:
        raise CMISCrossChainProvenanceContractError(
            "response asset identity kind must match current provenance representation"
        )

    _mapping(safe, "confidence")
    _sequence(safe, "sources")
    _sequence(safe, "warnings")
    _sequence(safe, "errors")
    return safe


__all__ = [
    "CMISCrossChainProvenanceContractError",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "normalize_cross_chain_provenance_request",
    "validate_cross_chain_provenance_response",
]
