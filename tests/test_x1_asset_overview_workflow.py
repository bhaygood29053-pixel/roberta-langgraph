from __future__ import annotations

import json

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.asset_overview_workflow import (
    X1_ASSET_OVERVIEW_CONTRACT,
    X1_ASSET_OVERVIEW_WORKFLOW_CONTRACT,
)
from roberta.x1_scout.tool import build_x1_scout_tool


def test_asset_overview_composes_scan_and_burn_products() -> None:
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "AGI",
                "objective": "asset overview for AGI",
                "operation": "asset_overview",
            }
        )
    )

    assert report["contract_version"] == X1_ASSET_OVERVIEW_WORKFLOW_CONTRACT
    assert report["product_contract_version"] == X1_ASSET_OVERVIEW_CONTRACT
    assert report["chain"] == "x1"
    assert report["requested_asset"] == "AGI"
    assert report["execution_authorized"] is False

    product = report["asset_overview_product_view"]
    assert product["contract_version"] == X1_ASSET_OVERVIEW_CONTRACT
    assert product["product"] == "x1_asset_overview"
    assert product["execution_authorized"] is False
    assert product["source_contracts"] == {
        "instant_x1_scan": "instant_x1_scan_product_view/v1",
        "burn_intelligence": "x1_burn_intelligence/v1",
    }
    assert product["instant_x1_scan"]["risk"]["execution_authorized"] is False
    assert product["burn_intelligence"]["proof_score_separate_from_risk"] is True

    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "burn_intelligence",
    ]
    text = report["asset_overview_product_text"]
    assert "Instant X1 Scan" in text
    assert "Burn Intelligence" in text
    assert "24h period-over-period" in text
    assert "Lifetime total burn verified: False" in text
    assert "Execution authorized: false" in text


def test_asset_overview_rejects_trade_compare_and_history_controls() -> None:
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
                    "objective": "asset overview for AGI",
                    "operation": "asset_overview",
                    **kwargs,
                }
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Asset Overview accepted forbidden inputs: {kwargs!r}"
            )


def test_asset_overview_preserves_burn_values_without_local_recalculation() -> None:
    report = json.loads(
        build_x1_scout_tool(MockCMISClient()).invoke(
            {
                "asset": "AGI",
                "objective": "asset overview for AGI",
                "operation": "asset_overview",
            }
        )
    )
    burn = report["asset_overview_product_view"]["burn_intelligence"]["burn_metrics"]

    assert burn["windows"]["24h"]["burned_tokens"] == "10"
    assert (
        burn["windows"]["24h"]["period_over_period"]["percent_change"]
        == "25"
    )
    assert burn["lifetime_total_burn_verified"] is False
