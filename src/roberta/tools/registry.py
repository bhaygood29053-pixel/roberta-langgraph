"""Roberta specialist/tool registry."""

from typing import Any

from langchain_core.tools import BaseTool

from roberta.cmis.client import CMISClient
from roberta.cmis.http import CMISHTTPClient
from roberta.x1_scout import build_x1_scout_tool


def get_roberta_tools(
    cmis_client: CMISClient | None = None,
    *,
    x1_planner_model: Any | None = None,
) -> list[BaseTool]:
    """Return specialist capabilities visible to Roberta.

    CMIS is intentionally not exposed as a Roberta tool. The runtime default is
    the external CMIS HTTP gateway; tests can inject a deterministic client.
    X1 Scout's planner model is injected separately from Roberta's Oracle model.
    """
    active_cmis = cmis_client or CMISHTTPClient.from_env()
    return [
        build_x1_scout_tool(
            active_cmis,
            planner_model=x1_planner_model,
        )
    ]


def get_phase1_tools() -> list[BaseTool]:
    """Backward-compatible alias retained while Phase 1 code is migrated."""
    return get_roberta_tools()
