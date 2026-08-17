"""Tests for deterministic next-step state after Phase 9 review."""

from langgraph.checkpoint.memory import InMemorySaver

from roberta.approval import ApprovalRequest, build_approval_graph, resume_approval, start_approval


def _request(request_id: str):
    return ApprovalRequest(
        request_id=request_id,
        action_type="review_only",
        summary="Review exact proposal.",
        scope=("this_exact_proposal",),
        proposal={"operation": "review", "id": request_id},
        policy_reasons=("Approval is required.",),
    )


def _resume(request, decision, **extra):
    return {
        "request_id": request.request_id,
        "proposal_sha256": request.proposal_sha256,
        "decision": decision,
        **extra,
    }


def test_approved_review_marks_proceed_without_executing():
    request = _request("approve-step")
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request, thread_id="approve-step-thread")
    result = resume_approval(
        graph,
        _resume(request, "approve"),
        thread_id="approve-step-thread",
    )

    assert result["status"] == "approved"
    assert result["next_step"] == "proceed"
    assert "execution_token" not in result["outcome"]


def test_rejected_review_marks_stop():
    request = _request("reject-step")
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request, thread_id="reject-step-thread")
    result = resume_approval(
        graph,
        _resume(request, "reject"),
        thread_id="reject-step-thread",
    )

    assert result["next_step"] == "stop"


def test_more_evidence_marks_research_not_proceed():
    request = _request("research-step")
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request, thread_id="research-step-thread")
    result = resume_approval(
        graph,
        _resume(request, "request_more_evidence"),
        thread_id="research-step-thread",
    )

    assert result["status"] == "more_evidence"
    assert result["next_step"] == "research"


def test_edit_marks_re_review_not_proceed():
    request = _request("edit-step")
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request, thread_id="edit-step-thread")
    edited = dict(request.proposal)
    edited["changed"] = True
    result = resume_approval(
        graph,
        _resume(request, "edit", edited_proposal=edited),
        thread_id="edit-step-thread",
    )

    assert result["status"] == "edited"
    assert result["next_step"] == "re_review"
