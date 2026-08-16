"""Tests for deterministic CMIS service-status explanations."""

from roberta.status_help import build_cmis_status_help


def test_partial_risk_status_explains_incomplete_verification_not_risk_level() -> None:
    help_data = build_cmis_status_help(
        "risk_check",
        "partial",
        {"verified_checks": 6, "total_checks": 8},
    )

    assert help_data is not None
    assert help_data["status"] == "partial"
    meaning = str(help_data["meaning"])
    assert "one or more verification checks are incomplete" in meaning
    assert "6 of 8 verification checks are satisfied" in meaning
    assert "2 remain incomplete" in meaning
    assert "fully verified WARN or BLOCK" in meaning
    assert "CMIS status ok" in meaning


def test_ok_risk_status_does_not_mean_pass_recommendation() -> None:
    help_data = build_cmis_status_help("risk_check", "ok", {})
    assert help_data is not None
    meaning = str(help_data["meaning"])
    assert "WARN or BLOCK" in meaning
    assert "service status" in meaning.lower()
