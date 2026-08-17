"""Tests for structural Oracle policy enforcement."""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage

from roberta.graph import make_oracle_node
from roberta.memory import MemoryRecord
from roberta.policy import (
    PolicyCompilation,
    PolicyDecision,
    PolicyEvaluation,
    PolicyEvaluationSummary,
    PolicyRuntimeContext,
    evaluate_policy_records,
)


class CountingModel:
    def __init__(self, response: AIMessage) -> None:
        self.response = response
        self.calls = 0
        self.messages = []

    def invoke(self, messages):
        self.calls += 1
        self.messages.append(list(messages))
        return self.response


def _context(status: str) -> PolicyRuntimeContext:
    if status == "blocked":
        evaluation = PolicyEvaluation(
            rule_id="block",
            kind="hard_constraint",
            outcome="block",
            description="Asset violates a hard user rule.",
            fact_key="asset.allowed",
            reason="test",
        )
        material = (evaluation,)
    elif status == "needs_evidence":
        evaluation = PolicyEvaluation(
            rule_id="fresh",
            kind="evidence_requirement",
            outcome="insufficient_evidence",
            description="Fresh market evidence is required.",
            fact_key="market.current",
            reason="test",
        )
        material = (evaluation,)
    elif status == "approval_required":
        evaluation = PolicyEvaluation(
            rule_id="approval",
            kind="approval_rule",
            outcome="approval_required",
            description="Value movement requires approval.",
            fact_key="action.moves_value",
            reason="test",
        )
        material = (evaluation,)
    else:
        material = ()

    summary = PolicyEvaluationSummary(results=material)
    return PolicyRuntimeContext(
        compilation=PolicyCompilation(rules=()),
        summary=summary,
        decision=PolicyDecision(status=status, material_results=material),
    )


def test_hard_block_short_circuits_before_model_invocation():
    model = CountingModel(AIMessage(content="I would have recommended proceeding."))
    node = make_oracle_node(
        model,
        policy_context_provider=lambda state: _context("blocked"),
    )

    result = node({"messages": [HumanMessage(content="Should I do it?")]})

    assert model.calls == 0
    assert result["status"] == "complete"
    assert result["messages"][0].content.startswith("Policy blocked")


def test_needs_evidence_cannot_finish_with_unsupported_model_answer():
    model = CountingModel(AIMessage(content="Looks fine to me."))
    node = make_oracle_node(
        model,
        policy_context_provider=lambda state: _context("needs_evidence"),
    )

    result = node({"messages": [HumanMessage(content="Assess it.")]})

    assert model.calls == 1
    assert result["status"] == "complete"
    assert result["messages"][0].content.startswith(
        "Policy cannot be evaluated yet because required evidence is unavailable."
    )
    assert "Looks fine" not in result["messages"][0].content


def test_needs_evidence_allows_model_to_request_read_only_specialist_tool():
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "x1_scout_investigate",
                "args": {"asset": "TEST", "objective": "assess market risk"},
                "id": "call-1",
                "type": "tool_call",
            }
        ],
    )
    model = CountingModel(response)
    node = make_oracle_node(
        model,
        policy_context_provider=lambda state: _context("needs_evidence"),
    )

    result = node({"messages": [HumanMessage(content="Assess TEST.")]})

    assert model.calls == 1
    assert result["status"] == "running"
    assert result["messages"][0].tool_calls[0]["name"] == "x1_scout_investigate"


def test_approval_required_keeps_model_analysis_non_authorizing():
    model = CountingModel(AIMessage(content="The proposed route has these tradeoffs."))
    node = make_oracle_node(
        model,
        policy_context_provider=lambda state: _context("approval_required"),
    )

    result = node({"messages": [HumanMessage(content="Prepare an action.")]})

    content = result["messages"][0].content
    assert content.startswith("Policy requires explicit user approval")
    assert "Non-authorizing analysis:" in content
    assert "these tradeoffs" in content


def test_policy_provider_failure_fails_closed_without_model_call():
    model = CountingModel(AIMessage(content="Proceed."))

    def broken_provider(state):
        raise RuntimeError("policy backend failed")

    node = make_oracle_node(model, policy_context_provider=broken_provider)
    result = node({"messages": [HumanMessage(content="Proceed?")]})

    assert model.calls == 0
    assert result["status"] == "error"
    assert "Policy evaluation is unavailable" in result["messages"][0].content


def test_malformed_durable_policy_becomes_needs_evidence_not_silent_allow():
    record = MemoryRecord(
        key="risk:malformed",
        category="user_risk_policy",
        content="not-json",
        source="test",
        authority="durable",
    )

    runtime = evaluate_policy_records([record], {})

    assert runtime.decision.status == "needs_evidence"
    assert runtime.summary.results[0].outcome == "insufficient_evidence"
    assert runtime.summary.results[0].source_memory_key == "risk:malformed"


def test_policy_context_is_added_as_guarded_system_data_when_model_runs():
    model = CountingModel(AIMessage(content="analysis"))
    node = make_oracle_node(
        model,
        policy_context_provider=lambda state: _context("allowed"),
    )

    node({"messages": [HumanMessage(content="Analyze.")]})

    system_contents = [getattr(message, "content", "") for message in model.messages[0]]
    assert any("Deterministic Oracle policy context." in content for content in system_contents)
    assert any('"status": "allowed"' in content for content in system_contents)
