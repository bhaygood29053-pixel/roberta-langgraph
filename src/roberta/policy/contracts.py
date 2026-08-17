"""Typed, provider-neutral Oracle policy contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

PolicyKind = Literal[
    "hard_constraint",
    "preference",
    "threshold_rule",
    "evidence_requirement",
    "approval_rule",
]
PolicyEffect = Literal["block", "warn", "preference", "evidence", "approval"]
PolicyOperator = Literal[
    "eq",
    "ne",
    "lt",
    "lte",
    "gt",
    "gte",
    "in",
    "not_in",
    "truthy",
    "falsy",
    "present",
]
PolicyOutcome = Literal[
    "pass",
    "block",
    "warn",
    "preference_met",
    "preference_missed",
    "insufficient_evidence",
    "approval_required",
]
EvidenceStatus = Literal[
    "verified",
    "unverified",
    "conflict",
    "insufficient_evidence",
]
FreshnessStatus = Literal["fresh", "historical", "unknown"]

POLICY_KINDS = frozenset(
    {
        "hard_constraint",
        "preference",
        "threshold_rule",
        "evidence_requirement",
        "approval_rule",
    }
)
POLICY_EFFECTS = frozenset({"block", "warn", "preference", "evidence", "approval"})
POLICY_OPERATORS = frozenset(
    {"eq", "ne", "lt", "lte", "gt", "gte", "in", "not_in", "truthy", "falsy", "present"}
)

_KIND_EFFECTS: dict[str, frozenset[str]] = {
    "hard_constraint": frozenset({"block"}),
    "preference": frozenset({"preference"}),
    "threshold_rule": frozenset({"block", "warn"}),
    "evidence_requirement": frozenset({"evidence"}),
    "approval_rule": frozenset({"approval"}),
}


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """One deterministic Oracle rule compiled from durable user policy."""

    rule_id: str
    kind: PolicyKind
    effect: PolicyEffect
    description: str
    fact_key: str
    operator: PolicyOperator = "present"
    expected: Any = None
    requires_fresh: bool = False
    source_memory_key: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be a non-empty string")
        if self.kind not in POLICY_KINDS:
            raise ValueError(f"unsupported policy kind: {self.kind!r}")
        if self.effect not in POLICY_EFFECTS:
            raise ValueError(f"unsupported policy effect: {self.effect!r}")
        if self.effect not in _KIND_EFFECTS[self.kind]:
            raise ValueError(
                f"policy effect {self.effect!r} is not valid for kind {self.kind!r}"
            )
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description must be a non-empty string")
        if not isinstance(self.fact_key, str) or not self.fact_key.strip():
            raise ValueError("fact_key must be a non-empty string")
        if self.operator not in POLICY_OPERATORS:
            raise ValueError(f"unsupported policy operator: {self.operator!r}")
        if self.operator not in {"truthy", "falsy", "present"} and self.expected is None:
            raise ValueError(f"operator {self.operator!r} requires an expected value")
        if not isinstance(self.requires_fresh, bool):
            raise TypeError("requires_fresh must be bool")


@dataclass(frozen=True, slots=True)
class PolicyFact:
    """A fact supplied to policy evaluation with explicit evidence authority."""

    value: Any
    evidence_status: EvidenceStatus = "verified"
    freshness: FreshnessStatus = "unknown"
    source: str = "runtime"

    def __post_init__(self) -> None:
        if self.evidence_status not in {
            "verified",
            "unverified",
            "conflict",
            "insufficient_evidence",
        }:
            raise ValueError(f"unsupported evidence status: {self.evidence_status!r}")
        if self.freshness not in {"fresh", "historical", "unknown"}:
            raise ValueError(f"unsupported freshness status: {self.freshness!r}")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("fact source must be a non-empty string")


@dataclass(frozen=True, slots=True)
class PolicyCompileIssue:
    """One durable-memory record that could not safely become a policy rule."""

    memory_key: str
    reason: str


@dataclass(frozen=True, slots=True)
class PolicyCompilation:
    """Deterministic durable-memory to policy compilation result."""

    rules: tuple[PolicyRule, ...]
    issues: tuple[PolicyCompileIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class PolicyEvaluation:
    """Explainable result for one deterministic policy rule."""

    rule_id: str
    kind: PolicyKind
    outcome: PolicyOutcome
    description: str
    fact_key: str
    observed: Any = None
    expected: Any = None
    source: str | None = None
    source_memory_key: str | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class PolicyEvaluationSummary:
    """Aggregate policy result without replacing rule-level explanations."""

    results: tuple[PolicyEvaluation, ...]

    @property
    def blocked(self) -> bool:
        return any(result.outcome == "block" for result in self.results)

    @property
    def approval_required(self) -> bool:
        return any(result.outcome == "approval_required" for result in self.results)

    @property
    def insufficient_evidence(self) -> bool:
        return any(result.outcome == "insufficient_evidence" for result in self.results)

    @property
    def warnings(self) -> tuple[PolicyEvaluation, ...]:
        return tuple(result for result in self.results if result.outcome == "warn")
