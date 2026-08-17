"""Runtime helpers for starting and resuming Roberta approval threads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from langgraph.types import Command

from roberta.approval.contracts import ApprovalRequest
from roberta.runtime import build_thread_config


def start_approval(
    graph: Any,
    request: ApprovalRequest,
    *,
    thread_id: str,
) -> Mapping[str, Any]:
    """Start one checkpointed approval request and run until interrupt."""

    result = graph.invoke(
        {"request": request.to_state_payload(), "status": "pending"},
        config=build_thread_config(thread_id),
    )
    if not isinstance(result, Mapping):
        raise TypeError("approval graph must return a mapping")
    return result


def resume_approval(
    graph: Any,
    decision: Mapping[str, Any],
    *,
    thread_id: str,
) -> Mapping[str, Any]:
    """Resume exactly one paused approval thread with explicit decision data."""

    if not isinstance(decision, Mapping):
        raise TypeError("approval decision must be a mapping")
    result = graph.invoke(
        Command(resume=dict(decision)),
        config=build_thread_config(thread_id),
    )
    if not isinstance(result, Mapping):
        raise TypeError("approval graph must return a mapping")
    return result
