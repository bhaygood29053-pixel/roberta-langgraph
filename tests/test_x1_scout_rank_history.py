"""Regression coverage for Roberta-controlled XDEX rank/history routing."""

import json
from unittest.mock import patch

from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.planner import (
    enforce_plan,
    rank_limit_from_objective,
    rank_metric_from_objective,
    select_cmis_operation,
)


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def _envelope(service: str, *, asset=None):
    return {
        "service": service,
        "chain": "x1",
        "status": "ok",
        "asset": asset or {},
        "data": {},
        "risk": None,
        "confidence": {"complete": True},
        "sources": [],
        "observed_at": "2026-08-17T22:00:00Z",
        "warnings": [],
        "errors": [],
    }


def test_deterministic_selector_recognizes_rank_and_history() -> None:
    assert select_cmis_operation("Top 10 XDEX tokens by volume") == "rank"
    assert (
        select_cmis_operation("How has AGI liquidity changed over the last week?")
        == "historical_compare"
    )


def test_rank_params_are_derived_deterministically_and_bounded() -> None:
    assert rank_metric_from_objective("Top 20 by liquidity") == "liquidity"
    assert rank_metric_from_objective("Show the biggest gainers") == "gainers"
    assert rank_metric_from_objective("What is trending on XDEX?") == "trending"
    assert rank_limit_from_objective("Top 25 by volume") == 25
    assert rank_limit_from_objective("Top 500 by volume") == 50
    assert rank_limit_from_objective("Show the biggest gainers") == 10


def test_rank_requirement_does_not_turn_safest_ranking_into_asset_risk_check() -> None:
    plan = enforce_plan(
        {
            "asset": "XDEX",
            "objective": "Show me the top 10 safest tokens on XDEX",
        },
        {"operations": ["risk_check"]},
    )
    assert plan["operations"][-1] == "rank"
    assert "risk_check" not in plan["operations"]


def test_x1_scout_dispatches_global_rank_through_cmis() -> None:
    client = MockCMISClient()
    graph = build_x1_scout_graph(client)
    objective = "Top 15 XDEX tokens by liquidity"

    result = graph.invoke(
        {
            "request": {
                "asset": "XDEX",
                "objective": objective,
            },
            "status": "running",
        }
    )

    assert client.calls == [
        {
            "operation": "rank",
            "chain": "x1",
            "metric": "liquidity",
            "limit": 15,
        }
    ]
    report = result["report"]
    assert report["source"]["operation"] == "rank"
    assert report["plan"]["operations"] == ["rank"]


def test_x1_scout_dispatches_historical_question_exactly_to_cmis() -> None:
    client = MockCMISClient()
    graph = build_x1_scout_graph(client)
    objective = "How has AGI liquidity changed over the last week?"

    result = graph.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": objective,
            },
            "status": "running",
        }
    )

    assert client.calls == [
        {
            "operation": "historical_compare",
            "chain": "x1",
            "asset": "AGI",
            "question": objective,
        }
    ]
    assert result["report"]["source"]["operation"] == "historical_compare"


def test_autonomous_planner_still_rejects_pretrade_proposal() -> None:
    plan = enforce_plan(
        {
            "asset": "AGI",
            "objective": "What is AGI doing today?",
        },
        {"operations": ["pre_trade_check"]},
    )
    assert plan["operations"] == ["market_report"]
    assert "planner_operation_rejected: pre_trade_check" in plan["warnings"]


def test_http_rank_uses_rank_service_without_fabricated_asset() -> None:
    seen = {}
    response = _envelope("rank")

    def fake_urlopen(request, timeout):
        seen["payload"] = json.loads(request.data.decode("utf-8"))
        seen["timeout"] = timeout
        return _FakeResponse(response)

    with patch("roberta.cmis.http.urlopen", side_effect=fake_urlopen):
        result = CMISHTTPClient(timeout_seconds=7).rank(
            chain="x1",
            metric="volume",
            limit=12,
        )

    assert result == response
    assert seen["timeout"] == 7
    assert seen["payload"] == {
        "service": "rank",
        "chain": "x1",
        "params": {"metric": "volume", "limit": 12},
    }


def test_http_history_preserves_asset_and_exact_question() -> None:
    seen = {}
    response = _envelope("historical_compare", asset={"symbol": "AGI"})
    question = "Has AGI liquidity fallen since last week?"

    def fake_urlopen(request, timeout):
        seen["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(response)

    with patch("roberta.cmis.http.urlopen", side_effect=fake_urlopen):
        result = CMISHTTPClient(timeout_seconds=7).historical_compare(
            chain="x1",
            asset="AGI",
            question=question,
        )

    assert result == response
    assert seen["payload"] == {
        "service": "historical_compare",
        "chain": "x1",
        "asset": "AGI",
        "params": {"question": question},
    }
