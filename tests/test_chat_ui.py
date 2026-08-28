"""Tests for Roberta terminal service menu and automatic status key."""

import json

from roberta.chat_ui import (
    SERVICE_MENU,
    STATUS_KEY,
    automatic_status_summary,
    compare_request,
    format_terminal_text,
    full_request,
    overview_request,
    history_request,
    pretrade_request,
    scan_request,
)
from roberta.chat_cli import _shortcut_request
from roberta.recommendation_policy import recommendation_intent
from roberta.x1_scout.planner import enforce_plan


def test_service_menu_exposes_requested_user_flows() -> None:
    assert "Instant X1 Scan" in SERVICE_MENU
    assert "/scan <asset>" in SERVICE_MENU
    assert "Asset Overview" in SERVICE_MENU
    assert "Compare Two Assets" in SERVICE_MENU
    assert "Risk Assessment" in SERVICE_MENU
    assert "Tokenomics Analysis" in SERVICE_MENU
    assert "Liquidity Analysis" in SERVICE_MENU
    assert "Historical Analysis" in SERVICE_MENU
    assert "Market Activity" in SERVICE_MENU
    assert "Concentration Change" in SERVICE_MENU
    assert "Rank X1 Assets" in SERVICE_MENU
    assert "Pre-Trade Analysis" in SERVICE_MENU
    assert "Evidence Quality Report" in SERVICE_MENU
    assert "Full Assessment" in SERVICE_MENU
    assert "Alert & Warning Key" in SERVICE_MENU


def test_instant_x1_scan_is_deterministic_bounded_three_service_flow() -> None:
    request = scan_request("XNT")

    assert "Instant X1 Scan of XNT" in request
    assert recommendation_intent(request) == "instant_scan"
    assert "market_report" in request
    assert "tokenomics" in request
    assert "risk_check" in request
    assert "not a full assessment" in request
    assert "Do not autonomously add rank" in request
    assert "historical_compare" in request
    assert "pre_trade_check" in request
    assert "/evidence XNT" in request
    assert "/full XNT" in request
    assert "IDENTITY" in request
    assert "EVIDENCE STATE" in request
    assert "DRILL-DOWN" in request

    plan = enforce_plan(
        {"asset": "XNT", "objective": request},
        {"operations": ["rank", "historical_compare"]},
    )
    assert plan["operations"] == [
        "market_report",
        "tokenomics",
        "risk_check",
    ]


def test_scan_shortcut_expands_without_changing_asset_text() -> None:
    assert _shortcut_request("/scan XNT") == scan_request("XNT")


def test_status_key_keeps_risk_service_and_proof_meanings_separate() -> None:
    assert "[WARN]" in STATUS_KEY
    assert "[PARTIAL]" in STATUS_KEY
    assert "[INSUFFICIENT_EVIDENCE]" in STATUS_KEY
    assert "[WEAK]" in STATUS_KEY
    assert "Proof strength is NOT asset safety" in STATUS_KEY
    assert "OK does not mean the asset is safe" in STATUS_KEY
    assert "[NOT RUN]" in STATUS_KEY


def test_compare_request_requires_fresh_symmetric_evidence() -> None:
    request = compare_request("XNT", "ANL")

    assert "XNT vs ANL" in request
    assert "For EACH asset" in request
    assert "market_report" in request
    assert "risk_check" in request
    assert "tokenomics" in request
    assert "historical_compare" in request
    assert "Do not reuse an earlier risk result" in request
    assert "missing, unverified, or non-comparable evidence" in request




def test_terminal_renderer_converts_markdown_comparison_table() -> None:
    rendered = format_terminal_text(
        """**Market structure**

| Metric | XNT | ANL |
|---|---|---|
| Liquidity (verified) | ~$102.7k | ~$15.7k |
| Market report status | partial (4/5) | ok (5/5) |
"""
    )

    assert "MARKET STRUCTURE" in rendered
    assert "Metric" in rendered
    assert "XNT" in rendered
    assert "ANL" in rendered
    assert "Liquidity (verified)" in rendered
    assert "|" not in rendered
    assert "**" not in rendered


def test_compare_request_requires_terminal_friendly_structure() -> None:
    request = compare_request("XNT", "ANL")

    assert "MARKET STRUCTURE" in request
    assert "IMPORTANT DIFFERENCES" in request
    assert "STATUS SUMMARY" in request
    assert "[VERIFIED]" in request
    assert "Show relative ratios only when CMIS or X1 Scout" in request
    assert "Do not use Markdown table syntax" in request



def test_single_asset_requests_require_compact_terminal_sections() -> None:
    overview = overview_request("AGI")
    history = history_request("AGI")

    assert "CURRENT MARKET" in overview
    assert "HISTORY" in overview
    assert "EVIDENCE STATUS" in overview
    assert "KEY LIMITATIONS" in overview
    assert "Do not lead with a long limitation paragraph" in overview
    assert "live market snapshot first" in overview

    assert "Status: UNAVAILABLE" in history
    assert "1-3 concise bullets" in history
    assert "Do not use Markdown table syntax" in history
    assert "Never describe missing, unavailable, or unverified evidence as zero" in history


def test_history_and_full_requests_route_to_all_available_history() -> None:
    history = history_request("AGI")
    full = full_request("AGI")

    assert "all available history" in history
    assert "entire history" in history
    assert "not a fixed-window request" in history
    assert "all available history" in full
    assert "entire history" in full
    assert "rather than requiring a fixed comparison period" in full


def test_full_terminal_request_is_recognized_as_deterministic_full_assessment() -> None:
    request = full_request("XNT")

    assert "full assessment of XNT" in request
    assert recommendation_intent(request) == "full_assessment"

    plan = enforce_plan(
        {"asset": "XNT", "objective": request},
        {"operations": ["rank"]},
    )
    assert plan["operations"] == [
        "market_report",
        "rank",
        "tokenomics",
        "historical_compare",
        "risk_check",
    ]
    assert not any(
        warning.startswith("planner_operation_rejected_for_rank_objective")
        for warning in plan["warnings"]
    )


def test_previous_terminal_full_wording_still_maps_to_full_assessment() -> None:
    objective = "On X1, produce the most complete current assessment possible for XNT."
    assert recommendation_intent(objective) == "full_assessment"


def test_pretrade_request_preserves_analysis_only_boundary() -> None:
    request = pretrade_request("AGI", "BUY", 2500)

    assert "BUY $2500.00" in request
    assert "pre_trade_check" in request
    assert "analysis_only=true" in request
    assert "execution_authorized=false" in request


def test_automatic_status_summary_explains_warning_states() -> None:
    report = {
        "investigations": [
            {
                "operation": "risk_check",
                "cmis_status": "partial",
                "risk_help": {
                    "recommendation": {
                        "value": "WARN",
                        "reasons": ["Verified historical price comparison was not supplied."],
                        "flags": ["historical_price_unavailable"],
                    }
                },
                "evidence_context": {
                    "proof_strength": "WEAK",
                    "verification_status": "INSUFFICIENT_EVIDENCE",
                    "freshness_verified": None,
                    "unknown_categories": ["historical_coverage"],
                },
                "warnings": ["historical_price_unavailable"],
                "errors": [],
            }
        ]
    }

    summary = automatic_status_summary(json.dumps(report))

    assert summary is not None
    assert "CMIS: [PARTIAL]" in summary
    assert "Risk: [WARN]" in summary
    assert "Proof: [WEAK]" in summary
    assert "Verification: [INSUFFICIENT_EVIDENCE]" in summary
    assert "Freshness: [UNKNOWN]" in summary
    assert "Verified historical price evidence is unavailable" in summary


def test_automatic_status_summary_keeps_clean_states_compact() -> None:
    report = {
        "investigations": [
            {
                "operation": "market_report",
                "cmis_status": "ok",
                "risk_help": None,
                "evidence_context": {
                    "proof_strength": "STRONG",
                    "verification_status": "AGREEMENT",
                    "freshness_verified": True,
                    "unknown_categories": [],
                },
                "warnings": [],
                "errors": [],
            }
        ]
    }

    summary = automatic_status_summary(report)

    assert summary is not None
    assert "CMIS: [OK]" in summary
    assert "Proof: [STRONG]" in summary
    assert "Verification: [AGREEMENT]" in summary
    assert "Freshness: [VERIFIED]" in summary
    assert "Meaning:" not in summary
