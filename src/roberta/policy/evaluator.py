"""Deterministic Oracle policy evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from roberta.policy.contracts import (
    PolicyEvaluation,
    PolicyEvaluationSummary,
    PolicyFact,
    PolicyRule,
)


def _comparison(operator: str, observed: Any, expected: Any) -> bool:
    if operator == "present":
        return observed is not None
    if operator == "truthy":
        return bool(observed)
    if operator == "falsy":
        return not bool(observed)
    if operator == "eq":
        return observed == expected
    if operator == "ne":
        return observed != expected
    if operator == "lt":
        return observed < expected
    if operator == "lte":
        return observed <= expected
    if operator == "gt":
        return observed > expected
    if operator == "gte":
        return observed >= expected
    if operator == "in":
        return observed in expected
    if operator == "not_in":
        return observed not in expected
    raise ValueError(f"unsupported policy operator: {operator!r}")


def _insufficient(rule: PolicyRule, fact: PolicyFact | None, reason: str) -> PolicyEvaluation:
    return PolicyEvaluation(
        rule_id=rule.rule_id,
        kind=rule.kind,
        outcome="insufficient_evidence",
        description=rule.description,
        fact_key=rule.fact_key,
        observed=None if fact is None else fact.value,
        expected=rule.expected,
        source=None if fact is None else fact.source,
        source_memory_key=rule.source_memory_key,
        reason=reason,
    )


def evaluate_policy_rule(
    rule: PolicyRule,
    facts: Mapping[str, PolicyFact],
) -> PolicyEvaluation:
    """Evaluate one rule without LLM inference or live-data lookup."""

    fact = facts.get(rule.fact_key)
    if fact is None:
        return _insufficient(rule, None, "required fact is missing")
    if not isinstance(fact, PolicyFact):
        raise TypeError("policy facts must contain PolicyFact values")
    if fact.evidence_status != "verified":
        return _insufficient(
            rule,
            fact,
            f"fact evidence status is {fact.evidence_status!r}, not verified",
        )
    if rule.requires_fresh and fact.freshness != "fresh":
        return _insufficient(
            rule,
            fact,
            f"rule requires fresh evidence but fact freshness is {fact.freshness!r}",
        )

    if rule.kind == "evidence_requirement":
        return PolicyEvaluation(
            rule_id=rule.rule_id,
            kind=rule.kind,
            outcome="pass",
            description=rule.description,
            fact_key=rule.fact_key,
            observed=fact.value,
            expected=rule.expected,
            source=fact.source,
            source_memory_key=rule.source_memory_key,
            reason="required verified evidence is available",
        )

    try:
        matched = _comparison(rule.operator, fact.value, rule.expected)
    except (TypeError, ValueError) as exc:
        return _insufficient(
            rule,
            fact,
            f"fact could not be compared under the declared rule: {exc}",
        )

    if rule.effect == "block":
        outcome = "pass" if matched else "block"
        reason = "hard/threshold constraint satisfied" if matched else "hard/threshold constraint violated"
    elif rule.effect == "warn":
        outcome = "pass" if matched else "warn"
        reason = "warning threshold satisfied" if matched else "warning threshold exceeded or missed"
    elif rule.effect == "preference":
        outcome = "preference_met" if matched else "preference_missed"
        reason = "soft preference matched" if matched else "soft preference not matched"
    elif rule.effect == "approval":
        outcome = "approval_required" if matched else "pass"
        reason = "declared approval condition matched" if matched else "declared approval condition did not match"
    else:
        raise ValueError(f"unsupported evaluable policy effect: {rule.effect!r}")

    return PolicyEvaluation(
        rule_id=rule.rule_id,
        kind=rule.kind,
        outcome=outcome,
        description=rule.description,
        fact_key=rule.fact_key,
        observed=fact.value,
        expected=rule.expected,
        source=fact.source,
        source_memory_key=rule.source_memory_key,
        reason=reason,
    )


def evaluate_policy(
    rules: Sequence[PolicyRule],
    facts: Mapping[str, PolicyFact],
) -> PolicyEvaluationSummary:
    """Evaluate rules independently and preserve every rule-level result."""

    return PolicyEvaluationSummary(
        results=tuple(evaluate_policy_rule(rule, facts) for rule in rules)
    )
