"""Deterministic durable-memory write policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from roberta.memory.contracts import (
    DURABLE_MEMORY_CATEGORIES,
    FRESHNESS_SENSITIVE_CATEGORIES,
    DurableMemoryStore,
    MemoryAuthority,
    MemoryCandidate,
    MemoryRecord,
)


@dataclass(frozen=True, slots=True)
class MemoryWriteDecision:
    """Deterministic policy result for one proposed permanent-memory write."""

    allowed: bool
    authority: MemoryAuthority | None
    reason: str


@dataclass(frozen=True, slots=True)
class MemoryWriteResult:
    """Result of applying write policy and, when allowed, mutating the store."""

    accepted: bool
    reason: str
    record: MemoryRecord | None = None


def classify_memory_candidate(candidate: MemoryCandidate) -> MemoryWriteDecision:
    """Classify a memory proposal without using an LLM or live-data inference."""

    if candidate.category in DURABLE_MEMORY_CATEGORIES:
        return MemoryWriteDecision(
            allowed=True,
            authority="durable",
            reason="stable category is eligible for durable memory",
        )
    if candidate.category in FRESHNESS_SENSITIVE_CATEGORIES:
        return MemoryWriteDecision(
            allowed=False,
            authority=None,
            reason=(
                "freshness-sensitive live-data snapshots are not eligible for "
                "permanent-memory truth; request fresh specialist/CMIS evidence instead"
            ),
        )
    return MemoryWriteDecision(
        allowed=False,
        authority=None,
        reason=f"unsupported memory category: {candidate.category!r}",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def remember(
    store: DurableMemoryStore,
    candidate: MemoryCandidate,
    *,
    observed_at: str | None = None,
) -> MemoryWriteResult:
    """Apply deterministic policy before writing one durable memory record."""

    decision = classify_memory_candidate(candidate)
    if not decision.allowed or decision.authority is None:
        return MemoryWriteResult(accepted=False, reason=decision.reason)

    timestamp = observed_at or _utc_now()
    existing = store.get(candidate.key)
    created_at = existing.created_at if existing is not None else timestamp
    record = MemoryRecord(
        key=candidate.key,
        category=candidate.category,
        content=candidate.content,
        topics=tuple(candidate.topics),
        source=candidate.source,
        rationale=candidate.rationale,
        authority=decision.authority,
        created_at=created_at,
        updated_at=timestamp,
    )
    store.upsert(record)
    return MemoryWriteResult(
        accepted=True,
        reason=decision.reason,
        record=record,
    )
