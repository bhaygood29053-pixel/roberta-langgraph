"""Provider-neutral durable-memory contracts for Roberta."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

MemoryAuthority = Literal["durable", "historical_context"]
MemoryCategory = Literal[
    "identity_role",
    "user_risk_policy",
    "stable_preference",
    "service_definition",
    "specialist_capability",
    "approval_rule",
    "long_term_goal",
    "decision",
    "market_snapshot",
    "wallet_snapshot",
    "risk_snapshot",
    "tokenomics_snapshot",
]

DURABLE_MEMORY_CATEGORIES = frozenset(
    {
        "identity_role",
        "user_risk_policy",
        "stable_preference",
        "service_definition",
        "specialist_capability",
        "approval_rule",
        "long_term_goal",
        "decision",
    }
)
FRESHNESS_SENSITIVE_CATEGORIES = frozenset(
    {
        "market_snapshot",
        "wallet_snapshot",
        "risk_snapshot",
        "tokenomics_snapshot",
    }
)


@dataclass(frozen=True, slots=True)
class MemoryCandidate:
    """A proposed durable-memory write before deterministic policy approval."""

    key: str
    category: MemoryCategory
    content: str
    topics: tuple[str, ...] = ()
    source: str = "runtime"
    rationale: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("memory key must be a non-empty string")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("memory content must be a non-empty string")


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """Stored memory with explicit authority and provenance."""

    key: str
    category: MemoryCategory
    content: str
    topics: tuple[str, ...] = ()
    source: str = "runtime"
    rationale: str | None = None
    authority: MemoryAuthority = "durable"
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("memory key must be a non-empty string")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("memory content must be a non-empty string")
        if self.authority not in {"durable", "historical_context"}:
            raise ValueError(f"unsupported memory authority: {self.authority!r}")


@runtime_checkable
class DurableMemoryStore(Protocol):
    """Minimal provider-neutral contract expected from HXMP/HMPX adapters."""

    def get(self, key: str) -> MemoryRecord | None:
        """Return one exact record by stable key when present."""

    def upsert(self, record: MemoryRecord) -> None:
        """Create or replace one exact record by stable key."""

    def search(self, query: str, *, limit: int = 12) -> list[MemoryRecord]:
        """Return candidate records for deterministic relevance filtering."""
