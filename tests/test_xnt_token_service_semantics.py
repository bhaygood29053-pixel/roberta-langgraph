from __future__ import annotations

from roberta.x1_scout.instant_scan_product_ux import (
    build_instant_x1_scan_product_view,
    render_instant_x1_scan_product_text,
)


def _report() -> dict:
    return {
        "source": {"service": "cmis", "operation": "instant_x1_scan"},
        "chain": "x1",
        "cmis_status": "partial",
        "requested_asset": "XNT",
        "observed_at": 1000,
        "observed_at_iso": "2026-09-11T13:47:00Z",
        "observed_at_display": "2026-09-11 13:47 UTC",
        "evidence_context": {},
        "warnings": [],
        "errors": [],
        "instant_x1_scan_presentation": {
            "contract_version": "instant_x1_scan/v6",
            "read_only": True,
            "execution_authorized": False,
            "limitations": [],
            "sections": {
                "identity": {
                    "status": "ok",
                    "verified": True,
                    "symbol": "XNT",
                    "name": "X1 Native Token",
                    "identity_key": "native:xnt",
                },
                "market": {
                    "status": "partial",
                    "price_usd": 0.341,
                    "price_verified": True,
                    "liquidity_usd": 80900,
                    "liquidity_verified": True,
                    "volume_24h_usd": 9900,
                    "volume_24h_verified": True,
                    "transactions_24h": 5003,
                    "transactions_24h_verified": True,
                    "freshness": {
                        "freshness_state": "PARTIAL",
                        "fields": {
                            "price_usd": {"freshness_verified": True},
                            "liquidity_usd": {"freshness_verified": True},
                            "volume_24h_usd": {"freshness_verified": False},
                            "transactions_24h": {"freshness_verified": False},
                        },
                        "completion_attempt": {
                            "state": "PARTIAL",
                            "attempted": True,
                            "reason": "runtime_freshness_producer_returned_failures",
                            "producer_failures": [
                                "rolling_activity_production_failed"
                            ],
                            "execution_authorized": False,
                        },
                    },
                },
                "tokenomics": {
                    "status": "ok",
                    "current_total_supply": 1_070_000_000,
                    "supply_verified": True,
                },
                "holder_concentration": {
                    "holders": None,
                    "holders_verified": False,
                    "holders_state": "not_applicable",
                    "holders_reason": (
                        "xnt_is_native_currency_not_spl_holder_population"
                    ),
                    "holder_semantics": {
                        "state": "not_applicable",
                        "counted_entity": "native_xnt_account_address",
                        "token_holder_count_applicable": False,
                    },
                    "top_account_concentration": {
                        "state": "unavailable",
                        "verified": False,
                        "value": None,
                        "reason": "native_xnt_account_concentration_not_verified",
                        "basis": (
                            "top_20_native_xnt_accounts_percent_of_circulating_xnt"
                        ),
                        "counted_entity": "native_xnt_account_address",
                    },
                    "native_account_concentration": {
                        "verified": False,
                        "holder_count_state": "not_applicable",
                    },
                },
                "history": {"status": "partial"},
                "risk": {
                    "status": "warn",
                    "recommendation": "WARN",
                    "score": None,
                    "score_verified": False,
                    "reasons": [],
                    "flags": [],
                },
                "evidence": {
                    "proof_score_separate_from_risk": True,
                    "component_statuses": {},
                },
            },
        },
    }


def test_xnt_holder_count_is_not_reframed_as_missing():
    view = build_instant_x1_scan_product_view(_report())
    assert view is not None

    holders = view["holder_concentration"]
    assert holders["holder_count_applicable"] is False
    assert holders["holders_state"] == "not_applicable"
    assert (
        holders["top_account_concentration"]["reason"]
        == "native_xnt_account_concentration_not_verified"
    )

    text = render_instant_x1_scan_product_text(view)
    assert "Holder count: NOT APPLICABLE — XNT is the native X1 currency" in text
    assert "Native XNT distribution is evaluated with native account concentration" in text
    assert (
        "Top-account concentration: NOT VERIFIED — "
        "native_xnt_account_concentration_not_verified"
    ) in text
    assert "Holder count: unknown" not in text


def test_token_text_surfaces_bounded_freshness_completion_result():
    view = build_instant_x1_scan_product_view(_report())
    assert view is not None

    completion = view["market"]["freshness_completion"]
    assert completion["state"] == "PARTIAL"
    assert completion["attempted"] is True

    text = render_instant_x1_scan_product_text(view)
    assert "Freshness evidence completion: PARTIAL" in text
    assert "Freshness completion attempt: bounded wait performed before answer" in text
    assert "runtime_freshness_producer_returned_failures" in text
    assert "rolling_activity_production_failed" in text
