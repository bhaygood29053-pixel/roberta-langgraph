"""Deterministic resolution of rule-level policy outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from roberta.policy.contracts import PolicyEvaluation, PolicyEvaluationSummary

PolicyDecisionStatus = Literal[
    "allowed",
    "blocked",
    "needs_evidence",
    "approval_required",
]


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Structural Oracle decision derived from rule outcomes, never from an LLM."""

    status: PolicyDecisionStatus
    material_results: tuple[PolicyEvaluation, ...]
    warnings: tuple[PolicyEvaluation, ...] = ()
    preferences: tuple[PolicyEvaluation, ...] = ()

    @property
    def may_proceed_without_approval(self) -> bool:
        return self.status == "allowed"


def resolve_policy_decision(summary: PolicyEvaluationSummary) -> PolicyDecision:
    """Resolve aggregate policy state using fail-closed precedence.

    Precedence is intentionally conservative:

    1. any verified hard block -> blocked
    2. otherwise any required missing/unusable evidence -> needs_evidence
    3. otherwise any matched approval rule -> approval_required
    4. otherwise -> allowed

    Warnings and preferences are preserved but can never override a stronger state.
    """

    blocks = tuple(result for result in summary.results if result.outcome == "block")
    insufficient = tuple(
        result for result in summary.results if result.outcome == "insufficient_evidence"
    )
    approvals = tuple(
        result for result in summary.results if result.outcome == "approval_required"
    )
    warnings = tuple(result for result in summary.results if result.outcome == "warn")
    preferences = tuple(
        result
        for result in summary.results
        if result.outcome in {"preference_met", "preference_missed"}
    )

    if blocks:
        return PolicyDecision(
            status="blocked",
            material_results=blocks,
            warnings=warnings,
            preferences=preferences,
        )
    if insufficient:
        return PolicyDecision(
            status="needs_evidence",
            material_results=insufficient,
            warnings=warnings,
            preferences=preferences,
        )
    if approvals:
        return PolicyDecision(
            status="approval_required",
            material_results=approvals,
            warnings=warnings,
            preferences=preferences,
        )
    return PolicyDecision(
        status="allowed",
        material_results=(),
        warnings=warnings,
        preferences=preferences,
    )
