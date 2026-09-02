from __future__ import annotations

import json

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.tool import build_x1_scout_tool
from roberta.x1_scout.what_changed_workflow import (
    X1_WHAT_CHANGED_CONTRACT,
    X1_WHAT_CHANGED_WORKFLOW_CONTRACT,
)


def test_what_changed_tool_composes_three_validated_scout_products() -> None:
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "AGI",
                "objective": "what changed with AGI?",
                "operation": "what_changed",
            }
        )
    )

    assert report["contract_version"] == X1_WHAT_CHANGED_WORKFLOW_CONTRACT
    assert report["product_contract_version"] == X1_WHAT_CHANGED_CONTRACT
    assert report["chain"] == "x1"
    assert report["requested_asset"] == "AGI"
    assert report["execution_authorized"] is False

    product = report["what_changed_product_view"]
    assert product["contract_version"] == X1_WHAT_CHANGED_CONTRACT
    assert product["product"] == "x1_what_changed"
    assert product["execution_authorized"] is False
    assert product["source_contracts"] == {
        "instant_x1_scan": "instant_x1_scan_product_view/v1",
        "burn_intelligence": "x1_burn_intelligence/v1",
        "discovery_intelligence": "x1_discovery_intelligence/v1",
    }

    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "burn_intelligence",
        "discovery_intelligence",
    ]
    assert "X1 WHAT CHANGED?" in report["what_changed_product_text"]
    assert "Token launch time: NOT VERIFIED" in report["what_changed_product_text"]
    assert "No ROBERTA market delta is calculated locally." in report["what_changed_product_text"]


def test_what_changed_preserves_burn_comparison_states_without_recalculation() -> None:
    report = json.loads(
        build_x1_scout_tool(MockCMISClient()).invoke(
            {
                "asset": "AGI",
                "objective": "what changed with AGI?",
                "operation": "what_changed",
            }
        )
    )
    product = report["what_changed_product_view"]

    comparison = product["burn_changes"]["windows"]["24h"]["period_over_period"]
    assert comparison["prior_burned_tokens"] == "8"
    assert comparison["percent_change"] == "25"
    assert comparison["change_state"] == "AVAILABLE"


def test_what_changed_preserves_discovery_non_launch_non_continuity_boundaries() -> None:
    report = json.loads(
        build_x1_scout_tool(MockCMISClient()).invoke(
            {
                "asset": "AGI",
                "objective": "what changed with AGI?",
                "operation": "what_changed",
            }
        )
    )
    discovery = report["what_changed_product_view"]["discovery_history"]

    assert discovery["token_launch_time"] is None
    assert discovery["token_launch_time_verified"] is False
    assert discovery["coverage"]["continuous_coverage_verified"] is False
    assert discovery["coverage"]["archive_completeness_verified"] is False


def test_what_changed_rejects_trade_compare_and_history_controls() -> None:
    tool = build_x1_scout_tool(MockCMISClient())

    for kwargs in (
        {"action": "BUY", "amount_usd": 100.0},
        {"compare_asset": "XNT"},
        {"include_history": True},
        {"intelligence_evidence_id": "ie_test"},
    ):
        try:
            tool.invoke(
                {
                    "asset": "AGI",
                    "objective": "what changed with AGI?",
                    "operation": "what_changed",
                    **kwargs,
                }
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"WHAT CHANGED accepted forbidden inputs: {kwargs!r}")
