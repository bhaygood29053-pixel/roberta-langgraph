from __future__ import annotations

from copy import deepcopy

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.instant_scan_product_ux import (
    PRODUCT_VIEW_CONTRACT,
    build_instant_x1_scan_product_view,
    render_instant_x1_scan_product_text,
)


def _scan_report() -> dict[str, object]:
    limitations = [
        "missing_or_unverified_fields_remain_unknown",
        "holder_count_requires_existing_verified_holder_semantics",
        "current_top_account_concentration_not_promoted_in_v2",
        "history_may_include_bounded_verified_provider_price_backfill",
        "provider_price_backfill_is_price_only",
        "provider_source_independence_not_verified",
        "provider_archive_completeness_not_verified",
        "history_does_not_imply_complete_asset_lifetime",
        "continuous_coverage_requires_separate_archive_completeness_proof",
        "proof_score_does_not_modify_market_facts_or_risk",
        "risk_score_remains_unavailable_until_separately_calibrated",
        "execution_authorized_false",
    ]
    return {
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": "AGI",
        "cmis_status": "partial",
        "observed_at": 1_777_777_777,
        "observed_at_iso": "2026-05-03T03:09:37Z",
        "observed_at_display": "2026-05-03 03:09:37 UTC",
        "source": {"service": "cmis", "operation": "instant_x1_scan"},
        "evidence_context": {
            "proof_score": {"score": 0.75, "strength": "MODERATE"},
            "risk_separate_from_proof": True,
        },
        "warnings": [
            {
                "code": "instant_x1_scan_holder_count_unverified",
                "message": "Verified holder count is unavailable.",
            }
        ],
        "errors": [],
        "instant_x1_scan_presentation": {
            "contract_version": "instant_x1_scan/v2",
            "read_only": True,
            "sections": {
                "identity": {
                    "status": "ok",
                    "verified": True,
                    "symbol": "AGI",
                    "name": "AGI",
                    "mint": "mint-agi",
                    "resolved_by": "exact_mint",
                    "match_quality": "exact",
                },
                "market": {
                    "status": "partial",
                    "price_usd": 1.25,
                    "price_verified": True,
                    "liquidity_usd": None,
                    "liquidity_verified": False,
                    "volume_24h_usd": 4200.0,
                    "volume_24h_verified": True,
                    "transactions_24h": 88,
                    "transactions_24h_verified": True,
                    "#LPs": 2,
                },
                "tokenomics": {
                    "status": "partial",
                    "current_total_supply": 1_000_000,
                    "supply_verified": True,
                    "mint_authority": "authority-1",
                    "mint_authority_verified": False,
                    "freeze_authority": None,
                    "freeze_authority_verified": True,
                    "circulating_supply": None,
                    "circulating_supply_verified": False,
                    "future_minting_possible": None,
                },
                "holder_concentration": {
                    "holders": None,
                    "holders_verified": False,
                    "holders_reported": 321,
                    "holders_observed": 300,
                    "holder_semantics": {
                        "verified": False,
                        "scope": "provider_reported",
                    },
                    "top_account_concentration": {
                        "state": "unavailable",
                        "verified": False,
                        "value": None,
                        "reason": "current_concentration_not_promoted_for_instant_x1_scan_v1",
                    },
                },
                "history": {
                    "status": "partial",
                    "coverage_scope": "cmis_stored_verified_observations",
                    "first_verified_observed_at": 1_700_000_000,
                    "last_verified_observed_at": 1_777_777_777,
                    "full_asset_lifetime_verified": False,
                    "continuous_coverage_verified": False,
                    "metrics": {
                        "price": {
                            "status": "partial",
                            "total_change_pct": 12.5,
                        }
                    },
                },
                "risk": {
                    "status": "ok",
                    "recommendation": "WARN",
                    "flags": ["TEST_FLAG"],
                    "reasons": ["deterministic reason"],
                    "score": None,
                    "score_verified": False,
                    "score_reason": "not_calibrated",
                    "execution_authorized": False,
                },
                "evidence": {
                    "component_statuses": {
                        "asset_lookup": "ok",
                        "market_report": "partial",
                    },
                    "component_source_count": 3,
                    "proof_score_separate_from_risk": True,
                    "runtime_evidence_receipt_post_processing_only": True,
                },
            },
            "limitations": limitations,
            "execution_authorized": False,
        },
    }


def test_product_view_projects_values_without_recomputing_authority() -> None:
    report = _scan_report()

    view = build_instant_x1_scan_product_view(report)

    assert view is not None
    assert view["contract_version"] == PRODUCT_VIEW_CONTRACT
    assert view["status"] == "partial"
    assert view["market"]["price_usd"] == {"value": 1.25, "verified": True}
    assert view["market"]["liquidity_usd"] == {"value": None, "verified": False}
    assert view["tokenomics"]["mint_authority"] == {
        "value": "authority-1",
        "verified": False,
    }
    assert view["tokenomics"]["mint_authority_state"] is None
    assert view["tokenomics"]["freeze_authority_state"] is None
    assert view["holder_concentration"]["holders"] == {
        "value": None,
        "verified": False,
    }
    assert view["holder_concentration"]["holders_reported"] == 321
    assert view["holder_concentration"]["top_account_concentration"] == {
        "state": "unavailable",
        "verified": False,
        "value": None,
        "reason": "current_concentration_not_promoted_for_instant_x1_scan_v1",
    }
    assert view["history"]["metrics"]["price"]["total_change_pct"] == 12.5
    assert view["risk"]["recommendation"] == "WARN"
    assert view["risk"]["score"] is None
    assert view["evidence"]["evidence_context"] == report["evidence_context"]
    assert view["evidence"]["proof_score_separate_from_risk"] is True
    assert view["limitations"] == report["instant_x1_scan_presentation"]["limitations"]
    assert view["warnings"] == report["warnings"]
    assert view["execution_authorized"] is False


def test_product_view_preserves_native_authority_not_applicable_states() -> None:
    report = _scan_report()
    tokenomics = report["instant_x1_scan_presentation"]["sections"]["tokenomics"]
    tokenomics.update(
        {
            "scope": "native_network",
            "asset_type": "native",
            "mint_authority": None,
            "mint_authority_verified": True,
            "mint_authority_state": "not_applicable",
            "freeze_authority": None,
            "freeze_authority_verified": True,
            "freeze_authority_state": "not_applicable",
        }
    )

    view = build_instant_x1_scan_product_view(report)

    assert view is not None
    assert view["tokenomics"]["scope"] == "native_network"
    assert view["tokenomics"]["asset_type"] == "native"
    assert view["tokenomics"]["mint_authority_state"] == "not_applicable"
    assert view["tokenomics"]["freeze_authority_state"] == "not_applicable"


def test_product_text_renders_unknowns_and_keeps_proof_separate_from_risk() -> None:
    view = build_instant_x1_scan_product_view(_scan_report())
    assert view is not None

    rendered = render_instant_x1_scan_product_text(view)

    assert "Instant X1 Scan — AGI" in rendered
    assert "Identity: verified" in rendered
    assert "Liquidity USD: unknown" in rendered
    assert "Mint Authority: authority-1 (unverified)" in rendered
    assert "Holders: unknown" in rendered
    assert "Top-account concentration: unknown" in rendered
    assert "Supported pair lifetime verified: False" in rendered
    assert "Pair price continuity verified: False" in rendered
    assert "Provider supported range complete: False" in rendered
    assert "Historical quote-to-USD equivalence verified: False" in rendered
    assert "Full USD lifetime verified: False" in rendered
    assert "Legacy full asset lifetime verified: False" in rendered
    assert "Verified history metrics:" in rendered
    assert "- Price status: partial" in rendered
    assert "  total change pct: 12.5" in rendered
    assert "Recommendation: WARN" in rendered
    assert "Risk score: unavailable/unverified" in rendered
    assert "Risk reasons:" in rendered
    assert "- deterministic reason" in rendered
    assert "Risk flags:" in rendered
    assert "- TEST_FLAG" in rendered
    assert "Proof Score is separate from risk: True" in rendered
    assert "- current_top_account_concentration_not_promoted_in_v2" in rendered
    assert "execution_authorized_false" in rendered
    assert "Holders: 0" not in rendered
    assert "Top-account concentration: 0" not in rendered


def test_product_view_suppresses_failed_scan_status_even_with_presentation() -> None:
    report = _scan_report()
    report["cmis_status"] = "unavailable"

    assert build_instant_x1_scan_product_view(report) is None


def test_product_text_uses_requested_asset_when_identity_is_unverified() -> None:
    report = _scan_report()
    report["requested_asset"] = "user-supplied-alias"
    report["instant_x1_scan_presentation"]["sections"]["identity"]["verified"] = False
    report["instant_x1_scan_presentation"]["sections"]["identity"]["symbol"] = "AGI?"

    view = build_instant_x1_scan_product_view(report)
    assert view is not None
    rendered = render_instant_x1_scan_product_text(view)

    assert "Instant X1 Scan — user-supplied-alias" in rendered
    assert "Identity: unverified (reported descriptor: AGI?)" in rendered
    assert "Instant X1 Scan — AGI?" not in rendered


def test_product_text_renders_preserved_partial_scan_errors() -> None:
    report = _scan_report()
    report["errors"] = [{
        "code": "component_partial_failure",
        "message": "A component could not be verified.",
    }]

    view = build_instant_x1_scan_product_view(report)
    assert view is not None
    rendered = render_instant_x1_scan_product_text(view)

    assert "Errors" in rendered
    assert (
        "- component_partial_failure: A component could not be verified."
        in rendered
    )


def test_product_view_does_not_apply_to_non_scan_report() -> None:
    report = _scan_report()
    report["source"] = {"service": "cmis", "operation": "risk_check"}

    assert build_instant_x1_scan_product_view(report) is None


def test_product_view_rejects_wrong_chain_or_non_cmis_source() -> None:
    wrong_chain = _scan_report()
    wrong_chain["chain"] = "solana"
    assert build_instant_x1_scan_product_view(wrong_chain) is None

    wrong_source = _scan_report()
    wrong_source["source"] = {
        "service": "provider",
        "operation": "instant_x1_scan",
    }
    assert build_instant_x1_scan_product_view(wrong_source) is None


def test_product_view_rejects_stale_or_non_read_only_scan_presentation() -> None:
    stale = _scan_report()
    stale["instant_x1_scan_presentation"]["contract_version"] = "instant_x1_scan/v0"
    assert build_instant_x1_scan_product_view(stale) is None

    writable = _scan_report()
    writable["instant_x1_scan_presentation"]["read_only"] = False
    assert build_instant_x1_scan_product_view(writable) is None


def test_product_view_rejects_any_execution_authority_drift() -> None:
    report = _scan_report()
    report["instant_x1_scan_presentation"]["execution_authorized"] = True

    assert build_instant_x1_scan_product_view(report) is None


def test_x1_scout_attaches_product_view_and_preserves_raw_scan_findings() -> None:
    cmis = MockCMISClient()
    result = build_x1_scout_graph(cmis).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "Instant X1 scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    raw_before = deepcopy(report["findings"]["data"])

    assert report["source"]["operation"] == "instant_x1_scan"
    assert report["instant_x1_scan_product_view"]["execution_authorized"] is False
    assert "Instant X1 Scan" in report["instant_x1_scan_product_text"]
    assert "Holders: unknown" in report["instant_x1_scan_product_text"]
    assert report["findings"]["data"] == raw_before
    assert [call["operation"] for call in cmis.calls] == ["instant_x1_scan"]


def test_non_scan_scout_report_does_not_gain_instant_scan_product_fields() -> None:
    cmis = MockCMISClient()
    result = build_x1_scout_graph(cmis).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["source"]["operation"] == "risk_check"
    assert "instant_x1_scan_product_view" not in report
    assert "instant_x1_scan_product_text" not in report


def test_product_text_renders_verified_pair_lifetime_separately_from_usd():
    report = _scan_report()
    history = report["instant_x1_scan_presentation"]["sections"]["history"]
    history.update(
        {
            "price_coverage_scope": "full_supported_pair_lifetime",
            "full_supported_pair_lifetime_verified": True,
            "continuous_pair_price_coverage_verified": True,
            "provider_range_complete_verified": True,
            "historical_quote_usd_equivalence_verified": False,
            "full_usd_lifetime_verified": False,
            "full_asset_lifetime_verified": False,
            "continuous_coverage_verified": False,
        }
    )

    view = build_instant_x1_scan_product_view(report)
    assert view is not None
    rendered = render_instant_x1_scan_product_text(view)

    assert "Supported pair lifetime verified: True" in rendered
    assert "Pair price continuity verified: True" in rendered
    assert "Provider supported range complete: True" in rendered
    assert "Historical quote-to-USD equivalence verified: False" in rendered
    assert "Full USD lifetime verified: False" in rendered
    assert "Legacy full asset lifetime verified: False" in rendered
