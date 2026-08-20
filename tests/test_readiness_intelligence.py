from langchain_core.messages import AIMessage, ToolMessage

from roberta.readiness_intelligence import (
    EVIDENCE_ID,
    IntelligenceReadinessFixtureCMISClient,
    run_concentration_intelligence_replay,
)


class _ScriptedIntelligenceModel:
    def __init__(self) -> None:
        self.bound_tools = []

    def bind_tools(self, tools):
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages):
        tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
        if not tool_messages:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "x1_scout_investigate",
                        "args": {
                            "asset": "AGI",
                            "objective": (
                                "Explain the exact concentration-change evidence, evidence quality, "
                                "and important unknowns."
                            ),
                            "operation": "concentration_change_intelligence",
                            "intelligence_evidence_id": EVIDENCE_ID,
                        },
                        "id": "intelligence-readiness-call",
                        "type": "tool_call",
                    }
                ],
            )

        return AIMessage(
            content=(
                "The evidence supports a 400 bps increase in the observed top-token-account "
                "concentration scope, but the evidence is partial. Evidence quality is "
                "moderate and freshness remains unknown; beneficial-owner identity is "
                "unresolved. Token accounts are not unique holders, so this does not prove "
                "ownership or whale behavior. Risk remains unavailable from this service."
            )
        )


def test_intelligence_readiness_fixture_is_partial_and_never_adds_risk_or_behavior() -> None:
    result = IntelligenceReadinessFixtureCMISClient(
        scenario="test_only"
    ).concentration_change_intelligence(
        chain="x1",
        asset="AGI",
        intelligence_evidence_id=EVIDENCE_ID,
    )

    assert result["status"] == "partial"
    assert result["risk"] is None
    assert result["data"]["facts"]["delta_bps"] == 400
    assert result["data"]["risk_interpretation"] is None
    assert result["data"]["behavioral_interpretation_added"] is False
    assert result["data"]["execution_authorized"] is False
    assert result["data"]["evidence"]["freshness_verified"] is None
    assert "beneficial_owner_identity" in result["data"]["evidence"]["unresolved_fields"]


def test_production_style_intelligence_replay_covers_scout_and_truth_preservation() -> None:
    result = run_concentration_intelligence_replay(_ScriptedIntelligenceModel)

    assert result.passed is True
    assert result.case_id == "x1-concentration-change-intelligence-partial"
    assert result.checks["service_coverage"] is True
    assert result.checks["exact_fact_preserved"] is True
    assert result.checks["risk_not_invented"] is True
    assert result.checks["partial_evidence_preserved"] is True
    assert result.checks["answer_discloses_uncertainty"] is True
    assert result.checks["answer_discloses_scope_caveat"] is True
    assert any(event["service"] == "concentration_change_intelligence" for event in result.cmis_events)
