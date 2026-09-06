"""ROBERTA-side validation for CMIS Large-Trade Discovery v1.

The validator preserves CMIS-owned ranking and scope exactly. It never
rediscovers pools, rebuilds 24h windows, recalculates historical USD notional,
re-derives BUY/SELL, re-sorts the ranking, infers wallet ownership/behavior,
or widens provider-scoped evidence into a global X1 DEX claim.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

SERVICE = "large_trade_discovery"
SERVICE_CONTRACT_VERSION = "large_trade_discovery/v1"
RANKING_SCOPE = "verified_provider_scoped_current_market_pool_set_exact_24h"
RANKING_METRIC = "verified_historical_usd_notional"
RANKING_ORDER = "usd_notional_desc_then_slot_asc_then_signature_then_pool"


class CMISLargeTradeDiscoveryContractError(ValueError):
    """Raised when CMIS #531 response/request violates the accepted contract."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CMISLargeTradeDiscoveryContractError(
            f"{field} must be normalized text"
        )
    return value


def _mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise CMISLargeTradeDiscoveryContractError(
            f"required Large-Trade Discovery object missing: {key}"
        )
    return value


def _sequence(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, Mapping)
    ):
        raise CMISLargeTradeDiscoveryContractError(
            f"required Large-Trade Discovery list malformed: {key}"
        )
    return list(value)


def _decimal(value: Any, field: str, *, positive: bool = False) -> Decimal:
    if value is None or isinstance(value, bool):
        raise CMISLargeTradeDiscoveryContractError(
            f"{field} must be numeric"
        )
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CMISLargeTradeDiscoveryContractError(
            f"{field} must be numeric"
        ) from exc
    if not parsed.is_finite():
        raise CMISLargeTradeDiscoveryContractError(
            f"{field} must be finite"
        )
    if positive and parsed <= 0:
        raise CMISLargeTradeDiscoveryContractError(
            f"{field} must be positive"
        )
    return parsed


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CMISLargeTradeDiscoveryContractError(
            f"{field} must be a non-negative integer"
        )
    return value


def normalize_large_trade_discovery_request(
    *,
    asset_mint: Any,
    direction: Any = "ANY",
    limit: Any = 5,
) -> dict[str, object]:
    mint = _text(asset_mint, "asset_mint")
    normalized_direction = _text(
        direction if direction is not None else "ANY",
        "direction",
    ).upper()
    if normalized_direction not in {"ANY", "BUY", "SELL"}:
        raise CMISLargeTradeDiscoveryContractError(
            "direction must be ANY, BUY, or SELL"
        )
    if isinstance(limit, bool):
        raise CMISLargeTradeDiscoveryContractError(
            "limit must be an integer between 1 and 20"
        )
    try:
        parsed_limit = int(limit)
    except (TypeError, ValueError) as exc:
        raise CMISLargeTradeDiscoveryContractError(
            "limit must be an integer between 1 and 20"
        ) from exc
    if parsed_limit < 1 or parsed_limit > 20:
        raise CMISLargeTradeDiscoveryContractError(
            "limit must be an integer between 1 and 20"
        )
    if isinstance(limit, float) and not limit.is_integer():
        raise CMISLargeTradeDiscoveryContractError(
            "limit must be an integer between 1 and 20"
        )
    return {
        "asset_mint": mint,
        "direction": normalized_direction,
        "limit": parsed_limit,
    }


def validate_large_trade_discovery_response(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CMISLargeTradeDiscoveryContractError(
            "CMIS Large-Trade Discovery response must be an object"
        )
    safe = deepcopy(dict(response))
    if safe.get("service") != SERVICE:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery service mismatch"
        )
    if safe.get("chain") != "x1":
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery chain must remain x1"
        )
    if safe.get("status") != "ok":
        raise CMISLargeTradeDiscoveryContractError(
            "promoted Large-Trade Discovery requires CMIS ok status"
        )
    if safe.get("risk") is not None:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery must not promote a risk conclusion"
        )
    if safe.get("execution_authorized") not in (None, False):
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery must preserve execution_authorized=false"
        )

    expected_mint = _text(
        expected_request.get("asset_mint"),
        "expected_request.asset_mint",
    )
    expected_direction = _text(
        expected_request.get("direction"),
        "expected_request.direction",
    ).upper()
    expected_limit = expected_request.get("limit")
    if (
        isinstance(expected_limit, bool)
        or not isinstance(expected_limit, int)
        or expected_limit < 1
        or expected_limit > 20
    ):
        raise CMISLargeTradeDiscoveryContractError(
            "expected request limit is invalid"
        )

    asset = _mapping(safe, "asset")
    if asset.get("mint") != expected_mint:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery asset mint must match exact request"
        )
    if asset.get("canonical_id") != expected_mint:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery canonical asset id must match exact request"
        )

    data = _mapping(safe, "data")
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery contract mismatch"
        )
    for field, expected in (
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("read_only", True),
        ("ranking_complete_for_scope", True),
        ("execution_authorized", False),
    ):
        if data.get(field) is not expected:
            raise CMISLargeTradeDiscoveryContractError(
                f"Large-Trade Discovery {field} must be {str(expected).lower()}"
            )

    if data.get("ranking_metric") != RANKING_METRIC:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery ranking metric drift"
        )
    if data.get("ranking_order") != RANKING_ORDER:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery ranking order drift"
        )
    if data.get("ranking_scope") != RANKING_SCOPE:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery ranking scope widened"
        )
    if data.get("requested_direction") != expected_direction:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery direction must match request"
        )
    if data.get("requested_limit") != expected_limit:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery limit must match request"
        )

    requested_window = _mapping(data, "requested_window")
    start = _decimal(
        requested_window.get("start_epoch"),
        "requested_window.start_epoch",
    )
    end = _decimal(
        requested_window.get("end_epoch"),
        "requested_window.end_epoch",
    )
    duration = _decimal(
        requested_window.get("duration_seconds"),
        "requested_window.duration_seconds",
    )
    if duration != Decimal("86400") or end - start != Decimal("86400"):
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery must preserve an exact 24h window"
        )
    _decimal(data.get("evaluated_at"), "evaluated_at")

    scope = _mapping(data, "pool_scope")
    if scope.get("contract_version") != "x1_ninja_current_pool_scope/v1":
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery pool-scope contract mismatch"
        )
    pool_addresses = _sequence(scope, "pool_addresses")
    normalized_pools = [
        _text(item, "pool_scope.pool_addresses item")
        for item in pool_addresses
    ]
    if len(normalized_pools) != len(set(normalized_pools)):
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery pool addresses must be unique"
        )
    if scope.get("pool_count") != len(normalized_pools):
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery pool count mismatch"
        )
    if scope.get("provider_scoped_pool_universe_verified") is not True:
        raise CMISLargeTradeDiscoveryContractError(
            "provider-scoped pool universe must remain verified"
        )
    if scope.get("global_xdex_pool_universe_verified") is not False:
        raise CMISLargeTradeDiscoveryContractError(
            "global XDEX pool universe must remain unverified"
        )

    exact_swap_count = _nonnegative_int(
        data.get("exact_swap_count_examined"),
        "exact_swap_count_examined",
    )
    eligible_count = _nonnegative_int(
        data.get("eligible_trade_count"),
        "eligible_trade_count",
    )
    result_count = _nonnegative_int(
        data.get("result_count"),
        "result_count",
    )
    if eligible_count > exact_swap_count:
        raise CMISLargeTradeDiscoveryContractError(
            "eligible trade count cannot exceed examined exact swaps"
        )
    if result_count > eligible_count or result_count > expected_limit:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery result count exceeds bounded query"
        )

    rows = _sequence(data, "results")
    if len(rows) != result_count:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery result count mismatch"
        )

    normalized_rows: list[tuple[Decimal, int, str, str]] = []
    signatures: set[str] = set()
    for index, raw in enumerate(rows, start=1):
        if not isinstance(raw, Mapping):
            raise CMISLargeTradeDiscoveryContractError(
                f"Large-Trade Discovery results[{index - 1}] must be an object"
            )
        row = raw
        if row.get("rank") != index:
            raise CMISLargeTradeDiscoveryContractError(
                "Large-Trade Discovery ranks must be contiguous and unchanged"
            )
        signature = _text(
            row.get("transaction_signature"),
            f"results[{index - 1}].transaction_signature",
        )
        if signature in signatures:
            raise CMISLargeTradeDiscoveryContractError(
                "Large-Trade Discovery transaction signatures must be unique"
            )
        signatures.add(signature)
        slot = _nonnegative_int(
            row.get("slot"),
            f"results[{index - 1}].slot",
        )
        _decimal(
            row.get("block_time"),
            f"results[{index - 1}].block_time",
        )
        pool_address = _text(
            row.get("pool_address"),
            f"results[{index - 1}].pool_address",
        )
        if pool_address not in set(normalized_pools):
            raise CMISLargeTradeDiscoveryContractError(
                "ranked trade pool must remain inside verified pool scope"
            )
        direction = _text(
            row.get("direction"),
            f"results[{index - 1}].direction",
        ).upper()
        if direction not in {"BUY", "SELL"}:
            raise CMISLargeTradeDiscoveryContractError(
                "ranked trade direction must remain BUY or SELL"
            )
        if expected_direction != "ANY" and direction != expected_direction:
            raise CMISLargeTradeDiscoveryContractError(
                "ranked trade direction violates request filter"
            )
        if row.get("asset_mint") != expected_mint:
            raise CMISLargeTradeDiscoveryContractError(
                "ranked trade exact asset mint mismatch"
            )
        _decimal(
            row.get("asset_amount"),
            f"results[{index - 1}].asset_amount",
            positive=True,
        )
        _text(
            row.get("quote_mint"),
            f"results[{index - 1}].quote_mint",
        )
        _decimal(
            row.get("quote_amount"),
            f"results[{index - 1}].quote_amount",
            positive=True,
        )
        notional = _decimal(
            row.get("verified_usd_notional"),
            f"results[{index - 1}].verified_usd_notional",
            positive=True,
        )
        if row.get("usd_notional_verified") is not True:
            raise CMISLargeTradeDiscoveryContractError(
                "ranked trade USD notional must remain verified"
            )

        wallet_verified = row.get("wallet_attribution_verified")
        if not isinstance(wallet_verified, bool):
            raise CMISLargeTradeDiscoveryContractError(
                "wallet attribution verification must remain explicit"
            )
        if row.get("real_world_wallet_owner_verified") is not False:
            raise CMISLargeTradeDiscoveryContractError(
                "public wallet address must not become real-world owner identity"
            )
        wallet_address = row.get("wallet_address")
        wallet_fact_time = row.get("wallet_fact_time")
        if wallet_verified:
            _text(
                wallet_address,
                f"results[{index - 1}].wallet_address",
            )
            _text(
                wallet_fact_time,
                f"results[{index - 1}].wallet_fact_time",
            )
        elif wallet_address is not None or wallet_fact_time is not None:
            raise CMISLargeTradeDiscoveryContractError(
                "unverified wallet attribution must not expose wallet identity/fact time"
            )

        handoff_id = row.get("trade_price_impact_evidence_id")
        handoff_ready = row.get("trade_price_impact_handoff_ready")
        if not isinstance(handoff_ready, bool):
            raise CMISLargeTradeDiscoveryContractError(
                "trade price-impact handoff readiness must remain explicit"
            )
        if handoff_ready:
            if not wallet_verified:
                raise CMISLargeTradeDiscoveryContractError(
                    "trade price-impact handoff requires verified wallet attribution"
                )
            _text(
                handoff_id,
                f"results[{index - 1}].trade_price_impact_evidence_id",
            )
        elif handoff_id is not None:
            raise CMISLargeTradeDiscoveryContractError(
                "non-ready trade price-impact handoff must not expose an evidence id"
            )

        normalized_rows.append(
            (notional, slot, signature, pool_address)
        )

    expected_order = sorted(
        normalized_rows,
        key=lambda item: (-item[0], item[1], item[2], item[3]),
    )
    if normalized_rows != expected_order:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery CMIS rank/order is not canonical"
        )

    boundaries = _mapping(data, "evidence_boundaries")
    expected_boundaries = {
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
    }
    if dict(boundaries) != expected_boundaries:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery evidence boundary drift"
        )

    confidence = _mapping(safe, "confidence")
    for field in (
        "ranking_complete_for_scope",
        "pool_scope_verified",
        "window_coverage_verified",
        "usd_notional_basis_verified",
    ):
        if confidence.get(field) is not True:
            raise CMISLargeTradeDiscoveryContractError(
                f"Large-Trade Discovery confidence {field} must remain verified"
            )
    if not isinstance(
        confidence.get("wallet_attribution_complete_for_results"),
        bool,
    ):
        raise CMISLargeTradeDiscoveryContractError(
            "wallet attribution completeness must remain explicit"
        )
    if confidence.get("source_independence_verified") is not False:
        raise CMISLargeTradeDiscoveryContractError(
            "Large-Trade Discovery source independence must remain unverified"
        )

    _sequence(safe, "sources")
    _sequence(safe, "warnings")
    _sequence(safe, "errors")
    return safe


__all__ = [
    "CMISLargeTradeDiscoveryContractError",
    "RANKING_METRIC",
    "RANKING_ORDER",
    "RANKING_SCOPE",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "normalize_large_trade_discovery_request",
    "validate_large_trade_discovery_response",
]
