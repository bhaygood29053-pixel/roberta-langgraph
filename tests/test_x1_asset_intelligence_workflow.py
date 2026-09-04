from __future__ import annotations

import json

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.asset_intelligence_workflow import (
    X1_ASSET_INTELLIGENCE_CONTRACT,
    X1_ASSET_INTELLIGENCE_WORKFLOW_CONTRACT,
    build_x1_asset_intelligence_packet,
)
from roberta.x1_scout.tool import build_x1_scout_tool


def test_asset_intelligence_collects_full_baseline_before_roberta_synthesis() -> None:
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "AGI",
                "objective": "Should I buy AGI?",
                "operation": "asset_intelligence",
            }
        )
    )

    assert report["contract_version"] == X1_ASSET_INTELLIGENCE_WORKFLOW_CONTRACT
    assert report["product_contract_version"] == X1_ASSET_INTELLIGENCE_CONTRACT
    assert report["specialist"] == "x1_scout"
    assert report["source"] == {
        "service": "x1_scout",
        "operation": "asset_intelligence",
    }
    assert report["execution_authorized"] is False

    packet = report["asset_intelligence_packet"]
    assert packet["contract_version"] == X1_ASSET_INTELLIGENCE_CONTRACT
    assert packet["product"] == "x1_asset_intelligence"
    assert packet["facts_authority"] == "chain_scout_cmis"
    assert packet["judgment_authority"] == "roberta"
    assert packet["execution_authorized"] is False
    assert packet["evidence_completion"]["baseline_required"] == [
        "instant_x1_scan",
        "burn_intelligence",
        "discovery_intelligence",
    ]
    assert packet["evidence_completion"]["baseline_attempted"] == [
        "instant_x1_scan",
        "burn_intelligence",
        "discovery_intelligence",
    ]
    assert packet["evidence_completion"]["requested_enrichments"] == []

    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "burn_intelligence",
        "discovery_intelligence",
    ]


def test_asset_intelligence_adds_pretrade_only_from_explicit_trade_inputs() -> None:
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "XNT",
                "objective": "Should I buy $100 worth of XNT today?",
                "operation": "asset_intelligence",
                "action": "BUY",
                "amount_usd": 100.0,
            }
        )
    )

    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "burn_intelligence",
        "discovery_intelligence",
        "pre_trade_check",
    ]

    packet = report["asset_intelligence_packet"]
    assert packet["evidence_completion"]["requested_enrichments"] == [
        "pre_trade_check"
    ]
    assert packet["evidence_completion"]["returned_enrichments"] == [
        "pre_trade_check"
    ]
    pretrade = packet["source_products"]["pre_trade_check"]
    assert pretrade["service"] == "pre_trade_check"
    assert pretrade["analysis_only"] is True
    assert pretrade["execution_authorized"] is False
    assert pretrade["pretrade_presentation"]["voice"] == "roberta"

    # The full packet is a Scout evidence product, so it must not look like the
    # legacy single-pretrade report that routes directly to pretrade_synthesis.
    assert report["source"]["operation"] == "asset_intelligence"


def test_asset_intelligence_requires_complete_explicit_trade_context() -> None:
    tool = build_x1_scout_tool(MockCMISClient())

    for partial in (
        {"action": "BUY"},
        {"amount_usd": 100.0},
    ):
        try:
            tool.invoke(
                {
                    "asset": "XNT",
                    "objective": "Should I buy $100 worth of XNT today?",
                    "operation": "asset_intelligence",
                    **partial,
                }
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Asset Intelligence accepted incomplete trade context: {partial!r}"
            )


def _scan_product(*, mint=None, identity_key=None):
    return {
        "contract_version": "instant_x1_scan_product_view/v1",
        "product": "instant_x1_scan",
        "chain": "x1",
        "status": "partial",
        "identity": {
            "verified": True,
            "symbol": "XNT",
            "name": "XNT",
            "mint": mint,
            "identity_key": identity_key,
        },
        "limitations": [],
        "warnings": [],
        "execution_authorized": False,
    }


def _burn_product(mint):
    return {
        "contract_version": "x1_burn_intelligence/v1",
        "product": "x1_burn_intelligence",
        "chain": "x1",
        "status": "partial",
        "asset": {"symbol": "XNT", "mint": mint},
        "limitations": [],
        "warnings": [],
        "execution_authorized": False,
    }


def _discovery_product(mint):
    return {
        "contract_version": "x1_discovery_intelligence/v1",
        "product": "x1_discovery_intelligence",
        "chain": "x1",
        "status": "partial",
        "asset": {"symbol": "XNT", "mint": mint},
        "limitations": [],
        "warnings": [],
        "execution_authorized": False,
    }


def _report(status="partial"):
    return {"cmis_status": status, "warnings": [], "errors": []}


def test_asset_intelligence_does_not_silently_collapse_native_xnt_into_wrapped_mint() -> None:
    wrapped_mint = "7SXmUpcBGSAwW5LmtzQVF9jHswZ7xzmdKqWa4nDgL3ER"
    packet = build_x1_asset_intelligence_packet(
        requested_asset="XNT",
        objective="Should I buy XNT?",
        scan=_scan_product(identity_key="native:xnt"),
        burn=_burn_product(wrapped_mint),
        discovery=_discovery_product(wrapped_mint),
        scan_report=_report(),
        burn_report=_report(),
        discovery_report=_report(),
    )

    assert packet["identity_bindings"]["instant_x1_scan"]["state"] == "authoritative_subject"
    assert packet["identity_bindings"]["burn_intelligence"]["state"] == "mismatch"
    assert packet["identity_bindings"]["discovery_intelligence"]["state"] == "mismatch"
    assert "burn_intelligence" in packet["unbound_sections"]
    assert "discovery_intelligence" in packet["unbound_sections"]
    assert "burn_intelligence" not in packet["available_sections"]
    assert "discovery_intelligence" not in packet["available_sections"]
    assert packet["status"] == "partial"
    assert packet["execution_authorized"] is False
