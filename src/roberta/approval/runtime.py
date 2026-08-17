"""Runtime helpers for starting and resuming Roberta approval threads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from langgraph.types import Command

from roberta.approval.contracts import ApprovalDecision, ApprovalRequest
from roberta.runtime import build_thread_config


def _snapshot_values(graph: Any, *, thread_id: str) -> Mapping[str, Any]:
    snapshot = graph.get_state(build_thread_config(thread_id))
    values = getattr(snapshot, "values", None)
    return values if isinstance(values, Mapping) else {}


def start_approval(
    graph: Any,
    request: ApprovalRequest,
    *,
    thread_id: str,
) -> Mapping[str, Any]:
    """Start one checkpointed approval request and run until interrupt.

    An approval thread is single-request context. Existing approval state cannot
    be overwritten/reused for a new proposal; callers must allocate a new thread.
    """

    existing = _snapshot_values(graph, thread_id=thread_id)
    if existing.get("request") is not None or existing.get("status") is not None:
        raise ValueError("approval thread already contains review state; use a new thread_id")

    result = graph.invoke(
        {"request": request.to_state_payload(), "status": "pending"},
        config=build_thread_config(thread_id),
    )
    if not isinstance(result, Mapping):
        raise TypeError("approval graph must return a mapping")
    return result


def _paused_request(graph: Any, *, thread_id: str) -> ApprovalRequest:
    """Read/validate the exact paused request before a resume enters LangGraph."""

    config = build_thread_config(thread_id)
    snapshot = graph.get_state(config)
    values = getattr(snapshot, "values", None)
    if not isinstance(values, Mapping) or values.get("status") != "pending":
        raise ValueError("approval thread is not awaiting a pending review")
    request_payload = values.get("request")
    if not isinstance(request_payload, Mapping):
        raise ValueError("pending approval thread is missing request state")
    interrupts = getattr(snapshot, "interrupts", None)
    if interrupts is not None and not interrupts:
        raise ValueError("approval thread is not paused at an interrupt")
    return ApprovalRequest.from_state_payload(request_payload)


def resume_approval(
    graph: Any,
    decision: Mapping[str, Any],
    *,
    thread_id: str,
) -> Mapping[str, Any]:
    """Resume one paused approval only after pre-validating exact checkpoint state.

    LangGraph associates a resume value with the interrupted task. A malformed or
    mismatched decision is therefore validated against the checkpoint *before*
    ``Command(resume=...)`` is sent, so invalid input cannot poison a later retry.
    """

    if not isinstance(decision, Mapping):
        raise TypeError("approval decision must be a mapping")
    request = _paused_request(graph, thread_id=thread_id)
    # Validation only. The approval node repeats this check after resume as a
    # defense-in-depth boundary against callers that bypass this runtime helper.
    ApprovalDecision.from_resume(decision, request=request)

    result = graph.invoke(
        Command(resume=dict(decision)),
        config=build_thread_config(thread_id),
    )
    if not isinstance(result, Mapping):
        raise TypeError("approval graph must return a mapping")
    return result
