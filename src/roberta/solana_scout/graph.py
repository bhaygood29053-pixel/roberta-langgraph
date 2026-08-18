"""Solana Scout LangGraph specialist subgraph.

Solana Scout owns Solana-specific investigation planning/interpretation. CMIS
owns freshness-sensitive market/tokenomics/risk services and the Solana Provider
beneath them once configured. Evidence quality remains chain-isolated and is
never blended with X1 evidence.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from roberta.cmis.client import CMISClient
from roberta.cmis.contracts import CMISEnvelope, CMISOperation
from roberta.evidence_aware import evidence_context
from roberta.presentation import format_component_status_table
from roberta.risk_help import build_risk_help
from roberta.specialists.planning import enforce_plan, propose_plan
from roberta.status_help import build_cmis_status_help
from roberta.time_utils import format_observed_at_utc, normalize_observed_at
from roberta.solana_scout.state import (
    SolanaScoutInvestigation,
    SolanaScoutReport,
    SolanaScoutState,
)


def make_plan_proposal_node(planner_model: Any | None) -> Callable[[SolanaScoutState], dict[str, Any]]:
    def propose_plan_node(state: SolanaScoutState) -> dict[str, Any]:
        request = state["request"]
        if "operation" in request or planner_model is None:
            return {"plan_proposal": None, "planner_error": None, "status": "running"}
        try:
            proposal = propose_plan(
                planner_model,
                chain="solana",
                asset=request["asset"],
                objective=request["objective"],
            )
        except Exception as exc:
            return {
                "plan_proposal": None,
                "planner_error": f"{type(exc).__name__}: {exc}",
                "status": "running",
            }
        return {"plan_proposal": proposal, "planner_error": None, "status": "running"}

    return propose_plan_node


def enforce_plan_node(state: SolanaScoutState) -> dict[str, Any]:
    plan = enforce_plan(
        state["request"],
        state.get("plan_proposal"),
        planner_error=state.get("planner_error"),
    )
    return {"plan": plan, "status": "running"}


def _dispatch_cmis_operation(
    cmis_client: CMISClient,
    request: dict[str, Any],
    operation: CMISOperation,
) -> CMISEnvelope:
    asset = request["asset"]
    if operation == "market_report":
        return cmis_client.market_report(chain="solana", asset=asset)
    if operation == "tokenomics":
        return cmis_client.tokenomics(chain="solana", asset=asset)
    if operation == "risk_check":
        return cmis_client.risk_check(chain="solana", asset=asset)
    if operation == "pre_trade_check":
        action = request.get("action")
        amount_usd = request.get("amount_usd")
        if action is None or amount_usd is None:
            raise ValueError("pre_trade_check requires action and amount_usd in Solana Scout state")
        return cmis_client.pre_trade_check(
            chain="solana",
            asset=asset,
            action=action,
            amount_usd=amount_usd,
        )
    raise ValueError(f"Unsupported CMIS operation: {operation!r}")  # pragma: no cover


def make_cmis_calls_node(
    cmis_client: CMISClient,
    *,
    provider_enabled: bool,
) -> Callable[[SolanaScoutState], dict[str, Any]]:
    def cmis_calls_node(state: SolanaScoutState) -> dict[str, Any]:
        if not provider_enabled:
            return {"provider_configured": False, "status": "running"}
        request = dict(state["request"])
        operations = state["plan"]["operations"]
        results = [
            _dispatch_cmis_operation(cmis_client, request, operation)
            for operation in operations
        ]
        if not results:  # pragma: no cover
            raise RuntimeError("Solana Scout plan completed without a CMIS operation")
        return {
            "provider_configured": True,
            "cmis_results": results,
            "cmis_result": results[-1],
            "status": "running",
        }

    return cmis_calls_node


def _summarize_cmis_result(result: CMISEnvelope) -> SolanaScoutInvestigation:
    service = result["service"]
    cmis_status = result["status"]
    observed_at = result["observed_at"]
    observed_at_iso = normalize_observed_at(observed_at)
    risk = dict(result["risk"]) if result["risk"] is not None else None
    confidence = dict(result["confidence"])
    risk_help = build_risk_help(risk, confidence)
    return {
        "operation": service,
        "cmis_status": cmis_status,
        "cmis_status_help": build_cmis_status_help(service, cmis_status, confidence),
        "observed_at": observed_at,
        "observed_at_iso": observed_at_iso,
        "observed_at_display": format_observed_at_utc(observed_at_iso),
        "findings": {"data": dict(result["data"]), "risk": risk},
        "confidence": confidence,
        "evidence_context": evidence_context(result),
        "risk_help": risk_help,
        "component_status_table": format_component_status_table(risk_help),
        "sources": list(result["sources"]),
        "warnings": list(result["warnings"]),
        "errors": list(result["errors"]),
    }


def _unconfigured_report(state: SolanaScoutState) -> SolanaScoutReport:
    request = state["request"]
    plan = state["plan"]
    primary_operation = plan["operations"][-1]
    warning = {
        "code": "SOLANA_PROVIDER_NOT_CONFIGURED",
        "message": (
            "Solana Scout is registered, but the Solana CMIS provider path is not "
            "enabled in this Roberta runtime. No live Solana market facts were requested."
        ),
    }
    unavailable_evidence = {
        "available": False,
        "chain": "solana",
        "service": primary_operation,
        "receipt_id": None,
        "verification_status": "UNVERIFIED",
        "proof_strength": "WEAK",
        "risk_level": "UNKNOWN",
        "risk_recommendation": "UNKNOWN",
        "unresolved_fields": ["solana_provider_configuration", "evidence_receipt", "proof_score"],
        "risk_separate_from_proof": True,
    }
    return {
        "specialist": "solana_scout",
        "chain": "solana",
        "requested_asset": request["asset"],
        "asset": {"input": request["asset"]},
        "objective": request["objective"],
        "status": "unavailable",
        "plan": plan,
        "investigations": [],
        "cmis_status": "unavailable",
        "cmis_status_help": None,
        "observed_at": None,
        "observed_at_iso": None,
        "observed_at_display": None,
        "findings": {"data": {}, "risk": None},
        "confidence": {
            "level": "UNAVAILABLE",
            "reason": "Solana provider is not enabled in the Roberta runtime.",
        },
        "evidence_context": unavailable_evidence,
        "risk_help": None,
        "component_status_table": None,
        "source": {"service": "roberta_configuration", "operation": primary_operation},
        "sources": [],
        "warnings": [warning],
        "errors": [],
    }


def interpret_cmis_result(state: SolanaScoutState) -> dict[str, Any]:
    if state.get("provider_configured") is False:
        report = _unconfigured_report(state)
        return {"report": report, "status": "unavailable"}

    request = state["request"]
    results = state.get("cmis_results")
    if not results:
        result = state.get("cmis_result")
        if result is None:
            raise RuntimeError("Solana Scout completed without CMIS result state")
        results = [result]

    investigations = [_summarize_cmis_result(result) for result in results]
    primary_result = results[-1]
    primary = investigations[-1]
    statuses = {investigation["cmis_status"] for investigation in investigations}
    if "error" in statuses:
        report_status = "error"
    elif "unavailable" in statuses:
        report_status = "unavailable"
    else:
        report_status = "complete"

    report: SolanaScoutReport = {
        "specialist": "solana_scout",
        "chain": "solana",
        "requested_asset": request["asset"],
        "asset": dict(primary_result["asset"]),
        "objective": request["objective"],
        "status": report_status,
        "plan": dict(state["plan"]),
        "investigations": investigations,
        "cmis_status": primary["cmis_status"],
        "cmis_status_help": primary["cmis_status_help"],
        "observed_at": primary["observed_at"],
        "observed_at_iso": primary["observed_at_iso"],
        "observed_at_display": primary["observed_at_display"],
        "findings": dict(primary["findings"]),
        "confidence": dict(primary["confidence"]),
        "evidence_context": dict(primary["evidence_context"]),
        "risk_help": primary["risk_help"],
        "component_status_table": primary["component_status_table"],
        "source": {"service": "cmis", "operation": primary["operation"]},
        "sources": list(primary["sources"]),
        "warnings": list(primary["warnings"]),
        "errors": list(primary["errors"]),
    }
    return {"report": report, "status": report_status}


def build_solana_scout_graph(
    cmis_client: CMISClient,
    planner_model: Any | None = None,
    *,
    provider_enabled: bool = False,
):
    builder = StateGraph(SolanaScoutState)
    builder.add_node("propose_plan", make_plan_proposal_node(planner_model))
    builder.add_node("enforce_plan", enforce_plan_node)
    builder.add_node(
        "cmis_calls",
        make_cmis_calls_node(cmis_client, provider_enabled=provider_enabled),
    )
    builder.add_node("interpret", interpret_cmis_result)
    builder.add_edge(START, "propose_plan")
    builder.add_edge("propose_plan", "enforce_plan")
    builder.add_edge("enforce_plan", "cmis_calls")
    builder.add_edge("cmis_calls", "interpret")
    builder.add_edge("interpret", END)
    return builder.compile()
