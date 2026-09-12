"""Versioned factual projection for ROBERTA Evaluation Telemetry v2.

The v2 projection is deliberately read-only and bounded. It projects only
structured facts already present in the current-turn X1 Scout result returned by
the same ROBERTA graph invocation. It does not query CMIS/providers again,
derive claims from natural-language prose, or widen provider/Scout scope.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import HumanMessage, ToolMessage


EVALUATION_TELEMETRY_V2 = "roberta_evaluation_telemetry/v2"
FACTUAL_EVIDENCE_CONTRACT = "roberta_evaluation_factual_evidence/v1"
PROJECTION_INTEGRITY_CONTRACT = "roberta_evaluation_projection_integrity/v1"
X1_ASSET_INTELLIGENCE_CONTRACT = "x1_asset_intelligence/v1"
X1_ASSET_INTELLIGENCE_WORKFLOW_CONTRACT = "x1_asset_intelligence_workflow/v1"
_X1_SCOUT_TOOL = "x1_scout_investigate"
_MAX_FACTUAL_CLAIMS = 32


def _clone_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _clone_json(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_clone_json(item) for item in value]
    return str(value)


def _current_turn_messages(messages: Sequence[object]) -> list[object]:
    last_human = -1
    for index, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            last_human = index
    if last_human >= 0:
        return list(messages[last_human + 1 :])
    return list(messages)


def _accepted_asset_intelligence_report(report: Mapping[str, Any]) -> bool:
    """Validate the exact accepted first-class X1 Asset Intelligence envelope."""

    source = report.get("source")
    packet = report.get("asset_intelligence_packet")
    if not isinstance(source, Mapping) or not isinstance(packet, Mapping):
        return False
    if (
        report.get("contract_version") != X1_ASSET_INTELLIGENCE_WORKFLOW_CONTRACT
        or report.get("product_contract_version") != X1_ASSET_INTELLIGENCE_CONTRACT
        or report.get("specialist") != "x1_scout"
        or report.get("chain") != "x1"
        or source.get("service") != "x1_scout"
        or source.get("operation") != "asset_intelligence"
        or report.get("execution_authorized") is not False
    ):
        return False
    return (
        packet.get("contract_version") == X1_ASSET_INTELLIGENCE_CONTRACT
        and packet.get("product") == "x1_asset_intelligence"
        and packet.get("chain") == "x1"
        and packet.get("facts_authority") == "chain_scout_cmis"
        and packet.get("judgment_authority") == "roberta"
        and packet.get("read_only") is True
        and packet.get("execution_authorized") is False
    )


def _current_turn_x1_scout_report(
    messages: Sequence[object],
) -> dict[str, Any] | None:
    for message in reversed(_current_turn_messages(messages)):
        if not isinstance(message, ToolMessage) or message.name != _X1_SCOUT_TOOL:
            continue
        content = message.content
        if not isinstance(content, str) or not content.strip():
            continue
        try:
            report = json.loads(content)
        except json.JSONDecodeError:
            continue
        if not isinstance(report, Mapping):
            continue
        if report.get("specialist") != "x1_scout" or report.get("chain") != "x1":
            continue
        source = report.get("source")
        if not isinstance(source, Mapping):
            continue
        operation = source.get("operation")
        if not isinstance(operation, str) or not operation.strip():
            continue
        if source.get("service") == "cmis":
            return dict(report)
        if _accepted_asset_intelligence_report(report):
            return dict(report)
    return None


def _factual_evidence(report: Mapping[str, Any]) -> dict[str, Any]:
    source = report.get("source")
    source_service = source.get("service") if isinstance(source, Mapping) else None
    operation = source.get("operation") if isinstance(source, Mapping) else None
    asset_intelligence = (
        source_service == "x1_scout"
        and operation == "asset_intelligence"
        and _accepted_asset_intelligence_report(report)
    )
    if asset_intelligence:
        packet = report.get("asset_intelligence_packet")
        findings = packet if isinstance(packet, Mapping) else {}
        subject = findings.get("subject") if isinstance(findings, Mapping) else None
        asset = subject if isinstance(subject, Mapping) else {}
        status = findings.get("status") if isinstance(findings, Mapping) else None
    else:
        findings = report.get("findings")
        asset = report.get("asset") if isinstance(report.get("asset"), Mapping) else {}
        status = report.get("cmis_status")

    evidence: dict[str, Any] = {
        "contract_version": FACTUAL_EVIDENCE_CONTRACT,
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": report.get("requested_asset"),
        "asset": _clone_json(asset),
        "source": {
            "service": source_service,
            "operation": operation,
        },
        "cmis_status": status,
        "observed_at_iso": report.get("observed_at_iso"),
        "findings": _clone_json(findings if isinstance(findings, Mapping) else {}),
        "confidence": _clone_json(
            report.get("confidence") if isinstance(report.get("confidence"), Mapping) else {}
        ),
        "evidence_context": _clone_json(
            report.get("evidence_context")
            if isinstance(report.get("evidence_context"), Mapping)
            else {}
        ),
    }
    freshness = report.get("freshness")
    if isinstance(freshness, Mapping):
        evidence["freshness"] = _clone_json(freshness)
    return evidence


def _scalar_claims(
    value: Any,
    *,
    path: str,
    name_prefix: str,
    output: list[dict[str, Any]],
) -> None:
    if len(output) >= _MAX_FACTUAL_CLAIMS:
        return
    if isinstance(value, Mapping):
        for raw_key in sorted(value, key=lambda item: str(item)):
            key = str(raw_key)
            if not key or "." in key:
                continue
            _scalar_claims(
                value[raw_key],
                path=f"{path}.{key}",
                name_prefix=f"{name_prefix}_{key}",
                output=output,
            )
            if len(output) >= _MAX_FACTUAL_CLAIMS:
                return
        return
    if value is None or isinstance(value, (list, tuple, dict)):
        return
    if isinstance(value, (str, int, float, bool)):
        output.append(
            {
                "name": name_prefix,
                "evidence_path": path,
                "value": value,
            }
        )


def _resolve_evidence_path(
    evidence: Mapping[str, Any],
    path: str,
) -> tuple[bool, Any]:
    value: Any = evidence
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return False, None
        value = value[part]
    return True, value


_COMMON_PRIORITY_CLAIMS: tuple[tuple[str, str], ...] = (
    ("asset.symbol", "asset_symbol"),
    ("asset.mint", "asset_mint"),
    ("asset.name", "asset_name"),
    ("cmis_status", "cmis_status"),
    ("observed_at_iso", "observed_at_iso"),
    ("evidence_context.verification_status", "evidence_verification_status"),
    ("evidence_context.freshness_verified", "evidence_freshness_verified"),
    ("evidence_context.available", "evidence_available"),
    ("evidence_context.category_coverage_percent", "evidence_category_coverage_percent"),
)

_OPERATION_PRIORITY_CLAIMS: dict[str, tuple[tuple[str, str], ...]] = {
    "market_report": (
        ("findings.data.price", "market_price"),
        ("findings.data.price_usd", "market_price_usd"),
        ("findings.data.liquidity", "market_liquidity"),
        ("findings.data.liquidity_usd", "market_liquidity_usd"),
        ("findings.data.volume_24h", "market_volume_24h"),
        ("findings.data.volume_24h_usd", "market_volume_24h_usd"),
        ("findings.data.transactions_24h", "market_transactions_24h"),
        ("findings.data.#LPs", "market_lp_count"),
    ),
    "instant_x1_scan": (
        ("findings.data.sections.market.price_usd", "market_price_usd"),
        ("findings.data.sections.market.liquidity_usd", "market_liquidity_usd"),
        ("findings.data.sections.market.volume_24h_usd", "market_volume_24h_usd"),
        ("findings.data.sections.market.transactions_24h", "market_transactions_24h"),
        ("findings.data.sections.market.#LPs", "market_lp_count"),
        (
            "findings.data.sections.market.price_freshness_verified",
            "market_price_freshness_verified",
        ),
        (
            "findings.data.sections.market.liquidity_freshness_verified",
            "market_liquidity_freshness_verified",
        ),
        (
            "findings.data.sections.market.volume_24h_freshness_verified",
            "market_volume_24h_freshness_verified",
        ),
        (
            "findings.data.sections.market.transactions_24h_freshness_verified",
            "market_transactions_24h_freshness_verified",
        ),
        (
            "findings.data.sections.tokenomics.current_total_supply",
            "tokenomics_current_total_supply",
        ),
        (
            "findings.data.sections.tokenomics.circulating_supply",
            "tokenomics_circulating_supply",
        ),
        (
            "findings.data.sections.tokenomics.mint_authority",
            "tokenomics_mint_authority",
        ),
        (
            "findings.data.sections.tokenomics.freeze_authority",
            "tokenomics_freeze_authority",
        ),
        ("findings.data.sections.risk.recommendation", "risk_recommendation"),
        ("findings.data.sections.risk.score", "risk_score"),
        ("findings.risk.recommendation", "risk_recommendation_primary"),
        ("findings.risk.score", "risk_score_primary"),
    ),
    "asset_intelligence": (
        ("findings.status", "asset_intelligence_status"),
        (
            "findings.evidence_completion.decision_input_ready",
            "asset_intelligence_decision_input_ready",
        ),
        (
            "findings.evidence_completion.all_baseline_attempts_terminal",
            "asset_intelligence_baseline_terminal",
        ),
        (
            "findings.evidence_completion.all_requested_enrichments_returned",
            "asset_intelligence_requested_enrichments_returned",
        ),
        (
            "findings.source_statuses.instant_x1_scan",
            "asset_intelligence_instant_scan_status",
        ),
        (
            "findings.source_statuses.burn_intelligence",
            "asset_intelligence_burn_status",
        ),
        (
            "findings.source_statuses.discovery_intelligence",
            "asset_intelligence_discovery_status",
        ),
    ),
    "tokenomics": (
        ("findings.data.total_supply", "tokenomics_total_supply"),
        ("findings.data.current_total_supply", "tokenomics_current_total_supply"),
        ("findings.data.circulating_supply", "tokenomics_circulating_supply"),
        ("findings.data.mint_authority", "tokenomics_mint_authority"),
        ("findings.data.freeze_authority", "tokenomics_freeze_authority"),
        ("findings.data.maximum_supply", "tokenomics_maximum_supply"),
    ),
    "risk_check": (
        ("findings.risk.outcome", "risk_outcome"),
        ("findings.risk.recommendation", "risk_recommendation"),
        ("findings.risk.score", "risk_score"),
        ("findings.risk.status", "risk_status"),
    ),
    "pre_trade_check": (
        ("findings.data.trade.side", "trade_side"),
        ("findings.data.trade.notional_usd", "trade_notional_usd"),
        ("findings.data.trade.amount_usd", "trade_amount_usd"),
        ("findings.risk.recommendation", "pretrade_recommendation"),
        ("findings.risk.score", "pretrade_risk_score"),
    ),
    "historical_compare": (
        ("findings.data.current_value", "history_current_value"),
        ("findings.data.historical_value", "history_historical_value"),
        ("findings.data.change_pct", "history_change_pct"),
        ("findings.data.absolute_change_pct", "history_absolute_change_pct"),
        ("findings.data.first_verified_observed_at", "history_first_verified_observed_at"),
        ("findings.data.last_verified_observed_at", "history_last_verified_observed_at"),
    ),
}


def _append_priority_claim(
    evidence: Mapping[str, Any],
    *,
    evidence_path: str,
    name: str,
    claims: list[dict[str, Any]],
    seen_paths: set[str],
) -> None:
    if len(claims) >= _MAX_FACTUAL_CLAIMS:
        return
    found, value = _resolve_evidence_path(evidence, evidence_path)
    if not found or value is None or isinstance(value, (Mapping, list, tuple)):
        return
    full_path = f"factual_response.{evidence_path}"
    if full_path in seen_paths:
        return
    if isinstance(value, (str, int, float, bool)):
        claims.append(
            {
                "name": name,
                "evidence_path": full_path,
                "value": value,
            }
        )
        seen_paths.add(full_path)


def _factual_claims(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    seen_paths: set[str] = set()

    for evidence_path, name in _COMMON_PRIORITY_CLAIMS:
        _append_priority_claim(
            evidence,
            evidence_path=evidence_path,
            name=name,
            claims=claims,
            seen_paths=seen_paths,
        )

    source = evidence.get("source")
    operation = source.get("operation") if isinstance(source, Mapping) else None
    if isinstance(operation, str):
        for evidence_path, name in _OPERATION_PRIORITY_CLAIMS.get(operation, ()):
            _append_priority_claim(
                evidence,
                evidence_path=evidence_path,
                name=name,
                claims=claims,
                seen_paths=seen_paths,
            )

    findings = evidence.get("findings")
    if not isinstance(findings, Mapping):
        return claims

    fallback: list[dict[str, Any]] = []
    for branch in ("data", "risk"):
        value = findings.get(branch)
        if not isinstance(value, Mapping):
            continue
        _scalar_claims(
            value,
            path=f"factual_response.findings.{branch}",
            name_prefix=f"factual_{branch}",
            output=fallback,
        )

    for claim in fallback:
        if len(claims) >= _MAX_FACTUAL_CLAIMS:
            break
        path = claim["evidence_path"]
        if path in seen_paths:
            continue
        claims.append(claim)
        seen_paths.add(path)

    return claims


def _factual_freshness(evidence: Mapping[str, Any]) -> dict[str, Any]:
    freshness = evidence.get("freshness")
    if isinstance(freshness, Mapping):
        explicit_state = None
        for key in ("state", "freshness_state", "status"):
            value = freshness.get(key)
            if isinstance(value, str) and value.strip():
                explicit_state = value
                break
        return {
            "state": explicit_state or "UNAVAILABLE",
            "source_ref": "factual_response.freshness",
            "source_value": _clone_json(freshness),
        }

    context = evidence.get("evidence_context")
    if isinstance(context, Mapping) and isinstance(
        context.get("freshness_verified"), bool
    ):
        verified = context["freshness_verified"]
        return {
            "state": "VERIFIED" if verified else "NOT_VERIFIED",
            "source_ref": "factual_response.evidence_context.freshness_verified",
            "source_value": verified,
        }

    return {
        "state": "UNAVAILABLE",
        "source_ref": None,
        "source_value": None,
    }


def _merge_asset_intelligence_source_contracts(
    provenance: dict[str, Any],
    report: Mapping[str, Any],
) -> None:
    if not _accepted_asset_intelligence_report(report):
        return
    packet = report.get("asset_intelligence_packet")
    if not isinstance(packet, Mapping):
        return
    raw_contracts = packet.get("source_contracts")
    if not isinstance(raw_contracts, Mapping):
        return
    existing = provenance.get("source_contracts")
    merged = list(existing) if isinstance(existing, list) else []
    for value in raw_contracts.values():
        if isinstance(value, str) and value and value not in merged:
            merged.append(value)
    if X1_ASSET_INTELLIGENCE_CONTRACT not in merged:
        merged.append(X1_ASSET_INTELLIGENCE_CONTRACT)
    provenance["source_contracts"] = merged


def extend_evaluation_telemetry_v2(
    base_telemetry: Mapping[str, Any],
    messages: Sequence[object],
) -> dict[str, Any]:
    """Extend accepted v1 final-message telemetry with bounded factual evidence."""

    payload = _clone_json(dict(base_telemetry))
    payload["evaluation_telemetry_version"] = EVALUATION_TELEMETRY_V2

    report = _current_turn_x1_scout_report(messages)
    if report is None:
        return payload

    factual = _factual_evidence(report)
    claims = _factual_claims(factual)
    evidence = payload.get("evaluation_evidence")
    if not isinstance(evidence, dict):
        evidence = {}
        payload["evaluation_evidence"] = evidence
    evidence["factual_response"] = factual

    existing_claims = payload.get("claims")
    merged_claims = list(existing_claims) if isinstance(existing_claims, list) else []
    existing_paths = {
        item.get("evidence_path")
        for item in merged_claims
        if isinstance(item, Mapping)
    }
    for claim in claims:
        if claim["evidence_path"] not in existing_paths:
            merged_claims.append(claim)
            existing_paths.add(claim["evidence_path"])
    payload["claims"] = merged_claims

    if claims:
        evidence["evaluation_projection_integrity"] = {
            "contract_version": PROJECTION_INTEGRITY_CONTRACT,
            "status": "PASS",
            "claim_count": len(claims),
            "source_scope": "current_turn_x1_scout_structured_projection",
            "facts_authority": "chain_scout_cmis",
            "judgment_authority": "roberta",
            "provider_truth_certified": False,
            "all_natural_language_claims_certified": False,
            "execution_authorized": False,
        }

    provenance = payload.get("evidence_provenance")
    if not isinstance(provenance, dict):
        provenance = {}
        payload["evidence_provenance"] = provenance
    provenance["factual_projection"] = {
        "facts_authority": "chain_scout_cmis",
        "source_service": factual["source"]["service"],
        "source_operation": factual["source"]["operation"],
        "telemetry_scope": "current_turn_x1_scout_structured_evidence_only",
        "second_cmis_query_performed": False,
        "prose_claim_inference_performed": False,
    }
    _merge_asset_intelligence_source_contracts(provenance, report)

    current_freshness = payload.get("evidence_freshness")
    if (
        not isinstance(current_freshness, Mapping)
        or current_freshness.get("state") in {None, "UNAVAILABLE"}
    ):
        payload["evidence_freshness"] = _factual_freshness(factual)

    # The projection never grants execution authority. If an accepted final
    # structure already exposed a violation, preserve it rather than masking it.
    if payload.get("execution_authorized") is not True:
        payload["execution_authorized"] = False

    return payload


__all__ = [
    "EVALUATION_TELEMETRY_V2",
    "FACTUAL_EVIDENCE_CONTRACT",
    "PROJECTION_INTEGRITY_CONTRACT",
    "extend_evaluation_telemetry_v2",
]
