"""X1 Scout LangGraph specialist subgraph.

X1 Scout owns chain-specific investigation flow. CMIS owns deterministic data
operations. The Roberta-facing tool still defaults to ``market_report`` in this
milestone; the optional operation field exists inside Scout state so future
Scout planning can choose among typed CMIS operations without changing the
service boundary.
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
        else:  # pragma: no cover - TypedDict contract protects normal callers.
            raise ValueError(f"Unsupported CMIS operation: {operation!r}")

        return {"cmis_result": result, "status": "running"}

    return cmis_call_node


def interpret_cmis_result(state: X1ScoutState) -> dict[str, Any]:
    """Convert a CMIS result into X1 Scout's structured specialist report."""
    request = state["request"]
    result = state["cmis_result"]
    operation = result["operation"]

    if operation == "market_report":
        findings: dict[str, object] = {
            "market": result["market"],
            "risk": result["risk"],
        }
    elif operation == "tokenomics":
        findings = {"tokenomics": result["tokenomics"]}
    elif operation == "risk_check":
        findings = {"risk": result["risk"]}
    else:
        findings = {
            "trade": {
                "action": result["action"],
                "amount_usd": result["amount_usd"],
            },
            "market": result["market"],
            "tokenomics": result["tokenomics"],
            "risk": result["risk"],
        }

    report_status: Literal["complete", "error"] = (
        "error" if result["errors"] else "complete"
    )
    report: X1ScoutReport = {
        "specialist": "x1_scout",
        "chain": "x1",
        "asset": result["asset"],
        "objective": request["objective"],
        "status": report_status,
        "timestamp": result["timestamp"],
        "data_confidence": result["data_confidence"],
        "findings": findings,
        "source": {
            "service": result["service"],
            "operation": operation,
        },
        "sources": list(result["sources"]),
        "warnings": list(result["warnings"]),
        "errors": list(result["errors"]),
    }
    return {"report": report, "status": report_status}


def build_x1_scout_graph(cmis_client: CMISClient):
    """Compile X1 Scout's deterministic service-dispatch subgraph.

    Flow::

        START -> cmis_call -> interpret -> END
    """
    builder = StateGraph(X1ScoutState)
    builder.add_node("cmis_call", make_cmis_call_node(cmis_client))
    builder.add_node("interpret", interpret_cmis_result)
    builder.add_edge(START, "cmis_call")
    builder.add_edge("cmis_call", "interpret")
    builder.add_edge("interpret", END)
    return builder.compile()
