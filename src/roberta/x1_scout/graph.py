"""X1 Scout LangGraph specialist subgraph.

X1 Scout owns X1-specific investigation planning and interpretation. CMIS owns
deterministic current market/tokenomics/risk services and the X1 Provider
beneath them.
"""

from collections.abc import Callable
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from roberta.cmis.client import CMISClient
from roberta.cmis.contracts import CMISOperation
from roberta.presentation import format_component_status_table
from roberta.risk_help import build_risk_help
from roberta.status_help import build_cmis_status_help
from roberta.time_utils import format_observed_at_utc, normalize_observed_at
from roberta.x1_scout.state import X1ScoutReport, X1ScoutState

_RISK_TERMS = (
    "risk",
    "risky",
    "safety",
    "safe",
    "danger",
    "rug",
)
_TOKENOMICS_TERMS = (
    "tokenomics",
    "supply",
    "mint authority",
    "freeze authority",
    "minting",
)


def select_cmis_operation(objective: str) -> CMISOperation:
    """Select the minimum deterministic CMIS operation required by an objective.

    This is a safety policy boundary, not market analysis. Risk objectives must
    use ``risk_check`` so an LLM never derives a categorical risk conclusion
    from raw ``market_report`` facts. Explicit operations supplied by internal
    callers remain authoritative and bypass this selector.
    """

    normalized = " ".join(str(objective or "").strip().lower().split())
    if any(term in normalized for term in _RISK_TERMS):
        return "risk_check"
    if any(term in normalized for term in _TOKENOMICS_TERMS):
        return "tokenomics"
    return "market_report"


def plan_cmis_operation(state: X1ScoutState) -> dict[str, Any]:
    """Populate an operation when the caller supplied only an investigation goal."""

    request = dict(state["request"])
    if "operation" not in request:
        request["operation"] = select_cmis_operation(request["objective"])
    return {"request": request, "status": "running"}


def make_cmis_call_node(
    cmis_client: CMISClient,
) -> Callable[[X1ScoutState], dict[str, Any]]:
    """Create the deterministic X1-scoped CMIS dispatch node."""

    def cmis_call_node(state: X1ScoutState) -> dict[str, Any]:
        request = state["request"]
        operation: CMISOperation = request["operation"]
        asset = request["asset"]

        if operation == "market_report":
            result = cmis_client.market_report(chain="x1", asset=asset)
        elif operation == "tokenomics":
            result = cmis_client.tokenomics(chain="x1", asset=asset)
        elif operation == "risk_check":
            result = cmis_client.risk_check(chain="x1", asset=asset)
        elif operation == "pre_trade_check":
            action = request.get("action")
            amount_usd = request.get("amount_usd")
            if action is None or amount_usd is None:
                raise ValueError(
                    "pre_trade_check requires action and amount_usd in X1 Scout state"
                )
            result = cmis_client.pre_trade_check(
                chain="x1",
                asset=asset,
                action=action,
                amount_usd=amount_usd,
            )
        else:  # pragma: no cover
            raise ValueError(f"Unsupported CMIS operation: {operation!r}")

        return {"cmis_result": result, "status": "running"}

    return cmis_call_node


def interpret_cmis_result(state: X1ScoutState) -> dict[str, Any]:
    """Preserve CMIS facts and attach deterministic user-facing presentation."""

    request = state["request"]
    result = state["cmis_result"]
    service = result["service"]
    cmis_status = result["status"]
    observed_at = result["observed_at"]
    observed_at_iso = normalize_observed_at(observed_at)
    risk = dict(result["risk"]) if result["risk"] is not None else None
    confidence = dict(result["confidence"])
    risk_help = build_risk_help(risk, confidence)

    report_status: Literal["complete", "error"] = (
        "error" if cmis_status in {"unavailable", "error"} else "complete"
    )
    report: X1ScoutReport = {
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": request["asset"],
        "asset": dict(result["asset"]),
        "objective": request["objective"],
        "status": report_status,
        "cmis_status": cmis_status,
        "cmis_status_help": build_cmis_status_help(
            service,
            cmis_status,
            confidence,
        ),
        "observed_at": observed_at,
        "observed_at_iso": observed_at_iso,
        "observed_at_display": format_observed_at_utc(observed_at_iso),
        "findings": {
            "data": dict(result["data"]),
            "risk": risk,
        },
        "confidence": confidence,
        "risk_help": risk_help,
        "component_status_table": format_component_status_table(risk_help),
        "source": {
            "service": "cmis",
            "operation": service,
        },
        "sources": list(result["sources"]),
        "warnings": list(result["warnings"]),
        "errors": list(result["errors"]),
    }
    return {"report": report, "status": report_status}


def build_x1_scout_graph(cmis_client: CMISClient):
    """Compile X1 Scout's objective-planning and CMIS dispatch subgraph.

    Flow::

        START -> plan -> cmis_call -> interpret -> END
    """

    builder = StateGraph(X1ScoutState)
    builder.add_node("plan", plan_cmis_operation)
    builder.add_node("cmis_call", make_cmis_call_node(cmis_client))
    builder.add_node("interpret", interpret_cmis_result)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "cmis_call")
    builder.add_edge("cmis_call", "interpret")
    builder.add_edge("interpret", END)
    return builder.compile()
