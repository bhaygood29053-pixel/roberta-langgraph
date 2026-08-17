"""Isolated LangGraph human-approval subgraph for Phase 9."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from roberta.approval.contracts import (
    ApprovalDecision,
    ApprovalRequest,
    resolve_approval_decision,
)
from roberta.approval.routing import ApprovalNextStep, approval_next_step

ApprovalGraphStatus = Literal[
    "pending",
    "approved",
    "rejected",
    "edited",
    "more_evidence",
]


class ApprovalState(TypedDict, total=False):
    """Checkpointed approval state; values remain JSON-serializable."""

    request: dict[str, Any]
    outcome: dict[str, Any]
    status: ApprovalGraphStatus
    next_step: ApprovalNextStep


def approval_node(state: ApprovalState) -> dict[str, Any]:
    """Pause for explicit review and return a validated, non-executing outcome.

    LangGraph re-executes this node from the beginning after resume. Everything
    before ``interrupt`` is therefore deterministic validation/serialization only;
    there are no writes, signing operations, broadcasts, or other side effects.
    """

    if "request" not in state:
        raise ValueError("approval graph requires request state")
    request = ApprovalRequest.from_state_payload(state["request"])
    resume_value = interrupt(request.to_interrupt_payload())
    decision = ApprovalDecision.from_resume(resume_value, request=request)
    outcome = resolve_approval_decision(request, decision)
    payload = outcome.to_state_payload()
    return {
        "outcome": payload,
        "status": outcome.status,
        "next_step": approval_next_step(payload),
    }


def build_approval_graph(*, checkpointer: Any):
    """Compile the resumable approval subgraph with an injected checkpointer."""

    if checkpointer is None:
        raise ValueError("approval graph requires a checkpointer for interrupt/resume")
    builder = StateGraph(ApprovalState)
    builder.add_node("approval", approval_node)
    builder.add_edge(START, "approval")
    builder.add_edge("approval", END)
    return builder.compile(checkpointer=checkpointer)
