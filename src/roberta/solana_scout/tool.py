"""Roberta-facing tool boundary for the Solana Scout specialist."""

import json
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

from roberta.cmis.client import CMISClient
from roberta.solana_scout.graph import build_solana_scout_graph


def build_solana_scout_tool(
    cmis_client: CMISClient,
    planner_model: Any | None = None,
    *,
    provider_enabled: bool = False,
) -> BaseTool:
    """Expose Solana Scout to Roberta without exposing CMIS directly."""

    scout_graph = build_solana_scout_graph(
        cmis_client,
        planner_model=planner_model,
        provider_enabled=provider_enabled,
    )

    def investigate_solana(asset: str, objective: str = "assess market risk") -> str:
        """Delegate a Solana-specific investigation to Solana Scout."""

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
            raise RuntimeError("Solana Scout completed without returning a report")
        return json.dumps(report, sort_keys=True)

    return StructuredTool.from_function(
        func=investigate_solana,
        name="solana_scout_investigate",
        description=(
            "Delegate a Solana-chain market or market-risk investigation to Solana "
            "Scout. Solana Scout obtains structured facts only through CMIS. Until "
            "the Solana CMIS/provider path is enabled, the tool returns an explicit "
            "provider-not-configured result instead of inventing live Solana facts."
        ),
    )
