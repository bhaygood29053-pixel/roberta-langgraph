"""Contract tests for the Roberta-side CMIS boundary."""

from roberta.cmis.mock import MockCMISClient

EXPECTED_KEYS = {
    "service",
    "chain",
    "status",
    "asset",
    "data",
    "risk",
    "confidence",
    "sources",
    "observed_at",
    "warnings",
    "errors",
}


def test_mock_cmis_matches_external_envelope_for_initial_operations() -> None:
    cmis = MockCMISClient()

    results = [
        cmis.market_report(chain="x1", asset="agi"),
        cmis.tokenomics(chain="x1", asset="agi"),
        cmis.risk_check(chain="x1", asset="agi"),
        cmis.pre_trade_check(
            chain="x1", asset="agi", action="BUY", amount_usd=500
        ),
    ]

    assert [call["operation"] for call in cmis.calls] == [
        "market_report",
        "tokenomics",
        "risk_check",
        "pre_trade_check",
    ]
    assert all(call["chain"] == "x1" for call in cmis.calls)
    assert all(call["asset"] == "AGI" for call in cmis.calls)

    for result in results:
        assert set(result) == EXPECTED_KEYS
        assert result["chain"] == "x1"
        assert result["status"] == "partial"
        assert result["asset"] == {"symbol": "AGI"}
        assert result["confidence"] == {"level": "TEST_ONLY"}
        assert result["observed_at"] == "2026-08-15T21:45:00Z"
        assert result["errors"] == []


def test_mock_cmis_preserves_unavailable_state_without_fabrication() -> None:
    result = MockCMISClient(scenario="unavailable").market_report(
        chain="x1", asset="AGI"
    )

    assert result["status"] == "unavailable"
    assert result["data"]["price"] is None
    assert result["data"]["liquidity"] is None
    assert any(
        isinstance(item, dict) and item.get("code") == "DATA_UNAVAILABLE"
        for item in result["warnings"]
    )
    assert result["errors"] == []


def test_mock_cmis_preserves_warning_state() -> None:
    result = MockCMISClient(scenario="warning").tokenomics(
        chain="x1", asset="AGI"
    )

    assert result["status"] == "partial"
    assert result["data"]["total_supply"] is None
    assert any(
        isinstance(item, dict) and item.get("code") == "PARTIAL_DATA"
        for item in result["warnings"]
    )


def test_mock_cmis_returns_structured_service_error() -> None:
    result = MockCMISClient(scenario="error").risk_check(
        chain="x1", asset="AGI"
    )

    assert result["status"] == "error"
    assert result["risk"] is None
    assert result["errors"] == [
        {
            "code": "CMIS_PROVIDER_UNAVAILABLE",
            "message": "Mock provider unavailable.",
        }
    ]


def test_mock_cmis_rejects_invalid_pre_trade_input() -> None:
    cmis = MockCMISClient()

    try:
        cmis.pre_trade_check(
            chain="x1", asset="AGI", action="BUY", amount_usd=0
        )
    except ValueError as exc:
        assert "amount_usd" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected invalid amount_usd to raise ValueError")
