"""End-to-end Phase 8 policy -> Phase 9 human review tests."""

from langgraph.checkpoint.memory import InMemorySaver

from roberta.approval import (
    ApprovalOutcome,
    approval_request_from_policy,
    build_approval_graph,
    build_approval_resume_payload,
    rereview_request_from_edit,
    resume_approval,
    start_approval,
)
from roberta.policy import (
    PolicyCompilation,
    PolicyDecision,
    PolicyEvaluation,
    PolicyEvaluationSummary,
    PolicyRuntimeContext,
)


def _approval_policy() -> PolicyRuntimeContext:
    result = PolicyEvaluation(
        rule_id="owner_approval",
        kind="approval_rule",
        outcome="approval_required",
        description="Owner approval is required for this exact consequential proposal.",
        fact_key="action.moves_value",
        reason="declared approval condition matched",
    )
    return PolicyRuntimeContext(
        compilation=PolicyCompilation(rules=()),
        summary=PolicyEvaluationSummary(results=(result,)),
        decision=PolicyDecision(
            status="approval_required",
            material_results=(result,),
        ),
    )


def _request(request_id="review-1"):
    return approval_request_from_policy(
        _approval_policy(),
        request_id=request_id,
        action_type="prepared_proposal",
        summary="Human review of an exact prepared proposal.",
        scope=("this_exact_proposal",),
        proposal={"chain": "x1", "operation": "transfer", "amount": "1"},
        evidence_summary=("Read-only analysis complete.",),
    )


def _decision(request, decision, **extra):
    feedback = extra.pop("feedback", None)
    edited = extra.pop("edited_proposal", None)
    payload = build_approval_resume_payload(
        request,
        decision,
        feedback=feedback,
        edited_proposal=edited,
    )
    payload.update(extra)
    return payload


def _outcome_from_state(payload) -> ApprovalOutcome:
    return ApprovalOutcome(
        status=payload["status"],
        request_id=payload["request_id"],
        original_proposal_sha256=payload["original_proposal_sha256"],
        approval_binding_sha256=payload["approval_binding_sha256"],
        reviewed_proposal=payload["reviewed_proposal"],
        reviewed_proposal_sha256=payload["reviewed_proposal_sha256"],
        scope=tuple(payload["scope"]),
        feedback=payload.get("feedback"),
    )


def test_policy_required_review_pauses_and_exact_approval_proceeds():
    request = _request()
    graph = build_approval_graph(checkpointer=InMemorySaver())
    paused = start_approval(graph, request, thread_id="policy-review-thread")

    interrupt_payload = paused["__interrupt__"][0].value
    assert interrupt_payload["proposal_sha256"] == request.proposal_sha256
    assert interrupt_payload["binding_sha256"] == request.binding_sha256
    assert interrupt_payload["policy_reasons"] == list(request.policy_reasons)

    finished = resume_approval(
        graph,
        _decision(request, "approve"),
        thread_id="policy-review-thread",
    )

    assert finished["status"] == "approved"
    assert finished["next_step"] == "proceed"
    assert finished["outcome"]["reviewed_proposal_sha256"] == request.proposal_sha256
    assert finished["outcome"]["approval_binding_sha256"] == request.binding_sha256


def test_edit_requires_new_request_and_second_human_review_before_proceed():
    first = _request("review-original")
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, first, thread_id="edit-original-thread")
    edited = {"chain": "x1", "operation": "transfer", "amount": "0.5"}

    edited_state = resume_approval(
        graph,
        _decision(
            first,
            "edit",
            edited_proposal=edited,
            feedback="Reduce the amount and ask again.",
        ),
        thread_id="edit-original-thread",
    )
    assert edited_state["next_step"] == "re_review"

    edited_outcome = _outcome_from_state(edited_state["outcome"])
    second = rereview_request_from_edit(
        first,
        edited_outcome,
        new_request_id="review-edited",
    )
    assert second.proposal_sha256 != first.proposal_sha256
    assert second.binding_sha256 != first.binding_sha256

    start_approval(graph, second, thread_id="edit-second-thread")
    approved = resume_approval(
        graph,
        _decision(second, "approve"),
        thread_id="edit-second-thread",
    )

    assert approved["status"] == "approved"
    assert approved["next_step"] == "proceed"
    assert approved["outcome"]["reviewed_proposal_sha256"] == second.proposal_sha256
    assert approved["outcome"]["approval_binding_sha256"] == second.binding_sha256
    assert approved["outcome"]["reviewed_proposal_sha256"] != first.proposal_sha256


def test_more_evidence_keeps_same_proposal_unapproved_for_research():
    request = _request("review-research")
    graph = build_approval_graph(checkpointer=InMemorySaver())
    start_approval(graph, request, thread_id="research-review-thread")

    result = resume_approval(
        graph,
        _decision(
            request,
            "request_more_evidence",
            feedback="Refresh the market evidence before I decide.",
        ),
        thread_id="research-review-thread",
    )

    assert result["status"] == "more_evidence"
    assert result["next_step"] == "research"
    assert result["outcome"]["reviewed_proposal_sha256"] == request.proposal_sha256
    assert result["outcome"]["approval_binding_sha256"] == request.binding_sha256
