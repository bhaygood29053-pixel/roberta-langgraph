"""End-to-end deterministic Phase 8 tests from durable memory to Oracle output."""

import json

from langchain_core.messages import AIMessage, HumanMessage

from roberta.graph import make_oracle_node
from roberta.memory import InMemoryDurableMemoryStore, MemoryRecord
from roberta.policy import PolicyFact, build_policy_context_provider


class Model:
    def __init__(self, content="model answer") -> None:
        self.content = content
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return AIMessage(content=self.content)


def _risk_policy(*, expected: bool = True) -> MemoryRecord:
    return MemoryRecord(
        key="policy:asset_allowed",
        category="user_risk_policy",
        content=json.dumps(
            {
                "policy_version": 1,
                "rule_id": "asset_allowed",
                "kind": "hard_constraint",
                "effect": "block",
                "description": "Asset must satisfy the user's eligibility rule.",
                "fact_key": "asset.allowed",
                "operator": "eq",
                "expected": expected,
                "requires_fresh": False,
            }
        ),
        topics=("oracle_policy",),
        source="test",
        authority="durable",
    )


def test_durable_hard_policy_blocks_oracle_before_model_end_to_end():
    store = InMemoryDurableMemoryStore([_risk_policy()])

    def facts(state, rules):
        return {"asset.allowed": PolicyFact(value=False, source="verified-test")}

    provider = build_policy_context_provider(store, facts)
    model = Model(content="Model would have said proceed.")
    node = make_oracle_node(model, policy_context_provider=provider)

    result = node({"messages": [HumanMessage(content="Should I proceed?")]})

    assert model.calls == 0
    assert result["status"] == "complete"
    assert "Policy blocked" in result["messages"][0].content
    assert "eligibility rule" in result["messages"][0].content


def test_durable_policy_pass_allows_oracle_synthesis_end_to_end():
    store = InMemoryDurableMemoryStore([_risk_policy()])

    def facts(state, rules):
        return {"asset.allowed": PolicyFact(value=True, source="verified-test")}

    provider = build_policy_context_provider(store, facts)
    model = Model(content="Policy-aware analysis.")
    result = make_oracle_node(model, policy_context_provider=provider)(
        {"messages": [HumanMessage(content="Assess it.")]}
    )

    assert model.calls == 1
    assert result["messages"][0].content == "Policy-aware analysis."


def test_free_form_phase7_risk_memory_does_not_activate_enforcement_end_to_end():
    store = InMemoryDurableMemoryStore(
        [
            MemoryRecord(
                key="risk:freeform",
                category="user_risk_policy",
                content="I tend to prefer conservative decisions.",
                source="test",
                authority="durable",
            )
        ]
    )
    fact_calls = 0

    def facts(state, rules):
        nonlocal fact_calls
        fact_calls += 1
        return {}

    provider = build_policy_context_provider(store, facts)
    model = Model(content="Normal no-policy behavior.")
    result = make_oracle_node(model, policy_context_provider=provider)(
        {"messages": [HumanMessage(content="Hello.")]}
    )

    assert fact_calls == 0
    assert model.calls == 1
    assert result["messages"][0].content == "Normal no-policy behavior."


def test_fresh_rule_with_historical_fact_cannot_be_passed_end_to_end():
    record = MemoryRecord(
        key="policy:fresh_risk",
        category="user_risk_policy",
        content=json.dumps(
            {
                "policy_version": 1,
                "rule_id": "fresh_risk",
                "kind": "evidence_requirement",
                "effect": "evidence",
                "description": "Fresh risk evidence is required.",
                "fact_key": "market.risk",
                "operator": "present",
                "requires_fresh": True,
            }
        ),
        topics=("oracle_policy",),
        source="test",
        authority="durable",
    )
    store = InMemoryDurableMemoryStore([record])

    def facts(state, rules):
        return {
            "market.risk": PolicyFact(
                value="old snapshot",
                evidence_status="verified",
                freshness="historical",
                source="memory",
            )
        }

    provider = build_policy_context_provider(store, facts)
    model = Model(content="Model tried to finish anyway.")
    result = make_oracle_node(model, policy_context_provider=provider)(
        {"messages": [HumanMessage(content="What is current risk?")]}
    )

    assert model.calls == 1
    assert "required evidence is unavailable" in result["messages"][0].content
    assert "Model tried" not in result["messages"][0].content
