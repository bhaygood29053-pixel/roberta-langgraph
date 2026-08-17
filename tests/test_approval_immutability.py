"""Tests that approval proposal identity cannot mutate after hashing."""

import pytest

from roberta.approval import (
    ApprovalDecision,
    ApprovalRequest,
    build_approval_resume_payload,
    resolve_approval_decision,
)


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
    original_binding = request.binding_sha256

    source["nested"]["amount"] = "999"
    source["routes"].append({"venue": "b"})

    assert request.proposal["nested"]["amount"] == "1"
    assert len(request.proposal["routes"]) == 1
    assert request.proposal_sha256 == original_hash
    assert request.binding_sha256 == original_binding


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
    original_binding = request.binding_sha256

    payload["proposal"]["nested"]["amount"] = "777"
    payload["scope"].append("broader_scope")

    assert request.proposal["nested"]["amount"] == "1"
    assert request.scope == ("this_exact_proposal",)
    assert request.proposal_sha256 == original_hash
    assert request.binding_sha256 == original_binding


def test_approved_outcome_keeps_same_immutable_exact_proposal_and_binding():
    _, request = _request()
    decision = ApprovalDecision.from_resume(
        build_approval_resume_payload(request, "approve"),
        request=request,
    )
    outcome = resolve_approval_decision(request, decision)

    assert outcome.reviewed_proposal_sha256 == request.proposal_sha256
    assert outcome.approval_binding_sha256 == request.binding_sha256
    with pytest.raises(TypeError):
        outcome.reviewed_proposal["nested"]["amount"] = "changed"


def test_changing_scope_changes_binding_even_when_proposal_hash_is_identical():
    _, request = _request()
    broader = ApprovalRequest(
        request_id=request.request_id,
        action_type=request.action_type,
        summary=request.summary,
        scope=("this_exact_proposal", "additional_scope"),
        proposal=request.to_state_payload()["proposal"],
        policy_reasons=request.policy_reasons,
    )

    assert broader.proposal_sha256 == request.proposal_sha256
    assert broader.binding_sha256 != request.binding_sha256
