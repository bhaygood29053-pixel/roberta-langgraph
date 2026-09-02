"""X1 Scout projection of the accepted CMIS Discovery Intelligence service."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


DISCOVERY_INTELLIGENCE_CONTRACT = "x1_discovery_intelligence/v1"
CMIS_DISCOVERY_INTELLIGENCE_CONTRACT = "discovery_intelligence/v1"
_BASE58 = frozenset("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


class X1DiscoveryIntelligenceContractError(ValueError):
    """Raised when CMIS Discovery Intelligence cannot satisfy X1 Scout."""


def _mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise X1DiscoveryIntelligenceContractError(
            f"required Discovery object missing: {key}"
        )
    return value


def _sequence(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, Mapping)):
        raise X1DiscoveryIntelligenceContractError(
            f"required Discovery list malformed: {key}"
        )
    return list(value)


def _mint(value: object) -> str:
    text = str(value or "").strip()
    if not (32 <= len(text) <= 44 and all(char in _BASE58 for char in text)):
        raise X1DiscoveryIntelligenceContractError(
            "Discovery Intelligence requires an exact address-shaped X1 mint"
        )
    return text


def _validate_data(data: Mapping[str, Any], mint: str) -> None:
    if data.get("contract_version") != CMIS_DISCOVERY_INTELLIGENCE_CONTRACT:
        raise X1DiscoveryIntelligenceContractError(
            "CMIS discovery_intelligence service contract mismatch"
        )
    if data.get("mint") != mint:
        raise X1DiscoveryIntelligenceContractError(
            "CMIS Discovery mint does not match resolved asset mint"
        )
    count = data.get("verified_observation_count")
    if type(count) is not int or count < 0:
        raise X1DiscoveryIntelligenceContractError(
            "verified_observation_count must be a non-negative integer"
        )
    if data.get("available") is not (count > 0):
        raise X1DiscoveryIntelligenceContractError(
            "Discovery availability does not match verified observation count"
        )
    if data.get("token_launch_time") is not None or data.get("token_launch_time_verified") is not False:
        raise X1DiscoveryIntelligenceContractError(
            "first observation must not be promoted as token launch time"
        )
    coverage = _mapping(data, "coverage")
    if coverage.get("continuous_coverage_verified") is not False:
        raise X1DiscoveryIntelligenceContractError(
            "Discovery history must not claim continuous coverage"
        )
    if coverage.get("archive_completeness_verified") is not False:
        raise X1DiscoveryIntelligenceContractError(
            "Discovery history must not claim archive completeness"
        )
    first = data.get("first_verified_observation")
    recent = data.get("most_recent_verified_observation")
    if count == 0:
        if first is not None or recent is not None:
            raise X1DiscoveryIntelligenceContractError(
                "empty Discovery scope cannot contain observation records"
            )
        return
    if not isinstance(first, Mapping) or not isinstance(recent, Mapping):
        raise X1DiscoveryIntelligenceContractError(
            "verified Discovery scope requires first and most-recent observations"
        )
    start = coverage.get("start_fact_time_unix")
    end = coverage.get("end_fact_time_unix")
    elapsed = coverage.get("elapsed_observed_seconds")
    if type(start) is not int or type(end) is not int or type(elapsed) is not int:
        raise X1DiscoveryIntelligenceContractError(
            "Discovery coverage bounds must be integer Unix seconds"
        )
    if start < 0 or end < start or elapsed != end - start:
        raise X1DiscoveryIntelligenceContractError("Discovery coverage bounds are inconsistent")
    if first.get("fact_time_unix") != start or recent.get("fact_time_unix") != end:
        raise X1DiscoveryIntelligenceContractError(
            "Discovery observation records do not match coverage bounds"
        )


def build_x1_discovery_intelligence(
    discovery_result: Mapping[str, Any],
    *,
    requested_asset: str | None = None,
) -> dict[str, object]:
    """Preserve one validated CMIS Discovery projection without recomputation."""

    if not isinstance(discovery_result, Mapping):
        raise X1DiscoveryIntelligenceContractError("CMIS Discovery result must be an object")
    if discovery_result.get("service") != "discovery_intelligence":
        raise X1DiscoveryIntelligenceContractError(
            "Discovery Intelligence requires CMIS discovery_intelligence"
        )
    if discovery_result.get("chain") != "x1":
        raise X1DiscoveryIntelligenceContractError("Discovery Intelligence v1 is X1-only")
    if discovery_result.get("status") not in {"partial", "unavailable"}:
        raise X1DiscoveryIntelligenceContractError("unsupported CMIS Discovery status")
    if discovery_result.get("execution_authorized") not in {None, False}:
        raise X1DiscoveryIntelligenceContractError(
            "Discovery Intelligence must preserve execution_authorized=false"
        )
    asset = _mapping(discovery_result, "asset")
    mint = _mint(asset.get("mint"))
    data = _mapping(discovery_result, "data")
    _validate_data(data, mint)
    confidence = _mapping(discovery_result, "confidence")
    sources = _sequence(discovery_result, "sources")
    warnings = _sequence(discovery_result, "warnings")
    errors = _sequence(discovery_result, "errors")
    return {
        "contract_version": DISCOVERY_INTELLIGENCE_CONTRACT,
        "product": "x1_discovery_intelligence",
        "chain": "x1",
        "status": discovery_result.get("status"),
        "requested_asset": requested_asset,
        "asset": deepcopy(dict(asset)),
        "discovery": deepcopy(dict(data)),
        "observed_at": discovery_result.get("observed_at"),
        "confidence": deepcopy(dict(confidence)),
        "sources": deepcopy(sources),
        "warnings": deepcopy(warnings),
        "errors": deepcopy(errors),
        "evidence_receipt": deepcopy(discovery_result.get("evidence_receipt")),
        "proof_score": deepcopy(discovery_result.get("proof_score")),
        "proof_score_separate_from_risk": True,
        "execution_authorized": False,
    }


__all__ = [
    "CMIS_DISCOVERY_INTELLIGENCE_CONTRACT",
    "DISCOVERY_INTELLIGENCE_CONTRACT",
    "X1DiscoveryIntelligenceContractError",
    "build_x1_discovery_intelligence",
]
