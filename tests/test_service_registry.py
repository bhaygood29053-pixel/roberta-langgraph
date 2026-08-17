"""Tests that Roberta exposes specialists, not CMIS internals."""

from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.mock import MockCMISClient
from roberta.tools.registry import get_roberta_tools


def test_roberta_registry_exposes_chain_scouts_not_cmis() -> None:
    tools = get_roberta_tools(cmis_client=MockCMISClient())
    names = [tool.name for tool in tools]

    assert names == ["x1_scout_investigate", "solana_scout_investigate"]
    assert "market_report" not in names
    assert "risk_check" not in names
    assert "cmis" not in names


def test_roberta_runtime_registry_defaults_to_one_shared_http_cmis(monkeypatch) -> None:
    marker = MockCMISClient()
    calls = []

    def fake_from_env():
        calls.append(True)
        return marker

    monkeypatch.setattr(CMISHTTPClient, "from_env", staticmethod(fake_from_env))
    tools = get_roberta_tools()

    assert calls == [True]
    assert [tool.name for tool in tools] == [
        "x1_scout_investigate",
        "solana_scout_investigate",
    ]
