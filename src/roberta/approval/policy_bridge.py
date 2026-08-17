"""Bridge deterministic Phase 8 approval policy into Phase 9 review requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from roberta.approval.contracts import ApprovalOutcome, ApprovalRequest
from roberta.policy import PolicyRuntimeContext


def approval_request_from_policy(
    policy: PolicyRuntimeContext,
    *,
    request_id: str,
    action_type: str,
    summary: str,
    scope: tuple[str, ...],
    proposal: Mapping[str, Any],
    evidence_summary: Sequence[str] = (),
) -> ApprovalRequest:
    """Build an exact review request only when deterministic policy requires it.

    The proposal and scope are explicit application inputs; the LLM does not
    manufacture either from the policy result. This helper performs no interrupt,
    memory write, transaction preparation, signing, or broadcasting.
    """

    if policy.decision.status != "approval_required":
        raise ValueError(
            "approval request can only be created from approval_required policy"
        )
    policy_reasons = tuple(
        result.description for result in policy.decision.material_results
    )
    if not policy_reasons:
        raise ValueError("approval_required policy must contain material reasons")
    return ApprovalRequest(
        request_id=request_id,
        action_type=action_type,
        summary=summary,
        scope=scope,
        proposal=proposal,
        policy_reasons=policy_reasons,
        evidence_summary=tuple(evidence_summary),
    )


def rereview_request_from_edit(
    previous: ApprovalRequest,
    outcome: ApprovalOutcome,
    *,
    new_request_id: str,
    summary: str | None = None,
) -> ApprovalRequest:
    """Create a new request for an edited proposal; prior approval never carries."""

    if outcome.status != "edited":
        raise ValueError("only an edited outcome can create a re-review request")
    if outcome.request_id != previous.request_id:
        raise ValueError("edited outcome does not belong to the previous request")
    if outcome.original_proposal_sha256 != previous.proposal_sha256:
        raise ValueError("edited outcome is not bound to the previous proposal")
    if outcome.reviewed_proposal_sha256 == previous.proposal_sha256:
        raise ValueError("edited proposal must differ from the previous proposal")
    if new_request_id == previous.request_id:
        raise ValueError("edited proposal re-review requires a new request_id")

    return ApprovalRequest(
        request_id=new_request_id,
        action_type=previous.action_type,
        summary=summary or f"Re-review edited proposal from {previous.request_id}.",
        scope=previous.scope,
        proposal=outcome.reviewed_proposal,
        policy_reasons=previous.policy_reasons,
        evidence_summary=previous.evidence_summary,
    )
