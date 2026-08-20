"""Deterministic provenance reconciliation for durable-memory context."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from roberta.memory.contracts import MemoryCategory

ReconciliationLabel = Literal["superseded", "evolution", "conflict", "unknown"]


@dataclass(frozen=True, slots=True)
class ReconciliationObservation:
    """One bounded observation supplied to deterministic memory reconciliation."""

    semantic_key: str
    category: MemoryCategory
    value: str
    observed_at: str | None
    chain: str | None = None
    scope: str | None = None
    accepted_evidence: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.semantic_key, str) or not self.semantic_key.strip():
            raise ValueError("semantic_key must be a non-empty string")
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("value must be a non-empty string")


@dataclass(frozen=True, slots=True)
class MemoryReconciliation:
    """Policy-only reconciliation result; never a market-fact or execution grant."""

    label: ReconciliationLabel
    reason: str
    requires_fresh_verification: bool
    evidence_sufficient: bool
    current_truth_authorized: bool = False
    execution_authorized: bool = False


def _normalized(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped.casefold() if stripped else None


def _parse_observed_at(value: str | None) -> datetime | None:
    if value is None or not str(value).strip():
        return None
    candidate = str(value).strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _unknown(reason: str) -> MemoryReconciliation:
    return MemoryReconciliation(
        label="unknown",
        reason=reason,
        requires_fresh_verification=True,
        evidence_sufficient=False,
    )


def reconcile_memory_observations(
    prior: ReconciliationObservation,
    candidate: ReconciliationObservation,
) -> MemoryReconciliation:
    """Classify provenance without promoting memory into current truth."""

    if prior.semantic_key.strip().casefold() != candidate.semantic_key.strip().casefold():
        return _unknown("semantic scope differs; comparison is insufficient")
    if prior.category != candidate.category:
        return _unknown("memory categories differ; comparison is insufficient")
    if _normalized(prior.chain) != _normalized(candidate.chain):
        return _unknown("chain scope differs or is missing; keep evidence isolated")
    if _normalized(prior.scope) != _normalized(candidate.scope):
        return _unknown("evidence scope differs or is missing; comparison is insufficient")
    if not candidate.accepted_evidence:
        return _unknown("candidate observation is not accepted evidence; request fresh verification")

    prior_time = _parse_observed_at(prior.observed_at)
    candidate_time = _parse_observed_at(candidate.observed_at)
    if prior_time is None or candidate_time is None:
        return _unknown("comparable accepted timestamps are required for deterministic reconciliation")
    if candidate_time < prior_time:
        return _unknown("candidate observation predates remembered context; ordering is unresolved")

    same_value = prior.value.strip() == candidate.value.strip()
    if candidate_time == prior_time:
        if not same_value:
            return MemoryReconciliation(
                label="conflict",
                reason="materially comparable observations disagree at the same observation time",
                requires_fresh_verification=True,
                evidence_sufficient=True,
            )
        return MemoryReconciliation(
            label="superseded",
            reason="accepted evidence confirms the same observation and supersedes historical context as the usable evidence source",
            requires_fresh_verification=False,
            evidence_sufficient=True,
        )
    if same_value:
        return MemoryReconciliation(
            label="superseded",
            reason="newer accepted evidence confirms the same value and supersedes older historical context",
            requires_fresh_verification=False,
            evidence_sufficient=True,
        )
    return MemoryReconciliation(
        label="evolution",
        reason="newer accepted evidence differs from older context at a later observation time; both observations may be historically valid",
        requires_fresh_verification=False,
        evidence_sufficient=True,
    )
