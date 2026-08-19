from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from roberta.decision_synthesis import (
    build_decision_synthesis_system_message,
    technical_decision_detail_requested,
)
from roberta.graph import make_oracle_node
from roberta.prompts import ORACLE_SYSTEM_PROMPT


class CapturingModel:
    def __init__(self):
        self.calls = []

    def invoke(self, messages):
        self.calls.append(list(messages))
        return AIMessage(content="Recommendation first. Evidence follows.")


def _system_contents(messages):
    return [message.content for message in messages if isinstance(message, SystemMessage)]


def test_decision_contract_is_absent_for_general_questions():
    assert build_decision_synthesis_system_message("Tell me what X1 is") is None


def test_decision_contract_is_answer_first_and_non_authorizing():
    message = build_decision_synthesis_system_message("Should I buy AGI?")

    assert message is not None
    assert "recognized_intent: trade_decision" in message
    assert "Lead with the recommendation, conclusion, or blocker immediately" in message
    assert "2-4 material evidence-backed reasons" in message
    assert "Risk and Evidence quality as separate dimensions" in message
    assert "Missing evidence remains unknown, never zero" in message
    assert "read-only and non-authorizing" in message
    assert "does not grant pre_trade_check" in message
    assert "User -> Roberta -> Chain Scout -> CMIS -> Chain Provider" in message


def test_decision_contract_carries_required_evidence_for_risk_question():
    message = build_decision_synthesis_system_message("Is AGI risky?")

    assert message is not None
    assert "recognized_intent: risk_assessment" in message
    assert "required_evidence_services: risk_check, market_report, tokenomics" in message
    assert "required_evidence_categories: risk, current_market, tokenomics, evidence_quality" in message


def test_default_decision_contract_uses_progressive_disclosure():
    message = build_decision_synthesis_system_message("Which token is safer?")

    assert message is not None
    assert "Use progressive disclosure" in message
    assert "do not dump raw envelopes" in message
    assert technical_decision_detail_requested("Which token is safer?") is False


def test_explicit_technical_request_allows_deeper_evidence_detail():
    objective = "Is AGI risky? Show technical details and sources."
    message = build_decision_synthesis_system_message(objective)

    assert message is not None
    assert technical_decision_detail_requested(objective) is True
    assert "explicitly requested technical/evidence detail" in message
    assert "fuller provenance" in message


def test_oracle_injects_task_specific_contract_only_after_specialist_evidence():
    model = CapturingModel()
    node = make_oracle_node(model)

    before_state = {
        "messages": [HumanMessage(content="Should I buy AGI?")],
    }
    node(before_state)
    before_system = _system_contents(model.calls[-1])
    assert before_system == [ORACLE_SYSTEM_PROMPT]

    after_state = {
        "messages": [
            HumanMessage(content="Should I buy AGI?"),
            ToolMessage(
                content='{"specialist":"x1_scout","chain":"x1"}',
                tool_call_id="decision-contract-test",
                name="x1_scout_investigate",
            ),
        ],
    }
    node(after_state)
    after_system = _system_contents(model.calls[-1])

    assert after_system[0] == ORACLE_SYSTEM_PROMPT
    assert len(after_system) == 2
    assert "recognized_intent: trade_decision" in after_system[1]
    assert "required_evidence_services" in after_system[1]


def test_general_post_tool_synthesis_does_not_gain_recommendation_contract():
    model = CapturingModel()
    node = make_oracle_node(model)
    state = {
        "messages": [
            HumanMessage(content="Explain this specialist result."),
            ToolMessage(
                content='{"specialist":"x1_scout","chain":"x1"}',
                tool_call_id="general-contract-test",
                name="x1_scout_investigate",
            ),
        ],
    }

    node(state)
    assert _system_contents(model.calls[-1]) == [ORACLE_SYSTEM_PROMPT]
