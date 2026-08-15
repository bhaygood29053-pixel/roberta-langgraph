"""Deterministic CMIS double for X1 Scout integration tests.

This is not a live market source. It exists only to prove service ownership,
chain scoping, structured results, and uncertainty propagation.
"""

from roberta.cmis.contracts import CMISMarketReport


class MockCMISClient:
    """Record CMIS calls and return deterministic TEST_ONLY data."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def market_report(self, *, chain: str, asset: str) -> CMISMarketReport:
        normalized_chain = chain.strip().lower()
        normalized_asset = asset.strip().upper()

        if normalized_chain != "x1":
            raise ValueError(
                f"Task 4 MockCMISClient supports only chain='x1', got {chain!r}."
            )
        if not normalized_asset:
            raise ValueError("asset must not be empty")

        self.calls.append(
            {
                "operation": "market_report",
                "chain": normalized_chain,
                "asset": normalized_asset,
            }
        )

        return {
            "service": "cmis",
            "operation": "market_report",
            "chain": "x1",
            "asset": normalized_asset,
            "data_confidence": "TEST_ONLY",
            "market": {
                "price": None,
                "liquidity": None,
                "volume_24h": None,
            },
            "risk": {
                "level": "TEST_ONLY",
                "flags": ["NOT_LIVE_DATA"],
            },
            "warnings": ["MOCK_CMIS", "NOT_LIVE_DATA"],
        }
