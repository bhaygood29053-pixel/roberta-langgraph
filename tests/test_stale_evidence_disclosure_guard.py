import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from roberta.decision_synthesis import decision_synthesis_failure_text
from roberta.graph import make_oracle_node


class SequenceModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(list(messages))
        return self.responses.pop(0)


def _stale_post_scout_state():
    report = {
        "specialist": "x1_scout",
        "chain": "x1",
        "investigations": [
            {
                "operation": "risk_check",
                "evidence_context": {"freshness_verified": False},
            },
            {
                "operation": "market_report",
                "evidence_context": {"freshness_verified": False},
            },
            {
                "operation": "tokenomics",
                "evidence_context": {"freshness_verified": False},
            },
        ],
    }
    return {
        "messages": [
            HumanMessage(content="On X1, is AGI risky?"),
            ToolMessage(
                content=json.dumps(report),
                tool_call_id="stale-evidence-guard",
                name="x1_scout_investigate",
            ),
        ]
    }


def test_oracle_retries_once_when_explicit_stale_evidence_is_not_disclosed():
    model = SequenceModel(
        [
            AIMessage(
                content=(
                    "I can't give you a meaningful risk read. Risk: unknown because no live market "
                    "data is available. Evidence quality: weak."
                )
            ),
            AIMessage(
                content=(
                    "I can't give you a current risk read because the specialist evidence is stale. "
                    "Risk: unknown. Evidence quality: weak."
                )
            ),
        ]
    )
    node = make_oracle_node(model)

    result = node(_stale_post_scout_state())

    assert len(model.calls) == 2
    assert result["status"] == "complete"
    assert "stale" in result["messages"][0].content.lower()
    retry_system_text = "\n".join(
        str(message.content)
        for message in model.calls[1]
        if getattr(message, "type", None) == "system"
    )
    assert "stale_evidence_not_disclosed" in retry_system_text
    assert "stale or not fresh" in retry_system_text


def test_repeated_stale_evidence_omission_fails_closed():
    model = SequenceModel(
        [
            AIMessage(
                content=(
                    "Risk: unknown because no live market facts are available. "
                    "Evidence quality: weak."
                )
            ),
            AIMessage(
                content=(
                    "Risk: unavailable because current market facts are unavailable. "
                    "Evidence quality: weak."
                )
            ),
        ]
    )
    node = make_oracle_node(model)

    result = node(_stale_post_scout_state())

    assert len(model.calls) == 2
    assert result["status"] == "complete"
    assert result["messages"][0].content == decision_synthesis_failure_text()
    assert "material evidence limitation" in result["messages"][0].content


def test_nonstale_specialist_evidence_does_not_trigger_freshness_retry():
    report = {
        "specialist": "x1_scout",
        "chain": "x1",
        "investigations": [
            {
                "operation": "risk_check",
                "evidence_context": {"freshness_verified": True},
            }
        ],
    }
    state = {
        "messages": [
            HumanMessage(content="On X1, is AGI risky?"),
            ToolMessage(
                content=json.dumps(report),
                tool_call_id="fresh-evidence-guard",
                name="x1_scout_investigate",
            ),
        ]
    }
    model = SequenceModel(
        [
            AIMessage(
                content=(
                    "Risk: unknown because the deterministic risk field is unavailable. "
                    "Evidence quality: unavailable."
                )
            )
        ]
    )
    node = make_oracle_node(model)

    result = node(state)

    assert len(model.calls) == 1
    assert result["status"] == "complete"
