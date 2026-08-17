"""Resilience tests for checkpointed Phase 9 approval interrupts."""

from langgraph.checkpoint.memory import InMemorySaver

from roberta.approval import (
    ApprovalRequest,
    build_approval_graph,
    build_approval_resume_payload,
    resume_approval,
    start_approval,
)


def _request(request_id="resilience-approval"):
    return ApprovalRequest(
        request_id=request_id,
        action_type="review_only_proposal",
        summary="Review this exact non-executing proposal.",
        scope=("this_exact_proposal",),
        proposal={"chain": "x1", "operation": "review", "amount": "1"},
        policy_reasons=("Explicit approval is required.",),
    )


def _approve(request):
    return build_approval_resume_payload(request, "approve")


def test_invalid_resume_does_not_destroy_paused_request():
    request = _request()
    saver = InMemorySaver()
    graph = build_approval_graph(checkpointer=saver)
    start_approval(graph, request, thread_id="retry-thread")

    try:
        resume_approval(
            graph,
            {
                "request_id": request.request_id,
                "proposal_sha256": "0" * 64,
                "binding_sha256": request.binding_sha256,
                "decision": "approve",
            },
            thread_id="retry-thread",
        )
    except ValueError as exc:
        assert "proposal hash does not match" in str(exc)
    else:
        raise AssertionError("mismatched proposal hash unexpectedly resumed approval")

    resumed = resume_approval(
        graph,
        _approve(request),
        thread_id="retry-thread",
    )

    assert resumed["status"] == "approved"
    assert resumed["outcome"]["request_id"] == request.request_id


def test_fresh_graph_instance_can_resume_same_paused_approval_backend():
    request = _request("fresh-graph-approval")
    saver = InMemorySaver()
    first_graph = build_approval_graph(checkpointer=saver)
    start_approval(first_graph, request, thread_id="fresh-graph-thread")

    second_graph = build_approval_graph(checkpointer=saver)
    resumed = resume_approval(
        second_graph,
        _approve(request),
        thread_id="fresh-graph-thread",
    )

    assert resumed["status"] == "approved"
    assert resumed["outcome"]["reviewed_proposal_sha256"] == request.proposal_sha256
    assert resumed["outcome"]["approval_binding_sha256"] == request.binding_sha256


def test_same_request_id_with_changed_proposal_changes_proposal_and_binding_hash():
    first = _request("same-id")
    second = ApprovalRequest(
        request_id="same-id",
        action_type=first.action_type,
        summary=first.summary,
        scope=first.scope,
        proposal={"chain": "x1", "operation": "review", "amount": "2"},
        policy_reasons=first.policy_reasons,
    )

    assert first.proposal_sha256 != second.proposal_sha256
    assert first.binding_sha256 != second.binding_sha256


def test_approved_outcome_contains_no_execution_credential_or_signature():
    request = _request("non-token")
    saver = InMemorySaver()
    graph = build_approval_graph(checkpointer=saver)
    start_approval(graph, request, thread_id="non-token-thread")
    resumed = resume_approval(
        graph,
        _approve(request),
        thread_id="non-token-thread",
    )

    outcome = resumed["outcome"]
    assert outcome["status"] == "approved"
    assert "signature" not in outcome
    assert "keypair" not in outcome
    assert "private_key" not in outcome
    assert "broadcast" not in outcome
    assert "execution_token" not in outcome
