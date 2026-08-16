"""Roberta durable-memory contracts, policy, retrieval, and adapters."""

from roberta.memory.context import (
    build_memory_system_message,
    format_memory_context,
    latest_user_query,
)
from roberta.memory.contracts import (
    ALL_MEMORY_CATEGORIES,
    DURABLE_MEMORY_CATEGORIES,
    FRESHNESS_SENSITIVE_CATEGORIES,
    DurableMemoryStore,
    MemoryAuthority,
    MemoryCandidate,
    MemoryCategory,
    MemoryRecord,
)
from roberta.memory.hxmp import (
    DEFAULT_HXMP_MEMORY_LANE,
    HXMPApprovalRequiredError,
    HXMPCommandRunner,
    HXMPMemoryConfig,
    HXMPMemoryError,
    HXMPMemoryStore,
    HXMPPreparedWrite,
    HXMPVerificationError,
    HXMPWriteCommit,
    HXMPWriteRefusedError,
    HXMP_MEMORY_SCHEMA,
    HXMP_MEMORY_VERSION,
    SubprocessHXMPCommandRunner,
    deserialize_memory_records,
    serialize_memory_records,
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
    "ALL_MEMORY_CATEGORIES",
    "DEFAULT_HXMP_MEMORY_LANE",
    "DURABLE_MEMORY_CATEGORIES",
    "FRESHNESS_SENSITIVE_CATEGORIES",
    "DurableMemoryStore",
    "HXMPApprovalRequiredError",
    "HXMPCommandRunner",
    "HXMPMemoryConfig",
    "HXMPMemoryError",
    "HXMPMemoryStore",
    "HXMPPreparedWrite",
    "HXMPVerificationError",
    "HXMPWriteCommit",
    "HXMPWriteRefusedError",
    "HXMP_MEMORY_SCHEMA",
    "HXMP_MEMORY_VERSION",
    "InMemoryDurableMemoryStore",
    "MemoryAuthority",
    "MemoryCandidate",
    "MemoryCategory",
    "MemoryRecord",
    "MemoryWriteDecision",
    "MemoryWriteResult",
    "SubprocessHXMPCommandRunner",
    "build_memory_system_message",
    "classify_memory_candidate",
    "deserialize_memory_records",
    "format_memory_context",
    "latest_user_query",
    "memory_relevance_score",
    "remember",
    "retrieve_relevant_memory",
    "select_relevant_memory",
    "serialize_memory_records",
]
