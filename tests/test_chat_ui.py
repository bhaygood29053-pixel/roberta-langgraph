"""Tests for Roberta terminal service menu and automatic status key."""

import json

from roberta.chat_ui import (
    HUMAN_ROBERTA_PRESENTATION_POLICY,
    SERVICE_MENU,
    STATUS_KEY,
    automatic_status_summary,
    burn_request,
    discovery_request,
    what_changed_request,
    compare_request,
    format_terminal_text,
    full_request,
    overview_request,
    history_request,
    pretrade_request,
    risk_request,
    tokenomics_request,
    liquidity_request,
    activity_request,
    concentration_request,
    rank_request,
    evidence_request,
)
from roberta.recommendation_policy import recommendation_intent
from roberta.x1_scout.planner import enforce_plan


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
    assert "Burn Intelligence" in SERVICE_MENU
    assert "/burn <asset>" in SERVICE_MENU
    assert "What Changed?" in SERVICE_MENU
    assert "/changed <asset>" in SERVICE_MENU
    assert "ROBERTA -> X1 Scout (scanner) -> CMIS -> X1 providers" in SERVICE_MENU


def test_status_key_keeps_risk_service_and_proof_meanings_separate() -> None:
    assert "[WARN]" in STATUS_KEY
    assert "[PARTIAL]" in STATUS_KEY
    assert "[INSUFFICIENT_EVIDENCE]" in STATUS_KEY
    assert "[WEAK]" in STATUS_KEY
    assert "Proof strength is NOT asset safety" in STATUS_KEY
    assert "OK does not mean the asset is safe" in STATUS_KEY
    assert "[NOT RUN]" in STATUS_KEY


def test_compare_request_routes_to_first_class_symmetric_compare() -> None:
    request = compare_request("XNT", "ANL")

    assert "XNT vs ANL" in request
    assert "operation='compare'" in request
    assert "asset='XNT'" in request
    assert "compare_asset='ANL'" in request
    assert "include_history=false" in request
    assert "one validated Instant X1 Scan for each asset" in request
    assert "deterministic risk" in request
    assert "missing, unverified, or incompatible evidence" in request
    assert "left and right PASS/WARN/BLOCK" in request
    assert "do not calculate a combined risk score" in request
    assert "do not average Proof Scores" in request
    assert "execution_authorized=false" in request




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
    assert "Do not use Markdown table syntax" in request
    assert "Do not create relative ratios" in request
    assert "accepted X1 Compare product" in request



def test_asset_overview_routes_to_first_class_scan_plus_burn_workflow() -> None:
    overview = overview_request("AGI")

    assert "Asset Overview for AGI" in overview
    assert "operation='asset_overview'" in overview
    assert "instant_x1_scan/v3" in overview
    assert "burn_intelligence/v1" in overview
    assert "same exact verified X1 mint" in overview
    assert "1h/24h/7d/30d Burn Intelligence" in overview
    assert "Do not claim lifetime burn" in overview
    assert "Proof Score separate from risk" in overview
    assert "execution_authorized=false" in overview


def test_history_request_keeps_compact_terminal_sections() -> None:
    history = history_request("AGI")

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
        "rank",
        "burn_intelligence",
        "instant_x1_scan",
    ]
    assert not any(
        warning.startswith("planner_operation_rejected_for_rank_objective")
        for warning in plan["warnings"]
    )


def test_previous_terminal_full_wording_still_maps_to_full_assessment() -> None:
    objective = "On X1, produce the most complete current assessment possible for XNT."
    assert recommendation_intent(objective) == "full_assessment"


def test_risk_request_routes_to_freshness_aware_runtime() -> None:
    request = risk_request("AGI")

    assert "operation='risk_check'" in request
    assert "field-scoped current-market freshness" in request
    assert "price, liquidity, rolling 24h volume" in request
    assert "preserve WARN/PARTIAL" in request
    assert "numeric risk score" in request
    assert "UNAVAILABLE" in request
    assert "Proof Score into risk" in request
    assert "execution_authorized=false" in request


def test_automatic_status_summary_explains_field_freshness_warnings() -> None:
    report = {
        "investigations": [
            {
                "operation": "risk_check",
                "cmis_status": "partial",
                "risk_help": {
                    "recommendation": {
                        "value": "WARN",
                        "reasons": [
                            "Liquidity freshness is not verified.",
                            "Rolling 24h volume freshness is not verified.",
                            "Rolling 24h transaction freshness is not verified.",
                        ],
                        "flags": [
                            "liquidity_freshness_unverified",
                            "volume_24h_freshness_unverified",
                            "transactions_24h_freshness_unverified",
                        ],
                    }
                },
                "evidence_context": {},
                "warnings": [],
                "errors": [],
            }
        ]
    }

    summary = automatic_status_summary(report)

    assert summary is not None
    assert "Risk: [WARN]" in summary
    assert "Live market freshness: [NOT FULLY VERIFIED]" in summary
    assert "Still needs provider fact-time proof for: liquidity, 24h volume, 24h transactions." in summary
    assert "Flag:" not in summary
    assert "liquidity_freshness_unverified" not in summary
    assert "volume_24h_freshness_unverified" not in summary
    assert "transactions_24h_freshness_unverified" not in summary


def test_current_market_menu_flows_use_scan_freshness_contract() -> None:
    liquidity = liquidity_request("AGI")
    activity = activity_request("AGI")
    evidence = evidence_request("AGI")

    for request in (liquidity, activity, evidence):
        assert "operation='instant_x1_scan'" in request

    assert "liquidity provider fact-time" in liquidity
    assert "liquidity value is not automatically fresh" in liquidity
    assert "volume freshness and transaction freshness separately" in activity
    assert "field-scoped freshness" in evidence
    assert "Proof Score separate from market risk" in evidence


def test_rank_does_not_inherit_scan_freshness_without_proof() -> None:
    request = rank_request("liquidity", 10)

    assert "rank service" in request
    assert "does not inherit Instant X1 Scan field-level freshness" in request
    assert "do not call ranking values fresh" in request


def test_full_assessment_uses_scan_burn_and_rank_systemwide_composition() -> None:
    request = full_request("AGI")

    assert "one Instant X1 Scan" in request
    assert "freshness-aware risk" in request
    assert "one first-class Burn Intelligence result" in request
    assert "ranking context" in request
    assert "1h/24h/7d/30d Burn Intelligence" in request
    assert "never relabel bounded observed burn" in request
    assert "all available history / entire history" in request
    assert "execution_authorized=false" in request


def test_pretrade_request_preserves_analysis_only_boundary() -> None:
    request = pretrade_request("AGI", "BUY", 2500)

    assert "BUY $2500.00" in request
    assert "pre_trade_check" in request
    assert "freshness-aware CMIS risk_check" in request
    assert "price/liquidity/24h-volume/24h-transaction freshness warnings" in request
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


def test_every_x1_chat_request_visibly_routes_through_x1_scout() -> None:
    requests = [
        overview_request("XNT"),
        compare_request("XNT", "ANL"),
        risk_request("XNT"),
        tokenomics_request("XNT"),
        liquidity_request("XNT"),
        history_request("XNT"),
        activity_request("XNT"),
        concentration_request("XNT", "ie_test"),
        rank_request("liquidity", 10),
        pretrade_request("XNT", "BUY", 100),
        evidence_request("XNT"),
        full_request("XNT"),
        what_changed_request("XNT"),
    ]

    for request in requests:
        assert "X1 Scout" in request
        assert "CMIS" in request


def test_human_roberta_presentation_policy_is_systemwide() -> None:
    assert "WHAT ROBERTA STILL NEEDS" in HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "no more than three prioritized" in HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "raw snake_case limitation codes" in HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "Round DISPLAY values" in HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "Do not repeat field-level freshness problems inside RISK" in HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "Show an unavailable numeric risk score only when" in HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "Use EVIDENCE QUALITY instead of a raw Evidence Status dump" in HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "BOTTOM LINE" in HUMAN_ROBERTA_PRESENTATION_POLICY

    requests = [
        overview_request("XNT"),
        compare_request("XNT", "AGI"),
        risk_request("XNT"),
        tokenomics_request("XNT"),
        liquidity_request("XNT"),
        history_request("XNT"),
        activity_request("XNT"),
        concentration_request("XNT", "ie_test"),
        rank_request("liquidity", 10),
        pretrade_request("XNT", "BUY", 100),
        evidence_request("XNT"),
        full_request("XNT"),
        burn_request("XNT"),
        discovery_request("XNT"),
        what_changed_request("XNT"),
    ]

    for request in requests:
        assert HUMAN_ROBERTA_PRESENTATION_POLICY in request


def test_single_asset_human_output_replaces_raw_key_limitations_heading() -> None:
    request = overview_request("XNT")

    assert "WHAT ROBERTA STILL NEEDS" in request
    assert "KEY LIMITATIONS for missing" not in request
    assert "Do not expose raw snake_case limitation codes" in request
    assert "Group related freshness gaps into one LIVE MARKET FRESHNESS statement" in request


def test_burn_request_uses_first_class_cmis_service() -> None:
    request = burn_request("AGI")
    assert "CMIS burn_intelligence service" in request
    assert "burn_intelligence/v1" in request


def test_discovery_request_preserves_verified_history_boundary() -> None:
    request = discovery_request("AGI")
    assert "operation='discovery_intelligence'" in request
    assert "discovery_intelligence/v1" in request
    assert "not token launch time" in request
    assert "execution_authorized=false" in request


def test_what_changed_request_is_first_class_and_fail_closed() -> None:
    request = what_changed_request("XNT")
    assert "operation='what_changed'" in request
    assert "Instant X1 Scan" in request
    assert "Burn Intelligence" in request
    assert "Discovery Intelligence" in request
    assert "do not calculate new deltas in ROBERTA" in request
    assert "do not infer causality" in request.lower()
    assert "execution_authorized=false" in request
