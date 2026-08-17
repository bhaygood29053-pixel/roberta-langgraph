"""Tests that material deterministic policy factors survive final synthesis."""

from langchain_core.messages import AIMessage, HumanMessage

from roberta.graph import make_oracle_node
from roberta.policy import (
    PolicyCompilation,
    PolicyDecision,
    PolicyEvaluation,
    PolicyEvaluationSummary,
    PolicyRuntimeContext,
    deterministic_policy_notes,
)


class Model:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return AIMessage(content="Model synthesis without mentioning policy details.")


def _runtime_with_warning_and_preference() -> PolicyRuntimeContext:
    warning = PolicyEvaluation(
        rule_id="warn_volume",
        kind="threshold_rule",
        outcome="warn",
        description="Volume is below the user's warning threshold.",
        fact_key="market.volume_usd",
        reason="warning threshold exceeded or missed",
    )
    preference = PolicyEvaluation(
        rule_id="prefer_x1",
        kind="preference",
        outcome="preference_met",
        description="Prefer X1 when otherwise eligible.",
        fact_key="asset.chain",
        reason="soft preference matched",
    )
    results = (warning, preference)
    return PolicyRuntimeContext(
        compilation=PolicyCompilation(rules=()),
        summary=PolicyEvaluationSummary(results=results),
        decision=PolicyDecision(
            status="allowed",
            material_results=(),
            warnings=(warning,),
            preferences=(preference,),
        ),
    )


def test_policy_notes_are_deterministic_and_explain_material_soft_factors():
    notes = deterministic_policy_notes(_runtime_with_warning_and_preference().decision)

    assert notes == (
        "Policy warning — Volume is below the user's warning threshold.: warning threshold exceeded or missed",
        "Preference matched — Prefer X1 when otherwise eligible.",
    )


def test_final_oracle_answer_cannot_omit_material_warning_or_preference():
    model = Model()
    node = make_oracle_node(
        model,
        policy_context_provider=lambda state: _runtime_with_warning_and_preference(),
    )

    result = node({"messages": [HumanMessage(content="Assess it.")]})
    content = result["messages"][0].content

    assert model.calls == 1
    assert "Model synthesis" in content
    assert "Deterministic policy factors:" in content
    assert "Volume is below the user's warning threshold" in content
    assert "Preference matched" in content
