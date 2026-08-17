"""Tests for safe durable-memory policy document construction."""

import json

from roberta.policy import PolicyRule
from roberta.policy.document import build_policy_memory_candidate, policy_rule_document


def test_risk_rule_maps_to_user_risk_policy_memory_without_writing():
    rule = PolicyRule(
        rule_id="liquidity_floor",
        kind="threshold_rule",
        effect="block",
        description="Require configured minimum liquidity.",
        fact_key="market.liquidity_usd",
        operator="gte",
        expected=10000,
        requires_fresh=True,
    )

    candidate = build_policy_memory_candidate(rule)
    document = json.loads(candidate.content)

    assert candidate.key == "policy:liquidity_floor"
    assert candidate.category == "user_risk_policy"
    assert "oracle_policy" in candidate.topics
    assert document["policy_version"] == 1
    assert document["expected"] == 10000
    assert document["requires_fresh"] is True


def test_preference_and_approval_rules_map_to_distinct_memory_categories():
    preference = PolicyRule(
        rule_id="prefer_x1",
        kind="preference",
        effect="preference",
        description="Prefer X1 when otherwise eligible.",
        fact_key="asset.chain",
        operator="eq",
        expected="x1",
    )
    approval = PolicyRule(
        rule_id="approve_value_move",
        kind="approval_rule",
        effect="approval",
        description="Require approval for value movement.",
        fact_key="action.moves_value",
        operator="truthy",
    )

    assert build_policy_memory_candidate(preference).category == "stable_preference"
    assert build_policy_memory_candidate(approval).category == "approval_rule"


def test_document_builder_contains_only_explicit_rule_fields():
    rule = PolicyRule(
        rule_id="verified_only",
        kind="hard_constraint",
        effect="block",
        description="Require verification.",
        fact_key="asset.verified",
        operator="truthy",
        source_memory_key="old-memory-key",
    )

    document = policy_rule_document(rule)

    assert "source_memory_key" not in document
    assert set(document) == {
        "policy_version",
        "rule_id",
        "kind",
        "effect",
        "description",
        "fact_key",
        "operator",
        "expected",
        "requires_fresh",
    }


def test_custom_key_source_and_rationale_are_preserved_as_provenance():
    rule = PolicyRule(
        rule_id="rule",
        kind="hard_constraint",
        effect="block",
        description="Rule description.",
        fact_key="fact",
        operator="truthy",
    )

    candidate = build_policy_memory_candidate(
        rule,
        key="user-policy:rule",
        source="user_confirmed",
        rationale="User explicitly confirmed this rule.",
    )

    assert candidate.key == "user-policy:rule"
    assert candidate.source == "user_confirmed"
    assert candidate.rationale == "User explicitly confirmed this rule."
