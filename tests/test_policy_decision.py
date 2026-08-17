"""Tests for deterministic policy decision precedence and Oracle formatting."""

from roberta.policy import (
    PolicyCompilation,
    PolicyEvaluation,
    PolicyEvaluationSummary,
    deterministic_policy_message,
    format_policy_context,
    resolve_policy_decision,
)


def _result(outcome: str, rule_id: str = "rule") -> PolicyEvaluation:
    return PolicyEvaluation(
        rule_id=rule_id,
        kind="hard_constraint" if outcome == "block" else "threshold_rule",
        outcome=outcome,
        description=f"description for {rule_id}",
        fact_key=f"fact.{rule_id}",
        reason="test",
    )


def test_block_has_precedence_over_warning_preference_and_approval():
    summary = PolicyEvaluationSummary(
        results=(
            _result("warn", "warn"),
            PolicyEvaluation(
                rule_id="pref",
                kind="preference",
                outcome="preference_met",
                description="preference",
                fact_key="fact.pref",
            ),
            PolicyEvaluation(
                rule_id="approval",
                kind="approval_rule",
                outcome="approval_required",
                description="approval",
                fact_key="fact.approval",
            ),
            _result("block", "block"),
        )
    )

    decision = resolve_policy_decision(summary)

    assert decision.status == "blocked"
    assert [item.rule_id for item in decision.material_results] == ["block"]
    assert [item.rule_id for item in decision.warnings] == ["warn"]
    assert [item.rule_id for item in decision.preferences] == ["pref"]
    assert decision.may_proceed_without_approval is False


def test_needs_evidence_precedes_approval_when_no_hard_block_exists():
    summary = PolicyEvaluationSummary(
        results=(
            _result("insufficient_evidence", "missing"),
            PolicyEvaluation(
                rule_id="approval",
                kind="approval_rule",
                outcome="approval_required",
                description="approval",
                fact_key="fact.approval",
            ),
        )
    )

    decision = resolve_policy_decision(summary)

    assert decision.status == "needs_evidence"
    assert decision.material_results[0].rule_id == "missing"


def test_approval_required_when_no_block_or_missing_evidence():
    summary = PolicyEvaluationSummary(
        results=(
            PolicyEvaluation(
                rule_id="approval",
                kind="approval_rule",
                outcome="approval_required",
                description="approval",
                fact_key="action.moves_value",
            ),
        )
    )

    decision = resolve_policy_decision(summary)

    assert decision.status == "approval_required"
    assert decision.may_proceed_without_approval is False


def test_allowed_preserves_warning_without_turning_it_into_block():
    summary = PolicyEvaluationSummary(results=(_result("warn", "warn"),))

    decision = resolve_policy_decision(summary)

    assert decision.status == "allowed"
    assert len(decision.warnings) == 1
    assert decision.may_proceed_without_approval is True


def test_policy_context_contains_structural_guardrails_and_json_status():
    summary = PolicyEvaluationSummary(results=(_result("block", "block"),))
    context = format_policy_context(PolicyCompilation(rules=()), summary)

    assert "Do not override decision.status=blocked" in context
    assert '"status": "blocked"' in context
    assert '"rule_id": "block"' in context


def test_deterministic_message_never_turns_block_into_model_recommendation():
    decision = resolve_policy_decision(
        PolicyEvaluationSummary(results=(_result("block", "block"),))
    )

    message = deterministic_policy_message(decision)

    assert message.startswith("Policy blocked this action/recommendation.")
