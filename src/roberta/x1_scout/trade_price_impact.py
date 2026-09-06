"""Deterministic X1 Scout projection of CMIS Trade Price-Impact Intelligence v1.

The Scout preserves the validated CMIS #498 projection verbatim. It does not
recalculate reserve changes, prices, price impact, volume contribution,
next-trade ordering, risk, recommendations, wallet identity, or causality.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.cmis.trade_price_impact import (
    SERVICE_CONTRACT_VERSION as CMIS_TRADE_PRICE_IMPACT_CONTRACT,
    validate_trade_price_impact_response,
)

TRADE_PRICE_IMPACT_CONTRACT = "x1_trade_price_impact_intelligence/v1"


class X1TradePriceImpactContractError(ValueError):
    """Raised when CMIS output cannot satisfy the X1 Scout product."""


def build_x1_trade_price_impact_intelligence(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, object]:
    try:
        safe = validate_trade_price_impact_response(
            result,
            expected_request=expected_request,
        )
    except Exception as exc:
        raise X1TradePriceImpactContractError(str(exc)) from exc

    data = safe["data"]
    return {
        "contract_version": TRADE_PRICE_IMPACT_CONTRACT,
        "product": "x1_trade_price_impact_intelligence",
        "chain": "x1",
        "status": "ok",
        "requested_asset_mint": expected_request["asset_mint"],
        "cmis_contract_version": CMIS_TRADE_PRICE_IMPACT_CONTRACT,
        "trade_price_impact": deepcopy(data),
        "observed_at": safe.get("observed_at"),
        "confidence": deepcopy(safe.get("confidence") or {}),
        "sources": deepcopy(safe.get("sources") or []),
        "warnings": deepcopy(safe.get("warnings") or []),
        "errors": deepcopy(safe.get("errors") or []),
        "evidence_receipt": deepcopy(safe.get("evidence_receipt")),
        "proof_score": deepcopy(safe.get("proof_score")),
        "wallet_address_is_real_world_identity": False,
        "whale_insider_manipulator_label_authorized": False,
        "intent_inference_authorized": False,
        "coordinated_wallet_inference_authorized": False,
        "whole_market_price_impact_claim_authorized": False,
        "volume_causality_claim_authorized": False,
        "automatic_risk_conclusion_authorized": False,
        "trade_recommendation_authorized": False,
        "pool_local_state_transition_authorized": True,
        "risk_interpretation": None,
        "execution_authorized": False,
    }


__all__ = [
    "CMIS_TRADE_PRICE_IMPACT_CONTRACT",
    "TRADE_PRICE_IMPACT_CONTRACT",
    "X1TradePriceImpactContractError",
    "build_x1_trade_price_impact_intelligence",
]
