"""Deterministic evidence-needs policy for recommendation-style questions.

This module selects *which read-only CMIS investigations are needed* before
Roberta can synthesize an answer. It does not calculate market facts, risk, or
trade outcomes. X1 Scout/CMIS remain authoritative for every returned fact.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

from roberta.cmis.contracts import CMISOperation


RecommendationIntent: TypeAlias = Literal[
    "trade_decision",
    "trade_size",
    "safer_asset",
    "market_change",
    "liquidity_risk",
    "lp_decision",
    "price_move_reason",
    "general",
]


def _normalize(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def recommendation_intent(objective: object) -> RecommendationIntent:
    text = _normalize(objective)
    if not text:
        return "general"
    if any(term in text for term in ("is $", "too much", "trade size", "position size")):
        return "trade_size"
    if any(
        term in text
        for term in (
            "should i buy",
            "should i sell",
            "is it ok to buy",
            "is it okay to buy",
            "is it ok to purchase",
            "is it okay to purchase",
            "worth buying",
        )
    ):
        return "trade_decision"
    if any(term in text for term in ("which token", "which asset", "looks safer", "safer token")):
        return "safer_asset"
    if any(term in text for term in ("should i add lp", "add liquidity", "provide liquidity", "add lp")):
        return "lp_decision"
    if "liquidity" in text and any(
        term in text for term in ("danger", "dangerous", "risk", "safe", "thin")
    ):
        return "liquidity_risk"
    if any(term in text for term in ("why is the price", "why price", "why did the price")):
        return "price_move_reason"
    if any(term in text for term in ("what changed", "what has changed", "changed since")):
        return "market_change"
    return "general"


def recommendation_evidence_plan(objective: object) -> dict[str, object]:
    """Return the minimum deterministic evidence plan for the recognized intent.

    `pre_trade_check` is named as a required service only for a concrete trade
    decision/size question. X1 Scout's existing explicit pre-trade guard still
    requires an exact BUY/SELL side and USD amount before it can actually run.
    This plan never grants that authority by itself.
    """

    intent = recommendation_intent(objective)
    service_map: dict[RecommendationIntent, tuple[CMISOperation, ...]] = {
        "trade_decision": (
            "pre_trade_check",
            "historical_compare",
            "risk_check",
        ),
        "trade_size": (
            "pre_trade_check",
            "market_report",
            "risk_check",
        ),
        "safer_asset": ("rank", "risk_check", "market_report"),
        "market_change": ("historical_compare", "market_report"),
        "liquidity_risk": ("market_report", "risk_check"),
        "lp_decision": ("market_report", "risk_check", "tokenomics"),
        "price_move_reason": ("historical_compare", "market_report"),
        "general": (),
    }
    category_map: dict[RecommendationIntent, tuple[str, ...]] = {
        "trade_decision": (
            "current_market",
            "trade_size_liquidity",
            "risk",
            "historical_context",
            "recent_verified_activity_when_available",
            "execution_evidence_when_available",
        ),
        "trade_size": (
            "current_market",
            "trade_size_liquidity",
            "risk",
            "execution_evidence_when_available",
        ),
        "safer_asset": (
            "risk",
            "current_market",
            "evidence_quality",
        ),
        "market_change": (
            "historical_context",
            "current_market",
            "evidence_quality",
        ),
        "liquidity_risk": (
            "current_market",
            "risk",
            "evidence_scope",
        ),
        "lp_decision": (
            "current_market",
            "risk",
            "tokenomics",
            "lp_specific_evidence_when_available",
        ),
        "price_move_reason": (
            "historical_context",
            "current_market",
            "recent_verified_activity_when_available",
        ),
        "general": (),
    }

    services = list(service_map[intent])
    return {
        "intent": intent,
        "required_services": services,
        "required_evidence_categories": list(category_map[intent]),
        "read_only": True,
        "execution_authorized": False,
        "missing_required_evidence_must_be_disclosed": True,
        "market_calculation_authority": "cmis",
    }


def autonomous_x1_operations_for_recommendation(objective: object) -> list[CMISOperation]:
    """Return only operations already allowed in X1 Scout autonomous planning.

    Explicit pre-trade remains outside the autonomous planner and cannot be
    smuggled in through recommendation wording.
    """

    allowed = {
        "market_report",
        "rank",
        "historical_compare",
        "tokenomics",
        "risk_check",
    }
    return [
        operation
        for operation in recommendation_evidence_plan(objective)["required_services"]
        if operation in allowed
    ]  # type: ignore[return-value]


__all__ = [
    "RecommendationIntent",
    "autonomous_x1_operations_for_recommendation",
    "recommendation_evidence_plan",
    "recommendation_intent",
]
