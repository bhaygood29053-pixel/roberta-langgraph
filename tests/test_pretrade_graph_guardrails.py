"""Guardrails for the deterministic post-tool pre-trade finalizer."""

from langchain_core.messages import AIMessage

from roberta.cmis.mock import MockCMISClient
from roberta.graph import build_graph
from roberta.policy import (
    PolicyCompilation,
    PolicyDecision,
    PolicyEvaluation,
    PolicyEvaluationSummary,
    PolicyRuntimeContext,
)
from roberta.tools import get_roberta_tools


class TechnicalObjectiveOracle:
    """Deliberately asks the tool for technical wording on its only model call."""

    def __init__(self):
        self.invoke_count = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.invoke_count += 1
        if self.invoke_count != 1:
            raise AssertionError("pre-trade finalizer must not call the model again")
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "x1_scout_investigate",
                    "args": {
                        "asset": "AGI",
                        "objective": "Show technical analysis for buying $500 of AGI.",
                        "operation": "pre_trade_check",
                        "action": "BUY",
                        "amount_usd": 500.0,
                    },
                    "id": "guard-pretrade-1",
                    "type": "tool_call",
                }
            ],
        )


def _policy_context(status: str) -> PolicyRuntimeContext:
    if status == "needs_evidence":
        result = PolicyEvaluation(
            rule_id="fresh",
            kind="evidence_requirement",
            outcome="insufficient_evidence",
            description="Fresh market evidence is required.",
            fact_key="market.current",
            reason="test",
        )
    elif status == "approval_required":
        result = PolicyEvaluation(
            rule_id="approval",
            kind="approval_rule",
            outcome="approval_required",
            description="Value movement requires approval.",
            fact_key="action.moves_value",
            reason="test",
        )
    else:  # pragma: no cover - tests use only guarded states
        raise ValueError(status)
    material = (result,)
    return PolicyRuntimeContext(
        compilation=PolicyCompilation(rules=()),
        summary=PolicyEvaluationSummary(results=material),
        decision=PolicyDecision(status=status, material_results=material),
    )


def _graph(model, *, policy_status=None):
    provider = (
        None
        if policy_status is None
        else lambda state: _policy_context(policy_status)
    )
    return build_graph(
        model=model,
        tools=get_roberta_tools(cmis_client=MockCMISClient()),
        policy_context_provider=provider,
    )


def test_tool_objective_cannot_enable_technical_mode_without_user_request():
    model = TechnicalObjectiveOracle()
    result = _graph(model).invoke(
        {
            "messages": [
                {"role": "user", "content": "Is it ok to purchase $500 of AGI?"}
            ],
            "status": "running",
        }
    )

    final = str(result["messages"][-1].content)
    assert model.invoke_count == 1
    assert "buying $500 of AGI" in final
    assert "Technical pre-trade details:" not in final
    assert "CMIS" not in final


def test_user_technical_request_wins_even_if_tool_objective_is_not_authoritative():
    model = TechnicalObjectiveOracle()
    result = _graph(model).invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Show me the technical analysis for buying $500 of AGI.",
                }
            ],
            "status": "running",
        }
    )

    final = str(result["messages"][-1].content)
    assert model.invoke_count == 1
    assert "Technical pre-trade details:" in final
    assert '"service": "pre_trade_check"' in final


def test_needs_evidence_policy_suppresses_pretrade_conversational_answer():
    model = TechnicalObjectiveOracle()
    result = _graph(model, policy_status="needs_evidence").invoke(
        {
            "messages": [
                {"role": "user", "content": "Is it ok to purchase $500 of AGI?"}
            ],
            "status": "running",
        }
    )

    final = str(result["messages"][-1].content)
    assert model.invoke_count == 1
    assert final.startswith(
        "Policy cannot be evaluated yet because required evidence is unavailable."
    )
    assert "buying $500 of AGI" not in final


def test_approval_required_policy_wraps_pretrade_analysis_without_authorizing():
    model = TechnicalObjectiveOracle()
    result = _graph(model, policy_status="approval_required").invoke(
        {
            "messages": [
                {"role": "user", "content": "Is it ok to purchase $500 of AGI?"}
            ],
            "status": "running",
        }
    )

    final = str(result["messages"][-1].content)
    assert model.invoke_count == 1
    assert final.startswith("Policy requires explicit user approval")
    assert "Non-authorizing analysis:" in final
    assert "buying $500 of AGI" in final
