"""Boundary tests for X1 Scout -> CMIS."""

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph


def test_x1_scout_scopes_market_report_to_x1_and_returns_structured_report() -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": "agi",
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    assert cmis.calls == [
        {
            "operation": "market_report",
            "chain": "x1",
            "asset": "AGI",
        }
    ]

    report = result["report"]
    assert result["status"] == "complete"
    assert report["specialist"] == "x1_scout"
    assert report["chain"] == "x1"
    assert report["asset"] == "AGI"
    assert report["source"] == {
        "service": "cmis",
        "operation": "market_report",
    }
    assert report["data_confidence"] == "TEST_ONLY"
    assert report["findings"]["market"]["price"] is None
    assert "NOT_LIVE_DATA" in report["warnings"]
