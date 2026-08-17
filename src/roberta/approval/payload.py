"""Canonical construction of explicit approval resume payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from roberta.approval.contracts import ApprovalDecisionType, ApprovalRequest


def build_approval_resume_payload(
    request: ApprovalRequest,
    decision: ApprovalDecisionType,
    *,
    feedback: str | None = None,
    edited_proposal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an explicit resume mapping bound to the exact paused request.

    The caller still chooses the decision. This helper only copies stable request,
    proposal, and scope-binding identifiers so UI/runtime layers do not re-create
    them inconsistently.
    """

    payload: dict[str, Any] = {
        "request_id": request.request_id,
        "proposal_sha256": request.proposal_sha256,
        "binding_sha256": request.binding_sha256,
        "decision": decision,
    }
    if feedback is not None:
        payload["feedback"] = feedback
    if edited_proposal is not None:
        payload["edited_proposal"] = dict(edited_proposal)
    return payload
