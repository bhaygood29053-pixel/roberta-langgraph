"""Regression coverage for X1 Scout deterministic risk-help metadata."""

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph


def test_x1_scout_attaches_deterministic_risk_help_to_risk_result() -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {"asset": "AGI", "objective": "assess market risk"},
            "status": "running",
        }
    )

    report = result["report"]
    help_data = report["risk_help"]

    assert help_data is not None
    assert help_data["recommendation"]["value"] == "TEST_ONLY"
    assert "NOT_LIVE_DATA" in help_data["recommendation"]["meaning"]
    assert (
        "No verified numeric risk score is available."
        in help_data["score"]["meaning"]
    )


def test_x1_scout_has_no_risk_help_when_cmis_risk_is_unavailable() -> None:
    cmis = MockCMISClient(scenario="unavailable")
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {"asset": "AGI", "objective": "assess market risk"},
            "status": "running",
        }
    )

    assert result["report"]["findings"]["risk"] is None
    assert result["report"]["risk_help"] is None
