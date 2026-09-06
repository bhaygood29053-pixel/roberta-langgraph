"""Deterministic X1 Scout projection of CMIS Large-Trade Discovery v1.

The Scout preserves the validated CMIS ranking verbatim. It does not discover
pools, rebuild windows, recalculate USD notional, derive direction, re-sort,
infer wallet ownership/behavior, widen scope, create risk, or recommend trades.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.cmis.large_trade_discovery import (
    SERVICE_CONTRACT_VERSION as CMIS_LARGE_TRADE_DISCOVERY_CONTRACT,
    validate_large_trade_discovery_response,
)

LARGE_TRADE_DISCOVERY_CONTRACT = "x1_large_trade_discovery/v1"


class X1LargeTradeDiscoveryContractError(ValueError):
    """Raised when CMIS output cannot satisfy the X1 Scout product."""


def build_x1_large_trade_discovery(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, object]:
    try:
        safe = validate_large_trade_discovery_response(
            result,
            expected_request=expected_request,
        )
    except Exception as exc:
        raise X1LargeTradeDiscoveryContractError(str(exc)) from exc

    data = safe["data"]
    return {
        "contract_version": LARGE_TRADE_DISCOVERY_CONTRACT,
        "product": "x1_large_trade_discovery",
        "chain": "x1",
        "status": "ok",
        "requested_asset_mint": expected_request["asset_mint"],
        "requested_direction": expected_request["direction"],
        "requested_limit": expected_request["limit"],
        "cmis_contract_version": CMIS_LARGE_TRADE_DISCOVERY_CONTRACT,
        "large_trade_discovery": deepcopy(data),
        "observed_at": safe.get("observed_at"),
        "confidence": deepcopy(safe.get("confidence") or {}),
        "sources": deepcopy(safe.get("sources") or []),
        "warnings": deepcopy(safe.get("warnings") or []),
        "errors": deepcopy(safe.get("errors") or []),
        "evidence_receipt": deepcopy(safe.get("evidence_receipt")),
        "proof_score": deepcopy(safe.get("proof_score")),
        "provider_scoped_ranking_is_global_x1_dex_ranking": False,
        "wallet_address_is_real_world_identity": False,
        "whale_insider_manipulator_label_authorized": False,
        "intent_inference_authorized": False,
        "coordinated_wallet_inference_authorized": False,
        "whole_market_price_impact_claim_authorized": False,
        "volume_causality_claim_authorized": False,
        "automatic_risk_conclusion_authorized": False,
        "trade_recommendation_authorized": False,
        "risk_interpretation": None,
        "execution_authorized": False,
    }


__all__ = [
    "CMIS_LARGE_TRADE_DISCOVERY_CONTRACT",
    "LARGE_TRADE_DISCOVERY_CONTRACT",
    "X1LargeTradeDiscoveryContractError",
    "build_x1_large_trade_discovery",
]
