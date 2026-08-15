"""Task 4 X1 Scout LangGraph specialist subgraph.

The Scout owns X1-specific investigation routing. CMIS owns deterministic
fresh-data/service operations. In Task 4 the CMIS implementation is mocked,
but the authority boundary is already the intended production shape.
"""

from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from roberta.cmis.client import CMISClient
from roberta.x1_scout.state import X1ScoutReport, X1ScoutState


def make_market_report_node(
    cmis_client: CMISClient,
) -> Callable[[X1ScoutState], dict[str, Any]]:
    """Create the node that asks CMIS for X1-scoped market facts."""

    def market_report_node(state: X1ScoutState) -> dict[str, Any]:
        request = state["request"]
        result = cmis_client.market_report(chain="x1", asset=request["asset"])
        return {"cmis_result": result, "status": "running"}

    return market_report_node


def interpret_cmis_result(state: X1ScoutState) -> dict[str, Any]:
    """Convert CMIS facts into X1 Scout's structured specialist report.

    This first version is deliberately deterministic. Agentic investigation
    planning can be added after the specialist/service boundary is proven.
    """
    request = state["request"]
    cmis_result = state["cmis_result"]

    report: X1ScoutReport = {
        "specialist": "x1_scout",
        "chain": "x1",
        "asset": cmis_result["asset"],
        "objective": request["objective"],
        "status": "complete",
        "data_confidence": cmis_result["data_confidence"],
        "findings": {
            "market": cmis_result["market"],
            "risk": cmis_result["risk"],
        },
        "source": {
            "service": cmis_result["service"],
            "operation": cmis_result["operation"],
        },
        "warnings": list(cmis_result["warnings"]),
    }
    return {"report": report, "status": "complete"}


def build_x1_scout_graph(cmis_client: CMISClient):
    """Compile the first X1 Scout specialist subgraph.

    Flow::

        START -> cmis_market_report -> interpret -> END
    """
    builder = StateGraph(X1ScoutState)
    builder.add_node("cmis_market_report", make_market_report_node(cmis_client))
    builder.add_node("interpret", interpret_cmis_result)
    builder.add_edge(START, "cmis_market_report")
    builder.add_edge("cmis_market_report", "interpret")
    builder.add_edge("interpret", END)
    return builder.compile()
