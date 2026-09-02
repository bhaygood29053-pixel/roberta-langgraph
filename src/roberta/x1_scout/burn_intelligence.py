"""Deterministic X1 Scout burn-intelligence projection.

This module projects the accepted CMIS ``burn_intelligence/v1`` envelope into
the X1 Scout ``x1_burn_intelligence/v1`` product contract. It performs no burn arithmetic,
price valuation, supply inference, or historical comparison calculation.
Every numerical/state field remains CMIS-owned.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any


BURN_INTELLIGENCE_CONTRACT = "x1_burn_intelligence/v1"
CMIS_BURN_INTELLIGENCE_CONTRACT = "burn_intelligence/v1"
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


def _require_sequence(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, Mapping)):
        raise X1BurnIntelligenceContractError(
            f"required burn evidence list malformed: {key}"
        )
    return list(value)


def _finite_decimal(value: object, *, context: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise X1BurnIntelligenceContractError(
            f"required numeric burn value missing: {context}"
        )
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise X1BurnIntelligenceContractError(
            f"required numeric burn value malformed: {context}"
        ) from exc
    if not parsed.is_finite():
        raise X1BurnIntelligenceContractError(
            f"required numeric burn value malformed: {context}"
        )
    return parsed


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
        required_fields = (
            "burned_raw",
            "burned_tokens",
            "burn_events",
            "minted_raw",
            "minted_tokens",
            "mint_events",
            "burn_to_emission_ratio",
            "net_issuance_raw",
            "net_issuance_tokens",
            "issuance_state",
        )
        for key in required_fields:
            if key not in value:
                raise X1BurnIntelligenceContractError(
                    f"verified burn window missing {key}: {label}"
                )
        for key in (
            "burned_raw",
            "burned_tokens",
            "burn_events",
            "minted_raw",
            "minted_tokens",
            "mint_events",
            "net_issuance_raw",
            "net_issuance_tokens",
            "issuance_state",
        ):
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
        if comparison_status == "ok":
            if change_state == "INSUFFICIENT_COVERAGE":
                raise X1BurnIntelligenceContractError(
                    f"available burn comparison cannot claim insufficient coverage: {label}"
                )
            for key in (
                "prior_start_exclusive",
                "prior_end_inclusive",
                "prior_burned_raw",
                "prior_burned_tokens",
            ):
                if comparison.get(key) is None:
                    raise X1BurnIntelligenceContractError(
                        f"available burn comparison missing {key}: {label}"
                    )
            if change_state in {"AVAILABLE", "NO_CHANGE_ZERO_BASE"}:
                _finite_decimal(
                    percent_change,
                    context=f"{label}.period_over_period.percent_change",
                )
            elif change_state == "NEW_BURN_ACTIVITY":
                if percent_change is not None:
                    raise X1BurnIntelligenceContractError(
                        f"non-numeric burn comparison state must preserve null percent: {label}"
                    )
        else:
            if change_state != "INSUFFICIENT_COVERAGE":
                raise X1BurnIntelligenceContractError(
                    f"unavailable burn comparison must preserve insufficient coverage: {label}"
                )
            if percent_change is not None:
                raise X1BurnIntelligenceContractError(
                    f"non-numeric burn comparison state must preserve null percent: {label}"
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
    burn_result: Mapping[str, Any],
    *,
    requested_asset: str | None = None,
) -> dict[str, object]:
    """Project one CMIS Burn Intelligence envelope without recomputing facts."""

    if not isinstance(burn_result, Mapping):
        raise X1BurnIntelligenceContractError("CMIS burn result must be an object")
    if burn_result.get("service") != "burn_intelligence":
        raise X1BurnIntelligenceContractError(
            "burn intelligence requires CMIS burn_intelligence"
        )
    if burn_result.get("chain") != "x1":
        raise X1BurnIntelligenceContractError("burn intelligence v1 is X1-only")
    if burn_result.get("status") not in {
        "ok",
        "partial",
        "unavailable",
    }:
        raise X1BurnIntelligenceContractError("unsupported CMIS burn status")

    if burn_result.get("execution_authorized") not in {None, False}:
        raise X1BurnIntelligenceContractError(
            "burn intelligence must preserve execution_authorized=false"
        )

    asset = _require_mapping(burn_result, "asset")
    data = _require_mapping(burn_result, "data")
    if data.get("contract_version") != CMIS_BURN_INTELLIGENCE_CONTRACT:
        raise X1BurnIntelligenceContractError(
            "CMIS burn_intelligence service contract mismatch"
        )
    asset_mint = _exact_x1_mint(asset.get("mint"))
    data_mint = _exact_x1_mint(data.get("mint"))
    if data_mint != asset_mint:
        raise X1BurnIntelligenceContractError(
            "CMIS burn data mint does not match resolved asset mint"
        )

    metrics = data.get("burn_metrics")
    if not isinstance(metrics, Mapping):
        raise X1BurnIntelligenceContractError("CMIS burn_metrics missing")
    _validate_burn_metrics(metrics)

    confidence = _require_mapping(tokenomics_result, "confidence")
    sources = _require_sequence(tokenomics_result, "sources")
    warnings = _require_sequence(tokenomics_result, "warnings")
    errors = _require_sequence(tokenomics_result, "errors")

    result: dict[str, object] = {
        "contract_version": BURN_INTELLIGENCE_CONTRACT,
        "product": "x1_burn_intelligence",
        "chain": "x1",
        "status": burn_result.get("status"),
        "requested_asset": requested_asset,
        "asset": deepcopy(dict(asset)),
        "burn_metrics": deepcopy(dict(metrics)),
        "observed_at": burn_result.get("observed_at"),
        "confidence": deepcopy(dict(confidence)),
        "sources": deepcopy(sources),
        "warnings": deepcopy(warnings),
        "errors": deepcopy(errors),
        "evidence_receipt": deepcopy(burn_result.get("evidence_receipt")),
        "proof_score": deepcopy(burn_result.get("proof_score")),
        "proof_score_separate_from_risk": True,
        "execution_authorized": False,
    }
    return result


__all__ = [
    "BURN_INTELLIGENCE_CONTRACT",
    "CMIS_BURN_INTELLIGENCE_CONTRACT",
    "X1BurnIntelligenceContractError",
    "build_x1_burn_intelligence",
]
