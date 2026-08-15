"""Boundary tests for X1 Scout -> CMIS."""

import pytest

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph


def test_x1_scout_scopes_market_report_to_x1_and_preserves_envelope() -> None:
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
    assert report["requested_asset"] == "agi"
    assert report["asset"] == {"symbol": "AGI"}
    assert report["source"] == {
        "service": "cmis",
        "operation": "market_report",
    }
    assert report["cmis_status"] == "partial"
    assert report["observed_at"] == "2026-08-15T21:45:00Z"
    assert report["confidence"] == {"level": "TEST_ONLY"}
    assert report["findings"]["data"]["price"] is None
    assert report["errors"] == []


@pytest.mark.parametrize(
    "operation",
    ["market_report", "tokenomics", "risk_check", "pre_trade_check"],
)
def test_x1_scout_dispatches_initial_cmis_operations(operation: str) -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)
    request: dict[str, object] = {
        "asset": "AGI",
        "objective": f"exercise {operation}",
        "operation": operation,
    }
    if operation == "pre_trade_check":
        request.update({"action": "BUY", "amount_usd": 500.0})

    result = scout.invoke({"request": request, "status": "running"})

    assert cmis.calls[0]["operation"] == operation
    assert cmis.calls[0]["chain"] == "x1"
    assert result["report"]["source"]["operation"] == operation
    assert result["report"]["cmis_status"] == "partial"
    assert result["report"]["status"] == "complete"


@pytest.mark.parametrize("scenario,status", [("unavailable", "unavailable"), ("error", "error")])
def test_x1_scout_propagates_failed_cmis_state_without_fabrication(
    scenario: str,
    status: str,
) -> None:
    cmis = MockCMISClient(scenario=scenario)
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "assess market risk",
                "operation": "risk_check",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert result["status"] == "error"
    assert report["status"] == "error"
    assert report["cmis_status"] == status
    assert report["findings"]["risk"] is None
