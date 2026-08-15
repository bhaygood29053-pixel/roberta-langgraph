"""Opt-in integration test for a running provider-backed CMIS gateway."""

import os

import pytest

from roberta.cmis.http import CMISHTTPClient


pytestmark = [
    pytest.mark.cmis_live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_CMIS_TESTS") != "1",
        reason="Set RUN_LIVE_CMIS_TESTS=1 to test a running CMIS gateway.",
    ),
]


def test_live_cmis_gateway_returns_chain_scoped_market_envelope() -> None:
    result = CMISHTTPClient.from_env().market_report(chain="x1", asset="AGI")

    assert result["service"] == "market_report"
    assert result["chain"] == "x1"
    assert result["status"] in {
        "ok",
        "partial",
        "unavailable",
        "ambiguous",
        "error",
    }
    for field in (
        "asset",
        "data",
        "risk",
        "confidence",
        "sources",
        "observed_at",
        "warnings",
        "errors",
    ):
        assert field in result
