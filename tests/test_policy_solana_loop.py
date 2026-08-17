"""Full LangGraph policy loop tests across the Solana Scout boundary."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from roberta.cmis.mock import MockCMISClient
from roberta.graph import build_graph
from roberta.memory import InMemoryDurableMemoryStore, MemoryRecord
from roberta.policy import build_policy_context_provider
from roberta.solana_scout import build_solana_scout_tool
from roberta.specialists.policy_facts import chain_policy_facts_from_state


class ResearchThenAnswerModel:
    """Request Solana research once, then answer only if policy permits."""

    def __init__(self) -> None:
        self.calls = 0
        self.bound_tools = []

    def bind_tools(self, tools):
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages):
        self.calls += 1
        has_solana_result = any(
            getattr(message, "name", None) == "solana_scout_investigate"
            for message in messages
        )
        if not has_solana_result:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "solana_scout_investigate",
                        "args": {
                            "asset": "TEST",
                            "objective": "show price and liquidity",
                        },
                        "id": "call-solana",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="Verified Solana evidence satisfies the durable policy.")


def _liquidity_policy(minimum: float) -> MemoryRecord:
    return MemoryRecord(
        key="policy:solana_min_liquidity",
        category="user_risk_policy",
        content=json.dumps(
            {
                "policy_version": 1,
                "rule_id": "solana_min_liquidity",
                "kind": "threshold_rule",
                "effect": "block",
                "description": "Require the configured minimum Solana liquidity.",
                "fact_key": "market.liquidity",
                "operator": "gte",
                "expected": minimum,
                "requires_fresh": True,
            }
        ),
        topics=("oracle_policy", "solana"),
        source="test",
        authority="durable",
    )


def _verified_solana_tool(liquidity: float):
    def investigate_solana(asset: str, objective: str = "show price and liquidity") -> str:
        report = {
            "specialist": "solana_scout",
            "chain": "solana",
            "requested_asset": asset,
            "asset": {"symbol": asset},
            "objective": objective,
            "investigations": [
                {
                    "operation": "market_report",
                    "cmis_status": "ok",
                    "observed_at_iso": "2026-08-17T14:00:00Z",
                    "findings": {
                        "data": {
                            "price": 1.0,
                            "liquidity": liquidity,
                            "#LPs": 10,
                            "volume_24h": 5000,
                        },
                        "risk": None,
                    },
                }
            ],
        }
        return json.dumps(report, sort_keys=True)

    return StructuredTool.from_function(
        func=investigate_solana,
        name="solana_scout_investigate",
        description="Deterministic verified Solana Scout test boundary.",
    )


def test_missing_evidence_routes_to_solana_scout_then_allows_final_answer() -> None:
    store = InMemoryDurableMemoryStore([_liquidity_policy(1000)])
    provider = build_policy_context_provider(store, chain_policy_facts_from_state)
    model = ResearchThenAnswerModel()
    graph = build_graph(
        model,
        tools=[_verified_solana_tool(5000)],
        policy_context_provider=provider,
    )

    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Assess TEST on Solana."}]}
    )

    assert model.calls == 2
    assert result["status"] == "complete"
    assert result["messages"][-1].content == (
        "Verified Solana evidence satisfies the durable policy."
    )


def test_solana_research_can_turn_unresolved_policy_into_structural_block() -> None:
    store = InMemoryDurableMemoryStore([_liquidity_policy(10000)])
    provider = build_policy_context_provider(store, chain_policy_facts_from_state)
    model = ResearchThenAnswerModel()
    graph = build_graph(
        model,
        tools=[_verified_solana_tool(5000)],
        policy_context_provider=provider,
    )

    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Assess TEST on Solana."}]}
    )

    # First Oracle call requests research. The second Oracle pass blocks
    # deterministically before the model can create a permissive answer.
    assert model.calls == 1
    assert result["status"] == "complete"
    assert result["messages"][-1].content.startswith(
        "Policy blocked this action/recommendation."
    )


def test_default_unconfigured_solana_scout_cannot_satisfy_fresh_policy() -> None:
    store = InMemoryDurableMemoryStore([_liquidity_policy(1000)])
    provider = build_policy_context_provider(store, chain_policy_facts_from_state)
    model = ResearchThenAnswerModel()
    client = MockCMISClient()
    tool = build_solana_scout_tool(client)  # provider gate remains disabled
    graph = build_graph(
        model,
        tools=[tool],
        policy_context_provider=provider,
    )

    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Assess TEST on Solana."}]}
    )

    assert client.calls == []
    assert model.calls == 2
    assert result["status"] == "complete"
    assert result["messages"][-1].content.startswith(
        "Policy cannot be evaluated yet because required evidence is unavailable."
    )


def test_partial_solana_cmis_result_cannot_satisfy_fresh_policy() -> None:
    store = InMemoryDurableMemoryStore([_liquidity_policy(1000)])
    provider = build_policy_context_provider(store, chain_policy_facts_from_state)
    model = ResearchThenAnswerModel()
    client = MockCMISClient()  # deterministic adapter returns partial, non-live data
    tool = build_solana_scout_tool(client, provider_enabled=True)
    graph = build_graph(
        model,
        tools=[tool],
        policy_context_provider=provider,
    )

    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Assess TEST on Solana."}]}
    )

    assert client.calls == [
        {"operation": "market_report", "chain": "solana", "asset": "TEST"}
    ]
    assert model.calls == 2
    assert result["messages"][-1].content.startswith(
        "Policy cannot be evaluated yet because required evidence is unavailable."
    )
