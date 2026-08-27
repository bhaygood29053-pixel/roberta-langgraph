"""Tests for Roberta terminal service menu and automatic status key."""

import json

from roberta.chat_ui import (
    SERVICE_MENU,
    STATUS_KEY,
    automatic_status_summary,
    compare_request,
    format_terminal_text,
    overview_request,
    history_request,
    pretrade_request,
)


def test_service_menu_exposes_requested_user_flows() -> None:
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
