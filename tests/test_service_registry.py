"""Tests that Roberta's registry exposes specialists, not CMIS internals."""

from roberta.cmis.mock import MockCMISClient
from roberta.tools.registry import get_roberta_tools


def test_roberta_registry_exposes_x1_scout_not_cmis() -> None:
    tools = get_roberta_tools(cmis_client=MockCMISClient())
    names = [tool.name for tool in tools]

    assert names == ["x1_scout_investigate"]
    assert "market_report" not in names
    assert "cmis" not in names
