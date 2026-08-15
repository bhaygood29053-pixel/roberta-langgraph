"""X1 Scout LangGraph specialist subgraph.

X1 Scout owns X1-specific investigation flow. CMIS owns deterministic current
market/tokenomics/risk services and the X1 Provider beneath them.
"""

from collections.abc import Callable
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from roberta.cmis.client import CMISClient
from roberta.cmis.contracts import CMISOperation
from roberta.x1_scout.state import X1ScoutReport, X1ScoutState


def make_cmis_call_node(
    cmis_client: CMISClient,
) -> Callable[[X1ScoutState], dict[str, Any]]:
    """Create the deterministic X1-scoped CMIS dispatch node."""

    def cmis_call_node(state: X1ScoutState) -> dict[str, Any]:
        request = state["request"]
        operation: CMISOperation = request.get("operation", "market_report")
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
    """Preserve the external CMIS envelope in X1 Scout's specialist report."""

    request = state["request"]
    result = state["cmis_result"]
    cmis_status = result["status"]

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
        "observed_at": result["observed_at"],
        "findings": {
            "data": dict(result["data"]),
            "risk": dict(result["risk"]) if result["risk"] is not None else None,
        },
        "confidence": dict(result["confidence"]),
        "source": {
            "service": "cmis",
            "operation": result["service"],
        },
        "sources": list(result["sources"]),
        "warnings": list(result["warnings"]),
        "errors": list(result["errors"]),
    }
    return {"report": report, "status": report_status}


def build_x1_scout_graph(cmis_client: CMISClient):
    """Compile X1 Scout's deterministic CMIS dispatch subgraph."""

    builder = StateGraph(X1ScoutState)
    builder.add_node("cmis_call", make_cmis_call_node(cmis_client))
    builder.add_node("interpret", interpret_cmis_result)
    builder.add_edge(START, "cmis_call")
    builder.add_edge("cmis_call", "interpret")
    builder.add_edge("interpret", END)
    return builder.compile()
