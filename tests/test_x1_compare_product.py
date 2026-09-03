from __future__ import annotations

from copy import deepcopy

import pytest

from roberta.x1_scout.compare_product import (
    X1_COMPARE_CONTRACT,
    build_x1_compare_product_view,
    render_x1_compare_product_text,
)
from roberta.x1_scout.instant_scan_product_ux import PRODUCT_VIEW_CONTRACT


def _scan(
    symbol: str,
    *,
    price: float | None,
    price_verified: bool,
    liquidity: float | None,
    liquidity_verified: bool,
    volume: float | None,
    volume_verified: bool,
    transactions: int | None,
    transactions_verified: bool,
    holders: int | None,
    holders_verified: bool,
    holder_semantics: dict[str, object] | None,
    risk: str,
) -> dict[str, object]:
    return {
        "contract_version": PRODUCT_VIEW_CONTRACT,
        "product": "instant_x1_scan",
        "chain": "x1",
        "requested_asset": symbol,
        "status": "partial",
        "observed_at": 1_777_777_777,
        "observed_at_iso": "2026-05-03T03:09:37Z",
        "observed_at_display": "2026-05-03 03:09:37 UTC",
        "identity": {
            "status": "ok",
            "verified": True,
            "symbol": symbol,
            "name": symbol,
            "mint": f"mint-{symbol.lower()}",
        },
        "market": {
            "status": "partial",
            "price_usd": {"value": price, "verified": price_verified},
            "liquidity_usd": {
                "value": liquidity,
                "verified": liquidity_verified,
            },
            "volume_24h_usd": {"value": volume, "verified": volume_verified},
            "transactions_24h": {
                "value": transactions,
                "verified": transactions_verified,
            },
            "freshness": {
                "contract_version": "x1_current_market_freshness/v1",
                "freshness_state": "VERIFIED",
                "fields": {
                    "price_usd": {"freshness_verified": True},
                    "liquidity_usd": {"freshness_verified": True},
                    "volume_24h_usd": {"freshness_verified": True},
                    "transactions_24h": {"freshness_verified": True},
                },
            },
            "#LPs": None,
        },
        "tokenomics": {
            "status": "partial",
            "current_total_supply": {"value": None, "verified": False},
            "mint_authority": {"value": None, "verified": False},
            "freeze_authority": {"value": None, "verified": False},
            "circulating_supply": {"value": None, "verified": False},
            "future_minting_possible": None,
        },
        "holder_concentration": {
            "holders": {"value": holders, "verified": holders_verified},
            "holders_reported": holders,
            "holders_observed": holders,
            "holder_semantics": holder_semantics,
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
            "full_asset_lifetime_verified": False,
            "continuous_coverage_verified": False,
            "metrics": {},
        },
        "risk": {
            "status": "ok",
            "recommendation": risk,
            "flags": [],
            "reasons": [],
            "score": None,
            "score_verified": False,
            "score_reason": "not_calibrated",
            "execution_authorized": False,
        },
        "evidence": {
            "proof_score_separate_from_risk": True,
            "component_statuses": {},
            "component_source_count": 1,
            "evidence_context": {
                "proof_score": {"score": 0.5, "strength": "MODERATE"},
                "risk_separate_from_proof": True,
            },
        },
        "limitations": [
            "current_top_account_concentration_not_promoted_in_v1",
            "execution_authorized_false",
        ],
        "warnings": [],
        "errors": [],
        "execution_authorized": False,
    }


def _left() -> dict[str, object]:
    return _scan(
        "AAA",
        price=2.0,
        price_verified=True,
        liquidity=1000.0,
        liquidity_verified=True,
        volume=500.0,
        volume_verified=True,
        transactions=50,
        transactions_verified=True,
        holders=100,
        holders_verified=True,
        holder_semantics={"scope": "verified_unique_holders"},
        risk="WARN",
    )


def _right() -> dict[str, object]:
    return _scan(
        "BBB",
        price=1.0,
        price_verified=True,
        liquidity=2000.0,
        liquidity_verified=True,
        volume=500.0,
        volume_verified=True,
        transactions=40,
        transactions_verified=True,
        holders=80,
        holders_verified=True,
        holder_semantics={"scope": "verified_unique_holders"},
        risk="PASS",
    )


def test_compare_projects_verified_relations_without_combining_risk_or_proof() -> None:
    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=_right(),
    )

    assert view["contract_version"] == X1_COMPARE_CONTRACT
    assert view["comparison"]["price_usd"]["relation"] == "left_higher"
    assert view["comparison"]["liquidity_usd"]["relation"] == "right_higher"
    assert view["comparison"]["volume_24h_usd"]["relation"] == "equal"
    assert view["comparison"]["transactions_24h"]["relation"] == "left_higher"
    assert view["comparison"]["holders"]["relation"] == "left_higher"
    assert view["comparison"]["holders"]["semantics_match"] is True

    assert view["risk"]["left"]["recommendation"] == "WARN"
    assert view["risk"]["right"]["recommendation"] == "PASS"
    assert view["risk"]["combined_score"] is None
    assert view["risk"]["combined_recommendation"] is None

    assert view["evidence"]["combined_proof_score"] is None
    assert view["evidence"]["proof_score_separate_from_risk"] is True
    assert view["execution_authorized"] is False


def test_compare_marks_one_side_unknown_as_not_comparable_not_zero() -> None:
    right = _right()
    right["market"]["liquidity_usd"] = {"value": None, "verified": False}

    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=right,
    )

    liquidity = view["comparison"]["liquidity_usd"]
    assert liquidity["comparable"] is False
    assert liquidity["relation"] == "not_comparable"
    assert liquidity["right"] == {"value": None, "verified": False}

    rendered = render_x1_compare_product_text(view)
    assert "Liquidity USD: not comparable from verified evidence" in rendered
    assert "Liquidity USD: right higher" not in rendered


def test_compare_rejects_stale_current_metric_even_when_value_is_verified() -> None:
    right = _right()
    right["market"]["freshness"]["freshness_state"] = "PARTIAL"
    right["market"]["freshness"]["fields"]["liquidity_usd"] = {
        "freshness_verified": False,
        "reason": "liquidity_provider_fact_time_not_verified",
    }

    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=right,
    )

    liquidity = view["comparison"]["liquidity_usd"]
    assert liquidity["left"]["verified"] is True
    assert liquidity["right"]["verified"] is True
    assert liquidity["freshness_comparable"] is False
    assert liquidity["comparable"] is False
    assert liquidity["relation"] == "not_comparable"

    rendered = render_x1_compare_product_text(view)
    assert "Liquidity USD: not comparable from verified fresh evidence" in rendered


def test_compare_requires_matching_verified_holder_semantics() -> None:
    right = _right()
    right["holder_concentration"]["holder_semantics"] = {
        "scope": "provider_reported_accounts"
    }

    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=right,
    )

    holders = view["comparison"]["holders"]
    assert holders["semantics_match"] is False
    assert holders["comparable"] is False
    assert holders["relation"] == "not_comparable"


def test_compare_keeps_current_concentration_unavailable_on_both_sides() -> None:
    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=_right(),
    )

    left = view["left"]["holder_concentration"]["top_account_concentration"]
    right = view["right"]["holder_concentration"]["top_account_concentration"]
    assert left["state"] == "unavailable"
    assert left["verified"] is False
    assert left["value"] is None
    assert right["state"] == "unavailable"
    assert right["verified"] is False
    assert right["value"] is None


def test_compare_preserves_cmis_all_available_pair_history_without_recomputing() -> None:
    pair_history = {
        "service": "historical_compare",
        "chain": "x1",
        "status": "partial",
        "asset": {"symbol": "AAA", "mint": "mint-aaa"},
        "data": {
            "mode": "all_available_pair",
            "asset": {"symbol": "AAA", "mint": "mint-aaa"},
            "compare_asset": {"symbol": "BBB", "mint": "mint-bbb"},
            "overlap_start": 1_700_000_000,
            "overlap_end": 1_710_000_000,
            "comparison": {
                "price": {
                    "left_total_change_pct": 12.0,
                    "right_total_change_pct": 4.0,
                }
            },
            "full_asset_lifetime_verified": False,
            "continuous_coverage_verified": False,
        },
        "risk": None,
        "confidence": {"complete": False},
        "sources": [{"source": "cmis_history"}],
        "observed_at": 1_777_777_777,
        "warnings": [{"code": "PARTIAL_HISTORY"}],
        "errors": [],
        "evidence_receipt": {"receipt_id": "er_test"},
        "proof_score": {"score": 0.8, "strength": "STRONG"},
    }

    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=_right(),
        pair_history=pair_history,
    )

    assert view["pair_history"]["data"] == pair_history["data"]
    assert view["pair_history"]["proof_score"] == pair_history["proof_score"]
    assert (
        view["pair_history"]["data"]["full_asset_lifetime_verified"]
        is False
    )
    assert (
        view["pair_history"]["data"]["continuous_coverage_verified"]
        is False
    )


def test_compare_rejects_non_pair_history_mode() -> None:
    pair_history = {
        "service": "historical_compare",
        "chain": "x1",
        "status": "partial",
        "data": {
            "mode": "all_available",
            "asset": {"symbol": "AAA", "mint": "mint-aaa"},
            "compare_asset": {"symbol": "BBB", "mint": "mint-bbb"},
        },
        "confidence": {},
        "sources": [],
        "warnings": [],
        "errors": [],
    }

    with pytest.raises(ValueError, match="all_available_pair"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=_right(),
            pair_history=pair_history,
        )


def test_compare_rejects_explicit_non_pair_mode_even_when_history_unavailable() -> None:
    pair_history = {
        "service": "historical_compare",
        "chain": "x1",
        "status": "unavailable",
        "asset": {},
        "data": {"mode": "window"},
        "risk": None,
        "confidence": {},
        "sources": [],
        "observed_at": None,
        "warnings": [{"code": "history_unavailable"}],
        "errors": [],
    }

    with pytest.raises(ValueError, match="all_available_pair"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=_right(),
            pair_history=pair_history,
        )


def test_compare_allows_data_free_unavailable_pair_history() -> None:
    pair_history = {
        "service": "historical_compare",
        "chain": "x1",
        "status": "unavailable",
        "asset": {},
        "data": {},
        "risk": None,
        "confidence": {},
        "sources": [],
        "observed_at": None,
        "warnings": [{"code": "history_unavailable"}],
        "errors": [],
    }

    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=_right(),
        pair_history=pair_history,
    )

    assert view["pair_history"]["status"] == "unavailable"
    assert view["pair_history"]["data"] == {}


def test_compare_requires_two_distinct_explicit_assets() -> None:
    with pytest.raises(ValueError, match="distinct"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="aaa",
            left_scan=_left(),
            right_scan=_right(),
        )


def test_compare_rejects_distinct_aliases_that_resolve_to_same_verified_mint() -> None:
    right = _right()
    right["requested_asset"] = "mint-aaa"
    right["identity"]["mint"] = "mint-aaa"
    right["identity"]["verified"] = True

    with pytest.raises(ValueError, match="same verified asset mint"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="mint-aaa",
            left_scan=_left(),
            right_scan=right,
        )


def test_compare_rejects_pair_history_for_different_asset_pair() -> None:
    pair_history = {
        "service": "historical_compare",
        "chain": "x1",
        "status": "partial",
        "asset": {"symbol": "CCC", "mint": "mint-ccc"},
        "data": {
            "mode": "all_available_pair",
            "asset": {"symbol": "CCC", "mint": "mint-ccc"},
            "compare_asset": {"symbol": "DDD", "mint": "mint-ddd"},
        },
        "risk": None,
        "confidence": {},
        "sources": [],
        "observed_at": 1_777_777_777,
        "warnings": [],
        "errors": [],
    }

    with pytest.raises(ValueError, match="primary asset"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=_right(),
            pair_history=pair_history,
        )


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
def test_compare_treats_nonfinite_verified_numbers_as_not_comparable(
    bad_value: float,
) -> None:
    right = _right()
    right["market"]["price_usd"] = {"value": bad_value, "verified": True}

    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=right,
    )

    price = view["comparison"]["price_usd"]
    assert price["comparable"] is False
    assert price["relation"] == "not_comparable"


def test_compare_accepts_repository_cmis_pair_history_response_shape() -> None:
    pair_history = {
        "service": "historical_compare",
        "chain": "x1",
        "status": "partial",
        "asset": {"symbol": "AAA"},
        "data": {
            "mode": "all_available_pair",
            "compare_asset_request": "BBB",
            "primary_profile": {
                "full_asset_lifetime_verified": False,
                "continuous_coverage_verified": False,
            },
            "secondary_profile": {
                "full_asset_lifetime_verified": False,
                "continuous_coverage_verified": False,
            },
        },
        "risk": None,
        "confidence": {},
        "sources": [],
        "observed_at": 1_777_777_777,
        "warnings": [],
        "errors": [],
    }

    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=_right(),
        pair_history=pair_history,
    )

    assert view["pair_history"]["asset"] == {"symbol": "AAA"}
    assert view["pair_history"]["data"]["compare_asset_request"] == "BBB"


def test_compare_rejects_scans_supplied_on_the_wrong_requested_side() -> None:
    with pytest.raises(ValueError, match="left Instant X1 Scan"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_right(),
            right_scan=_left(),
        )


def test_compare_preserves_case_for_base58_mint_identity() -> None:
    left_mint = "1111111111111111111111111111111A"
    right_mint = "1111111111111111111111111111111a"
    left = _left()
    right = _right()
    left["requested_asset"] = left_mint
    right["requested_asset"] = right_mint
    left["identity"]["mint"] = left_mint
    right["identity"]["mint"] = right_mint
    left["identity"]["symbol"] = "LEFT"
    right["identity"]["symbol"] = "RIGHT"

    view = build_x1_compare_product_view(
        left_requested_asset=left_mint,
        right_requested_asset=right_mint,
        left_scan=left,
        right_scan=right,
    )

    assert view["requested_assets"] == {
        "left": left_mint,
        "right": right_mint,
    }


def test_compare_handles_arbitrarily_large_verified_integers_without_overflow() -> None:
    right = _right()
    right["market"]["transactions_24h"] = {
        "value": 10**400,
        "verified": True,
    }

    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=right,
    )

    assert view["comparison"]["transactions_24h"]["comparable"] is True
    assert view["comparison"]["transactions_24h"]["relation"] == "right_higher"


def test_compare_rejects_failed_or_authority_drifted_scan_views() -> None:
    failed = _right()
    failed["status"] = "unavailable"
    with pytest.raises(ValueError, match="ok/partial"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=failed,
        )

    risk_authorized = _right()
    risk_authorized["risk"]["execution_authorized"] = True
    with pytest.raises(ValueError, match="comparison risk"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=risk_authorized,
        )

    proof_rewritten = _right()
    proof_rewritten["evidence"]["proof_score_separate_from_risk"] = False
    with pytest.raises(ValueError, match="Proof Score separate from risk"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=proof_rewritten,
        )


def test_compare_rejects_promoted_current_concentration_in_input_view() -> None:
    right = _right()
    right["holder_concentration"]["top_account_concentration"] = {
        "state": "available",
        "verified": True,
        "value": 0.42,
    }

    with pytest.raises(ValueError, match="current concentration unavailable"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=right,
        )


def test_compare_rejects_misrouted_identity_on_failed_pair_history() -> None:
    pair_history = {
        "service": "historical_compare",
        "chain": "x1",
        "status": "unavailable",
        "asset": {"symbol": "CCC"},
        "data": {
            "mode": "all_available_pair",
            "compare_asset_request": "DDD",
        },
        "risk": None,
        "confidence": {},
        "sources": [],
        "observed_at": None,
        "warnings": [{"code": "history_unavailable"}],
        "errors": [],
    }

    with pytest.raises(ValueError, match="primary asset"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=_right(),
            pair_history=pair_history,
        )


def test_compare_rejects_execution_authority_drift() -> None:
    right = deepcopy(_right())
    right["execution_authorized"] = True

    with pytest.raises(ValueError, match="execution_authorized=false"):
        build_x1_compare_product_view(
            left_requested_asset="AAA",
            right_requested_asset="BBB",
            left_scan=_left(),
            right_scan=right,
        )


def test_compare_text_keeps_risk_and_proof_separate() -> None:
    view = build_x1_compare_product_view(
        left_requested_asset="AAA",
        right_requested_asset="BBB",
        left_scan=_left(),
        right_scan=_right(),
    )

    rendered = render_x1_compare_product_text(view)

    assert "X1 Compare — AAA vs BBB" in rendered
    assert "Left: WARN" in rendered
    assert "Right: PASS" in rendered
    assert "Combined risk: not calculated" in rendered
    assert "Proof scores remain separate per asset and separate from risk." in rendered
