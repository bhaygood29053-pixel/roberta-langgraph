"""Deterministic X1 Scout burn-intelligence projection.

This module projects an accepted CMIS ``tokenomics`` envelope into the first
``x1_burn_intelligence/v1`` product contract. It performs no burn arithmetic,
price valuation, supply inference, or historical comparison calculation.
Every numerical/state field remains CMIS-owned.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


BURN_INTELLIGENCE_CONTRACT = "x1_burn_intelligence/v1"
_REQUIRED_WINDOWS = ("1h", "24h", "7d", "30d")
_COMPARISON_WINDOWS = ("24h", "7d", "30d")
_ACCEPTED_CHANGE_STATES = {
    "AVAILABLE",
    "NO_CHANGE_ZERO_BASE",
    "NEW_BURN_ACTIVITY",
    "INSUFFICIENT_COVERAGE",
}
_BASE58_CHARS = frozenset(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)


class X1BurnIntelligenceContractError(ValueError):
    """Raised when CMIS tokenomics cannot satisfy burn-intelligence v1."""


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _require_mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise X1BurnIntelligenceContractError(f"required burn object missing: {key}")
    return value


def _require_bool(container: Mapping[str, Any], key: str) -> bool:
    value = container.get(key)
    if not isinstance(value, bool):
        raise X1BurnIntelligenceContractError(f"required burn boolean malformed: {key}")
    return value


def _exact_x1_mint(value: object) -> str:
    text = str(value or "").strip()
    if not (
        32 <= len(text) <= 44
        and all(character in _BASE58_CHARS for character in text)
    ):
        raise X1BurnIntelligenceContractError(
            "burn intelligence requires an exact address-shaped X1 mint"
        )
    return text


def _validate_window(label: str, value: object) -> None:
    if not isinstance(value, Mapping):
        raise X1BurnIntelligenceContractError(f"burn window missing or malformed: {label}")
    status = value.get("status")
    if status not in {"ok", "unavailable"}:
        raise X1BurnIntelligenceContractError(f"unsupported burn window status: {label}")
    coverage_verified = value.get("coverage_verified")
    if not isinstance(coverage_verified, bool):
        raise X1BurnIntelligenceContractError(f"burn window coverage malformed: {label}")

    if coverage_verified is True:
        if status != "ok":
            raise X1BurnIntelligenceContractError(
                f"verified burn window must preserve ok status: {label}"
            )
        for key in ("burned_raw", "burned_tokens", "burn_events"):
            if value.get(key) is None:
                raise X1BurnIntelligenceContractError(
                    f"verified burn window missing {key}: {label}"
                )
    elif status != "unavailable":
        raise X1BurnIntelligenceContractError(
            f"unverified burn window must remain unavailable: {label}"
        )

    if label in _COMPARISON_WINDOWS:
        comparison = value.get("period_over_period")
        if not isinstance(comparison, Mapping):
            raise X1BurnIntelligenceContractError(
                f"period-over-period burn comparison missing: {label}"
            )
        comparison_status = comparison.get("status")
        if comparison_status not in {"ok", "unavailable"}:
            raise X1BurnIntelligenceContractError(
                f"unsupported burn comparison status: {label}"
            )
        change_state = comparison.get("change_state")
        if change_state not in _ACCEPTED_CHANGE_STATES:
            raise X1BurnIntelligenceContractError(
                f"unsupported burn comparison state: {label}"
            )
        percent_change = comparison.get("percent_change")
        if change_state in {"NEW_BURN_ACTIVITY", "INSUFFICIENT_COVERAGE"}:
            if percent_change is not None:
                raise X1BurnIntelligenceContractError(
                    f"non-numeric burn comparison state must preserve null percent: {label}"
                )
        if comparison_status == "ok" and change_state == "INSUFFICIENT_COVERAGE":
            raise X1BurnIntelligenceContractError(
                f"available burn comparison cannot claim insufficient coverage: {label}"
            )
        if comparison_status == "unavailable" and change_state != "INSUFFICIENT_COVERAGE":
            raise X1BurnIntelligenceContractError(
                f"unavailable burn comparison must preserve insufficient coverage: {label}"
            )


def _validate_burn_metrics(metrics: Mapping[str, Any]) -> None:
    available = _require_bool(metrics, "available")
    status = metrics.get("status")
    if status not in {"ok", "partial", "unavailable"}:
        raise X1BurnIntelligenceContractError("unsupported burn_metrics status")

    lifetime = metrics.get("lifetime_total_burn_verified")
    if not isinstance(lifetime, bool):
        raise X1BurnIntelligenceContractError(
            "lifetime_total_burn_verified must be explicit boolean"
        )

    if available is False:
        if status != "unavailable":
            raise X1BurnIntelligenceContractError(
                "unavailable burn metrics must preserve unavailable status"
            )
        return

    windows = _require_mapping(metrics, "windows")
    for label in _REQUIRED_WINDOWS:
        _validate_window(label, windows.get(label))

    _require_bool(metrics, "coverage_verified")
    _require_bool(metrics, "time_buckets_verified")
    _require_bool(metrics, "observed_event_totals_verified")

    valuation = _require_mapping(metrics, "valuation")
    if valuation.get("status") not in {"ok", "partial", "unavailable"}:
        raise X1BurnIntelligenceContractError("unsupported burn valuation status")
    valuation_complete = valuation.get("valuation_coverage_complete")
    if not isinstance(valuation_complete, bool):
        raise X1BurnIntelligenceContractError(
            "burn valuation completeness must be explicit boolean"
        )

    circulation = _require_mapping(metrics, "circulating_supply")
    circulating_verified = circulation.get("circulating_supply_verified")
    if circulating_verified is not None and not isinstance(circulating_verified, bool):
        raise X1BurnIntelligenceContractError(
            "circulating supply verification state must be boolean when supplied"
        )


def build_x1_burn_intelligence(
    tokenomics_result: Mapping[str, Any],
    *,
    requested_asset: str | None = None,
) -> dict[str, object]:
    """Project one CMIS tokenomics envelope without recomputing its burn facts."""

    if not isinstance(tokenomics_result, Mapping):
        raise X1BurnIntelligenceContractError("CMIS tokenomics result must be an object")
    if tokenomics_result.get("service") != "tokenomics":
        raise X1BurnIntelligenceContractError("burn intelligence requires CMIS tokenomics")
    if tokenomics_result.get("chain") != "x1":
        raise X1BurnIntelligenceContractError("burn intelligence v1 is X1-only")
    if tokenomics_result.get("status") not in {
        "ok",
        "partial",
        "unavailable",
    }:
        raise X1BurnIntelligenceContractError("unsupported CMIS tokenomics status")

    if tokenomics_result.get("execution_authorized") not in {None, False}:
        raise X1BurnIntelligenceContractError(
            "burn intelligence must preserve execution_authorized=false"
        )

    asset = _require_mapping(tokenomics_result, "asset")
    data = _require_mapping(tokenomics_result, "data")
    asset_mint = _exact_x1_mint(asset.get("mint"))
    data_mint = _exact_x1_mint(data.get("mint"))
    if data_mint != asset_mint:
        raise X1BurnIntelligenceContractError(
            "CMIS tokenomics data mint does not match resolved asset mint"
        )

    metrics = data.get("burn_metrics")
    if not isinstance(metrics, Mapping):
        raise X1BurnIntelligenceContractError("CMIS tokenomics burn_metrics missing")
    _validate_burn_metrics(metrics)

    result: dict[str, object] = {
        "contract_version": BURN_INTELLIGENCE_CONTRACT,
        "product": "x1_burn_intelligence",
        "chain": "x1",
        "status": tokenomics_result.get("status"),
        "requested_asset": requested_asset,
        "asset": deepcopy(dict(asset)),
        "burn_metrics": deepcopy(dict(metrics)),
        "observed_at": tokenomics_result.get("observed_at"),
        "confidence": deepcopy(dict(_mapping(tokenomics_result.get("confidence")))),
        "sources": deepcopy(list(tokenomics_result.get("sources") or [])),
        "warnings": deepcopy(list(tokenomics_result.get("warnings") or [])),
        "errors": deepcopy(list(tokenomics_result.get("errors") or [])),
        "evidence_receipt": deepcopy(tokenomics_result.get("evidence_receipt")),
        "proof_score": deepcopy(tokenomics_result.get("proof_score")),
        "proof_score_separate_from_risk": True,
        "execution_authorized": False,
    }
    return result


__all__ = [
    "BURN_INTELLIGENCE_CONTRACT",
    "X1BurnIntelligenceContractError",
    "build_x1_burn_intelligence",
]
