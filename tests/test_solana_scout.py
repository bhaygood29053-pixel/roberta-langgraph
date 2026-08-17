"""Deterministic tests for the gated Solana Scout specialist."""

import json

from langchain_core.messages import AIMessage

from roberta.cmis.mock import MockCMISClient
from roberta.solana_scout import build_solana_scout_graph, build_solana_scout_tool


class _Planner:
    def invoke(self, messages):
        return AIMessage(content='{"operations":["pre_trade_check","risk_check"]}')


def _request(objective: str = "assess market risk") -> dict[str, object]:
    return {
        "request": {"asset": "JUP", "objective": objective},
        "status": "running",
    }


def test_solana_provider_gate_returns_unavailable_without_cmis_call() -> None:
    client = MockCMISClient()
    graph = build_solana_scout_graph(client)

    result = graph.invoke(_request())
    report = result["report"]

    assert client.calls == []
    assert result["status"] == "unavailable"
    assert report["specialist"] == "solana_scout"
    assert report["chain"] == "solana"
    assert report["status"] == "unavailable"
    assert report["cmis_status"] == "unavailable"
    assert report["investigations"] == []
    assert report["source"]["service"] == "roberta_configuration"
    assert report["warnings"][0]["code"] == "SOLANA_PROVIDER_NOT_CONFIGURED"
    assert report["observed_at"] is None


def test_enabled_solana_scout_uses_shared_cmis_contract_with_explicit_chain() -> None:
    client = MockCMISClient()
    graph = build_solana_scout_graph(client, provider_enabled=True)

    result = graph.invoke(_request())
    report = result["report"]

    assert client.calls == [
        {"operation": "risk_check", "chain": "solana", "asset": "JUP"}
    ]
    assert result["status"] == "complete"
    assert report["chain"] == "solana"
    assert report["source"] == {"service": "cmis", "operation": "risk_check"}
    assert report["cmis_status"] == "partial"
    assert report["findings"]["risk"]["outcome"] == "TEST_ONLY"
    assert report["warnings"][0]["code"] == "MOCK_CMIS"


def test_solana_planner_cannot_autonomously_add_pre_trade() -> None:
    client = MockCMISClient()
    graph = build_solana_scout_graph(client, planner_model=_Planner())

    result = graph.invoke(_request())
    report = result["report"]

    assert client.calls == []
    assert report["plan"]["operations"] == ["risk_check"]
    assert "planner_operation_rejected: pre_trade_check" in report["plan"]["warnings"]


def test_solana_tool_is_visible_but_fails_explicitly_closed_by_default() -> None:
    client = MockCMISClient()
    tool = build_solana_scout_tool(client)

    raw = tool.invoke({"asset": "JUP", "objective": "show price"})
    report = json.loads(raw)

    assert tool.name == "solana_scout_investigate"
    assert client.calls == []
    assert report["status"] == "unavailable"
    assert report["warnings"][0]["code"] == "SOLANA_PROVIDER_NOT_CONFIGURED"


def test_enabled_solana_tool_never_exposes_cmis_as_roberta_tool_name() -> None:
    client = MockCMISClient()
    tool = build_solana_scout_tool(client, provider_enabled=True)

    raw = tool.invoke({"asset": "JUP", "objective": "verify token supply"})
    report = json.loads(raw)

    assert tool.name == "solana_scout_investigate"
    assert client.calls == [
        {"operation": "tokenomics", "chain": "solana", "asset": "JUP"}
    ]
    assert report["source"]["service"] == "cmis"
    assert report["source"]["operation"] == "tokenomics"
