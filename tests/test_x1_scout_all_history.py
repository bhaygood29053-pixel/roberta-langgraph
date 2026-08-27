"""Regression coverage for CMIS 1.10 all-available history adoption."""

import json

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.planner import (
    historical_mode_from_objective,
    is_all_available_history_objective,
)
from roberta.x1_scout.tool import build_x1_scout_tool


def test_full_history_language_selects_all_available_modes_deterministically() -> None:
    objective = "Show me AGI's entire history"
    assert is_all_available_history_objective(objective) is True
    assert historical_mode_from_objective(objective) == "all_available"
    assert (
        historical_mode_from_objective(
            "Compare XNT and ANL over their entire history",
            compare_asset="ANL",
        )
        == "all_available_pair"
    )
    assert (
        historical_mode_from_objective(
            "How has AGI liquidity changed over the last week?",
            compare_asset="ANL",
        )
        == "window"
    )


def test_x1_scout_dispatches_single_asset_all_available_history_once() -> None:
    client = MockCMISClient()
    graph = build_x1_scout_graph(client)
    objective = "Show me AGI's full history"

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
            "mode": "all_available",
        }
    ]
    report = result["report"]
    assert report["source"]["operation"] == "historical_compare"
    assert report["findings"]["data"]["mode"] == "all_available"
    assert report["findings"]["data"]["full_asset_lifetime_verified"] is False
    assert report["findings"]["data"]["continuous_coverage_verified"] is False


def test_x1_scout_dispatches_pair_history_as_one_cmis_request() -> None:
    client = MockCMISClient()
    graph = build_x1_scout_graph(client)
    objective = "Compare XNT and ANL over their entire history"

    result = graph.invoke(
        {
            "request": {
                "asset": "XNT",
                "compare_asset": "ANL",
                "objective": objective,
            },
            "status": "running",
        }
    )

    assert client.calls == [
        {
            "operation": "historical_compare",
            "chain": "x1",
            "asset": "XNT",
            "question": objective,
            "mode": "all_available_pair",
            "compare_asset": "ANL",
        }
    ]
    report = result["report"]
    assert report["requested_asset"] == "XNT"
    assert report["requested_compare_asset"] == "ANL"
    assert report["findings"]["data"]["mode"] == "all_available_pair"
    assert report["findings"]["data"]["compare_asset_request"] == "ANL"
    assert report["findings"]["data"]["full_asset_lifetime_verified"] is False


def test_roberta_facing_x1_tool_exposes_compare_asset_and_preserves_pair_request() -> None:
    client = MockCMISClient()
    tool = build_x1_scout_tool(client)
    schema = tool.args_schema.model_json_schema()
    assert "compare_asset" in schema["properties"]

    raw = tool.invoke(
        {
            "asset": "XNT",
            "compare_asset": "ANL",
            "objective": "Compare XNT and ANL over their lifetime history",
        }
    )
    report = json.loads(raw)

    assert client.calls == [
        {
            "operation": "historical_compare",
            "chain": "x1",
            "asset": "XNT",
            "question": "Compare XNT and ANL over their lifetime history",
            "mode": "all_available_pair",
            "compare_asset": "ANL",
        }
    ]
    assert report["requested_compare_asset"] == "ANL"


def test_roberta_facing_x1_tool_rejects_compare_asset_outside_full_history() -> None:
    tool = build_x1_scout_tool(MockCMISClient())

    try:
        tool.invoke(
            {
                "asset": "XNT",
                "compare_asset": "ANL",
                "objective": "What is XNT doing today?",
            }
        )
    except ValueError as exc:
        assert "entire/full/lifetime-history" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("compare_asset outside full history should fail closed")
