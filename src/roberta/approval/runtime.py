"""Runtime helpers for starting and resuming Roberta approval threads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from langgraph.types import Command

from roberta.approval.contracts import (
    ApprovalDecision,
    ApprovalOutcome,
    ApprovalRequest,
)
from roberta.runtime import build_thread_config


_AUTHENTICATED_APPROVAL_ISSUER = object()


@dataclass(frozen=True, slots=True)
class AuthenticatedApprovalContext:
    """Application-authenticated context for one completed human review.

    The human principal is supplied as trusted application/session metadata to
    ``resume_approval_authenticated``. It is deliberately not accepted inside
    the LangGraph resume payload and therefore cannot be supplied by candidate
    text, source text, model output, or an arbitrary approval decision field.
    """

    authority: str
    thread_id: str
    human_principal_id: str
    request: ApprovalRequest
    outcome: ApprovalOutcome
    _issuer: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._issuer is not _AUTHENTICATED_APPROVAL_ISSUER:
            raise ValueError(
                "AuthenticatedApprovalContext must originate from approval runtime"
            )
        if self.authority != "human_review/v1":
            raise ValueError("unsupported authenticated approval authority")
        for name, value in (
            ("thread_id", self.thread_id),
            ("human_principal_id", self.human_principal_id),
        ):
            if not isinstance(value, str) or not value or value != value.strip():
                raise ValueError(f"{name} must be a normalized non-empty string")
        if not isinstance(self.request, ApprovalRequest):
            raise TypeError("authenticated approval request must be ApprovalRequest")
        if not isinstance(self.outcome, ApprovalOutcome):
            raise TypeError("authenticated approval outcome must be ApprovalOutcome")
        if self.outcome.request_id != self.request.request_id:
            raise ValueError("authenticated approval request/outcome identity mismatch")
        if self.outcome.original_proposal_sha256 != self.request.proposal_sha256:
            raise ValueError("authenticated approval proposal identity mismatch")
        if self.outcome.approval_binding_sha256 != self.request.binding_sha256:
            raise ValueError("authenticated approval binding identity mismatch")
        if self.outcome.scope != self.request.scope:
            raise ValueError("authenticated approval scope mismatch")


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


def resume_approval_authenticated(
    graph: Any,
    decision: Mapping[str, Any],
    *,
    thread_id: str,
    human_principal_id: str,
) -> tuple[Mapping[str, Any], AuthenticatedApprovalContext]:
    """Resume human review and bind trusted application principal metadata.

    ``human_principal_id`` is an application/session-layer input, not part of the
    resume decision mapping. Deployments are responsible for passing only an
    already-authenticated principal from their trusted session boundary.
    """

    if (
        not isinstance(human_principal_id, str)
        or not human_principal_id
        or human_principal_id != human_principal_id.strip()
    ):
        raise ValueError("human_principal_id must be a normalized non-empty string")

    request = _paused_request(graph, thread_id=thread_id)
    result = resume_approval(graph, decision, thread_id=thread_id)
    request_payload = result.get("request")
    outcome_payload = result.get("outcome")
    if not isinstance(request_payload, Mapping):
        raise ValueError("completed approval state is missing exact request")
    if not isinstance(outcome_payload, Mapping):
        raise ValueError("completed approval state is missing validated outcome")

    completed_request = ApprovalRequest.from_state_payload(request_payload)
    if completed_request != request:
        raise ValueError("completed approval request changed across resume")
    outcome = ApprovalOutcome(
        status=outcome_payload.get("status"),
        request_id=outcome_payload.get("request_id"),
        original_proposal_sha256=outcome_payload.get("original_proposal_sha256"),
        approval_binding_sha256=outcome_payload.get("approval_binding_sha256"),
        reviewed_proposal=outcome_payload.get("reviewed_proposal") or {},
        reviewed_proposal_sha256=outcome_payload.get("reviewed_proposal_sha256"),
        scope=tuple(outcome_payload.get("scope") or ()),
        feedback=outcome_payload.get("feedback"),
    )
    context = AuthenticatedApprovalContext(
        authority="human_review/v1",
        thread_id=thread_id,
        human_principal_id=human_principal_id,
        request=completed_request,
        outcome=outcome,
        _issuer=_AUTHENTICATED_APPROVAL_ISSUER,
    )
    return result, context
