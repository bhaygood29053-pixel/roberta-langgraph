"""Tests for deterministic CMIS risk-help construction."""

from roberta.risk_help import build_risk_help


def test_risk_help_explains_warn_from_returned_reasons_and_flags() -> None:
    risk = {
        "recommendation": "WARN",
        "score": None,
        "score_reason": "risk_score_not_calibrated",
        "score_verified": False,
        "reasons": [
            "Verified bounded mint/burn activity was not supplied.",
            "Verified historical price comparison was not supplied to the risk core.",
        ],
        "flags": ["token_activity_unavailable", "historical_price_unavailable"],
        "confidence": {
            "level": "medium",
            "verified_checks": 6,
            "total_checks": 8,
            "verification_ratio": 0.75,
        },
        "components": {
            "tokenomics": {
                "status": "WARN",
                "reasons": ["Verified bounded mint/burn activity was not supplied."],
                "flags": ["token_activity_unavailable"],
            },
            "liquidity": {
                "status": "PASS",
                "reasons": [],
                "flags": [],
            },
        },
    }

    help_data = build_risk_help(risk)

    assert help_data is not None
    recommendation = help_data["recommendation"]
    assert recommendation["value"] == "WARN"
    assert "Verified bounded mint/burn activity was not supplied." in recommendation["meaning"]
    assert "historical_price_unavailable" in recommendation["meaning"]

    tokenomics = help_data["components"]["tokenomics"]
    assert tokenomics["status"] == "WARN"
    assert "CMIS component status is WARN." in tokenomics["meaning"]
    assert "token_activity_unavailable" in tokenomics["meaning"]


def test_risk_help_confidence_is_coverage_not_safety_probability() -> None:
    help_data = build_risk_help(
        {
            "recommendation": "WARN",
            "score": None,
            "score_verified": False,
            "confidence": {
                "level": "medium",
                "verified_checks": 6,
                "total_checks": 8,
                "verification_ratio": 0.75,
            },
        }
    )

    assert help_data is not None
    confidence = help_data["confidence"]
    assert confidence["verified_checks"] == 6
    assert confidence["total_checks"] == 8
    assert "6 of 8 verification checks" in confidence["meaning"]
    assert "75%" in confidence["meaning"]
    assert "not the probability that the asset is safe" in confidence["meaning"]


def test_risk_help_never_invents_uncalibrated_numeric_score() -> None:
    help_data = build_risk_help(
        {
            "recommendation": "WARN",
            "score": None,
            "score_reason": "risk_score_not_calibrated",
            "score_verified": False,
        }
    )

    assert help_data is not None
    score = help_data["score"]
    assert score["value"] is None
    assert score["verified"] is False
    assert score["reason"] == "risk_score_not_calibrated"
    assert "No verified numeric risk score is available." in score["meaning"]
    assert "Do not convert the categorical recommendation into a number." in score["meaning"]


def test_no_risk_produces_no_risk_help() -> None:
    assert build_risk_help(None, {"level": "medium"}) is None
