"""Roberta regression fixture for the accepted CMIS bounded pre-trade projection."""

from roberta.pretrade_ux import build_pretrade_presentation


def completed_cmis_projection():
    return {
        "service": "pre_trade_check",
        "chain": "x1",
        "status": "ok",
        "asset": {"symbol": "AGI", "mint": "agi-mint"},
        "data": {
            "trade": {
                "side": "buy",
                "chain": "x1",
                "asset": {"symbol": "AGI", "mint": "agi-mint"},
                "notional_usd": 2500.0,
            },
            "market": {
                "verified_liquidity_usd": 100000.0,
                "verified_volume_24h_usd": None,
            },
            "trade_size": {
                "assessment": "PASS",
                "notional_usd": 2500.0,
                "notional_to_liquidity_ratio": 0.025,
                "warn_threshold_notional_usd": None,
                "hard_block_notional_usd_threshold": None,
                "assessment_complete": True,
            },
            "route_analysis": {
                "status": "unavailable",
                "route_scope": None,
                "estimated_price_impact_percent": None,
                "estimated_slippage_percent": None,
                "estimated_fees": None,
                "route_quality": None,
                "bridge_dependency": None,
                "transaction_simulation": None,
            },
            "execution_capabilities": {
                "slippage": {
                    "status": "unavailable",
                    "value": None,
                    "reason_code": "verified_slippage_evidence_unavailable",
                },
                "price_impact": {
                    "status": "unavailable",
                    "value": None,
                    "reason_code": "verified_price_impact_evidence_unavailable",
                },
                "route_quality": {
                    "status": "unavailable",
                    "value": None,
                    "reason_code": "verified_route_evidence_unavailable",
                },
                "fees": {
                    "status": "unavailable",
                    "value": None,
                    "reason_code": "verified_execution_fee_evidence_unavailable",
                },
            },
            "analysis_only": True,
            "execution_authorized": False,
        },
        "risk": {
            "recommendation": "PASS",
            "flags": [],
            "reasons": [],
            "analysis_only": True,
            "execution_authorized": False,
        },
        "confidence": {"complete": True},
        "sources": [{"source": "pre_trade_engine", "role": "pre_trade_check"}],
        "observed_at": 1000,
        "warnings": [],
        "errors": [],
    }


def test_roberta_preserves_completed_cmis_size_and_liquidity_while_humanizing_display():
    payload = completed_cmis_projection()
    presentation = build_pretrade_presentation(payload)

    assert presentation is not None
    assert presentation["recommendation"] == "PASS"
    assert presentation["facts"]["market"] == payload["data"]["market"]
    assert presentation["facts"]["trade_size"] == payload["data"]["trade_size"]
    assert presentation["facts"]["route_analysis"] == payload["data"]["route_analysis"]
    text = presentation["user_text"]
    assert "AGI has about $100,000 in verified liquidity" in text
    assert "2.5%" in text
    assert "trade size passed" in text.lower()
    assert "0.025" not in text
    assert "PASS" not in text


def test_roberta_preserves_unavailable_execution_estimates_instead_of_inventing_values():
    presentation = build_pretrade_presentation(completed_cmis_projection())

    assert presentation is not None
    assert presentation["missing_evidence"] == [
        "price-impact estimate",
        "slippage estimate",
        "fee estimate",
    ]
    text = presentation["user_text"]
    assert "not fully evaluated" in text
    assert "price impact" in text
    assert "slippage" in text
    assert "fees" in text
    assert "0%" not in text
    assert "0.0%" not in text


def test_roberta_does_not_treat_pretrade_pass_as_execution_authorization():
    payload = completed_cmis_projection()
    presentation = build_pretrade_presentation(payload)

    assert presentation is not None
    assert payload["data"]["execution_authorized"] is False
    assert payload["risk"]["execution_authorized"] is False
    text = presentation["user_text"]
    assert "did not block the trade" in text
    assert "execution risk is not fully evaluated yet" in text


def test_technical_mode_preserves_null_route_values_and_raw_ratio_exactly():
    payload = completed_cmis_projection()
    presentation = build_pretrade_presentation(
        payload,
        objective="Show me the technical analysis for that trade.",
    )

    assert presentation is not None
    assert presentation["mode"] == "technical"
    technical = presentation["technical_text"]
    assert '"assessment": "PASS"' in technical
    assert '"notional_to_liquidity_ratio": 0.025' in technical
    assert '"estimated_price_impact_percent": null' in technical
    assert '"estimated_slippage_percent": null' in technical
    assert '"estimated_fees": null' in technical
