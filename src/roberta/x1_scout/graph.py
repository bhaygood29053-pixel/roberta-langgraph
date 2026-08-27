"""X1 Scout LangGraph specialist subgraph.

X1 Scout owns X1-specific investigation planning and interpretation. CMIS owns
deterministic current market/tokenomics/risk/verification services and the X1
Provider beneath them. Evidence receipt/proof metadata is projected separately
from market findings so Roberta can explain proof without rewriting facts.
"""

from collections.abc import Callable
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from roberta.cmis.client import CMISClient
from roberta.cmis.contracts import CMISEnvelope, CMISOperation
from roberta.evidence_aware import evidence_context
from roberta.presentation import format_component_status_table
from roberta.pretrade_ux import build_pretrade_presentation
from roberta.risk_help import build_risk_help
from roberta.status_help import build_cmis_status_help
from roberta.time_utils import format_observed_at_utc, normalize_observed_at
from roberta.x1_scout.planner import (
    compare_asset_from_objective,
    enforce_plan,
    propose_plan,
    historical_mode_from_objective,
    rank_limit_from_objective,
    rank_metric_from_objective,
    select_cmis_operation,
)
from roberta.x1_scout.state import (
    X1ScoutInvestigation,
    X1ScoutReport,
    X1ScoutState,
)


def plan_cmis_operation(state: X1ScoutState) -> dict[str, Any]:
    """Backward-compatible deterministic single-operation planning helper."""
    request = dict(state["request"])
    if "operation" not in request:
        request["operation"] = select_cmis_operation(request["objective"])
    return {"request": request, "status": "running"}


def make_plan_proposal_node(planner_model: Any | None) -> Callable[[X1ScoutState], dict[str, Any]]:
    def propose_plan_node(state: X1ScoutState) -> dict[str, Any]:
        request = state["request"]
        if "operation" in request or planner_model is None:
            return {"plan_proposal": None, "planner_error": None, "status": "running"}
        try:
            proposal = propose_plan(planner_model, request)
        except Exception as exc:
            return {
                "plan_proposal": None,
                "planner_error": f"{type(exc).__name__}: {exc}",
                "status": "running",
            }
        return {"plan_proposal": proposal, "planner_error": None, "status": "running"}

    return propose_plan_node


def enforce_plan_node(state: X1ScoutState) -> dict[str, Any]:
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
    objective = request["objective"]
    if operation == "market_report":
        return cmis_client.market_report(chain="x1", asset=asset)
    if operation == "rank":
        return cmis_client.rank(
            chain="x1",
            metric=rank_metric_from_objective(objective),
            limit=rank_limit_from_objective(objective),
        )
    if operation == "historical_compare":
        mode = historical_mode_from_objective(
            objective,
            compare_asset=request.get("compare_asset"),
        )
        return cmis_client.historical_compare(
            chain="x1",
            asset=asset,
            question=str(objective),
            mode=mode,
            compare_asset=(
                str(request["compare_asset"])
                if mode == "all_available_pair"
                else None
            ),
        )
    if operation == "tokenomics":
        return cmis_client.tokenomics(chain="x1", asset=asset)
    if operation == "risk_check":
        return cmis_client.risk_check(chain="x1", asset=asset)
    if operation == "verification_evidence":
        return cmis_client.verification_evidence(
            chain="x1",
            evidence_id=request.get("evidence_id"),
            fact_type=request.get("fact_type"),
            subject_id=request.get("subject_id"),
        )
    if operation == "concentration_change_intelligence":
        intelligence_evidence_id = request.get("intelligence_evidence_id")
        if intelligence_evidence_id is None:
            raise ValueError(
                "concentration_change_intelligence requires an exact intelligence_evidence_id"
            )
        return cmis_client.concentration_change_intelligence(
            chain="x1",
            asset=asset,
            intelligence_evidence_id=intelligence_evidence_id,
        )
    if operation == "pre_trade_check":
        action = request.get("action")
        amount_usd = request.get("amount_usd")
        if action is None or amount_usd is None:
            raise ValueError("pre_trade_check requires action and amount_usd in X1 Scout state")
        return cmis_client.pre_trade_check(
            chain="x1",
            asset=asset,
            action=action,
            amount_usd=amount_usd,
        )
    raise ValueError(f"Unsupported CMIS operation: {operation!r}")  # pragma: no cover


def make_cmis_calls_node(cmis_client: CMISClient) -> Callable[[X1ScoutState], dict[str, Any]]:
    def cmis_calls_node(state: X1ScoutState) -> dict[str, Any]:
        request = dict(state["request"])
        if "compare_asset" not in request:
            inferred_compare = compare_asset_from_objective(
                request.get("objective"),
                primary_asset=request.get("asset"),
            )
            if inferred_compare is not None:
                request["compare_asset"] = inferred_compare

        operations = state["plan"]["operations"]
        results = [
            _dispatch_cmis_operation(cmis_client, request, operation)
            for operation in operations
        ]
        if not results:  # pragma: no cover
            raise RuntimeError("X1 Scout plan completed without a CMIS operation.")
        return {
            "request": request,
            "cmis_results": results,
            "cmis_result": results[-1],
            "status": "running",
        }

    return cmis_calls_node


def make_cmis_call_node(cmis_client: CMISClient) -> Callable[[X1ScoutState], dict[str, Any]]:
    return make_cmis_calls_node(cmis_client)


def _summarize_cmis_result(
    result: CMISEnvelope,
    *,
    objective: object = None,
) -> X1ScoutInvestigation:
    service = result["service"]
    cmis_status = result["status"]
    observed_at = result["observed_at"]
    observed_at_iso = normalize_observed_at(observed_at)
    risk = dict(result["risk"]) if result["risk"] is not None else None
    confidence = dict(result["confidence"])
    risk_help = build_risk_help(risk, confidence)
    proof = evidence_context(result)

    return {
        "operation": service,
        "cmis_status": cmis_status,
        "cmis_status_help": build_cmis_status_help(service, cmis_status, confidence),
        "observed_at": observed_at,
        "observed_at_iso": observed_at_iso,
        "observed_at_display": format_observed_at_utc(observed_at_iso),
        "findings": {"data": dict(result["data"]), "risk": risk},
        "confidence": confidence,
        "evidence_context": proof,
        "risk_help": risk_help,
        "component_status_table": format_component_status_table(risk_help),
        "pretrade_presentation": build_pretrade_presentation(result, objective=objective),
        "sources": list(result["sources"]),
        "warnings": list(result["warnings"]),
        "errors": list(result["errors"]),
    }


def interpret_cmis_result(state: X1ScoutState) -> dict[str, Any]:
    """Preserve every CMIS result and attach deterministic presentation/evidence."""
    request = state["request"]
    results = state.get("cmis_results") or [state["cmis_result"]]
    investigations = [
        _summarize_cmis_result(result, objective=request["objective"])
        for result in results
    ]
    primary_result = results[-1]
    primary = investigations[-1]

    report_status: Literal["complete", "error"] = (
        "error"
        if any(
            investigation["cmis_status"] in {"unavailable", "error"}
            for investigation in investigations
        )
        else "complete"
    )

    report: X1ScoutReport = {
        "specialist": "x1_scout",
        "chain": "x1",
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
        "pretrade_presentation": primary["pretrade_presentation"],
        "source": {"service": "cmis", "operation": primary["operation"]},
        "sources": list(primary["sources"]),
        "warnings": list(primary["warnings"]),
        "errors": list(primary["errors"]),
    }
    compare_asset = request.get("compare_asset")
    if compare_asset is not None:
        report["requested_compare_asset"] = str(compare_asset)
    return {"report": report, "status": report_status}


def build_x1_scout_graph(cmis_client: CMISClient, planner_model: Any | None = None):
    builder = StateGraph(X1ScoutState)
    builder.add_node("propose_plan", make_plan_proposal_node(planner_model))
    builder.add_node("enforce_plan", enforce_plan_node)
    builder.add_node("cmis_calls", make_cmis_calls_node(cmis_client))
    builder.add_node("interpret", interpret_cmis_result)
    builder.add_edge(START, "propose_plan")
    builder.add_edge("propose_plan", "enforce_plan")
    builder.add_edge("enforce_plan", "cmis_calls")
    builder.add_edge("cmis_calls", "interpret")
    builder.add_edge("interpret", END)
    return builder.compile()
