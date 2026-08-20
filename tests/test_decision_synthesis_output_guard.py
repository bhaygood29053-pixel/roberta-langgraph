from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from roberta.decision_synthesis import (
    decision_response_violation,
    decision_synthesis_failure_text,
)
from roberta.graph import make_oracle_node


class SequenceModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(list(messages))
        return self.responses.pop(0)


def _post_scout_state(objective):
    return {
        "messages": [
            HumanMessage(content=objective),
            ToolMessage(
                content='{"specialist":"x1_scout","chain":"x1"}',
                tool_call_id="decision-output-guard",
                name="x1_scout_investigate",
            ),
        ]
    }


def test_raw_json_is_an_obvious_normal_decision_violation():
    assert (
        decision_response_violation("Should I buy AGI?", '{"service":"cmis"}')
        == "raw_service_dump"
    )


def test_diagnostic_or_orchestration_first_is_rejected():
    for content in (
        "CMIS pre-trade analysis — AGI",
        "X1 Scout returned these findings...",
        "Liquidity Scout reply: WARN",
        "Market service: OK",
        "I have the results from X1 Scout.",
        "Let me synthesize the report.",
    ):
        assert (
            decision_response_violation("Is AGI risky?", content)
            == "diagnostic_or_orchestration_first"
        )


def test_conversational_answer_first_draft_is_not_rejected():
    content = (
        "I would be cautious here. The verified risk result is WARN, while evidence quality "
        "is moderate and one important tokenomics field is still unavailable."
    )
    assert decision_response_violation("Should I buy AGI?", content) is None


def test_price_move_answer_without_evidence_quality_is_rejected():
    content = (
        "I can't explain the price move definitively. No deterministic risk assessment or "
        "historical comparison is available, so I won't speculate."
    )
    assert (
        decision_response_violation("On X1, why is AGI's price falling?", content)
        == "risk_evidence_separation_not_disclosed"
    )


def test_price_move_answer_without_risk_is_rejected():
    content = "Evidence quality: WEAK because the provider path is unavailable."
    assert (
        decision_response_violation("On X1, why is AGI's price falling?", content)
        == "risk_evidence_separation_not_disclosed"
    )


def test_explicit_raw_or_technical_request_is_not_blocked_by_presentation_guard():
    objective = "Is AGI risky? Show me the raw technical details and sources."
    assert decision_response_violation(objective, '{"service":"risk_check"}') is None


def test_general_non_recommendation_output_is_outside_this_guard():
    assert decision_response_violation("Explain this JSON response", '{"foo":"bar"}') is None


def test_oracle_retries_once_after_raw_recommendation_dump():
    model = SequenceModel(
        [
            AIMessage(content='{"service":"risk_check","status":"ok"}'),
            AIMessage(
                content=(
                    "I would be cautious. The deterministic risk result is WARN. "
                    "Risk and evidence quality remain separate, and missing evidence stays unknown."
                )
            ),
        ]
    )
    node = make_oracle_node(model)

    result = node(_post_scout_state("Is AGI risky?"))

    assert len(model.calls) == 2
    assert result["status"] == "complete"
    assert result["messages"][0].content.startswith("I would be cautious.")
    retry_system_text = "\n".join(
        str(message.content)
        for message in model.calls[1]
        if getattr(message, "type", None) == "system"
    )
    assert "previous recommendation draft violated" in retry_system_text
    assert "raw_service_dump" in retry_system_text


def test_oracle_retries_once_after_diagnostic_first_recommendation():
    model = SequenceModel(
        [
            AIMessage(content="CMIS service: OK. Verified price follows..."),
            AIMessage(
                content=(
                    "Avoid treating this as low risk. Risk: HIGH. "
                    "Evidence quality: MODERATE."
                )
            ),
        ]
    )
    node = make_oracle_node(model)

    result = node(_post_scout_state("Should I buy AGI?"))

    assert len(model.calls) == 2
    assert result["messages"][0].content.startswith("Avoid treating this as low risk")


def test_oracle_retries_once_when_risk_evidence_separation_is_omitted():
    model = SequenceModel(
        [
            AIMessage(
                content=(
                    "I can't explain the price move definitively. No deterministic risk "
                    "assessment or historical comparison is available."
                )
            ),
            AIMessage(
                content=(
                    "I can't explain the price move definitively. Risk: unavailable because no "
                    "deterministic risk assessment was produced. Evidence quality: weak because "
                    "the market and historical services are unavailable."
                )
            ),
        ]
    )
    node = make_oracle_node(model)

    result = node(_post_scout_state("On X1, why is AGI's price falling?"))

    assert len(model.calls) == 2
    assert result["status"] == "complete"
    assert "Evidence quality:" in result["messages"][0].content
    retry_system_text = "\n".join(
        str(message.content)
        for message in model.calls[1]
        if getattr(message, "type", None) == "system"
    )
    assert "risk_evidence_separation_not_disclosed" in retry_system_text
    assert "`Risk:` and `Evidence quality:`" in retry_system_text


def test_repeated_risk_evidence_separation_omission_fails_closed():
    model = SequenceModel(
        [
            AIMessage(content="No deterministic risk assessment is available."),
            AIMessage(content="Risk remains unavailable because the provider path failed."),
        ]
    )
    node = make_oracle_node(model)

    result = node(_post_scout_state("On X1, why is AGI's price falling?"))

    assert len(model.calls) == 2
    assert result["status"] == "complete"
    assert result["messages"][0].content == decision_synthesis_failure_text()


def test_repeated_noncompliance_fails_closed_instead_of_exposing_raw_dump():
    model = SequenceModel(
        [
            AIMessage(content='{"service":"risk_check"}'),
            AIMessage(content="X1 Scout report: raw diagnostics again"),
        ]
    )
    node = make_oracle_node(model)

    result = node(_post_scout_state("Is AGI risky?"))

    assert len(model.calls) == 2
    assert result["status"] == "complete"
    assert result["messages"][0].content == decision_synthesis_failure_text()
    assert "raw service dump" in result["messages"][0].content
    assert "No transaction or execution is authorized" in result["messages"][0].content


def test_technical_decision_request_can_receive_raw_output_without_retry():
    raw = '{"service":"risk_check","proof_score":{"proof_strength":"STRONG"}}'
    model = SequenceModel([AIMessage(content=raw)])
    node = make_oracle_node(model)

    result = node(
        _post_scout_state("Is AGI risky? Show raw technical details and verification sources.")
    )

    assert len(model.calls) == 1
    assert result["messages"][0].content == raw


def test_pre_specialist_model_output_is_not_retried_by_post_scout_guard():
    model = SequenceModel([AIMessage(content='{"tool":"proposal"}')])
    node = make_oracle_node(model)

    result = node({"messages": [HumanMessage(content="Should I buy AGI?")]})

    assert len(model.calls) == 1
    assert result["messages"][0].content == '{"tool":"proposal"}'
