"""Additional fail-closed safeguards for Phase 9 approval state."""

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from roberta.approval import ApprovalRequest, build_approval_graph, resume_approval, start_approval


def _request(request_id: str, proposal=None):
    return ApprovalRequest(
        request_id=request_id,
        action_type="review_only",
        summary="Review exact proposal.",
        scope=("this_exact_proposal",),
        proposal=proposal or {"operation": "review", "id": request_id},
        policy_reasons=("Approval is required.",),
    )


def _approve(request):
    return {
        "request_id": request.request_id,
        "proposal_sha256": request.proposal_sha256,
        "decision": "approve",
    }


def test_nested_secret_like_field_name_is_refused():
    with pytest.raises(ValueError, match="secret-bearing field"):
        _request(
            "secret-nested",
            proposal={
                "operation": "review",
                "wallet": {"wallet_private_key_hex": "do-not-checkpoint"},
            },
        )


def test_non_secret_similar_word_does_not_false_positive():
    request = _request(
        "non-secret-word",
        proposal={"operation": "review", "secretary_note": "public text"},
    )

    assert request.proposal["secretary_note"] == "public text"


def test_pending_thread_cannot_be_overwritten_by_new_request():
    saver = InMemorySaver()
    graph = build_approval_graph(checkpointer=saver)
    first = _request("first")
    second = _request("second")
    start_approval(graph, first, thread_id="single-request-thread")

    with pytest.raises(ValueError, match="already contains review state"):
        start_approval(graph, second, thread_id="single-request-thread")


def test_completed_thread_cannot_be_reused_for_new_request():
    saver = InMemorySaver()
    graph = build_approval_graph(checkpointer=saver)
    first = _request("first-complete")
    start_approval(graph, first, thread_id="completed-thread")
    resume_approval(graph, _approve(first), thread_id="completed-thread")

    with pytest.raises(ValueError, match="already contains review state"):
        start_approval(
            graph,
            _request("second-complete"),
            thread_id="completed-thread",
        )


def test_completed_approval_cannot_be_resumed_again():
    saver = InMemorySaver()
    graph = build_approval_graph(checkpointer=saver)
    request = _request("once")
    start_approval(graph, request, thread_id="once-thread")
    first = resume_approval(graph, _approve(request), thread_id="once-thread")
    assert first["status"] == "approved"

    with pytest.raises(ValueError, match="not awaiting a pending review"):
        resume_approval(graph, _approve(request), thread_id="once-thread")
