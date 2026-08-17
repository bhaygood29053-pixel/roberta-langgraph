"""Deterministic tests for Phase 8 Oracle policy contracts."""

from __future__ import annotations

import json

import pytest

from roberta.memory import MemoryRecord
from roberta.policy import (
    PolicyFact,
    PolicyRule,
    compile_policy_memories,
    evaluate_policy,
    evaluate_policy_rule,
)


def _memory(
    *,
    key: str,
    category: str,
    document: dict,
    authority: str = "durable",
) -> MemoryRecord:
    return MemoryRecord(
        key=key,
        category=category,
        content=json.dumps(document, sort_keys=True),
        topics=("policy",),
        source="test",
        authority=authority,
    )


def test_compile_explicit_hard_constraint_from_durable_risk_policy():
    record = _memory(
        key="risk:max_single_asset_pct",
        category="user_risk_policy",
        document={
            "policy_version": 1,
            "rule_id": "max_single_asset_pct",
            "kind": "threshold_rule",
            "effect": "block",
            "description": "Do not exceed the configured single-asset exposure.",
            "fact_key": "portfolio.single_asset_pct",
            "operator": "lte",
            "expected": 25,
            "requires_fresh": True,
        },
    )

    compiled = compile_policy_memories([record])

    assert compiled.issues == ()
    assert len(compiled.rules) == 1
    rule = compiled.rules[0]
    assert rule.rule_id == "max_single_asset_pct"
    assert rule.effect == "block"
    assert rule.requires_fresh is True
    assert rule.source_memory_key == record.key


def test_free_form_policy_memory_is_not_silently_inferred_into_rule():
    record = MemoryRecord(
        key="risk:freeform",
        category="user_risk_policy",
        content="I prefer conservative trades.",
        source="test",
        authority="durable",
    )

    compiled = compile_policy_memories([record])

    assert compiled.rules == ()
    assert len(compiled.issues) == 1
    assert "valid JSON" in compiled.issues[0].reason


def test_historical_context_cannot_become_enforceable_policy():
    record = _memory(
        key="risk:old",
        category="user_risk_policy",
        authority="historical_context",
        document={
            "policy_version": 1,
            "rule_id": "old_rule",
            "kind": "hard_constraint",
            "description": "Old rule",
            "fact_key": "x",
            "operator": "truthy",
        },
    )

    compiled = compile_policy_memories([record])

    assert compiled.rules == ()
    assert compiled.issues[0].reason == "policy memory must have durable authority"


def test_memory_category_restricts_policy_kind():
    record = _memory(
        key="pref:bad",
        category="stable_preference",
        document={
            "policy_version": 1,
            "rule_id": "bad_pref",
            "kind": "hard_constraint",
            "description": "Must not be promoted",
            "fact_key": "asset.chain",
            "operator": "eq",
            "expected": "x1",
        },
    )

    compiled = compile_policy_memories([record])

    assert compiled.rules == ()
    assert "not valid for memory category" in compiled.issues[0].reason


def test_threshold_rule_requires_explicit_block_or_warn_effect():
    record = _memory(
        key="risk:threshold",
        category="user_risk_policy",
        document={
            "policy_version": 1,
            "rule_id": "threshold",
            "kind": "threshold_rule",
            "description": "Threshold",
            "fact_key": "market.liquidity_usd",
            "operator": "gte",
            "expected": 1000,
        },
    )

    compiled = compile_policy_memories([record])

    assert compiled.rules == ()
    assert "requires explicit effect" in compiled.issues[0].reason


def test_duplicate_rule_ids_fail_closed_after_first_rule():
    document = {
        "policy_version": 1,
        "rule_id": "same",
        "kind": "preference",
        "description": "Prefer X1",
        "fact_key": "asset.chain",
        "operator": "eq",
        "expected": "x1",
    }
    compiled = compile_policy_memories(
        [
            _memory(key="pref:a", category="stable_preference", document=document),
            _memory(key="pref:b", category="stable_preference", document=document),
        ]
    )

    assert len(compiled.rules) == 1
    assert len(compiled.issues) == 1
    assert "duplicate rule_id" in compiled.issues[0].reason


def test_hard_constraint_cannot_be_overridden_by_soft_preference():
    rules = [
        PolicyRule(
            rule_id="block_unverified",
            kind="hard_constraint",
            effect="block",
            description="Only verified assets are eligible.",
            fact_key="asset.verified",
            operator="truthy",
        ),
        PolicyRule(
            rule_id="prefer_x1",
            kind="preference",
            effect="preference",
            description="Prefer X1 when otherwise eligible.",
            fact_key="asset.chain",
            operator="eq",
            expected="x1",
        ),
    ]
    facts = {
        "asset.verified": PolicyFact(value=False, evidence_status="verified"),
        "asset.chain": PolicyFact(value="x1", evidence_status="verified"),
    }

    summary = evaluate_policy(rules, facts)

    assert summary.blocked is True
    assert summary.results[0].outcome == "block"
    assert summary.results[1].outcome == "preference_met"


def test_missing_fact_is_insufficient_evidence_not_block_or_pass():
    rule = PolicyRule(
        rule_id="liquidity_floor",
        kind="threshold_rule",
        effect="block",
        description="Require minimum liquidity.",
        fact_key="market.liquidity_usd",
        operator="gte",
        expected=10000,
        requires_fresh=True,
    )

    result = evaluate_policy_rule(rule, {})

    assert result.outcome == "insufficient_evidence"
    assert result.reason == "required fact is missing"


@pytest.mark.parametrize(
    "status",
    ["unverified", "conflict", "insufficient_evidence"],
)
def test_non_verified_fact_cannot_satisfy_policy(status):
    rule = PolicyRule(
        rule_id="verified_liquidity",
        kind="threshold_rule",
        effect="block",
        description="Require verified liquidity.",
        fact_key="market.liquidity_usd",
        operator="gte",
        expected=1000,
    )
    fact = PolicyFact(
        value=5000,
        evidence_status=status,
        freshness="fresh",
        source="cmis",
    )

    result = evaluate_policy_rule(rule, {"market.liquidity_usd": fact})

    assert result.outcome == "insufficient_evidence"


def test_historical_fact_cannot_satisfy_fresh_policy_requirement():
    rule = PolicyRule(
        rule_id="fresh_risk",
        kind="evidence_requirement",
        effect="evidence",
        description="Current risk evidence is required.",
        fact_key="market.risk",
        requires_fresh=True,
    )
    fact = PolicyFact(
        value="low",
        evidence_status="verified",
        freshness="historical",
        source="memory",
    )

    result = evaluate_policy_rule(rule, {"market.risk": fact})

    assert result.outcome == "insufficient_evidence"
    assert "requires fresh evidence" in result.reason


def test_warning_threshold_warns_without_hard_block():
    rule = PolicyRule(
        rule_id="soft_volume",
        kind="threshold_rule",
        effect="warn",
        description="Prefer stronger volume.",
        fact_key="market.volume_usd",
        operator="gte",
        expected=10000,
    )
    summary = evaluate_policy(
        [rule],
        {"market.volume_usd": PolicyFact(value=5000, evidence_status="verified")},
    )

    assert summary.blocked is False
    assert len(summary.warnings) == 1
    assert summary.results[0].outcome == "warn"


def test_approval_rule_marks_requirement_but_does_not_execute():
    rule = PolicyRule(
        rule_id="approval_for_value_move",
        kind="approval_rule",
        effect="approval",
        description="Value movement requires user approval.",
        fact_key="action.moves_value",
        operator="truthy",
    )

    summary = evaluate_policy(
        [rule],
        {"action.moves_value": PolicyFact(value=True, evidence_status="verified")},
    )

    assert summary.approval_required is True
    assert summary.results[0].outcome == "approval_required"


def test_comparison_type_error_fails_as_insufficient_evidence():
    rule = PolicyRule(
        rule_id="numeric_only",
        kind="threshold_rule",
        effect="block",
        description="Numeric comparison.",
        fact_key="value",
        operator="gte",
        expected=10,
    )

    result = evaluate_policy_rule(
        rule,
        {"value": PolicyFact(value="not-a-number", evidence_status="verified")},
    )

    assert result.outcome == "insufficient_evidence"
    assert "could not be compared" in result.reason
