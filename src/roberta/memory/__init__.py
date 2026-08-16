"""Roberta durable-memory contracts, policy, retrieval, and test adapter."""

from roberta.memory.context import (
    build_memory_system_message,
    format_memory_context,
    latest_user_query,
)
from roberta.memory.contracts import (
    DURABLE_MEMORY_CATEGORIES,
    FRESHNESS_SENSITIVE_CATEGORIES,
    DurableMemoryStore,
    MemoryAuthority,
    MemoryCandidate,
    MemoryCategory,
    MemoryRecord,
)
from roberta.memory.in_memory import InMemoryDurableMemoryStore
from roberta.memory.policy import (
    MemoryWriteDecision,
    MemoryWriteResult,
    classify_memory_candidate,
    remember,
)
from roberta.memory.retrieval import (
    memory_relevance_score,
    retrieve_relevant_memory,
    select_relevant_memory,
)

__all__ = [
    "DURABLE_MEMORY_CATEGORIES",
    "FRESHNESS_SENSITIVE_CATEGORIES",
    "DurableMemoryStore",
    "InMemoryDurableMemoryStore",
    "MemoryAuthority",
    "MemoryCandidate",
    "MemoryCategory",
    "MemoryRecord",
    "MemoryWriteDecision",
    "MemoryWriteResult",
    "build_memory_system_message",
    "classify_memory_candidate",
    "format_memory_context",
    "latest_user_query",
    "memory_relevance_score",
    "remember",
    "retrieve_relevant_memory",
    "select_relevant_memory",
]
