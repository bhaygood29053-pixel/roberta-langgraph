"""Deterministic tests for Phase 9 human approval contracts and interrupt flow."""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from roberta.approval import (
    ApprovalDecision,
    ApprovalRequest,
    build_approval_graph,
    canonical_proposal_sha256,
    resolve_approval_decision,
    resume_approval,
    start_approval,
)


def _request(
    request_id: str = "approval-1",
    proposal: dict | None = None,
) -> ApprovalRequest:
    return ApprovalRequest(
        request_id=request_id,
        action_type="proposed_transaction",
        summary="Review a prepared, non-broadcast transaction proposal.",
        scope=("sign_this_exact_proposal", "broadcast_this_exact_proposal"),
        proposal=proposal or {
            "chain": "x1",
            "operation": "transfer",
            "asset": "TEST",
            "amount": "1",
            "destination": "public-destination",
        },
        policy_reasons=("Value movement requires explicit user approval.",),
        evidence_summary=("Proposal is prepared only; no transaction has been sent.",),
    )


def _decision(request: ApprovalRequest, decision: str, **extra):
    return {
        "request_id": request.request_id,
        "proposal_sha256": request.proposal_sha256,
        "decision": decision,
        **extra,
    }


def _interrupt_value(result):
    interrupts = result["__interrupt__"]
    assert len(interrupts) == 1
    return interrupts[0].value


def test_canonical_hash_is_stable_across_mapping_order():
    left = {"b": 2, "a": {"z": 3, "y": 4}}
    right = {"a": {"y": 4, "z": 3}, "b": 2}

    assert canonical_proposal_sha256(left) == canonical_proposal_sha256(right)


def test_secret_bearing_fields_are_refused_from_interrupt_checkpoint_payload():
    with pytest.raises(ValueError, match="secret-bearing field"):
        _request(proposal={"operation": "sign", "private_key": "do-not-store"})


def test_request_interrupt_payload_binds_id_hash_scope_and_allowed_decisions():
    request = _request()
    payload = request.to_interrupt_payload()

    assert payload["request_id"] == request.request_id
    assert payload["proposal_sha256"] == request.proposal_sha256
    assert payload["scope"] == list(request.scope)
    assert payload["allowed_decisions"] == [
        "approve",
        "reject",
        "edit",
        "request_more_evidence",
    ]
    assert "private_key" not in str(payload)


def test_boolean_or_yes_string_can_never_mean_approve():
    request = _request()

    for resume in (True, "yes", "approve"):
        with pytest.raises(ValueError, match="explicit mapping"):
            ApprovalDecision.from_resume(resume, request=request)


def test_approve_must_match_exact_request_and_proposal_hash():
    request = _request()

    with pytest.raises(ValueError, match="request_id does not match"):
        ApprovalDecision.from_resume(
            {
                "request_id": "different-request",
                "proposal_sha256": request.proposal_sha256,
                "decision": "approve",
            },
            request=request,
        )

    with pytest.raises(ValueError, match="proposal hash does not match"):
        ApprovalDecision.from_resume(
            {
                "request_id": request.request_id,
                "proposal_sha256": "0" * 64,
                "decision": "approve",
            },
            request=request,
        )


def test_unknown_resume_fields_fail_closed():
    request = _request()
    resume = _decision(request, "approve", future_blanket_authority=True)

    with pytest.raises(ValueError, match="unknown fields"):
        ApprovalDecision.from_resume(resume, request=request)


def test_edit_requires_new_proposal_and_never_resolves_as_approved():
    request = _request()
    edited = dict(request.proposal)
    edited["amount"] = "0.5"
    decision = ApprovalDecision.from_resume(
        _decision(request, "edit", edited_proposal=edited, feedback="Reduce amount."),
        request=request,
    )

    outcome = resolve_approval_decision(request, decision)

    assert outcome.status == "edited"
    assert outcome.reviewed_proposal["amount"] == "0.5"
    assert outcome.reviewed_proposal_sha256 != request.proposal_sha256
    assert outcome.scope == request.scope


def test_non_edit_decision_cannot_smuggle_edited_proposal():
    request = _request()

    with pytest.raises(ValueError, match="only valid for an edit"):
        ApprovalDecision.from_resume(
            _decision(request, "approve", edited_proposal={"amount": "999"}),
            request=request,
        )


def test_approval_graph_requires_checkpointer():
    with pytest.raises(ValueError, match="requires a checkpointer"):
        build_approval_graph(checkpointer=None)


def test_graph_pauses_then_approve_resumes_same_thread():
    request = _request()
    graph = build_approval_graph(checkpointer=InMemorySaver())

    paused = start_approval(graph, request, thread_id="approval-thread-1")
    payload = _interrupt_value(paused)

    assert payload["request_id"] == request.request_id
    assert payload["proposal_sha256"] == request.proposal_sha256
    assert "outcome" not in paused

    resumed = resume_approval(
        graph,
        _decision(request, "approve", feedback="Approve this exact proposal."),
        thread_id="approval-thread-1",
    )

    assert resumed["status"] == "approved"
    assert resumed["outcome"]["request_id"] == request.request_id
    assert resumed["outcome"]["reviewed_proposal_sha256"] == request.proposal_sha256


def test_reject_ends_safely_without_approved_status():
    request = _request()
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request, thread_id="reject-thread")

    resumed = resume_approval(
        graph,
        _decision(request, "reject", feedback="Do not execute."),
        thread_id="reject-thread",
    )

    assert resumed["status"] == "rejected"
    assert resumed["outcome"]["feedback"] == "Do not execute."


def test_request_more_evidence_is_not_approval():
    request = _request()
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request, thread_id="evidence-thread")

    resumed = resume_approval(
        graph,
        _decision(
            request,
            "request_more_evidence",
            feedback="Re-check current liquidity before I decide.",
        ),
        thread_id="evidence-thread",
    )

    assert resumed["status"] == "more_evidence"
    assert resumed["outcome"]["reviewed_proposal_sha256"] == request.proposal_sha256


def test_edit_resume_returns_new_reviewed_proposal_not_authorization():
    request = _request()
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request, thread_id="edit-thread")
    edited = dict(request.proposal)
    edited["amount"] = "0.25"

    resumed = resume_approval(
        graph,
        _decision(
            request,
            "edit",
            edited_proposal=edited,
            feedback="Use this smaller amount for a new review.",
        ),
        thread_id="edit-thread",
    )

    assert resumed["status"] == "edited"
    assert resumed["outcome"]["reviewed_proposal"]["amount"] == "0.25"
    assert resumed["outcome"]["reviewed_proposal_sha256"] != request.proposal_sha256


def test_approval_cannot_be_borrowed_across_thread_ids():
    request_a = _request("approval-A")
    request_b = _request("approval-B")
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request_a, thread_id="thread-A")
    start_approval(graph, request_b, thread_id="thread-B")

    with pytest.raises(ValueError, match="request_id does not match"):
        resume_approval(
            graph,
            _decision(request_a, "approve"),
            thread_id="thread-B",
        )

    resumed_a = resume_approval(
        graph,
        _decision(request_a, "approve"),
        thread_id="thread-A",
    )
    assert resumed_a["status"] == "approved"
