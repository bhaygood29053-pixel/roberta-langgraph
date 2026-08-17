"""Compile explicit durable-memory policy documents into typed rules."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from roberta.memory.contracts import MemoryRecord
from roberta.policy.contracts import (
    PolicyCompilation,
    PolicyCompileIssue,
    PolicyRule,
)

POLICY_DOCUMENT_VERSION = 1
_POLICY_MEMORY_CATEGORIES = frozenset(
    {"user_risk_policy", "stable_preference", "approval_rule"}
)
_ALLOWED_KINDS_BY_CATEGORY: dict[str, frozenset[str]] = {
    "user_risk_policy": frozenset(
        {"hard_constraint", "threshold_rule", "evidence_requirement"}
    ),
    "stable_preference": frozenset({"preference"}),
    "approval_rule": frozenset({"approval_rule"}),
}


def _default_effect(kind: str) -> str:
    return {
        "hard_constraint": "block",
        "preference": "preference",
        "evidence_requirement": "evidence",
        "approval_rule": "approval",
    }.get(kind, "")


def _parse_policy_document(record: MemoryRecord) -> Mapping[str, Any]:
    try:
        parsed = json.loads(record.content)
    except json.JSONDecodeError as exc:
        raise ValueError("policy memory content must be valid JSON") from exc
    if not isinstance(parsed, Mapping):
        raise ValueError("policy memory content must be a JSON object")
    if parsed.get("policy_version") != POLICY_DOCUMENT_VERSION:
        raise ValueError(
            f"policy_version must equal {POLICY_DOCUMENT_VERSION}"
        )
    return parsed


def _compile_record(record: MemoryRecord) -> PolicyRule:
    if record.authority != "durable":
        raise ValueError("policy memory must have durable authority")
    if record.category not in _POLICY_MEMORY_CATEGORIES:
        raise ValueError(
            f"memory category {record.category!r} is not a deterministic policy category"
        )

    document = _parse_policy_document(record)
    kind = document.get("kind")
    if kind not in _ALLOWED_KINDS_BY_CATEGORY[record.category]:
        raise ValueError(
            f"policy kind {kind!r} is not valid for memory category {record.category!r}"
        )

    effect = document.get("effect") or _default_effect(str(kind))
    if kind == "threshold_rule" and not effect:
        raise ValueError("threshold_rule requires explicit effect 'block' or 'warn'")

    return PolicyRule(
        rule_id=document.get("rule_id"),
        kind=kind,
        effect=effect,
        description=document.get("description"),
        fact_key=document.get("fact_key"),
        operator=document.get("operator", "present"),
        expected=document.get("expected"),
        requires_fresh=document.get("requires_fresh", False),
        source_memory_key=record.key,
    )


def compile_policy_memories(records: Iterable[MemoryRecord]) -> PolicyCompilation:
    """Compile only explicit, durable structured policy documents.

    Free-form memory is never converted into an enforceable rule. Invalid records
    are returned as issues while valid independent records continue compiling.
    Duplicate rule ids fail closed for every duplicate after the first.
    """

    rules: list[PolicyRule] = []
    issues: list[PolicyCompileIssue] = []
    seen_rule_ids: set[str] = set()

    for record in records:
        if record.category not in _POLICY_MEMORY_CATEGORIES:
            continue
        try:
            rule = _compile_record(record)
            if rule.rule_id in seen_rule_ids:
                raise ValueError(f"duplicate rule_id: {rule.rule_id!r}")
        except (TypeError, ValueError) as exc:
            issues.append(PolicyCompileIssue(memory_key=record.key, reason=str(exc)))
            continue
        seen_rule_ids.add(rule.rule_id)
        rules.append(rule)

    return PolicyCompilation(rules=tuple(rules), issues=tuple(issues))
