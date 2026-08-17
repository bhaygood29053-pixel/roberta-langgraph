"""Deterministic user-facing presentation for CMIS pre-trade results.

Roberta owns the conversation, but not the underlying trade analysis.  This
module therefore formats only values already returned by CMIS.  It never
calculates trade-size risk, slippage, price impact, route quality, fees, or a
replacement risk recommendation.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any


_TECHNICAL_TERMS = (
    "technical analysis",
    "technical details",
    "show technical",
    "diagnostic",
    "diagnostics",
    "full report",
    "raw evidence",
    "show evidence",
    "underlying evidence",
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def technical_pretrade_details_requested(value: object) -> bool:
    """Return true only for an explicit technical/diagnostic detail request."""

    normalized = " ".join(str(value or "").strip().lower().split())
    return any(term in normalized for term in _TECHNICAL_TERMS)


def _asset_label(result: Mapping[str, Any]) -> str:
    asset = _mapping(result.get("asset"))
    for key in ("symbol", "name", "mint"):
        value = asset.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "this asset"


def _money(value: object) -> str | None:
    """Format one already-returned USD value without deriving a new value."""

    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return f"${value:,}"
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        if value.is_integer():
            return f"${int(value):,}"
        return f"${value:,}"
    if isinstance(value, str) and value.strip():
        text = value.strip()
        return text if text.startswith("$") else f"${text}"
    return None


def _trade_phrase(asset: str, trade: Mapping[str, Any]) -> str:
    side = trade.get("side")
    side_text = str(side or "").strip().upper()
    verb = {"BUY": "buying", "SELL": "selling"}.get(side_text, "making this trade in")
    notional = _money(trade.get("notional_usd"))
    if notional:
        return f"{verb} {notional} of {asset}"
    return f"{verb} {asset}"


def _recommendation(risk: Mapping[str, Any]) -> object:
    value = risk.get("recommendation")
    return value if value is not None else risk.get("outcome")


def _lead(recommendation: object, trade_phrase: str) -> str:
    token = str(recommendation or "").strip().upper()
    if token == "BLOCK":
        return f"I would not proceed with {trade_phrase} based on the checks I have."
    if token == "WARN":
        return f"I would be cautious about {trade_phrase}."
    if token == "PASS":
        return (
            f"The checks I have did not flag a warning or block for {trade_phrase}, "
            "but that only covers the evidence that was actually verified."
        )
    return f"I can't give a reliable go-ahead for {trade_phrase} from the evidence I have."


def _missing_evidence(
    data: Mapping[str, Any],
) -> list[str]:
    trade_size = _mapping(data.get("trade_size"))
    route = _mapping(data.get("route_analysis"))
    missing: list[str] = []

    if trade_size.get("assessment") is None:
        missing.append("trade-size assessment")
    if route.get("estimated_price_impact_percent") is None:
        missing.append("price-impact estimate")
    if route.get("estimated_slippage_percent") is None:
        missing.append("slippage estimate")
    if route.get("status") is None and route.get("route_scope") is None:
        missing.append("route analysis")
    if route.get("estimated_fees") is None:
        missing.append("fee estimate")
    return missing


def _fact_sentences(data: Mapping[str, Any]) -> list[str]:
    """Render only named fields already supplied by CMIS; never derive ratios."""

    sentences: list[str] = []
    market = _mapping(data.get("market"))
    trade_size = _mapping(data.get("trade_size"))
    route = _mapping(data.get("route_analysis"))

    liquidity = _money(market.get("verified_liquidity_usd"))
    volume = _money(market.get("verified_volume_24h_usd"))
    if liquidity is not None:
        sentences.append(f"Verified liquidity returned for this analysis is {liquidity}.")
    if volume is not None:
        sentences.append(f"Verified 24-hour volume returned for this analysis is {volume}.")

    assessment = trade_size.get("assessment")
    ratio = trade_size.get("notional_to_liquidity_ratio")
    if assessment is not None:
        text = f"The returned trade-size assessment is {assessment}."
        if ratio is not None:
            text += f" The returned notional-to-liquidity ratio is {ratio}."
        sentences.append(text)

    impact = route.get("estimated_price_impact_percent")
    slippage = route.get("estimated_slippage_percent")
    fees = route.get("estimated_fees")
    if impact is not None:
        sentences.append(f"The returned price-impact estimate is {impact}.")
    if slippage is not None:
        sentences.append(f"The returned slippage estimate is {slippage}.")
    if fees is not None:
        sentences.append(f"The returned fee estimate is {fees}.")

    return sentences


def _technical_text(
    result: Mapping[str, Any],
    *,
    recommendation: object,
    missing: list[str],
) -> str:
    data = _mapping(result.get("data"))
    payload = {
        "service": result.get("service"),
        "chain": result.get("chain"),
        "status": result.get("status"),
        "asset": dict(_mapping(result.get("asset"))),
        "trade": dict(_mapping(data.get("trade"))),
        "market": dict(_mapping(data.get("market"))),
        "trade_size": dict(_mapping(data.get("trade_size"))),
        "route_analysis": dict(_mapping(data.get("route_analysis"))),
        "risk_recommendation": recommendation,
        "risk": dict(_mapping(result.get("risk"))),
        "confidence": dict(_mapping(result.get("confidence"))),
        "warnings": list(result.get("warnings")) if isinstance(result.get("warnings"), list) else [],
        "errors": list(result.get("errors")) if isinstance(result.get("errors"), list) else [],
        "missing_analysis": list(missing),
    }
    return "Technical pre-trade details:\n" + json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        default=str,
    )


def build_pretrade_presentation(
    result: Mapping[str, Any],
    *,
    objective: object = None,
) -> dict[str, object] | None:
    """Build Roberta's deterministic conversational/technical pre-trade view.

    ``None`` is returned for non-pre-trade CMIS envelopes so ordinary Scout
    reports keep their existing Oracle synthesis path. Direct Scout callers may
    select technical mode from ``objective``; the top-level Roberta graph makes
    the final mode choice from the user's actual message instead.
    """

    if result.get("service") != "pre_trade_check":
        return None

    data = _mapping(result.get("data"))
    trade = _mapping(data.get("trade"))
    risk = _mapping(result.get("risk"))
    recommendation = _recommendation(risk)
    asset = _asset_label(result)
    phrase = _trade_phrase(asset, trade)
    missing = _missing_evidence(data)

    parts = [_lead(recommendation, phrase)]
    parts.extend(_fact_sentences(data))

    reasons = _string_list(risk.get("reasons"))
    flags = _string_list(risk.get("flags"))
    token = str(recommendation or "").strip().upper()
    if token == "WARN":
        parts.append("One or more returned checks raised a caution condition.")
    elif token == "BLOCK":
        parts.append("One or more returned checks produced a blocking condition.")

    if missing:
        if len(missing) == 1:
            missing_text = missing[0]
        else:
            missing_text = ", ".join(missing[:-1]) + f", and {missing[-1]}"
        parts.append(
            f"I still do not have a structured {missing_text} in this result, "
            "so I would treat the trade as not fully evaluated."
        )

    conversational = " ".join(part for part in parts if part).strip()
    technical = _technical_text(
        result,
        recommendation=recommendation,
        missing=missing,
    )
    technical_mode = technical_pretrade_details_requested(objective)

    return {
        "mode": "technical" if technical_mode else "conversational",
        "voice": "roberta",
        "user_text": technical if technical_mode else conversational,
        "conversational_text": conversational,
        "technical_text": technical,
        "cmis_status": result.get("status"),
        "recommendation": recommendation,
        "reasons": reasons,
        "flags": flags,
        "facts": {
            "asset": asset,
            "trade": dict(trade),
            "market": dict(_mapping(data.get("market"))),
            "trade_size": dict(_mapping(data.get("trade_size"))),
            "route_analysis": dict(_mapping(data.get("route_analysis"))),
        },
        "missing_evidence": missing,
    }


__all__ = [
    "build_pretrade_presentation",
    "technical_pretrade_details_requested",
]
