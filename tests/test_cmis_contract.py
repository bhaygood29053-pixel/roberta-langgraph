"""Contract tests for the Roberta-side CMIS boundary."""

from roberta.cmis.mock import MockCMISClient


def test_mock_cmis_supports_initial_operations_with_explicit_chain_scope() -> None:
    cmis = MockCMISClient()

    market = cmis.market_report(chain="x1", asset="agi")
    tokenomics = cmis.tokenomics(chain="x1", asset="agi")
    risk = cmis.risk_check(chain="x1", asset="agi")
    pre_trade = cmis.pre_trade_check(
        chain="x1", asset="agi", action="BUY", amount_usd=500
    )

    assert [call["operation"] for call in cmis.calls] == [
        "market_report",
        "tokenomics",
        "risk_check",
        "pre_trade_check",
    ]
    assert all(call["chain"] == "x1" for call in cmis.calls)
    assert all(call["asset"] == "AGI" for call in cmis.calls)

    for result in (market, tokenomics, risk, pre_trade):
        assert result["service"] == "cmis"
        assert result["chain"] == "x1"
        assert result["timestamp"] == "2026-08-15T21:45:00Z"
        assert result["data_confidence"] == "TEST_ONLY"
        assert result["sources"] == ["mock://cmis"]
        assert result["errors"] == []


def test_mock_cmis_preserves_unavailable_values_and_warning() -> None:
    cmis = MockCMISClient(scenario="unavailable")
    result = cmis.market_report(chain="x1", asset="AGI")

    assert result["data_confidence"] == "UNAVAILABLE"
    assert result["market"]["price"] is None
    assert result["market"]["liquidity"] is None
    assert result["risk"]["decision"] == "UNAVAILABLE"
    assert "DATA_UNAVAILABLE" in result["warnings"]
    assert result["errors"] == []


def test_mock_cmis_preserves_warning_without_inventing_values() -> None:
    cmis = MockCMISClient(scenario="warning")
    result = cmis.tokenomics(chain="x1", asset="AGI")

    assert result["tokenomics"]["supply"] is None
    assert result["data_confidence"] == "TEST_ONLY"
    assert "PARTIAL_DATA" in result["warnings"]


def test_mock_cmis_returns_structured_service_error() -> None:
    cmis = MockCMISClient(scenario="error")
    result = cmis.risk_check(chain="x1", asset="AGI")

    assert result["data_confidence"] == "UNAVAILABLE"
    assert result["risk"]["score"] is None
    assert result["risk"]["decision"] == "UNAVAILABLE"
    assert result["errors"] == [
        {
            "code": "CMIS_PROVIDER_UNAVAILABLE",
            "message": "Mock provider unavailable.",
            "retryable": True,
            "source": "mock_cmis",
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
