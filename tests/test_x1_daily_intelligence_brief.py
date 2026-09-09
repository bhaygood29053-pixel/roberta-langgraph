from __future__ import annotations

from copy import deepcopy

import pytest

from roberta.x1_scout.daily_intelligence_brief import (
    CMIS_BRIEF_INPUTS_CONTRACT,
    ROBERTA_DAILY_BRIEF_CLAIM_INTEGRITY_CONTRACT,
    ROBERTA_DAILY_BRIEF_DECISION_INPUT_CONTRACT,
    X1_DAILY_BRIEF_CONTRACT,
    X1DailyIntelligenceBriefContractError,
    build_daily_brief_claim_integrity,
    build_daily_brief_decision_input,
    build_x1_daily_intelligence_brief,
    render_x1_daily_intelligence_brief_text,
)


MINT = "7SXmUpcBGSAwW5LmtzQVF9jHswZ7xzmdKqWa4nDgL3ER"


def _item(*, service, contract, priority, event, facts, fact_time):
    return {
        "brief_item_id": f"xbi_{event}",
        "subject_mint": MINT,
        "source_service": service,
        "source_contract_version": contract,
        "priority": priority,
        "priority_rank": {
            "persistent_warning": 20,
            "large_verified_activity": 30,
            "new_verified_observation": 40,
            "informational": 60,
        }[priority],
        "fact_time": fact_time,
        "event_key": event,
        "facts": facts,
        "source_status": "ok" if service != "discovery_intelligence" else "partial",
        "source_observed_at": fact_time,
        "source_freshness": {"state": "VERIFIED"},
        "source_confidence": {"basis": "accepted"},
        "source_sources": [{"source": "CMIS"}],
        "source_warnings": [],
        "source_errors": [],
        "risk": None,
        "proof_strength_separate_from_risk": True,
        "priority_is_risk_severity": False,
        "complete_x1_ecosystem_coverage_verified": False,
        "execution_authorized": False,
    }


def source():
    warning = _item(
        service="concentration_warning_intelligence",
        contract="concentration_warning_intelligence/v1",
        priority="persistent_warning",
        event="warning",
        fact_time="2026-09-09T08:00:00Z",
        facts={
            "warning_id": "cw_test",
            "warning_level": "WATCH",
            "warning_active": True,
            "warning_level_is_risk_severity": False,
            "policy": {"metric": "absolute_delta_bps"},
            "persistence": {"mode": "two_distinct_compatible_observations"},
            "evidence": {"receipt_ids": ["er_test"]},
            "limitations": ["not_risk_severity"],
            "risk_interpretation": None,
        },
    )
    trade = _item(
        service="large_trade_discovery",
        contract="large_trade_discovery/v1",
        priority="large_verified_activity",
        event="trade",
        fact_time="2026-09-09T06:00:00Z",
        facts={
            "transaction_signature": "sig-1",
            "slot": 100,
            "pool_address": "pool-1",
            "direction": "BUY",
            "asset_amount": "1000",
            "quote_mint": "quote",
            "quote_amount": "100",
            "verified_usd_notional": "500",
            "usd_notional_verified": True,
            "wallet_address": "wallet-1",
            "wallet_attribution_verified": True,
            "real_world_wallet_owner_verified": False,
            "trade_price_impact_evidence_id": None,
            "ranking_scope": "bounded",
            "requested_window": {"duration_seconds": "86400"},
            "evidence_boundaries": {
                "global_x1_dex_trade_ranking_authorized": False,
                "wallet_owner_identity_inference_authorized": False,
                "whale_insider_manipulator_label_authorized": False,
                "intent_inference_authorized": False,
                "coordinated_wallet_inference_authorized": False,
                "whole_market_price_impact_claim_authorized": False,
                "volume_causality_claim_authorized": False,
                "automatic_risk_conclusion_authorized": False,
                "trade_recommendation_authorized": False,
            },
        },
    )
    discovery = _item(
        service="discovery_intelligence",
        contract="discovery_intelligence/v1",
        priority="new_verified_observation",
        event="discovery",
        fact_time="2026-09-09T03:00:00Z",
        facts={
            "observation_kind": "market_verified",
            "verification_state": "verified",
            "source_id": "xdex",
            "first_verified_observation": {"fact_time_unix": 1},
            "most_recent_verified_observation": {"fact_time_unix": 2},
            "verified_observation_count": 2,
            "coverage": {
                "continuous_coverage_verified": False,
                "archive_completeness_verified": False,
            },
            "token_launch_time": None,
            "token_launch_time_verified": False,
        },
    )
    items = [warning, trade, discovery]
    return {
        "brief_inputs_id": "xib_test",
        "contract_version": CMIS_BRIEF_INPUTS_CONTRACT,
        "chain": "x1",
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "subjects": [MINT],
        "requested_services": [
            "concentration_warning_intelligence",
            "discovery_intelligence",
            "large_trade_discovery",
        ],
        "window": {
            "start": "2026-09-09T00:00:00Z",
            "end": "2026-09-10T00:00:00Z",
            "end_exclusive": True,
            "duration_seconds": 86400,
        },
        "items": items,
        "component_evaluations": [],
        "coverage": {
            "requested_subject_count": 1,
            "resolved_subject_count": 1,
            "requested_service_count": 3,
            "input_service_classes_requested": [
                "concentration_warning_intelligence",
                "discovery_intelligence",
                "large_trade_discovery",
            ],
            "input_service_classes_evaluated": [
                "concentration_warning_intelligence",
                "discovery_intelligence",
                "large_trade_discovery",
            ],
            "partial_service_classes": ["discovery_intelligence"],
            "unavailable_service_classes": [],
            "error_or_ambiguous_service_classes": [],
            "component_response_matrix_complete": True,
            "duplicate_exact_component_responses_collapsed": 0,
            "included_item_count": 3,
            "outside_window_item_count": 0,
            "window_start": "2026-09-09T00:00:00Z",
            "window_end": "2026-09-10T00:00:00Z",
            "window_end_exclusive": True,
            "earliest_included_fact_time": "2026-09-09T03:00:00Z",
            "latest_included_fact_time": "2026-09-09T08:00:00Z",
            "complete_x1_ecosystem_coverage_verified": False,
        },
        "priority_is_risk_severity": False,
        "proof_score_separate_from_risk": True,
        "missing_evidence_zero_filled": False,
        "complete_x1_ecosystem_coverage_verified": False,
        "execution_authorized": False,
    }


def test_projects_typed_daily_brief_without_recomputation():
    upstream = source()
    before = deepcopy(upstream)

    brief = build_x1_daily_intelligence_brief(upstream)

    assert brief["contract_version"] == X1_DAILY_BRIEF_CONTRACT
    assert brief["product"] == "x1_daily_intelligence_brief"
    assert brief["chain"] == "x1"
    assert brief["status"] == "partial"
    assert brief["what_changed"] == upstream["items"]
    assert brief["runtime_reliance_authorized"] is False
    assert brief["public_runtime_dependency"] == "cmis#637"
    assert brief["complete_x1_ecosystem_coverage_verified"] is False
    assert brief["proof_score_separate_from_risk"] is True
    assert brief["priority_is_risk_severity"] is False
    assert brief["execution_authorized"] is False
    assert upstream == before


def test_builds_typed_decision_input_and_claim_integrity_pass():
    brief = build_x1_daily_intelligence_brief(source())
    decision = build_daily_brief_decision_input(brief)
    integrity = build_daily_brief_claim_integrity(decision)

    assert (
        decision["contract_version"]
        == ROBERTA_DAILY_BRIEF_DECISION_INPUT_CONTRACT
    )
    assert decision["facts_authority"] == "chain_scout_cmis"
    assert decision["judgment_authority"] == "roberta"
    assert decision["decision_policy_applied"] is False
    assert decision["claim_integrity_required"] is True
    assert decision["runtime_reliance_authorized"] is False
    assert decision["complete_x1_ecosystem_coverage_verified"] is False
    assert decision["execution_authorized"] is False

    assert (
        integrity["contract_version"]
        == ROBERTA_DAILY_BRIEF_CLAIM_INTEGRITY_CONTRACT
    )
    assert integrity["status"] == "PASS"
    assert integrity["provider_truth_certified"] is False
    assert integrity["checks"]["whole_x1_coverage_not_claimed"] is True
    assert integrity["checks"]["wallet_ownership_not_inferred"] is True
    assert integrity["checks"]["causality_not_inferred"] is True
    assert (
        integrity["checks"]["runtime_reliance_not_authorized_before_cmis_637"]
        is True
    )
    assert integrity["execution_authorized"] is False


def test_presentation_basis_is_explicitly_not_new_fact_or_risk():
    brief = build_x1_daily_intelligence_brief(source())

    assert len(brief["why_it_matters_basis"]) == 3
    for row in brief["why_it_matters_basis"]:
        assert row["basis_type"] == "roberta_presentation_basis"
        assert row["new_chain_fact_added"] is False
        assert row["risk_conclusion_added"] is False
        assert row["causality_added"] is False


def test_large_trade_truth_boundary_upgrade_fails_closed():
    upstream = source()
    upstream["items"][1]["facts"]["evidence_boundaries"][
        "whale_insider_manipulator_label_authorized"
    ] = True

    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="whale_insider_manipulator_label_authorized",
    ):
        build_x1_daily_intelligence_brief(upstream)


def test_wallet_owner_promotion_fails_closed():
    upstream = source()
    upstream["items"][1]["facts"]["real_world_wallet_owner_verified"] = True

    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="real-world wallet ownership",
    ):
        build_x1_daily_intelligence_brief(upstream)


def test_warning_level_cannot_be_promoted_to_risk_severity():
    upstream = source()
    upstream["items"][0]["facts"]["warning_level_is_risk_severity"] = True

    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="warning_level_is_risk_severity",
    ):
        build_x1_daily_intelligence_brief(upstream)


def test_discovery_first_observation_cannot_be_promoted_to_launch():
    upstream = source()
    upstream["items"][2]["facts"]["token_launch_time"] = 1
    upstream["items"][2]["facts"]["token_launch_time_verified"] = True

    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="launch time",
    ):
        build_x1_daily_intelligence_brief(upstream)


def test_whole_x1_coverage_claim_fails_closed():
    upstream = source()
    upstream["coverage"]["complete_x1_ecosystem_coverage_verified"] = True

    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="complete_x1_ecosystem_coverage_verified",
    ):
        build_x1_daily_intelligence_brief(upstream)


def test_coverage_scope_must_bind_exact_requested_window_and_services():
    upstream = source()
    upstream["coverage"]["window_end"] = "2026-09-10T00:00:01Z"
    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="coverage window_end",
    ):
        build_x1_daily_intelligence_brief(upstream)

    upstream = source()
    upstream["coverage"]["input_service_classes_requested"] = [
        "concentration_warning_intelligence",
        "discovery_intelligence",
    ]
    upstream["coverage"]["input_service_classes_evaluated"] = [
        "concentration_warning_intelligence",
        "discovery_intelligence",
    ]
    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="coverage service classes",
    ):
        build_x1_daily_intelligence_brief(upstream)


def test_runtime_promotion_is_not_accepted_by_foundation_tracer_bullet():
    for field in ("public_service_promoted", "scout_reliance_promoted"):
        upstream = source()
        upstream[field] = True
        with pytest.raises(
            X1DailyIntelligenceBriefContractError,
            match=field,
        ):
            build_x1_daily_intelligence_brief(upstream)


def test_execution_authority_fails_closed_at_every_layer():
    upstream = source()
    upstream["execution_authorized"] = True
    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="execution_authorized",
    ):
        build_x1_daily_intelligence_brief(upstream)

    brief = build_x1_daily_intelligence_brief(source())
    brief["execution_authorized"] = True
    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="execution_authorized",
    ):
        build_daily_brief_decision_input(brief)


def test_empty_bounded_brief_does_not_become_no_x1_activity_claim():
    upstream = source()
    upstream["items"] = []
    upstream["coverage"]["included_item_count"] = 0
    upstream["coverage"]["earliest_included_fact_time"] = None
    upstream["coverage"]["latest_included_fact_time"] = None

    brief = build_x1_daily_intelligence_brief(upstream)
    decision = build_daily_brief_decision_input(brief)
    integrity = build_daily_brief_claim_integrity(decision)
    text = render_x1_daily_intelligence_brief_text(brief)

    assert brief["what_changed"] == []
    assert brief["unknowns"]["empty_brief_means_no_activity_on_x1"] is False
    assert integrity["checks"]["empty_brief_not_promoted_to_no_x1_activity"] is True
    assert "does not mean nothing happened on X1" in text


def test_human_preview_has_five_product_sections_and_runtime_boundary():
    brief = build_x1_daily_intelligence_brief(source())
    text = render_x1_daily_intelligence_brief_text(brief)

    for heading in (
        "WHAT CHANGED",
        "WHY IT MATTERS",
        "EVIDENCE",
        "WHAT IS UNKNOWN / INCOMPLETE",
        "WHAT TO WATCH NEXT",
    ):
        assert heading in text
    assert "Live runtime reliance: NOT AUTHORIZED until CMIS #637 is accepted." in text
    assert "Execution authorized: false" in text


def test_decision_input_claim_integrity_rejects_presentation_fact_upgrade():
    decision = build_daily_brief_decision_input(
        build_x1_daily_intelligence_brief(source())
    )
    decision["presentation_basis"][0]["new_chain_fact_added"] = True

    with pytest.raises(
        X1DailyIntelligenceBriefContractError,
        match="new_chain_fact_added",
    ):
        build_daily_brief_claim_integrity(decision)
