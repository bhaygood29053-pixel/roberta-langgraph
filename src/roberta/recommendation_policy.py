"""Deterministic evidence-needs policy for recommendation-style questions.

This module selects *which read-only CMIS investigations are needed* before
Roberta can synthesize an answer. It does not calculate market facts, risk, or
trade outcomes. Chain Scouts/CMIS remain authoritative for every returned fact.
"""

from __future__ import annotations

import re
from typing import Literal, TypeAlias

from roberta.cmis.contracts import CMISOperation


RecommendationIntent: TypeAlias = Literal[
    "trade_decision",
    "trade_size",
    "safer_asset",
    "risk_assessment",
    "market_change",
    "liquidity_risk",
    "lp_decision",
    "price_move_reason",
    "general",
]


def _normalize(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _has_amount_cue(text: str) -> bool:
    """Recognize a user-visible amount cue without parsing or authorizing it."""

    return bool(
        re.search(r"\$\s*\d", text)
        or re.search(r"\b\d[\d,.]*\s*(?:usd|usdc|dollars?)\b", text)
    )


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def recommendation_intent(objective: object) -> RecommendationIntent:
    """Classify common user decision language into a deterministic evidence intent.

    This is deliberately a small intent classifier, not a market-reasoning model.
    It recognizes ordinary wording variants while leaving actual side/amount
    extraction and explicit pre-trade authorization to the existing guarded path.
    """

    text = _normalize(objective)
    if not text:
        return "general"

    # Concrete amount/position questions are primarily sizing questions. Merely
    # recognizing the wording does not authorize pre_trade_check; the Scout's
    # explicit side+amount guard remains authoritative.
    trade_words = (
        "buy",
        "buying",
        "purchase",
        "purchasing",
        "sell",
        "selling",
        "trade",
        "position",
    )
    size_words = (
        "too much",
        "too large",
        "too big",
        "trade size",
        "position size",
        "order size",
        "size this",
        "size my",
    )
    if _has_any(text, size_words) or (
        _has_amount_cue(text) and _has_any(text, trade_words)
    ):
        return "trade_size"

    trade_decision_patterns = (
        r"\bshould i (?:buy|sell|purchase|trade)\b",
        r"\bcan i (?:buy|sell|purchase|trade)\b",
        r"\bcould i (?:buy|sell|purchase|trade)\b",
        r"\bwould (?:buying|selling|purchasing|trading)\b",
        r"\bdo you think i should (?:buy|sell|purchase|trade)\b",
        r"\bis it (?:ok|okay) to (?:buy|sell|purchase|trade)\b",
    )
    if any(re.search(pattern, text) for pattern in trade_decision_patterns) or _has_any(
        text,
        (
            "worth buying",
            "worth selling",
            "good idea to buy",
            "good idea to sell",
            "a good buy",
        ),
    ):
        return "trade_decision"

    safer_comparison = bool(
        re.search(r"\bwhich\b.*\b(?:safer|less risky|lower risk)\b", text)
    )
    if safer_comparison or _has_any(
        text,
        (
            "which token",
            "which asset",
            "which is safer",
            "which one is safer",
            "safer token",
            "safer asset",
            "less risky",
            "lower risk",
        ),
    ):
        return "safer_asset"

    # LP intent is checked before generic liquidity-risk language so "should I
    # provide liquidity" is treated as a decision rather than a market-risk ask.
    if _has_any(
        text,
        (
            "should i add lp",
            "should i add liquidity",
            "should i provide liquidity",
            "do you think i should add liquidity",
            "add liquidity",
            "provide liquidity",
            "supply liquidity",
            "liquidity provider",
        ),
    ):
        return "lp_decision"

    if "liquidity" in text and _has_any(
        text,
        (
            "danger",
            "dangerous",
            "risk",
            "risky",
            "safe",
            "thin",
            "shallow",
            "low liquidity",
        ),
    ):
        return "liquidity_risk"

    price_reason_question = bool(
        re.search(r"\bwhy\s+(?:is|did|has)\b.{0,80}\bprice\b", text)
        or re.search(r"\bwhat\s+caused\b.{0,80}\bprice\b", text)
        or re.search(r"\bwhat(?:'s|\s+is)\s+driving\b.{0,80}\bprice\b", text)
    )
    if price_reason_question and _has_any(
        text,
        (
            "fall",
            "falling",
            "fell",
            "drop",
            "dropping",
            "down",
            "rise",
            "rising",
            "rose",
            "up",
            "pump",
            "pumping",
            "move",
            "moving",
        ),
    ):
        return "price_move_reason"

    if _has_any(
        text,
        (
            "what changed",
            "what has changed",
            "what's changed",
            "what is different",
            "changed since",
            "change since",
            "how has this market changed",
            "how has the market changed",
        ),
    ):
        return "market_change"

    # A plain token/asset safety question deserves an explicit recommendation
    # evidence plan instead of relying only on the Scout's generic risk keyword
    # fallback. This still does not invent a risk level: only CMIS risk_check may
    # provide the deterministic current risk assessment. Exact-mint wording and
    # ordinary "risk for/of <asset>" wording are recognized explicitly so symbol
    # ambiguity cannot bypass the post-Scout Decision Quality contract.
    exact_asset_risk_question = bool(
        re.search(
            r"\bis\s+(?:exact\s+mint\s+)?[a-z0-9._-]+\s+(?:risky|safe)\b",
            text,
        )
    )
    named_asset_risk_question = bool(
        re.search(
            r"\b(?:what(?:'s|\s+is)\s+(?:the\s+)?(?:verified\s+)?|verified\s+)"
            r"risk\s+(?:for|of)\s+[a-z0-9._-]+\b",
            text,
        )
    )
    if _has_any(
        text,
        (
            "is this token risky",
            "is this asset risky",
            "is this token safe",
            "is this asset safe",
            "how risky is this token",
            "how risky is this asset",
            "risk level",
            "rug risk",
        ),
    ) or exact_asset_risk_question or named_asset_risk_question:
        return "risk_assessment"

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
        "risk_assessment": ("risk_check", "market_report", "tokenomics"),
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
        "risk_assessment": (
            "risk",
            "current_market",
            "tokenomics",
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
    smuggled in through recommendation wording. If the ideal plan includes a
    pre-trade check that cannot run autonomously, market_report is added so the
    Scout still gathers current market evidence instead of silently skipping it.
    """

    plan = recommendation_evidence_plan(objective)
    raw_services = list(plan["required_services"])
    allowed = {
        "market_report",
        "rank",
        "historical_compare",
        "tokenomics",
        "risk_check",
    }
    result: list[CMISOperation] = []
    if "pre_trade_check" in raw_services:
        result.append("market_report")
    for operation in raw_services:
        if operation in allowed and operation not in result:
            result.append(operation)  # type: ignore[arg-type]
    return result[:3]


__all__ = [
    "RecommendationIntent",
    "autonomous_x1_operations_for_recommendation",
    "recommendation_evidence_plan",
    "recommendation_intent",
]
