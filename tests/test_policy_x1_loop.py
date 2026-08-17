"""Full LangGraph policy loop tests with an X1 Scout tool boundary."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from roberta.graph import build_graph
from roberta.memory import InMemoryDurableMemoryStore, MemoryRecord
from roberta.policy import build_policy_context_provider
from roberta.x1_scout import x1_policy_facts_from_state


class ResearchThenAnswerModel:
    """Request X1 research once, then produce a final synthesis if policy allows."""

    def __init__(self) -> None:
        self.calls = 0
        self.bound_tools = []

    def bind_tools(self, tools):
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages):
        self.calls += 1
        has_x1_result = any(
            getattr(message, "name", None) == "x1_scout_investigate"
            for message in messages
        )
        if not has_x1_result:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "x1_scout_investigate",
                        "args": {"asset": "TEST", "objective": "assess market risk"},
                        "id": "call-x1",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="Verified evidence satisfies the durable policy.")


def _liquidity_policy(minimum: float) -> MemoryRecord:
    return MemoryRecord(
        key="policy:min_liquidity",
        category="user_risk_policy",
        content=json.dumps(
            {
                "policy_version": 1,
                "rule_id": "min_liquidity",
                "kind": "threshold_rule",
                "effect": "block",
                "description": "Require the configured minimum X1 liquidity.",
                "fact_key": "market.liquidity",
                "operator": "gte",
                "expected": minimum,
                "requires_fresh": True,
            }
        ),
        topics=("oracle_policy",),
        source="test",
        authority="durable",
    )


def _x1_tool(liquidity: float):
    def investigate_x1(asset: str, objective: str = "assess market risk") -> str:
        report = {
            "specialist": "x1_scout",
            "chain": "x1",
            "requested_asset": asset,
            "asset": {"symbol": asset},
            "objective": objective,
            "investigations": [
                {
                    "operation": "market_report",
                    "cmis_status": "ok",
                    "observed_at_iso": "2026-08-17T13:00:00Z",
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
        func=investigate_x1,
        name="x1_scout_investigate",
        description="Deterministic test X1 Scout boundary.",
    )


def test_missing_evidence_triggers_x1_research_then_allows_final_answer():
    store = InMemoryDurableMemoryStore([_liquidity_policy(1000)])
    provider = build_policy_context_provider(store, x1_policy_facts_from_state)
    model = ResearchThenAnswerModel()
    graph = build_graph(
        model,
        tools=[_x1_tool(5000)],
        policy_context_provider=provider,
    )

    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Assess TEST on X1."}]}
    )

    assert model.calls == 2
    assert result["status"] == "complete"
    assert result["messages"][-1].content == (
        "Verified evidence satisfies the durable policy."
    )


def test_x1_research_can_turn_unresolved_policy_into_structural_block():
    store = InMemoryDurableMemoryStore([_liquidity_policy(10000)])
    provider = build_policy_context_provider(store, x1_policy_facts_from_state)
    model = ResearchThenAnswerModel()
    graph = build_graph(
        model,
        tools=[_x1_tool(5000)],
        policy_context_provider=provider,
    )

    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Assess TEST on X1."}]}
    )

    # First call requests research. On the second Oracle pass the deterministic
    # policy blocks before the model can synthesize a permissive answer.
    assert model.calls == 1
    assert result["status"] == "complete"
    assert result["messages"][-1].content.startswith(
        "Policy blocked this action/recommendation."
    )


def test_partial_x1_evidence_cannot_satisfy_fresh_policy():
    store = InMemoryDurableMemoryStore([_liquidity_policy(1000)])
    provider = build_policy_context_provider(store, x1_policy_facts_from_state)
    model = ResearchThenAnswerModel()

    def partial_x1(asset: str, objective: str = "assess market risk") -> str:
        return json.dumps(
            {
                "specialist": "x1_scout",
                "chain": "x1",
                "asset": {"symbol": asset},
                "investigations": [
                    {
                        "operation": "market_report",
                        "cmis_status": "partial",
                        "observed_at_iso": "2026-08-17T13:00:00Z",
                        "findings": {
                            "data": {"liquidity": 999999},
                            "risk": None,
                        },
                    }
                ],
            }
        )

    tool = StructuredTool.from_function(
        func=partial_x1,
        name="x1_scout_investigate",
        description="Partial X1 evidence test tool.",
    )
    graph = build_graph(
        model,
        tools=[tool],
        policy_context_provider=provider,
    )

    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Assess TEST on X1."}]}
    )

    assert model.calls == 2
    assert result["messages"][-1].content.startswith(
        "Policy cannot be evaluated yet because required evidence is unavailable."
    )
