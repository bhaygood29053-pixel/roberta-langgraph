"""Safe construction of explicit Oracle policy durable-memory candidates."""

from __future__ import annotations

import json
from dataclasses import asdict

from roberta.memory import MemoryCandidate, MemoryCategory
from roberta.policy.compiler import POLICY_DOCUMENT_VERSION
from roberta.policy.contracts import PolicyRule

_CATEGORY_BY_KIND: dict[str, MemoryCategory] = {
    "hard_constraint": "user_risk_policy",
    "threshold_rule": "user_risk_policy",
    "evidence_requirement": "user_risk_policy",
    "preference": "stable_preference",
    "approval_rule": "approval_rule",
}


def policy_rule_document(rule: PolicyRule) -> dict[str, object]:
    """Return the canonical JSON-serializable document for one typed rule."""

    return {
        "policy_version": POLICY_DOCUMENT_VERSION,
        "rule_id": rule.rule_id,
        "kind": rule.kind,
        "effect": rule.effect,
        "description": rule.description,
        "fact_key": rule.fact_key,
        "operator": rule.operator,
        "expected": rule.expected,
        "requires_fresh": rule.requires_fresh,
    }


def build_policy_memory_candidate(
    rule: PolicyRule,
    *,
    key: str | None = None,
    source: str = "oracle_policy",
    rationale: str | None = None,
) -> MemoryCandidate:
    """Build but do not write one durable policy memory candidate.

    HXMP execution remains separately approval-gated. This helper has no store,
    wallet, keypair, network, signing, or broadcast behavior.
    """

    category = _CATEGORY_BY_KIND[rule.kind]
    stable_key = key or f"policy:{rule.rule_id}"
    document = policy_rule_document(rule)
    return MemoryCandidate(
        key=stable_key,
        category=category,
        content=json.dumps(document, ensure_ascii=False, sort_keys=True),
        topics=("oracle_policy", f"fact:{rule.fact_key}", f"kind:{rule.kind}"),
        source=source,
        rationale=rationale or rule.description,
    )
