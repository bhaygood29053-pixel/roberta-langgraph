"""Tests that Roberta exposes specialists, not CMIS internals."""

import json

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


def test_registry_solana_provider_gate_wires_to_shared_cmis_client() -> None:
    client = MockCMISClient()
    tools = get_roberta_tools(
        cmis_client=client,
        solana_provider_enabled=True,
    )
    solana_tool = next(tool for tool in tools if tool.name == "solana_scout_investigate")

    raw = solana_tool.invoke({"asset": "JUP", "objective": "verify token supply"})
    report = json.loads(raw)

    assert client.calls == [
        {"operation": "tokenomics", "chain": "solana", "asset": "JUP"}
    ]
    assert report["specialist"] == "solana_scout"
    assert report["chain"] == "solana"
    assert report["source"] == {"service": "cmis", "operation": "tokenomics"}


def test_registry_default_keeps_solana_provider_gate_closed() -> None:
    client = MockCMISClient()
    tools = get_roberta_tools(cmis_client=client)
    solana_tool = next(tool for tool in tools if tool.name == "solana_scout_investigate")

    raw = solana_tool.invoke({"asset": "JUP", "objective": "verify token supply"})
    report = json.loads(raw)

    assert client.calls == []
    assert report["status"] == "unavailable"
    assert report["warnings"][0]["code"] == "SOLANA_PROVIDER_NOT_CONFIGURED"
