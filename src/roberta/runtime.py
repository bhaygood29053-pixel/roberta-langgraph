"""Runtime helpers for explicit LangGraph thread invocation."""

from collections.abc import Mapping
from typing import Any


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
