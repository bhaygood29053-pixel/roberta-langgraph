"""Runtime helpers for explicit thread invocation and durable-memory writes."""

from collections.abc import Mapping
from typing import Any

from roberta.memory import (
    DurableMemoryStore,
    MemoryCandidate,
    MemoryWriteResult,
    remember,
)


def build_thread_config(thread_id: str) -> dict[str, dict[str, str]]:
    """Return the LangGraph config for one validated conversation thread."""
    if not isinstance(thread_id, str):
        raise TypeError("thread_id must be a string")
    if not thread_id.strip():
        raise ValueError("thread_id must not be empty")
    return {"configurable": {"thread_id": thread_id}}


def invoke_thread(
    graph: Any,
    inputs: Mapping[str, Any],
    *,
    thread_id: str,
) -> dict[str, Any]:
    """Invoke a persistence-enabled Roberta graph on one explicit thread."""
    result = graph.invoke(dict(inputs), config=build_thread_config(thread_id))
    if not isinstance(result, dict):
        raise TypeError("Roberta graph must return a state mapping")
    return result


def write_durable_memory(
    memory_store: DurableMemoryStore,
    candidate: MemoryCandidate,
    *,
    observed_at: str | None = None,
) -> MemoryWriteResult:
    """Apply Roberta's deterministic permanent-memory policy before writing."""

    return remember(memory_store, candidate, observed_at=observed_at)
