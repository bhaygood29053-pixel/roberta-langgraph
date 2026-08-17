"""Tests that approval proposal identity cannot mutate after hashing."""

import pytest

from roberta.approval import ApprovalDecision, ApprovalRequest, resolve_approval_decision


def _request():
    source = {
        "operation": "review",
        "nested": {"amount": "1"},
        "routes": [{"venue": "a"}],
    }
    return source, ApprovalRequest(
        request_id="immutable-request",
        action_type="review_only",
        summary="Review exact immutable proposal.",
        scope=("this_exact_proposal",),
        proposal=source,
        policy_reasons=("Approval is required.",),
    )


def test_mutating_original_source_after_request_creation_cannot_change_request():
    source, request = _request()
    original_hash = request.proposal_sha256

    source["nested"]["amount"] = "999"
    source["routes"].append({"venue": "b"})

    assert request.proposal["nested"]["amount"] == "1"
    assert len(request.proposal["routes"]) == 1
    assert request.proposal_sha256 == original_hash


def test_request_proposal_mapping_and_nested_mapping_are_immutable():
    _, request = _request()

    with pytest.raises(TypeError):
        request.proposal["operation"] = "changed"
    with pytest.raises(TypeError):
        request.proposal["nested"]["amount"] = "changed"


def test_interrupt_payload_is_a_detached_mutable_copy_not_internal_state():
    _, request = _request()
    payload = request.to_interrupt_payload()
    original_hash = request.proposal_sha256

    payload["proposal"]["nested"]["amount"] = "777"

    assert request.proposal["nested"]["amount"] == "1"
    assert request.proposal_sha256 == original_hash


def test_approved_outcome_keeps_same_immutable_exact_proposal_hash():
    _, request = _request()
    decision = ApprovalDecision.from_resume(
        {
            "request_id": request.request_id,
            "proposal_sha256": request.proposal_sha256,
            "decision": "approve",
        },
        request=request,
    )
    outcome = resolve_approval_decision(request, decision)

    assert outcome.reviewed_proposal_sha256 == request.proposal_sha256
    with pytest.raises(TypeError):
        outcome.reviewed_proposal["nested"]["amount"] = "changed"
