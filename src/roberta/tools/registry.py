"""Roberta specialist/tool registry."""

from typing import Any

from langchain_core.tools import BaseTool

from roberta.cmis.client import CMISClient
from roberta.cmis.http import CMISHTTPClient
from roberta.solana_scout import build_solana_scout_tool
from roberta.x1_scout import build_x1_scout_tool


def get_roberta_tools(
    cmis_client: CMISClient | None = None,
    *,
    x1_planner_model: Any | None = None,
    solana_planner_model: Any | None = None,
    solana_provider_enabled: bool = False,
) -> list[BaseTool]:
    """Return specialist capabilities visible to Roberta.

    CMIS is intentionally not exposed as a Roberta tool. One provider-neutral
    CMIS client is shared by chain Scouts; tests can inject a deterministic
    client. X1 remains enabled. Solana Scout is always visible so unsupported
    requests can fail explicitly, but its CMIS/provider path stays behind the
    deterministic ``solana_provider_enabled`` gate until that backend is verified.
    Planner models are injected separately from Roberta's Oracle model.
    """

    active_cmis = cmis_client or CMISHTTPClient.from_env()
    return [
        build_x1_scout_tool(
            active_cmis,
            planner_model=x1_planner_model,
        ),
        build_solana_scout_tool(
            active_cmis,
            planner_model=solana_planner_model,
            provider_enabled=solana_provider_enabled,
        ),
    ]


def get_phase1_tools() -> list[BaseTool]:
    """Backward-compatible alias retained while Phase 1 code is migrated."""
    return get_roberta_tools()
