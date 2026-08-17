"""Regression coverage for Roberta's conversational pre-trade UX."""

import json

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from roberta.cmis.mock import MockCMISClient
from roberta.graph import build_graph
from roberta.pretrade_ux import build_pretrade_presentation
from roberta.tools import get_roberta_tools
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.tool import build_x1_scout_tool


def _result(
    *,
    side="buy",
    amount=500.0,
    status="partial",
    recommendation="WARN",
    data_extra=None,
    warnings=None,
):
    data = {"trade": {"side": side, "notional_usd": amount}}
    if data_extra:
        data.update(data_extra)
    return {
        "service": "pre_trade_check",
        "chain": "x1",
        "status": status,
        "asset": {"symbol": "AGI", "mint": "agi-mint"},
        "data": data,
        "risk": {
            "recommendation": recommendation,
            "reasons": ["Returned deterministic reason."],
            "flags": ["RETURNED_FLAG"],
        },
        "confidence": {"verified_checks": 6, "total_checks": 8},
        "sources": [{"source": "test"}],
        "observed_at": "2026-08-17T18:00:00Z",
        "warnings": list(warnings or []),
        "errors": [],
    }


@pytest.mark.parametrize(
    ("side", "amount", "expected"),
    [
        ("buy", 50.0, "buying $50 of AGI"),
        ("buy", 500.0, "buying $500 of AGI"),
        ("buy", 2000.0, "buying $2,000 of AGI"),
        ("sell", 1000.0, "selling $1,000 of AGI"),
    ],
)
def test_conversational_mode_preserves_user_trade_without_recomputing(
    side, amount, expected
):
    presentation = build_pretrade_presentation(_result(side=side, amount=amount))

    assert presentation is not None
    assert presentation["mode"] == "conversational"
    assert presentation["voice"] == "roberta"
    assert expected in presentation["user_text"]
    assert presentation["facts"]["trade"]["notional_usd"] == amount
    assert presentation["recommendation"] == "WARN"
    assert "CMIS" not in presentation["user_text"]
    assert "Liquidity Scout reply:" not in presentation["user_text"]


def test_missing_analysis_remains_explicit_and_is_not_fabricated():
    presentation = build_pretrade_presentation(_result())

    assert presentation is not None
    assert presentation["missing_evidence"] == [
        "trade-size assessment",
        "price-impact estimate",
        "slippage estimate",
        "route analysis",
        "fee estimate",
    ]
    text = presentation["user_text"]
    assert "not fully evaluated" in text
    assert "price-impact estimate" in text
    assert "slippage estimate" in text
    assert "0%" not in text


def test_returned_trade_size_and_route_values_are_copied_exactly():
    result = _result(
        amount=2000.0,
        data_extra={
            "market": {
                "verified_liquidity_usd": "3380.125",
                "verified_volume_24h_usd": "124.50",
            },
            "trade_size": {
                "notional_to_liquidity_ratio": "0.5916942847741605",
                "policy_version": "trade-size-v1",
                "assessment": "HIGH",
                "evidence_status": "VERIFIED",
            },
            "route_analysis": {
                "status": "PARTIAL",
                "route_scope": "pool-123",
                "estimated_execution_price": "0.0042",
                "estimated_price_impact_percent": "3.75",
                "estimated_slippage_percent": "1.25",
                "estimated_fees": "0.30",
            },
        },
    )
    presentation = build_pretrade_presentation(result)

    assert presentation is not None
    text = presentation["user_text"]
    assert "$3380.125" in text
    assert "$124.50" in text
    assert "HIGH" in text
    assert "0.5916942847741605" in text
    assert "3.75" in text
    assert "1.25" in text
    assert "0.30" in text
    assert presentation["facts"]["trade_size"] == result["data"]["trade_size"]
    assert presentation["facts"]["route_analysis"] == result["data"]["route_analysis"]
    assert presentation["missing_evidence"] == []


def test_technical_mode_preserves_structured_status_warnings_and_conflict():
    warning = {
        "code": "MARKET_EVIDENCE_CONFLICT",
        "message": "Two sources disagree; no value was promoted.",
    }
    presentation = build_pretrade_presentation(
        _result(warnings=[warning]),
        objective="Show me the technical analysis for that trade.",
    )

    assert presentation is not None
    assert presentation["mode"] == "technical"
    text = presentation["user_text"]
    assert '"service": "pre_trade_check"' in text
    assert '"status": "partial"' in text
    assert '"recommendation": "WARN"' in text
    assert "MARKET_EVIDENCE_CONFLICT" in text
    assert "Two sources disagree; no value was promoted." in text
    assert "Liquidity Scout reply:" not in text


def test_non_pretrade_result_has_no_pretrade_presentation():
    result = _result()
    result["service"] = "risk_check"
    assert build_pretrade_presentation(result) is None


def test_x1_scout_attaches_pretrade_presentation_only_to_explicit_pretrade():
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)
    result = scout.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "Is it ok to purchase $500 of AGI?",
                "operation": "pre_trade_check",
                "action": "BUY",
                "amount_usd": 500.0,
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["source"]["operation"] == "pre_trade_check"
    assert report["pretrade_presentation"] is not None
    assert "buying $500 of AGI" in report["pretrade_presentation"]["user_text"]
    assert cmis.calls[-1] == {
        "operation": "pre_trade_check",
        "chain": "x1",
        "asset": "AGI",
        "action": "BUY",
        "amount_usd": 500.0,
    }


def test_x1_scout_tool_requires_explicit_side_and_amount_for_pretrade():
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    with pytest.raises(ValueError):
        tool.invoke(
            {
                "asset": "AGI",
                "objective": "buy AGI",
                "amount_usd": 500.0,
            }
        )

    raw = tool.invoke(
        {
            "asset": "AGI",
            "objective": "Is it ok to purchase $500 of AGI?",
            "operation": "pre_trade_check",
            "action": "BUY",
            "amount_usd": 500.0,
        }
    )
    report = json.loads(raw)
    assert report["source"]["operation"] == "pre_trade_check"
    assert report["pretrade_presentation"]["voice"] == "roberta"


class OneShotPretradeOracle:
    """Request one pre-trade tool call and fail if a second model rewrite occurs."""

    def __init__(self, *, technical=False):
        self.technical = technical
        self.invoke_count = 0
        self.bound_tools = []

    def bind_tools(self, tools):
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages):
        self.invoke_count += 1
        if self.invoke_count != 1:
            raise AssertionError("pre-trade final reply must not use a second free-form model pass")
        objective = (
            "Show me the technical analysis for buying $500 of AGI."
            if self.technical
            else "Is it ok to purchase $500 of AGI?"
        )
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "x1_scout_investigate",
                    "args": {
                        "asset": "AGI",
                        "objective": objective,
                        "operation": "pre_trade_check",
                        "action": "BUY",
                        "amount_usd": 500.0,
                    },
                    "id": "pretrade-1",
                    "type": "tool_call",
                }
            ],
        )


def test_roberta_graph_uses_deterministic_conversational_pretrade_finalizer():
    model = OneShotPretradeOracle()
    graph = build_graph(
        model=model,
        tools=get_roberta_tools(cmis_client=MockCMISClient()),
    )

    result = graph.invoke(
        {
            "messages": [
                {"role": "user", "content": "Is it ok to purchase $500 of AGI?"}
            ],
            "status": "running",
        }
    )

    assert result["status"] == "complete"
    assert model.invoke_count == 1
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    final = result["messages"][-1]
    assert isinstance(final, AIMessage)
    assert "buying $500 of AGI" in str(final.content)
    assert "CMIS" not in str(final.content)
    assert "Liquidity Scout reply:" not in str(final.content)


def test_roberta_graph_uses_explicit_technical_pretrade_mode():
    model = OneShotPretradeOracle(technical=True)
    graph = build_graph(
        model=model,
        tools=get_roberta_tools(cmis_client=MockCMISClient()),
    )

    result = graph.invoke(
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

    assert model.invoke_count == 1
    final = result["messages"][-1]
    assert isinstance(final, AIMessage)
    assert "Technical pre-trade details:" in str(final.content)
    assert '"service": "pre_trade_check"' in str(final.content)
