"""Deterministic answer-first presentation for CMIS pre-trade results.

Roberta owns the conversation, not the market calculation. This formatter uses
only values and statuses already returned by CMIS. Risk, proof strength, and
missing evidence remain separate. The normal response is concise; exact
technical evidence is available only on explicit request.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from roberta.evidence_aware import evidence_context


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
_EVIDENCE_CATEGORY_LABELS = {
    "identity": "asset identity proof",
    "semantics": "field semantics",
    "freshness": "freshness",
    "source_independence": "independent-source verification",
    "agreement": "independent-source agreement",
    "scope": "evidence scope",
    "historical_coverage": "historical coverage",
    "source_traceability": "source traceability",
}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def technical_pretrade_details_requested(value: object) -> bool:
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
    number = _decimal(value)
    if number is None:
        return None
    if number == number.to_integral_value():
        return f"${number:,.0f}"
    text = format(number, "f").rstrip("0").rstrip(".")
    return f"${text}"


def _friendly_money(value: object) -> str | None:
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
    ratio = _decimal(value)
    if ratio is None:
        return None
    percent = ratio * Decimal("100")
    quantum = Decimal("0.01") if abs(percent) < Decimal("1") else Decimal("0.1")
    rounded = percent.quantize(quantum, rounding=ROUND_HALF_UP)
    text = format(rounded, "f").rstrip("0").rstrip(".") or "0"
    return f"{text}%"


def _friendly_percent_value(value: object) -> str | None:
    percent = _decimal(value)
    if percent is None:
        return None
    rounded = percent.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    text = format(rounded, "f").rstrip("0").rstrip(".") or "0"
    return f"{text}%"


def _friendly_scalar(value: object) -> str | None:
    number = _decimal(value)
    if number is None:
        return str(value).strip() if isinstance(value, str) and value.strip() else None
    rounded = number.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return format(rounded, "f").rstrip("0").rstrip(".") or "0"


def _trade_phrase(asset: str, trade: Mapping[str, Any]) -> str:
    side_text = str(trade.get("side") or "").strip().upper()
    verb = {"BUY": "buying", "SELL": "selling"}.get(side_text, "making this trade in")
    notional = _money(trade.get("notional_usd"))
    return f"{verb} {notional} of {asset}" if notional else f"{verb} {asset}"


def _recommendation(risk: Mapping[str, Any]) -> object:
    value = risk.get("recommendation")
    return value if value is not None else risk.get("outcome")


def _lead(recommendation: object, trade_phrase: str, *, proof_strength: str) -> str:
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
    if proof_strength == "WEAK":
        return f"I can't judge {trade_phrase} reliably yet because the evidence is too weak."
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


def _evidence_missing(context: Mapping[str, Any]) -> list[str]:
    categories = context.get("unknown_categories")
    if not isinstance(categories, list):
        return []
    result: list[str] = []
    for category in categories:
        label = _EVIDENCE_CATEGORY_LABELS.get(str(category), str(category).replace("_", " "))
        if label not in result:
            result.append(label)
    return result[:3]


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
        ratio_sentence = f"The order is about {ratio} of the verified liquidity used in this analysis."
        return f"{sentence} {ratio_sentence}".strip()
    return sentence or None


def _reason_sentences(
    data: Mapping[str, Any],
    risk: Mapping[str, Any],
    *,
    asset: str,
) -> list[str]:
    """Return at most four user-relevant reasons from already-returned facts."""

    market = _mapping(data.get("market"))
    trade_size = _mapping(data.get("trade_size"))
    route = _mapping(data.get("route_analysis"))
    reasons: list[str] = []

    trade_size_text = _trade_size_sentence(trade_size)
    if trade_size_text:
        reasons.append(trade_size_text)

    liquidity = _friendly_money(market.get("verified_liquidity_usd"))
    volume = _friendly_money(market.get("verified_volume_24h_usd"))
    if liquidity is not None:
        reasons.append(f"{asset} has about {liquidity} in verified liquidity for this analysis.")
    if volume is not None:
        reasons.append(f"Verified 24-hour volume is about {volume}.")

    impact = _friendly_percent_value(route.get("estimated_price_impact_percent"))
    slippage = _friendly_percent_value(route.get("estimated_slippage_percent"))
    fees = _friendly_scalar(route.get("estimated_fees"))
    if impact is not None:
        reasons.append(f"Estimated price impact is {impact}.")
    if slippage is not None:
        reasons.append(f"Estimated slippage is {slippage}.")
    if fees is not None:
        reasons.append(f"Estimated fees are {fees}.")

    # Returned human-readable reasons may fill an otherwise sparse explanation,
    # but are never used to change the deterministic recommendation.
    for reason in _string_list(risk.get("reasons")):
        if reason not in reasons:
            reasons.append(reason)
        if len(reasons) >= 4:
            break
    return reasons[:4]


def _plain_list(values: list[str]) -> str:
    labels = [_PLAIN_MISSING_LABELS.get(value, value) for value in values]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


def _missing_paragraph(missing: list[str], evidence_missing: list[str]) -> str | None:
    parts: list[str] = []
    if missing:
        details = _plain_list(missing)
        parts.append(
            f"I still don't have verified information for {details}, so I would treat the trade "
            "as not fully evaluated. That means I can't reliably tell you the final execution "
            "price or fill quality yet."
        )
    if evidence_missing:
        parts.append("Evidence still missing or unproven: " + _plain_list(evidence_missing) + ".")
    return " ".join(parts) if parts else None


def _bottom_line(recommendation: object, *, missing: list[str]) -> str:
    token = str(recommendation or "").strip().upper()
    if token == "BLOCK":
        return "Execution recommendation: do not proceed based on the current deterministic checks."
    if token == "WARN":
        return (
            "Execution recommendation: do not treat this trade as cleared for execution yet. "
            "The current checks call for caution."
        )
    if token == "PASS":
        if missing:
            return (
                "Bottom line: the currently available checks did not block the trade, but "
                "execution risk is not fully evaluated yet. Analysis only; no execution authority."
            )
        return (
            "Bottom line: the currently available checks did not flag a warning or block. "
            "This is still analysis, not an automatic trade or execution authorization."
        )
    return "Execution recommendation: no go-ahead; the available evidence is not sufficient."


def _technical_text(
    result: Mapping[str, Any],
    *,
    recommendation: object,
    missing: list[str],
    context: Mapping[str, Any],
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
        "evidence_context": dict(context),
        "evidence_receipt": dict(_mapping(result.get("evidence_receipt"))),
        "proof_score": dict(_mapping(result.get("proof_score"))),
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
    """Build Roberta's deterministic answer-first pre-trade presentation."""

    if result.get("service") != "pre_trade_check":
        return None

    data = _mapping(result.get("data"))
    trade = _mapping(data.get("trade"))
    risk = _mapping(result.get("risk"))
    recommendation = _recommendation(risk)
    asset = _asset_label(result)
    context = evidence_context(result)
    proof_strength = str(context.get("proof_strength") or "WEAK")
    phrase = _trade_phrase(asset, trade)
    missing = _missing_evidence(data)
    evidence_missing = _evidence_missing(context)

    paragraphs = [_lead(recommendation, phrase, proof_strength=proof_strength)]
    reasons = _reason_sentences(data, risk, asset=asset)
    if reasons:
        paragraphs.append("Why:\n" + "\n".join(f"• {reason}" for reason in reasons))

    risk_level = str(context.get("risk_level") or "UNKNOWN")
    paragraphs.append(f"Risk: {risk_level}\nEvidence quality: {proof_strength}")

    missing_text = _missing_paragraph(missing, evidence_missing)
    if missing_text:
        paragraphs.append(missing_text)

    paragraphs.append(_bottom_line(recommendation, missing=missing))
    conversational = "\n\n".join(part for part in paragraphs if part).strip()
    technical = _technical_text(
        result,
        recommendation=recommendation,
        missing=missing,
        context=context,
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
        "risk_level": risk_level,
        "evidence_quality": proof_strength,
        "verification_status": context.get("verification_status"),
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
        "proof_missing_evidence": evidence_missing,
        "evidence_context": dict(context),
    }


__all__ = [
    "build_pretrade_presentation",
    "technical_pretrade_details_requested",
]
