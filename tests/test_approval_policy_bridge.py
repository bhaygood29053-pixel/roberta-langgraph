"""Tests for policy-to-approval bridging and deterministic review routing."""

from roberta.approval import (
    ApprovalDecision,
    approval_next_step,
    approval_request_from_policy,
    build_approval_resume_payload,
    rereview_request_from_edit,
    resolve_approval_decision,
)
from roberta.policy import (
    PolicyCompilation,
    PolicyDecision,
    PolicyEvaluation,
    PolicyEvaluationSummary,
    PolicyRuntimeContext,
)


def _policy(status="approval_required"):
    material = ()
    if status == "approval_required":
        result = PolicyEvaluation(
            rule_id="approve_value_move",
            kind="approval_rule",
            outcome="approval_required",
            description="Value movement requires explicit user approval.",
            fact_key="action.moves_value",
            reason="declared approval condition matched",
        )
        material = (result,)
    return PolicyRuntimeContext(
        compilation=PolicyCompilation(rules=()),
        summary=PolicyEvaluationSummary(results=material),
        decision=PolicyDecision(status=status, material_results=material),
    )


def _request_from_policy():
    return approval_request_from_policy(
        _policy(),
        request_id="review-1",
        action_type="prepared_transaction",
        summary="Review this exact prepared proposal.",
        scope=("this_exact_proposal",),
        proposal={"chain": "x1", "operation": "transfer", "amount": "1"},
        evidence_summary=("Read-only analysis completed.",),
    )


def test_policy_bridge_requires_deterministic_approval_required_status():
    for status in ("allowed", "blocked", "needs_evidence"):
        try:
            approval_request_from_policy(
                _policy(status),
                request_id="review",
                action_type="proposal",
                summary="review",
                scope=("proposal",),
                proposal={"operation": "noop"},
            )
        except ValueError as exc:
            assert "approval_required" in str(exc)
        else:
            raise AssertionError(f"{status} unexpectedly created approval request")


def test_policy_bridge_preserves_material_reason_and_exact_proposal_scope():
    request = _request_from_policy()

    assert request.policy_reasons == (
        "Value movement requires explicit user approval.",
    )
    assert request.scope == ("this_exact_proposal",)
    assert request.proposal["amount"] == "1"
    assert request.evidence_summary == ("Read-only analysis completed.",)


def test_approval_next_step_is_deterministic_and_non_executing():
    assert approval_next_step({"status": "approved"}) == "proceed"
    assert approval_next_step({"status": "rejected"}) == "stop"
    assert approval_next_step({"status": "edited"}) == "re_review"
    assert approval_next_step({"status": "more_evidence"}) == "research"


def test_edit_creates_new_request_and_does_not_inherit_approval():
    previous = _request_from_policy()
    edited = dict(previous.proposal)
    edited["amount"] = "0.5"
    decision = ApprovalDecision.from_resume(
        build_approval_resume_payload(
            previous,
            "edit",
            edited_proposal=edited,
            feedback="Reduce amount.",
        ),
        request=previous,
    )
    outcome = resolve_approval_decision(previous, decision)

    rereview = rereview_request_from_edit(
        previous,
        outcome,
        new_request_id="review-2",
    )

    assert outcome.status == "edited"
    assert approval_next_step(outcome.to_state_payload()) == "re_review"
    assert rereview.request_id == "review-2"
    assert rereview.proposal_sha256 == outcome.reviewed_proposal_sha256
    assert rereview.proposal_sha256 != previous.proposal_sha256
    assert rereview.binding_sha256 != previous.binding_sha256
    assert rereview.scope == previous.scope


def test_edit_re_review_refuses_same_request_id():
    previous = _request_from_policy()
    edited = dict(previous.proposal)
    edited["amount"] = "0.5"
    outcome = resolve_approval_decision(
        previous,
        ApprovalDecision.from_resume(
            build_approval_resume_payload(
                previous,
                "edit",
                edited_proposal=edited,
            ),
            request=previous,
        ),
    )

    try:
        rereview_request_from_edit(
            previous,
            outcome,
            new_request_id=previous.request_id,
        )
    except ValueError as exc:
        assert "new request_id" in str(exc)
    else:
        raise AssertionError("edited proposal reused the previous approval request id")
