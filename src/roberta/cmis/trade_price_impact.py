"""ROBERTA-side validation for promoted CMIS Trade Price-Impact Intelligence v1.

The validator preserves CMIS-owned wallet/transaction/pool/price-impact facts
without recalculating reserve math, execution price, price impact, volume
contribution, next-trade ordering, risk, or recommendations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

SERVICE = "trade_price_impact_intelligence"
SERVICE_CONTRACT_VERSION = "trade_price_impact_intelligence/v1"
PROMOTED_WINDOW_SCOPE = "exact_selected_pool_rolling_24h"


class CMISTradePriceImpactContractError(ValueError):
    """Raised when the promoted CMIS #498 contract is violated."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CMISTradePriceImpactContractError(
            f"{field} must be normalized text"
        )
    return value


def _mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise CMISTradePriceImpactContractError(
            f"required trade price-impact object missing: {key}"
        )
    return value


def _sequence(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, Mapping)
    ):
        raise CMISTradePriceImpactContractError(
            f"required trade price-impact list malformed: {key}"
        )
    return list(value)


def _numeric_text(value: Any, field: str) -> str:
    text = _text(value, field)
    try:
        parsed = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise CMISTradePriceImpactContractError(
            f"{field} must be numeric text"
        ) from exc
    if not parsed.is_finite():
        raise CMISTradePriceImpactContractError(
            f"{field} must be finite numeric text"
        )
    return text


def normalize_trade_price_impact_request(
    *,
    evidence_id: Any,
    asset_mint: Any,
) -> dict[str, str]:
    return {
        "evidence_id": _text(evidence_id, "evidence_id"),
        "asset_mint": _text(asset_mint, "asset_mint"),
    }


def validate_trade_price_impact_response(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CMISTradePriceImpactContractError(
            "CMIS trade price-impact response must be an object"
        )
    safe = deepcopy(dict(response))
    if safe.get("service") != SERVICE:
        raise CMISTradePriceImpactContractError(
            "trade price-impact service mismatch"
        )
    if safe.get("chain") != "x1":
        raise CMISTradePriceImpactContractError(
            "trade price-impact chain must remain x1"
        )
    if safe.get("status") != "ok":
        raise CMISTradePriceImpactContractError(
            "promoted trade price-impact requires CMIS ok status"
        )
    if safe.get("risk") is not None:
        raise CMISTradePriceImpactContractError(
            "trade price-impact must not promote an automatic risk conclusion"
        )
    if safe.get("execution_authorized") is not False:
        raise CMISTradePriceImpactContractError(
            "trade price-impact must preserve execution_authorized=false"
        )

    asset = _mapping(safe, "asset")
    expected_mint = _text(
        expected_request.get("asset_mint"),
        "expected_request.asset_mint",
    )
    if asset.get("mint") != expected_mint:
        raise CMISTradePriceImpactContractError(
            "response asset mint must match exact request identity"
        )
    if asset.get("canonical_id") != expected_mint:
        raise CMISTradePriceImpactContractError(
            "response canonical asset id must match exact request identity"
        )

    data = _mapping(safe, "data")
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISTradePriceImpactContractError(
            "trade price-impact service contract mismatch"
        )
    for field, expected in (
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("read_only", True),
        ("execution_authorized", False),
    ):
        if data.get(field) is not expected:
            raise CMISTradePriceImpactContractError(
                f"trade price-impact {field} must be {str(expected).lower()}"
            )

    trade = _mapping(data, "wallet_trade")
    if trade.get("requested_asset_mint") != expected_mint:
        raise CMISTradePriceImpactContractError(
            "wallet trade mint must match exact request identity"
        )
    _text(trade.get("wallet_address"), "wallet_trade.wallet_address")
    _text(
        trade.get("transaction_signature"),
        "wallet_trade.transaction_signature",
    )
    if isinstance(trade.get("slot"), bool) or not isinstance(
        trade.get("slot"), int
    ) or trade["slot"] < 0:
        raise CMISTradePriceImpactContractError(
            "wallet_trade.slot must be a non-negative integer"
        )
    _text(trade.get("fact_time"), "wallet_trade.fact_time")
    if trade.get("direction") not in {"BUY", "SELL"}:
        raise CMISTradePriceImpactContractError(
            "wallet_trade.direction must remain BUY or SELL"
        )
    if trade.get("real_world_identity_verified") is not False:
        raise CMISTradePriceImpactContractError(
            "wallet address must not become real-world identity"
        )
    if trade.get("wallet_trade_amount_attribution_verified") is not True:
        raise CMISTradePriceImpactContractError(
            "wallet trade amount attribution must remain verified"
        )
    _numeric_text(trade.get("asset_amount"), "wallet_trade.asset_amount")
    _numeric_text(trade.get("quote_amount"), "wallet_trade.quote_amount")
    _text(trade.get("amount_basis"), "wallet_trade.amount_basis")

    pool = _mapping(data, "pool")
    _text(pool.get("pool_address"), "pool.pool_address")
    for field in (
        "transaction_pool_membership_verified",
        "single_recognized_amm_attribution_verified",
        "pool_local_state_transition_verified",
    ):
        if pool.get(field) is not True:
            raise CMISTradePriceImpactContractError(
                f"pool.{field} must remain verified"
            )
    for field in (
        "pre_trade_asset_reserve",
        "pre_trade_quote_reserve",
        "post_trade_asset_reserve",
        "post_trade_quote_reserve",
        "pre_trade_spot_price_native",
        "average_execution_price_native",
        "post_trade_spot_price_native",
        "spot_price_change_percent",
        "execution_price_impact_percent_vs_pre_spot",
    ):
        _numeric_text(pool.get(field), f"pool.{field}")

    measured = _mapping(data, "measured_window")
    if measured.get("scope") != PROMOTED_WINDOW_SCOPE:
        raise CMISTradePriceImpactContractError(
            "measured-window scope must remain exact selected pool rolling 24h"
        )
    _mapping(measured, "requested_window")
    for field in (
        "trade_usd_notional",
        "verified_window_volume_usd",
        "trade_volume_contribution_percent",
    ):
        _numeric_text(measured.get(field), f"measured_window.{field}")
    if measured.get(
        "numerator_denominator_same_verified_usd_basis"
    ) is not True:
        raise CMISTradePriceImpactContractError(
            "trade/window USD basis must remain verified and common"
        )
    if measured.get("window_coverage_verified") is not True:
        raise CMISTradePriceImpactContractError(
            "measured-window coverage must remain verified"
        )

    next_trade = _mapping(data, "next_verified_trade")
    if not isinstance(next_trade.get("verified"), bool):
        raise CMISTradePriceImpactContractError(
            "next_verified_trade.verified must remain explicit"
        )
    _text(next_trade.get("reason"), "next_verified_trade.reason")
    if next_trade["verified"] is True:
        _text(
            next_trade.get("signature"),
            "next_verified_trade.signature",
        )
        if isinstance(next_trade.get("slot"), bool) or not isinstance(
            next_trade.get("slot"), int
        ) or next_trade["slot"] < 0:
            raise CMISTradePriceImpactContractError(
                "verified next trade slot must be a non-negative integer"
            )
        _numeric_text(
            next_trade.get("execution_price_native"),
            "next_verified_trade.execution_price_native",
        )
    else:
        if next_trade.get("execution_price_native") is not None:
            raise CMISTradePriceImpactContractError(
                "unverified next trade must not expose an execution price"
            )

    boundaries = _mapping(data, "evidence_boundaries")
    expected_boundaries = {
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
    }
    if dict(boundaries) != expected_boundaries:
        raise CMISTradePriceImpactContractError(
            "trade price-impact evidence boundary drift"
        )

    _mapping(safe, "confidence")
    _sequence(safe, "sources")
    _sequence(safe, "warnings")
    _sequence(safe, "errors")
    return safe


__all__ = [
    "CMISTradePriceImpactContractError",
    "PROMOTED_WINDOW_SCOPE",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "normalize_trade_price_impact_request",
    "validate_trade_price_impact_response",
]
