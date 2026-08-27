"""Terminal presentation helpers for Roberta interactive chat."""

from __future__ import annotations

import json
import textwrap
from collections.abc import Mapping
from typing import Any


LINE_WIDTH = 72
ANSWER_WIDTH = 68
LINE = "=" * LINE_WIDTH
SUBLINE = "-" * LINE_WIDTH


CMIS_STATUS_MEANINGS = {
    "ok": (
        "CMIS completed the requested service with its required verification "
        "checks complete. This describes service completeness, not asset safety."
    ),
    "partial": (
        "CMIS returned a usable result, but one or more verification checks "
        "are incomplete."
    ),
    "unavailable": (
        "CMIS could not produce a usable result because required verified "
        "input or a provider dependency was unavailable."
    ),
    "ambiguous": (
        "CMIS could not uniquely resolve the requested asset. Do not assume "
        "which asset was intended."
    ),
    "error": (
        "CMIS encountered a validation or service error. Treat the requested "
        "result as unavailable."
    ),
}

RISK_MEANINGS = {
    "PASS": (
        "CMIS returned PASS under its deterministic risk policy for the "
        "evidence evaluated. PASS is not permission to trade."
    ),
    "WARN": (
        "CMIS returned WARN. One or more deterministic risk conditions require "
        "caution; read the returned reasons and flags."
    ),
    "BLOCK": (
        "CMIS returned BLOCK. A deterministic risk policy condition is "
        "blocking the requested assessment or action from being treated as acceptable."
    ),
    "UNKNOWN": "No deterministic CMIS risk recommendation was returned.",
}

VERIFICATION_MEANINGS = {
    "AGREEMENT": "Accepted evidence agrees for the exact fact being verified.",
    "CONFLICT": "Evidence sources disagree about the exact fact.",
    "INSUFFICIENT_EVIDENCE": (
        "Some evidence exists, but it is not sufficient to verify the claim."
    ),
    "UNVERIFIED": "The claim has not passed CMIS verification.",
}

PROOF_MEANINGS = {
    "STRONG": "Evidence provenance and proof coverage are strong.",
    "MODERATE": (
        "Useful evidence exists, but important proof dimensions are incomplete."
    ),
    "WEAK": (
        "Evidence is sparse, insufficiently corroborated, or missing important "
        "verification dimensions."
    ),
}

WARNING_CODE_MEANINGS = {
    "historical_price_unavailable": (
        "Verified historical price evidence is unavailable, so Roberta cannot "
        "make a verified historical-performance or volatility claim."
    ),
    "token_activity_unavailable": (
        "Verified bounded token activity evidence was not available for the "
        "risk evaluation."
    ),
    "holder_data_incomplete": (
        "Holder information cannot be treated as a complete unique-holder total."
    ),
    "holders_incomplete": (
        "Holder information cannot be treated as a complete unique-holder total."
    ),
    "market_cap_unverified": (
        "Market-cap information is provider-reported or otherwise not verified "
        "to the required CMIS standard."
    ),
    "fdv_unverified": (
        "Fully diluted valuation is provider-reported or otherwise not verified "
        "to the required CMIS standard."
    ),
    "source_independence_unknown": (
        "CMIS has not proven that the supporting sources are genuinely independent."
    ),
    "scope_unknown": (
        "CMIS cannot safely widen the evidence to a broader asset/global scope."
    ),
    "semantics_unknown": (
        "CMIS has not sufficiently proven what the provider field represents."
    ),
    "identity_unknown": (
        "Exact asset, pool, route, or account identity has not been fully proven."
    ),
    "historical_coverage_unknown": (
        "CMIS cannot prove the completeness or depth of the historical series."
    ),
}


SERVICE_MENU = """\
ROBERTA SERVICE MENU
------------------------------------------------------------------------
  1. Asset Overview              /overview <asset>
  2. Compare Two Assets          /compare <asset1> <asset2>
  3. Risk Assessment             /risk <asset>
  4. Tokenomics Analysis         /tokenomics <asset>
  5. Liquidity Analysis          /liquidity <asset>
  6. Historical Analysis         /history <asset>
  7. Market Activity             /activity <asset>
  8. Concentration Change        /concentration <asset> <ie_id>
  9. Rank X1 Assets              /rank <metric> [limit]
 10. Pre-Trade Analysis          /pretrade <asset> <BUY|SELL> <usd>
 11. Evidence Quality Report     /evidence <asset>
 12. Full Assessment             /full <asset>
 13. Alert & Warning Key         /key

Other commands:
     /menu   Show this menu
     /new    Start a new conversation
     /exit   End the session

You can also type a normal question at any time.
"""


STATUS_KEY = """\
ROBERTA — ALERT & STATUS KEY
------------------------------------------------------------------------
RISK / DECISION STATUS

[PASS]
  CMIS returned PASS under its deterministic risk policy for the
  evidence evaluated. PASS is not permission to trade.

[WARN]
  One or more deterministic risk conditions require caution.
  Read the returned reasons and flags.

[BLOCK]
  A deterministic risk policy condition is blocking the result
  from being treated as acceptable.

[UNKNOWN]
  No deterministic CMIS risk recommendation was returned.

CMIS SERVICE STATUS

[OK]
  CMIS completed the requested service with its required
  verification checks complete. OK does not mean the asset is safe.

[PARTIAL]
  A usable result was returned, but one or more verification
  checks are incomplete.

[UNAVAILABLE]
  Required verified information or a provider dependency was
  unavailable.

[AMBIGUOUS]
  CMIS could not uniquely resolve the requested asset.

[ERROR]
  CMIS encountered a validation or service error. Treat that
  requested result as unavailable.

EVIDENCE VERIFICATION

[AGREEMENT]
  Accepted evidence agrees for the exact fact being verified.

[CONFLICT]
  Evidence sources disagree about the exact fact.

[INSUFFICIENT_EVIDENCE]
  Some evidence exists, but it is not enough to verify the claim.

[UNVERIFIED]
  The claim has not passed CMIS verification.

PROOF STRENGTH

[STRONG]
  Evidence provenance and proof coverage are strong.

[MODERATE]
  Useful evidence exists, but important proof dimensions remain
  incomplete.

[WEAK]
  Evidence is sparse, insufficiently corroborated, or missing
  important verification dimensions.

IMPORTANT:
  Proof strength is NOT asset safety. CMIS can have STRONG proof
  of a WARN or BLOCK condition.

FRESHNESS

[FRESHNESS VERIFIED]
  The evidence meets the required freshness contract.

[FRESHNESS NOT VERIFIED]
  The freshness requirement was not proven.

[FRESHNESS UNKNOWN]
  There is not enough metadata to determine freshness.

COMMON DATA WARNINGS

[HISTORY UNAVAILABLE]
  Verified historical evidence is unavailable. Roberta must not
  estimate historical performance.

[HOLDER DATA INCOMPLETE]
  Holder information cannot be treated as a complete unique-holder
  or beneficial-owner count.

[MARKET CAP UNVERIFIED]
  Market-cap information has not passed the required verification.

[FDV UNVERIFIED]
  Fully diluted valuation has not passed the required verification.

[SOURCE INDEPENDENCE UNKNOWN]
  Multiple sources may exist, but their independence is not proven.

[SCOPE UNKNOWN]
  Evidence scope cannot safely be widened to asset/global truth.

[SEMANTICS UNKNOWN]
  The meaning of a provider field is not sufficiently proven.

[IDENTITY UNKNOWN]
  Exact subject identity is not sufficiently proven.

[HISTORICAL COVERAGE UNKNOWN]
  Historical completeness or depth is not proven.

PRESENTATION-ONLY STATE

[NOT RUN]
  The relevant CMIS service was not requested in this investigation.
  NOT RUN is a Roberta UI label, not a CMIS service status.

EXECUTION

[ANALYSIS ONLY]
  The result is informational/read-only.

[EXECUTION NOT AUTHORIZED]
  Roberta, Scouts, and CMIS do not gain signing, broadcast, custody,
  trading, bridge-transfer, or value-moving authority from a result.
"""


def format_terminal_text(text: object, *, width: int = ANSWER_WIDTH) -> str:
    """Wrap prose and list items for comfortable terminal reading."""

    raw = str(text or "")
    output: list[str] = []

    for raw_line in raw.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            output.append("")
            continue

        if stripped.startswith(("- ", "* ", "• ")):
            wrapped = textwrap.fill(
                stripped[2:].strip(),
                width=width,
                initial_indent="  • ",
                subsequent_indent="    ",
                break_long_words=False,
                break_on_hyphens=False,
            )
        else:
            wrapped = textwrap.fill(
                stripped,
                width=width,
                initial_indent="  ",
                subsequent_indent="  ",
                break_long_words=False,
                break_on_hyphens=False,
            )
        output.append(wrapped)

    return "\n".join(output)


def _as_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: object) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: object) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _warning_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return json.dumps(dict(value), sort_keys=True)
    return str(value)


def warning_meaning(value: object) -> str | None:
    """Return a concise meaning for a known warning/flag code."""

    text = _warning_text(value).strip()
    if text in WARNING_CODE_MEANINGS:
        return WARNING_CODE_MEANINGS[text]

    lowered = text.lower()
    for code, meaning in WARNING_CODE_MEANINGS.items():
        if code in lowered:
            return meaning
    return None


def parse_scout_payload(content: object) -> dict[str, Any] | None:
    """Parse the JSON object returned by a Scout tool when available."""

    if isinstance(content, Mapping):
        return dict(content)
    if not isinstance(content, str):
        return None
    try:
        decoded = json.loads(content)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return dict(decoded) if isinstance(decoded, Mapping) else None


def automatic_status_summary(content: object) -> str | None:
    """Build the compact status/key explanation shown after Scout tool results."""

    report = parse_scout_payload(content)
    if report is None:
        return None

    investigations = _as_list(report.get("investigations"))
    if not investigations:
        investigations = [report]

    lines: list[str] = []

    for raw_investigation in investigations:
        investigation = _as_mapping(raw_investigation)
        operation = (
            _text(investigation.get("operation"))
            or _text(investigation.get("service"))
            or "CMIS result"
        )

        block: list[str] = [operation]

        cmis_status = (_text(investigation.get("cmis_status")) or "").lower()
        if cmis_status:
            block.append(f"  CMIS: [{cmis_status.upper()}]")
            if cmis_status != "ok":
                meaning = CMIS_STATUS_MEANINGS.get(cmis_status)
                if meaning:
                    block.append(f"    Meaning: {meaning}")

        risk_help = _as_mapping(investigation.get("risk_help"))
        recommendation = _as_mapping(risk_help.get("recommendation"))
        risk_value = (_text(recommendation.get("value")) or "").upper()
        if risk_value:
            block.append(f"  Risk: [{risk_value}]")
            if risk_value != "PASS":
                meaning = RISK_MEANINGS.get(risk_value)
                if meaning:
                    block.append(f"    Meaning: {meaning}")

            reasons = _as_list(recommendation.get("reasons"))
            for reason in reasons:
                block.append(f"    Reason: {_warning_text(reason)}")

            flags = _as_list(recommendation.get("flags"))
            for flag in flags:
                flag_text = _warning_text(flag)
                block.append(f"    Flag: {flag_text}")
                meaning = warning_meaning(flag)
                if meaning:
                    block.append(f"      Meaning: {meaning}")

        evidence = _as_mapping(investigation.get("evidence_context"))
        proof_strength = (_text(evidence.get("proof_strength")) or "").upper()
        if proof_strength:
            block.append(f"  Proof: [{proof_strength}]")
            if proof_strength != "STRONG":
                meaning = PROOF_MEANINGS.get(proof_strength)
                if meaning:
                    block.append(f"    Meaning: {meaning}")

        verification = (_text(evidence.get("verification_status")) or "").upper()
        if verification:
            block.append(f"  Verification: [{verification}]")
            if verification != "AGREEMENT":
                meaning = VERIFICATION_MEANINGS.get(verification)
                if meaning:
                    block.append(f"    Meaning: {meaning}")

        if evidence:
            freshness = evidence.get("freshness_verified")
            if freshness is True:
                block.append("  Freshness: [VERIFIED]")
            elif freshness is False:
                block.append("  Freshness: [NOT VERIFIED]")
                block.append(
                    "    Meaning: The evidence freshness requirement was not proven."
                )
            elif freshness is None:
                block.append("  Freshness: [UNKNOWN]")
                block.append(
                    "    Meaning: There is not enough metadata to determine freshness."
                )

            unknown_categories = [
                _warning_text(item)
                for item in _as_list(evidence.get("unknown_categories"))
            ]
            if unknown_categories:
                block.append(
                    "  Unknown evidence: " + ", ".join(unknown_categories)
                )

        warnings = _as_list(investigation.get("warnings"))
        for warning in warnings:
            warning_text = _warning_text(warning)
            block.append(f"  Warning: {warning_text}")
            meaning = warning_meaning(warning)
            if meaning:
                block.append(f"    Meaning: {meaning}")

        errors = _as_list(investigation.get("errors"))
        for error in errors:
            block.append(f"  Error: {_warning_text(error)}")

        if len(block) > 1:
            if lines:
                lines.append("")
            lines.extend(block)

    if not lines:
        return None
    return "\n".join(lines)


def overview_request(asset: str) -> str:
    return (
        f"On X1, give me a complete current overview of {asset}. "
        "Use X1 Scout and fresh CMIS evidence. Gather a market_report, "
        "deterministic risk_check, and tokenomics for this asset. Do not rely "
        "on stale values from earlier conversation turns. Separate verified "
        "facts from interpretation, explain evidence quality, and identify "
        "warnings, incomplete checks, and unavailable fields."
    )


def compare_request(asset1: str, asset2: str) -> str:
    return (
        f"On X1, compare {asset1} vs {asset2}. For EACH asset, gather fresh "
        "CMIS market_report, deterministic risk_check, and tokenomics evidence. "
        "Then run separate historical_compare investigations for both assets "
        "when historical evidence is available; use separate X1 Scout calls if "
        "needed because each Scout investigation is bounded. Do not reuse an "
        "earlier risk result. Compare liquidity, 24-hour volume, transactions, "
        "risk components, tokenomics, evidence quality, and historical context. "
        "Quantify relative differences only when supported by CMIS facts. "
        "Clearly identify missing, unverified, or non-comparable evidence, then "
        "explain which asset has the stronger current market structure and "
        "whether verified evidence supports saying either appears safer."
    )


def risk_request(asset: str) -> str:
    return (
        f"On X1, assess the current risk of {asset}. Run a fresh deterministic "
        "CMIS risk_check plus market_report and tokenomics. Explain each risk "
        "component, returned reasons and flags, evidence quality, and anything "
        "CMIS could not verify. Do not convert Proof Score into risk."
    )


def tokenomics_request(asset: str) -> str:
    return (
        f"On X1, analyze the tokenomics of {asset}. Use fresh CMIS tokenomics, "
        "market_report, and risk_check evidence. Cover verified supply, mint "
        "authority, freeze authority, token activity/burn evidence when "
        "available, risk implications, and all verification limitations."
    )


def liquidity_request(asset: str) -> str:
    return (
        f"On X1, analyze liquidity for {asset}. Use fresh CMIS market_report "
        "and risk_check evidence. Cover verified liquidity, pool count and "
        "primary-pool context when available, 24-hour volume, transaction "
        "activity, volume-to-liquidity context, evidence scope, and liquidity "
        "risk. Do not invent route, slippage, fill, or price-impact evidence."
    )


def history_request(asset: str) -> str:
    return (
        f"On X1, analyze the verified market history of {asset}. Run CMIS "
        "historical_compare plus a fresh market_report. Compare the current "
        "state with every verified historical window CMIS can support. Cover "
        "price, liquidity, volume, activity, volatility or drawdown only when "
        "those facts are actually supported. State historical coverage and "
        "missing evidence explicitly."
    )


def activity_request(asset: str) -> str:
    return (
        f"On X1, analyze current market activity for {asset}. Use fresh CMIS "
        "market_report and historical_compare evidence where supported. Cover "
        "24-hour volume, transaction count, recent activity, available changes "
        "over time, and evidence quality. Do not infer complete wallet history, "
        "intent, manipulation, or ownership from bounded activity."
    )


def concentration_request(asset: str, evidence_id: str) -> str:
    return (
        f"On X1, use the promoted CMIS concentration_change_intelligence "
        f"service for {asset} with this exact CMIS-owned intelligence evidence "
        f"id: {evidence_id}. Preserve the exact scope and proof. Explain the "
        "verified top-account concentration change and any threshold output, "
        "but do not infer unique holders, beneficial owners, whales, insiders, "
        "bots, manipulation, intent, or common ownership."
    )


def rank_request(metric: str, limit: int) -> str:
    return (
        f"On X1, rank the top {limit} XDEX assets by {metric} using X1 Scout "
        "and the CMIS rank service. Preserve verification status and evidence "
        "limitations. Do not silently substitute a different ranking metric."
    )


def pretrade_request(asset: str, action: str, amount_usd: float) -> str:
    return (
        f"On X1, run an explicit analysis-only pre-trade check for {asset}: "
        f"{action.upper()} $" + f"{amount_usd:.2f}. Use X1 Scout with the CMIS "
        "pre_trade_check operation and copy this exact side and USD amount. "
        "Explain verified liquidity/notional constraints, warnings, and missing "
        "route/slippage/fee/simulation evidence. Preserve analysis_only=true and "
        "execution_authorized=false."
    )


def evidence_request(asset: str) -> str:
    return (
        f"On X1, give me an evidence-quality report for {asset}. Use fresh X1 "
        "Scout/CMIS market and risk evidence so Evidence Receipt and Proof Score "
        "metadata are current. Explain verification status, proof strength, "
        "freshness, evidence scope, unknown categories, unresolved fields, "
        "disagreements, source independence when proven, and limitations. "
        "Keep proof strength separate from market risk."
    )


def full_request(asset: str) -> str:
    return (
        f"On X1, produce the most complete current assessment possible for "
        f"{asset}. Use multiple X1 Scout calls as needed. Gather fresh CMIS "
        "market_report, risk_check, tokenomics, historical_compare, ranking "
        "context when useful, and evidence-quality metadata. Include "
        "concentration intelligence only if an exact eligible CMIS-owned "
        "evidence id is already available; never invent one. Separate verified "
        "facts, X1 Scout interpretation, and Roberta reasoning. Cover market "
        "structure, liquidity, activity, tokenomics, risk, history, evidence "
        "quality, strengths, weaknesses, key unknowns, and overall assessment. "
        "Identify every important unavailable or unverified dimension."
    )
