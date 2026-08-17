"""Deterministic user-facing presentation for CMIS pre-trade results.

Roberta owns the conversation, but not the underlying trade analysis. This
module therefore formats only values already returned by CMIS. It never
calculates trade-size risk, slippage, price impact, route quality, fees, or a
replacement risk recommendation.

Conversational mode may round or relabel returned values for readability, but
the exact CMIS values remain untouched in ``facts`` and technical mode.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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

_PLAIN_MISSING_LABELS = {
    "trade-size assessment": "trade-size assessment",
    "price-impact estimate": "price impact",
    "slippage estimate": "slippage",
    "route analysis": "route quality",
    "fee estimate": "fees",
}


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


def _decimal(value: object) -> Decimal | None:
    """Read one returned numeric value for display formatting only."""

    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, (int, float)):
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            return None
    elif isinstance(value, str) and value.strip():
        text = value.strip().replace(",", "")
        if text.startswith("$"):
            text = text[1:]
        if text.endswith("%"):
            text = text[:-1]
        try:
            number = Decimal(text)
        except InvalidOperation:
            return None
    else:
        return None
    return number if number.is_finite() else None


def _money(value: object) -> str | None:
    """Format one returned USD notional without changing its meaning."""

    number = _decimal(value)
    if number is None:
        return None
    if number == number.to_integral_value():
        return f"${number:,.0f}"
    text = format(number, "f").rstrip("0").rstrip(".")
    return f"${text}"


def _friendly_money(value: object) -> str | None:
    """Round a returned USD value for normal conversational display."""

    number = _decimal(value)
    if number is None:
        return None
    magnitude = abs(number)
    if magnitude >= Decimal("1000"):
        rounded = number.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"${rounded:,.0f}"
    if magnitude >= Decimal("1"):
        rounded = number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if rounded == rounded.to_integral_value():
            return f"${rounded:,.0f}"
        return f"${rounded:,.2f}"
    rounded = number.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    text = format(rounded, "f").rstrip("0").rstrip(".") or "0"
    return f"${text}"


def _friendly_fraction_percent(value: object) -> str | None:
    """Display a returned ratio as a percentage without re-evaluating it."""

    ratio = _decimal(value)
    if ratio is None:
        return None
    percent = ratio * Decimal("100")
    quantum = Decimal("0.01") if abs(percent) < Decimal("1") else Decimal("0.1")
    rounded = percent.quantize(quantum, rounding=ROUND_HALF_UP)
    text = format(rounded, "f").rstrip("0").rstrip(".") or "0"
    return f"{text}%"


def _friendly_percent_value(value: object) -> str | None:
    """Display a CMIS field whose unit is already percentage points."""

    percent = _decimal(value)
    if percent is None:
        return None
    quantum = Decimal("0.01") if abs(percent) < Decimal("1") else Decimal("0.01")
    rounded = percent.quantize(quantum, rounding=ROUND_HALF_UP)
    text = format(rounded, "f").rstrip("0").rstrip(".") or "0"
    return f"{text}%"


def _friendly_scalar(value: object) -> str | None:
    number = _decimal(value)
    if number is None:
        return str(value).strip() if isinstance(value, str) and value.strip() else None
    rounded = number.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return format(rounded, "f").rstrip("0").rstrip(".") or "0"


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
            f"Based on the checks I can currently verify, I don't see a warning or block "
            f"for {trade_phrase}."
        )
    return f"I can't give a reliable go-ahead for {trade_phrase} from the evidence I have."


def _missing_evidence(data: Mapping[str, Any]) -> list[str]:
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


def _trade_size_sentence(trade_size: Mapping[str, Any]) -> str | None:
    assessment = str(trade_size.get("assessment") or "").strip().upper()
    ratio = _friendly_fraction_percent(trade_size.get("notional_to_liquidity_ratio"))

    sentence = ""
    if assessment == "PASS":
        sentence = "The trade size passed the current trade-size check."
    elif assessment == "WARN":
        sentence = "The current trade-size check raised a caution."
    elif assessment == "BLOCK":
        sentence = "The current trade-size check returned a block."
    elif assessment:
        sentence = "The trade-size check returned a result that needs review."

    if ratio:
        ratio_sentence = (
            f"The order is about {ratio} of the verified liquidity used in this analysis."
        )
        return f"{sentence} {ratio_sentence}".strip()
    return sentence or None


def _fact_sentences(data: Mapping[str, Any], *, asset: str) -> list[str]:
    """Render human-readable views of fields already supplied by CMIS."""

    sentences: list[str] = []
    market = _mapping(data.get("market"))
    trade_size = _mapping(data.get("trade_size"))
    route = _mapping(data.get("route_analysis"))

    liquidity = _friendly_money(market.get("verified_liquidity_usd"))
    volume = _friendly_money(market.get("verified_volume_24h_usd"))
    if liquidity is not None:
        sentences.append(f"{asset} has about {liquidity} in verified liquidity for this analysis.")
    if volume is not None:
        sentences.append(f"Verified 24-hour volume is about {volume}.")

    trade_size_text = _trade_size_sentence(trade_size)
    if trade_size_text:
        sentences.append(trade_size_text)

    impact = _friendly_percent_value(route.get("estimated_price_impact_percent"))
    slippage = _friendly_percent_value(route.get("estimated_slippage_percent"))
    fees = _friendly_scalar(route.get("estimated_fees"))
    if impact is not None:
        sentences.append(f"Estimated price impact is {impact}.")
    if slippage is not None:
        sentences.append(f"Estimated slippage is {slippage}.")
    if fees is not None:
        sentences.append(f"Estimated fees are {fees}.")

    return sentences


def _plain_list(values: list[str]) -> str:
    labels = [_PLAIN_MISSING_LABELS.get(value, value) for value in values]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def _missing_paragraph(missing: list[str]) -> str | None:
    if not missing:
        return None
    details = _plain_list(missing)
    return (
        f"I still don't have verified information for {details}, so I would treat the trade "
        "as not fully evaluated. That means I can't reliably tell you the final execution "
        "price or fill quality yet."
    )


def _bottom_line(recommendation: object, *, missing: list[str]) -> str:
    token = str(recommendation or "").strip().upper()
    if token == "BLOCK":
        return "Bottom line: based on the current checks, I would not proceed with this trade."
    if token == "WARN":
        if missing:
            return (
                "Bottom line: the current checks call for caution, and some execution risk is "
                "still not fully evaluated."
            )
        return "Bottom line: the current checks call for caution."
    if token == "PASS":
        if missing:
            return (
                "Bottom line: the currently available checks did not block the trade, but "
                "execution risk is not fully evaluated yet."
            )
        return (
            "Bottom line: the currently available checks did not flag a warning or block. "
            "This is still analysis, not an automatic trade or execution authorization."
        )
    return "Bottom line: I do not have enough verified evidence to give a reliable go-ahead."


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

    paragraphs = [_lead(recommendation, phrase)]
    facts = _fact_sentences(data, asset=asset)
    if facts:
        paragraphs.append(" ".join(facts))

    missing_text = _missing_paragraph(missing)
    if missing_text:
        paragraphs.append(missing_text)

    paragraphs.append(_bottom_line(recommendation, missing=missing))

    conversational = "\n\n".join(part for part in paragraphs if part).strip()
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
        "reasons": _string_list(risk.get("reasons")),
        "flags": _string_list(risk.get("flags")),
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
