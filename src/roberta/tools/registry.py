"""Roberta service/tool registry for the first X1 Scout integration."""

from langchain_core.tools import BaseTool

from roberta.cmis.client import CMISClient
from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout import build_x1_scout_tool


def get_roberta_tools(cmis_client: CMISClient | None = None) -> list[BaseTool]:
    """Return specialist capabilities visible to Roberta.

    CMIS is intentionally not exposed as a Roberta tool. Roberta delegates X1
    investigations to X1 Scout, and X1 Scout owns the CMIS call beneath it.
    """
    active_cmis = cmis_client or MockCMISClient()
    return [build_x1_scout_tool(active_cmis)]


def get_phase1_tools() -> list[BaseTool]:
    """Backward-compatible alias retained while Phase 1 code is migrated."""
    return get_roberta_tools()
