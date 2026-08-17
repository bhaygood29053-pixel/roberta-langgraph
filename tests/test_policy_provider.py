"""Tests for HXMP-compatible durable policy loading/provider composition."""

from __future__ import annotations

import json

import pytest
from langchain_core.messages import HumanMessage

from roberta.memory import InMemoryDurableMemoryStore, MemoryRecord
from roberta.policy import PolicyFact
from roberta.policy.provider import (
    PolicyLoadError,
    build_policy_context_provider,
    load_policy_records,
)


def _policy_record(key: str, category: str, *, rule_id: str | None = None) -> MemoryRecord:
    kind = {
        "user_risk_policy": "hard_constraint",
        "stable_preference": "preference",
        "approval_rule": "approval_rule",
    }[category]
    document = {
        "policy_version": 1,
        "rule_id": rule_id or key.replace(":", "_"),
        "kind": kind,
        "description": f"policy {key}",
        "fact_key": f"fact.{key}",
        "operator": "truthy",
    }
    return MemoryRecord(
        key=key,
        category=category,
        content=json.dumps(document),
        topics=("something-unrelated-to-current-query",),
        source="test",
        authority="durable",
    )


def test_loader_finds_policy_by_category_not_current_user_query():
    store = InMemoryDurableMemoryStore(
        [
            _policy_record("risk:one", "user_risk_policy"),
            _policy_record("pref:one", "stable_preference"),
            _policy_record("approval:one", "approval_rule"),
            MemoryRecord(
                key="goal:unrelated",
                category="long_term_goal",
                content="Build Roberta",
                source="test",
                authority="durable",
            ),
        ]
    )

    loaded = load_policy_records(store)

    assert [record.key for record in loaded] == [
        "approval:one",
        "pref:one",
        "risk:one",
    ]


def test_no_policy_records_preserves_no_policy_behavior_without_fact_call():
    store = InMemoryDurableMemoryStore(
        [
            MemoryRecord(
                key="goal:one",
                category="long_term_goal",
                content="Build Roberta",
                source="test",
                authority="durable",
            )
        ]
    )
    called = False

    def fact_provider(state, rules):
        nonlocal called
        called = True
        return {}

    provider = build_policy_context_provider(store, fact_provider)
    result = provider({"messages": [HumanMessage(content="hello")]})

    assert result is None
    assert called is False


def test_loaded_hard_policy_produces_structural_block():
    record = _policy_record("risk:block", "user_risk_policy")
    store = InMemoryDurableMemoryStore([record])

    def fact_provider(state, rules):
        return {rules[0].fact_key: PolicyFact(value=False, source="test")}

    provider = build_policy_context_provider(store, fact_provider)
    runtime = provider({"messages": [HumanMessage(content="assess")]} )

    assert runtime is not None
    assert runtime.decision.status == "blocked"


def test_loader_rejects_truncation_instead_of_silently_losing_rule():
    store = InMemoryDurableMemoryStore(
        [
            _policy_record(f"risk:{index}", "user_risk_policy")
            for index in range(3)
        ]
    )

    with pytest.raises(PolicyLoadError, match="exceeds configured bound"):
        load_policy_records(store, max_records_per_category=2)


def test_policy_fact_provider_must_return_mapping():
    store = InMemoryDurableMemoryStore(
        [_policy_record("risk:one", "user_risk_policy")]
    )
    provider = build_policy_context_provider(store, lambda state, rules: [])

    with pytest.raises(TypeError, match="must return a mapping"):
        provider({"messages": [HumanMessage(content="assess")]})
