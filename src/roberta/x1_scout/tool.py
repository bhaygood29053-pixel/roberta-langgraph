"""Roberta-facing tool boundary for the X1 Scout specialist."""

import json
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

from roberta.cmis.client import CMISClient
from roberta.x1_scout.graph import build_x1_scout_graph


def build_x1_scout_tool(
    cmis_client: CMISClient,
    planner_model: Any | None = None,
) -> BaseTool:
    """Expose X1 Scout to Roberta without exposing CMIS directly."""
    scout_graph = build_x1_scout_graph(cmis_client, planner_model=planner_model)

    def investigate_x1(asset: str, objective: str = "assess market risk") -> str:
        """Delegate an X1-specific investigation to X1 Scout."""
        result = scout_graph.invoke(
            {
                "request": {
                    "asset": asset,
                    "objective": objective,
                },
                "status": "running",
            }
        )
        report = result.get("report")
        if report is None:
            raise RuntimeError("X1 Scout completed without returning a report.")
        return json.dumps(report, sort_keys=True)

    return StructuredTool.from_function(
        func=investigate_x1,
        name="x1_scout_investigate",
        description=(
            "Delegate an X1-chain market or market-risk investigation to X1 Scout. "
            "Use this for X1 assets when current market facts or market-risk context "
            "would be needed. X1 Scout owns X1-specific investigation and obtains "
            "structured facts from CMIS."
        ),
    )
