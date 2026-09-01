"""Deterministic product-facing UX for validated Instant X1 Scan reports.

The X1 Scout/CMIS report remains the source of truth. This module only projects
already-validated values into a stable product view and text rendering. It does
not calculate market facts, historical coverage, risk, proof quality, holder
semantics, concentration, or execution authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


PRODUCT_VIEW_CONTRACT = "instant_x1_scan_product_view/v1"


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _verified_value(
    section: Mapping[str, Any],
    value_key: str,
    verified_key: str,
) -> dict[str, object]:
    verified = section.get(verified_key) is True
    return {
        "value": section.get(value_key),
        "verified": verified,
    }


def build_instant_x1_scan_product_view(
    report: Mapping[str, Any],
) -> dict[str, object] | None:
    """Build one compact deterministic view from a validated Scout scan report."""

    source = _mapping(report.get("source"))
    if (
        source.get("service") != "cmis"
        or source.get("operation") != "instant_x1_scan"
        or report.get("chain") != "x1"
    ):
        return None
    if report.get("cmis_status") not in {"ok", "partial"}:
        return None

    presentation = _mapping(report.get("instant_x1_scan_presentation"))
    if not presentation:
        return None
    if presentation.get("contract_version") != "instant_x1_scan/v2":
        return None
    if presentation.get("read_only") is not True:
        return None
    if presentation.get("execution_authorized") is not False:
        return None

    sections = _mapping(presentation.get("sections"))
    identity = _mapping(sections.get("identity"))
    market = _mapping(sections.get("market"))
    tokenomics = _mapping(sections.get("tokenomics"))
    holders = _mapping(sections.get("holder_concentration"))
    history = _mapping(sections.get("history"))
    risk = _mapping(sections.get("risk"))
    evidence = _mapping(sections.get("evidence"))

    limitations = presentation.get("limitations")
    if not isinstance(limitations, list):
        return None

    top_concentration = _mapping(holders.get("top_account_concentration"))

    return {
        "contract_version": PRODUCT_VIEW_CONTRACT,
        "product": "instant_x1_scan",
        "chain": report.get("chain"),
        "requested_asset": report.get("requested_asset"),
        "status": report.get("cmis_status"),
        "observed_at": report.get("observed_at"),
        "observed_at_iso": report.get("observed_at_iso"),
        "observed_at_display": report.get("observed_at_display"),
        "identity": {
            "status": identity.get("status"),
            "verified": identity.get("verified") is True,
            "symbol": identity.get("symbol"),
            "name": identity.get("name"),
            "mint": identity.get("mint"),
            "resolved_by": identity.get("resolved_by"),
            "match_quality": identity.get("match_quality"),
        },
        "market": {
            "status": market.get("status"),
            "price_usd": _verified_value(market, "price_usd", "price_verified"),
            "liquidity_usd": _verified_value(
                market,
                "liquidity_usd",
                "liquidity_verified",
            ),
            "volume_24h_usd": _verified_value(
                market,
                "volume_24h_usd",
                "volume_24h_verified",
            ),
            "transactions_24h": _verified_value(
                market,
                "transactions_24h",
                "transactions_24h_verified",
            ),
            "#LPs": market.get("#LPs"),
        },
        "tokenomics": {
            "status": tokenomics.get("status"),
            "scope": tokenomics.get("scope"),
            "asset_type": tokenomics.get("asset_type"),
            "current_total_supply": _verified_value(
                tokenomics,
                "current_total_supply",
                "supply_verified",
            ),
            "mint_authority": _verified_value(
                tokenomics,
                "mint_authority",
                "mint_authority_verified",
            ),
            "mint_authority_state": tokenomics.get("mint_authority_state"),
            "freeze_authority": _verified_value(
                tokenomics,
                "freeze_authority",
                "freeze_authority_verified",
            ),
            "freeze_authority_state": tokenomics.get("freeze_authority_state"),
            "circulating_supply": _verified_value(
                tokenomics,
                "circulating_supply",
                "circulating_supply_verified",
            ),
            "future_minting_possible": tokenomics.get("future_minting_possible"),
        },
        "holder_concentration": {
            "holders": _verified_value(
                holders,
                "holders",
                "holders_verified",
            ),
            "holders_reported": holders.get("holders_reported"),
            "holders_observed": holders.get("holders_observed"),
            "holder_semantics": holders.get("holder_semantics"),
            "top_account_concentration": {
                "state": top_concentration.get("state"),
                "verified": top_concentration.get("verified") is True,
                "value": top_concentration.get("value"),
                "reason": top_concentration.get("reason"),
            },
        },
        "history": dict(history),
        "risk": {
            "status": risk.get("status"),
            "recommendation": risk.get("recommendation"),
            "flags": list(risk.get("flags") or []),
            "reasons": list(risk.get("reasons") or []),
            "score": risk.get("score"),
            "score_verified": risk.get("score_verified") is True,
            "score_reason": risk.get("score_reason"),
            "execution_authorized": False,
        },
        "evidence": {
            "proof_score_separate_from_risk": (
                evidence.get("proof_score_separate_from_risk") is True
            ),
            "component_statuses": dict(
                _mapping(evidence.get("component_statuses"))
            ),
            "component_source_count": evidence.get("component_source_count"),
            "evidence_context": dict(_mapping(report.get("evidence_context"))),
        },
        "limitations": list(limitations),
        "warnings": list(report.get("warnings") or []),
        "errors": list(report.get("errors") or []),
        "execution_authorized": False,
    }


def _render_verified(label: str, item: object) -> str:
    value = _mapping(item)
    raw = value.get("value")
    verified = value.get("verified") is True
    if verified:
        return f"{label}: {raw}"
    if raw is None:
        return f"{label}: unknown"
    return f"{label}: {raw} (unverified)"


def render_instant_x1_scan_product_text(view: Mapping[str, Any]) -> str:
    """Render a compact chat/terminal summary without changing fact semantics."""

    if view.get("contract_version") != PRODUCT_VIEW_CONTRACT:
        raise ValueError("unsupported Instant X1 Scan product-view contract")
    if view.get("execution_authorized") is not False:
        raise ValueError("Instant X1 Scan product view must not authorize execution")

    identity = _mapping(view.get("identity"))
    market = _mapping(view.get("market"))
    tokenomics = _mapping(view.get("tokenomics"))
    holder = _mapping(view.get("holder_concentration"))
    concentration = _mapping(holder.get("top_account_concentration"))
    history = _mapping(view.get("history"))
    risk = _mapping(view.get("risk"))
    evidence = _mapping(view.get("evidence"))

    descriptor = (
        identity.get("symbol")
        or identity.get("name")
        or identity.get("mint")
    )
    requested_asset = str(view.get("requested_asset") or "").strip()
    identity_verified = identity.get("verified") is True
    asset_label = (
        descriptor
        if identity_verified and descriptor
        else requested_asset or "requested X1 asset"
    )
    identity_status = (
        "verified"
        if identity_verified
        else (
            f"unverified (reported descriptor: {descriptor})"
            if descriptor
            else "unverified"
        )
    )
    lines = [
        f"Instant X1 Scan — {asset_label}",
        f"Identity: {identity_status}",
        f"Status: {view.get('status') or 'unknown'}",
        f"Observed: {view.get('observed_at_display') or view.get('observed_at_iso') or 'unknown'}",
        "",
        "Market",
        _render_verified("Price USD", market.get("price_usd")),
        _render_verified("Liquidity USD", market.get("liquidity_usd")),
        _render_verified("24h Volume USD", market.get("volume_24h_usd")),
        _render_verified("24h Transactions", market.get("transactions_24h")),
        "",
        "Tokenomics",
        _render_verified(
            "Total Supply",
            tokenomics.get("current_total_supply"),
        ),
        _render_verified("Mint Authority", tokenomics.get("mint_authority")),
        _render_verified(
            "Freeze Authority",
            tokenomics.get("freeze_authority"),
        ),
        "",
        "Holders / Concentration",
        _render_verified("Holders", holder.get("holders")),
        (
            "Top-account concentration: unknown"
            if concentration.get("verified") is not True
            else f"Top-account concentration: {concentration.get('value')}"
        ),
        "",
        "History",
        f"Coverage status: {history.get('status') or 'unknown'}",
        f"Coverage scope: {history.get('coverage_scope') or 'unknown'}",
        (
            "Full asset lifetime verified: "
            f"{history.get('full_asset_lifetime_verified') is True}"
        ),
        (
            "Continuous coverage verified: "
            f"{history.get('continuous_coverage_verified') is True}"
        ),
    ]

    history_metrics = history.get("metrics")
    if isinstance(history_metrics, Mapping) and history_metrics:
        lines.append("Verified history metrics:")
        for metric_name in sorted(history_metrics):
            metric = _mapping(history_metrics.get(metric_name))
            label = str(metric_name).replace("_", " ").title()
            status = metric.get("status") or "unknown"
            lines.append(f"- {label} status: {status}")
            if metric.get("observation_count") is not None:
                lines.append(
                    f"  observations: {metric.get('observation_count')}"
                )
            if metric.get("current_value") is not None:
                suffix = "" if metric.get("current_verified") is True else " (unverified)"
                lines.append(
                    f"  current value: {metric.get('current_value')}{suffix}"
                )
            if metric.get("total_change_pct") is not None:
                lines.append(
                    f"  total change pct: {metric.get('total_change_pct')}"
                )
            if metric.get("sampled_max_drawdown_pct") is not None:
                lines.append(
                    "  sampled max drawdown pct: "
                    f"{metric.get('sampled_max_drawdown_pct')}"
                )
            if metric.get("reason"):
                lines.append(f"  reason: {metric.get('reason')}")

    lines.extend([
        "",
        "Risk",
        f"Recommendation: {risk.get('recommendation') or 'unknown'}",
        (
            f"Risk score: {risk.get('score')}"
            if risk.get("score_verified") is True
            else "Risk score: unavailable/unverified"
        ),
    ])

    risk_reasons = risk.get("reasons")
    if isinstance(risk_reasons, list) and risk_reasons:
        lines.append("Risk reasons:")
        lines.extend(f"- {item}" for item in risk_reasons)

    risk_flags = risk.get("flags")
    if isinstance(risk_flags, list) and risk_flags:
        lines.append("Risk flags:")
        lines.extend(f"- {item}" for item in risk_flags)

    lines.extend([
        "",
        "Evidence",
        (
            "Proof Score is separate from risk: "
            f"{evidence.get('proof_score_separate_from_risk') is True}"
        ),
    ])

    limitations = view.get("limitations")
    if isinstance(limitations, list) and limitations:
        lines.extend(["", "Limitations"])
        lines.extend(f"- {item}" for item in limitations)

    warnings = view.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "Warnings"])
        for warning in warnings:
            if isinstance(warning, Mapping):
                code = warning.get("code")
                message = warning.get("message")
                lines.append(f"- {code}: {message}" if code else f"- {message}")
            else:
                lines.append(f"- {warning}")

    errors = view.get("errors")
    if isinstance(errors, list) and errors:
        lines.extend(["", "Errors"])
        for error in errors:
            if isinstance(error, Mapping):
                code = error.get("code")
                message = error.get("message")
                lines.append(f"- {code}: {message}" if code else f"- {message}")
            else:
                lines.append(f"- {error}")

    return "\n".join(lines)


__all__ = [
    "PRODUCT_VIEW_CONTRACT",
    "build_instant_x1_scan_product_view",
    "render_instant_x1_scan_product_text",
]
