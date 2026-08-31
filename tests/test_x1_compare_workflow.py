from __future__ import annotations

import json

import pytest

from roberta.cmis.capabilities import HISTORICAL_PAIR_REQUIRED_LIMITATION
from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.compare_product import X1_COMPARE_CONTRACT
from roberta.x1_scout.compare_workflow import X1_COMPARE_WORKFLOW_CONTRACT
from roberta.x1_scout.tool import build_x1_scout_tool


def test_compare_tool_runs_two_validated_scans_without_history() -> None:
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "AAA",
                "objective": "compare AAA and BBB",
                "operation": "compare",
                "compare_asset": "BBB",
            }
        )
    )

    assert report["contract_version"] == X1_COMPARE_WORKFLOW_CONTRACT
    assert report["product_contract_version"] == X1_COMPARE_CONTRACT
    assert report["chain"] == "x1"
    assert report["requested_assets"] == {"left": "AAA", "right": "BBB"}
    assert report["include_history"] is False
    assert report["pair_history"] is None
    assert report["compare_product_view"]["contract_version"] == X1_COMPARE_CONTRACT
    assert report["compare_product_view"]["execution_authorized"] is False
    assert "X1 Compare — AAA vs BBB" in report["compare_product_text"]
    assert report["execution_authorized"] is False
    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "instant_x1_scan",
    ]


def test_compare_tool_requests_one_cmis_all_available_pair_history() -> None:
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "AAA",
                "objective": "compare the full history of AAA and BBB",
                "operation": "compare",
                "compare_asset": "BBB",
                "include_history": True,
            }
        )
    )

    assert report["include_history"] is True
    assert report["pair_history"]["service"] == "historical_compare"
    assert report["pair_history"]["data"]["mode"] == "all_available_pair"
    assert (
        report["compare_product_view"]["pair_history"]["data"]["mode"]
        == "all_available_pair"
    )
    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "instant_x1_scan",
        "historical_compare",
    ]
    history_call = cmis.calls[-1]
    assert history_call["mode"] == "all_available_pair"
    assert history_call["asset"] == "AAA"
    assert history_call["compare_asset"] == "BBB"
    assert history_call["provider_history_backfill"] is False
    assert history_call["onchain_max_signatures"] == 1000


def test_compare_tool_skips_history_when_a_scan_is_unavailable() -> None:
    cmis = MockCMISClient(scenario="unavailable")
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "AAA",
                "objective": "compare the full history of AAA and BBB",
                "operation": "compare",
                "compare_asset": "BBB",
                "include_history": True,
            }
        )
    )

    assert report["status"] == "error"
    assert report["compare_product_view"] is None
    assert report["compare_product_text"] is None
    assert report["pair_history"] is None
    assert {item["code"] for item in report["errors"]} == {
        "x1_compare_left_scan_unavailable",
        "x1_compare_right_scan_unavailable",
    }
    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "instant_x1_scan",
    ]


def test_compare_tool_preserves_capability_failure_as_pair_history_unknown() -> None:
    class NoPairHistoryCMIS(MockCMISClient):
        def capabilities(self):
            manifest = super().capabilities()
            limitations = manifest["chains"]["x1"]["services"]["historical_compare"][
                "limitations"
            ]
            manifest["chains"]["x1"]["services"]["historical_compare"][
                "limitations"
            ] = [
                item
                for item in limitations
                if item != HISTORICAL_PAIR_REQUIRED_LIMITATION
            ]
            return manifest

    cmis = NoPairHistoryCMIS()
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "AAA",
                "objective": "compare the full history of AAA and BBB",
                "operation": "compare",
                "compare_asset": "BBB",
                "include_history": True,
            }
        )
    )

    assert report["status"] == "partial"
    assert report["pair_history"]["status"] == "unavailable"
    assert report["pair_history"]["data"] == {}
    assert (
        report["pair_history"]["warnings"][0]["code"]
        == "cmis_pair_history_contract_unavailable"
    )
    assert report["compare_product_view"]["pair_history"]["status"] == "unavailable"
    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "instant_x1_scan",
    ]


def test_compare_tool_requires_second_asset_and_rejects_trade_inputs() -> None:
    tool = build_x1_scout_tool(MockCMISClient())

    with pytest.raises(ValueError, match="compare requires compare_asset"):
        tool.invoke(
            {
                "asset": "AAA",
                "objective": "compare AAA and BBB",
                "operation": "compare",
            }
        )

    with pytest.raises(ValueError, match="trade action/amount"):
        tool.invoke(
            {
                "asset": "AAA",
                "objective": "compare AAA and BBB",
                "operation": "compare",
                "compare_asset": "BBB",
                "action": "BUY",
                "amount_usd": 100.0,
            }
        )


def test_compare_history_requires_explicit_all_available_history_intent() -> None:
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    with pytest.raises(ValueError, match="full/entire/lifetime-history"):
        tool.invoke(
            {
                "asset": "AAA",
                "objective": "compare AAA and BBB",
                "operation": "compare",
                "compare_asset": "BBB",
                "include_history": True,
            }
        )

    assert cmis.calls == []


def test_include_history_is_rejected_outside_compare() -> None:
    tool = build_x1_scout_tool(MockCMISClient())

    with pytest.raises(ValueError, match="accepted only for compare"):
        tool.invoke(
            {
                "asset": "AAA",
                "objective": "Instant X1 scan AAA",
                "operation": "instant_x1_scan",
                "include_history": True,
            }
        )
