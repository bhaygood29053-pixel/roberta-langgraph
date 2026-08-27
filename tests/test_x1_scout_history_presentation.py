from roberta.x1_scout.history_presentation import (
    build_historical_coverage_presentation,
)


def envelope(data):
    return {
        "service": "historical_compare",
        "chain": "x1",
        "status": "partial",
        "asset": {"symbol": "AGI"},
        "data": data,
        "risk": None,
        "confidence": {},
        "sources": [],
        "observed_at": None,
        "warnings": [],
        "errors": [],
    }


def test_partial_verified_market_history_is_never_projected_as_zero_history() -> None:
    result = build_historical_coverage_presentation(
        envelope(
            {
                "mode": "all_available",
                "status": "partial",
                "available_metric_count": 1,
                "multi_point_metric_count": 1,
                "first_verified_observed_at": 100,
                "last_verified_observed_at": 300,
                "full_asset_lifetime_verified": False,
                "continuous_coverage_verified": False,
                "provider_history_imported": True,
                "provider_price_history": {
                    "available": True,
                    "observation_count": 2,
                    "first_observed_at": 100,
                    "last_observed_at": 200,
                },
                "metrics": {
                    "price": {
                        "observation_count": 3,
                        "provider_history_imported": True,
                    }
                },
                "coverage": {
                    "market": {
                        "status": "partial",
                        "first_verified_observed_at": 100,
                        "last_verified_observed_at": 300,
                        "provider_history_imported": True,
                    },
                    "onchain": {
                        "status": "unavailable",
                        "coverage_scope": "x1_rpc_visible_mint_address_history",
                    },
                },
            }
        )
    )

    assert result is not None
    assert result["interpretation"] == "verified_partial_history"
    assert result["verified_history_available"] is True
    assert result["must_not_describe_missing_history_as_zero"] is True
    assert result["full_asset_lifetime_verified"] is False
    assert result["continuous_coverage_verified"] is False
    assert result["market"]["history_available"] is True
    assert result["market"]["price_observation_count"] == 3
    assert result["market"]["provider_history_imported"] is True


def test_missing_history_remains_unproven_not_zero() -> None:
    result = build_historical_coverage_presentation(
        envelope(
            {
                "mode": "all_available",
                "status": "unavailable",
                "available_metric_count": 0,
                "multi_point_metric_count": 0,
                "first_verified_observed_at": None,
                "last_verified_observed_at": None,
                "full_asset_lifetime_verified": False,
                "continuous_coverage_verified": False,
                "provider_history_imported": False,
                "metrics": {},
                "coverage": {
                    "market": {
                        "status": "unavailable",
                        "first_verified_observed_at": None,
                        "last_verified_observed_at": None,
                        "provider_history_imported": False,
                    },
                    "onchain": {
                        "status": "unavailable",
                        "coverage_scope": "x1_rpc_visible_mint_address_history",
                        "rpc_visible_mint_history_complete": False,
                    },
                },
            }
        )
    )

    assert result is not None
    assert result["interpretation"] == "verified_history_unavailable_or_unproven"
    assert result["verified_history_available"] is False
    assert result["must_not_describe_missing_history_as_zero"] is True
    assert result["market"]["history_available"] is False
    assert result["onchain"]["history_available"] is False


def test_window_history_does_not_get_all_available_presentation_projection() -> None:
    result = build_historical_coverage_presentation(
        envelope({"mode": "window"})
    )
    assert result is None
