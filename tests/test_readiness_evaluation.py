import json

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from roberta.readiness import (
    CMISObservation,
    CMISTrace,
    ModelTrace,
    ObservedCMISClient,
    ObservedModel,
    ReadinessScenario,
    evaluate_readiness_result,
    load_readiness_scenarios,
)


class FakeModel:
    def __init__(self, response):
        self.response = response

    def bind_tools(self, tools):
        return self

    def invoke(self, messages, *args, **kwargs):
        return self.response


class FakeCMIS:
    def capabilities(self):
        return {"schema_version": 1}

    def market_report(self, *, chain, asset):
        return {"service": "market_report", "chain": chain, "status": "partial"}

    def rank(self, *, chain, metric="volume", limit=10):
        return {"service": "rank", "chain": chain, "status": "ok"}

    def historical_compare(self, *, chain, asset, question):
        return {"service": "historical_compare", "chain": chain, "status": "ok"}

    def tokenomics(self, *, chain, asset):
        return {"service": "tokenomics", "chain": chain, "status": "ok"}

    def risk_check(self, *, chain, asset):
        return {"service": "risk_check", "chain": chain, "status": "ok"}

    def pre_trade_check(self, *, chain, asset, action, amount_usd):
        return {"service": "pre_trade_check", "chain": chain, "status": "ok"}

    def verification_evidence(
        self,
        *,
        chain,
        evidence_id=None,
        fact_type=None,
        subject_id=None,
    ):
        return {"service": "verification_evidence", "chain": chain, "status": "ok"}


def test_observed_model_records_retry_instruction_without_changing_response():
    trace = ModelTrace(role="oracle")
    expected = AIMessage(content="Answer first.")
    model = ObservedModel(FakeModel(expected), trace=trace)

    response = model.invoke([{"role": "system", "content": "ordinary"}])
    assert response is expected
    assert len(trace.events) == 1
    assert trace.events[0].retry_instruction is False
    assert trace.events[0].elapsed_ms >= 0

    from langchain_core.messages import SystemMessage

    model.invoke(
        [
            SystemMessage(
                content=(
                    "The previous recommendation draft violated Roberta's "
                    "deterministic decision-presentation contract."
                )
            )
        ]
    )
    assert trace.events[-1].retry_instruction is True


def test_observed_cmis_records_service_status_and_latency():
    trace = CMISTrace()
    client = ObservedCMISClient(FakeCMIS(), trace=trace)

    result = client.market_report(chain="x1", asset="AGI")

    assert result["status"] == "partial"
    assert len(trace.events) == 1
    assert trace.events[0].service == "market_report"
    assert trace.events[0].chain == "x1"
    assert trace.events[0].status == "partial"
    assert trace.events[0].elapsed_ms >= 0


def test_evaluation_requires_service_coverage_answer_first_and_unknown_disclosure():
    scenario = ReadinessScenario(
        scenario_id="risk",
        turns=("On X1, is AGI risky?",),
        expected_chains=("x1",),
        expected_services={"x1": ("risk_check", "market_report", "tokenomics")},
        require_risk_evidence_labels=True,
    )
    messages = [
        ToolMessage(
            name="x1_scout_investigate",
            tool_call_id="tool-1",
            content=json.dumps(
                {
                    "specialist": "x1_scout",
                    "chain": "x1",
                    "cmis_status": "partial",
                    "warnings": [{"code": "missing_tokenomics"}],
                }
            ),
        ),
        AIMessage(
            content=(
                "I would be cautious. The verified risk result is WARN. "
                "Risk: UNKNOWN. Evidence quality: WEAK. Important tokenomics "
                "evidence is unavailable, so the risk level remains unknown."
            )
        ),
    ]
    cmis_events = [
        CMISObservation("risk_check", "x1", "ok", 1.0, None),
        CMISObservation("market_report", "x1", "partial", 1.0, None),
        CMISObservation("tokenomics", "x1", "unavailable", 1.0, None),
    ]

    result = evaluate_readiness_result(
        scenario,
        graph_result={"messages": messages, "status": "complete"},
        total_elapsed_ms=10,
        oracle_events=[],
        planner_events=[],
        cmis_events=cmis_events,
    )

    assert result.passed is True
    assert result.uncertainty_detected is True
    assert all(result.checks.values())


def test_evaluation_fails_when_degraded_evidence_is_hidden_from_user():
    scenario = ReadinessScenario(
        scenario_id="risk",
        turns=("On X1, is AGI risky?",),
        expected_chains=("x1",),
        expected_services={"x1": ("risk_check",)},
        require_risk_evidence_labels=True,
    )
    messages = [
        ToolMessage(
            name="x1_scout_investigate",
            tool_call_id="tool-1",
            content='{"status":"partial","warnings":[{"code":"missing"}]}',
        ),
        AIMessage(content="I would buy it. Risk: LOW. Evidence quality: STRONG."),
    ]

    result = evaluate_readiness_result(
        scenario,
        graph_result={"messages": messages, "status": "complete"},
        total_elapsed_ms=10,
        oracle_events=[],
        planner_events=[],
        cmis_events=[CMISObservation("risk_check", "x1", "partial", 1.0, None)],
    )

    assert result.passed is False
    assert result.checks["important_unknowns"] is False


def test_evaluation_rejects_unexpected_chain_substitution():
    scenario = ReadinessScenario(
        scenario_id="x1-only",
        turns=("On X1, is AGI risky?",),
        expected_chains=("x1",),
        expected_services={"x1": ("risk_check",)},
        require_risk_evidence_labels=True,
    )
    result = evaluate_readiness_result(
        scenario,
        graph_result={
            "messages": [AIMessage(content="Risk: UNKNOWN. Evidence quality: WEAK.")],
            "status": "complete",
        },
        total_elapsed_ms=1,
        oracle_events=[],
        planner_events=[],
        cmis_events=[CMISObservation("risk_check", "solana", "ok", 1.0, None)],
    )

    assert result.checks["chain_isolation"] is False
    assert result.checks["service_coverage"] is False
    assert result.passed is False


def test_corpus_loader_rejects_unknown_or_execution_like_service(tmp_path):
    path = tmp_path / "corpus.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "scenarios": [
                    {
                        "id": "bad",
                        "turns": ["do it"],
                        "expected_services": {"x1": ["sign"]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="non-read-only/unknown services"):
        load_readiness_scenarios(path)
