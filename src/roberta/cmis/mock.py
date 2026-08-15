"""Deterministic CMIS test adapter.

This adapter never represents live market data. It exercises the production
contract shape, explicit chain scoping, unavailable-value behavior, warnings,
and structured service errors without depending on an X1 provider.
"""

from typing import Literal

from roberta.cmis.contracts import (
    CMISError,
    CMISMarketReport,
    CMISPreTradeCheck,
    CMISRiskCheck,
    CMISTokenomicsReport,
    DataConfidence,
    MarketSnapshot,
    RiskSnapshot,
    TokenomicsSnapshot,
    TradeAction,
)

MockScenario = Literal["test_only", "warning", "unavailable", "error"]


class MockCMISClient:
    """Record CMIS calls and return deterministic contract-complete results."""

    def __init__(
        self,
        *,
        scenario: MockScenario = "test_only",
        timestamp: str = "2026-08-15T21:45:00Z",
    ) -> None:
        self.scenario = scenario
        self.timestamp = timestamp
        self.calls: list[dict[str, object]] = []

    def _normalize(self, *, chain: str, asset: str) -> tuple[str, str]:
        normalized_chain = chain.strip().lower()
        normalized_asset = asset.strip().upper()
        if not normalized_chain:
            raise ValueError("chain must not be empty")
        if not normalized_asset:
            raise ValueError("asset must not be empty")
        return normalized_chain, normalized_asset

    def _confidence(self) -> DataConfidence:
        if self.scenario in {"unavailable", "error"}:
            return "UNAVAILABLE"
        return "TEST_ONLY"

    def _warnings(self) -> list[str]:
        warnings = ["MOCK_CMIS", "NOT_LIVE_DATA"]
        if self.scenario == "warning":
            warnings.append("PARTIAL_DATA")
        elif self.scenario == "unavailable":
            warnings.append("DATA_UNAVAILABLE")
        elif self.scenario == "error":
            warnings.append("SERVICE_ERROR")
        return warnings

    def _errors(self) -> list[CMISError]:
        if self.scenario != "error":
            return []
        return [
            {
                "code": "CMIS_PROVIDER_UNAVAILABLE",
                "message": "Mock provider unavailable.",
                "retryable": True,
                "source": "mock_cmis",
            }
        ]

    def _market(self) -> MarketSnapshot:
        return {
            "price": None,
            "liquidity": None,
            "lp_count": None,
            "volume_24h": None,
            "volume_rank": None,
            "liquidity_rank": None,
        }

    def _tokenomics(self) -> TokenomicsSnapshot:
        return {
            "supply": None,
            "mint_authority": None,
            "freeze_authority": None,
        }

    def _risk(self) -> RiskSnapshot:
        if self.scenario in {"unavailable", "error"}:
            return {
                "score": None,
                "level": "UNKNOWN",
                "decision": "UNAVAILABLE",
                "flags": ["DATA_UNAVAILABLE"],
            }
        return {
            "score": None,
            "level": "TEST_ONLY",
            "decision": "TEST_ONLY",
            "flags": ["NOT_LIVE_DATA"],
        }

    def _base(self, *, chain: str, asset: str) -> dict[str, object]:
        return {
            "service": "cmis",
            "chain": chain,
            "asset": asset,
            "timestamp": self.timestamp,
            "data_confidence": self._confidence(),
            "sources": ["mock://cmis"],
            "warnings": self._warnings(),
            "errors": self._errors(),
        }

    def market_report(self, *, chain: str, asset: str) -> CMISMarketReport:
        chain, asset = self._normalize(chain=chain, asset=asset)
        self.calls.append({"operation": "market_report", "chain": chain, "asset": asset})
        return {
            **self._base(chain=chain, asset=asset),
            "operation": "market_report",
            "market": self._market(),
            "risk": self._risk(),
        }  # type: ignore[return-value]

    def tokenomics(self, *, chain: str, asset: str) -> CMISTokenomicsReport:
        chain, asset = self._normalize(chain=chain, asset=asset)
        self.calls.append({"operation": "tokenomics", "chain": chain, "asset": asset})
        return {
            **self._base(chain=chain, asset=asset),
            "operation": "tokenomics",
            "tokenomics": self._tokenomics(),
        }  # type: ignore[return-value]

    def risk_check(self, *, chain: str, asset: str) -> CMISRiskCheck:
        chain, asset = self._normalize(chain=chain, asset=asset)
        self.calls.append({"operation": "risk_check", "chain": chain, "asset": asset})
        return {
            **self._base(chain=chain, asset=asset),
            "operation": "risk_check",
            "risk": self._risk(),
        }  # type: ignore[return-value]

    def pre_trade_check(
        self,
        *,
        chain: str,
        asset: str,
        action: TradeAction,
        amount_usd: float,
    ) -> CMISPreTradeCheck:
        chain, asset = self._normalize(chain=chain, asset=asset)
        normalized_action = action.strip().upper()
        if normalized_action not in {"BUY", "SELL"}:
            raise ValueError("action must be BUY or SELL")
        if amount_usd <= 0:
            raise ValueError("amount_usd must be greater than zero")
        self.calls.append(
            {
                "operation": "pre_trade_check",
                "chain": chain,
                "asset": asset,
                "action": normalized_action,
                "amount_usd": amount_usd,
            }
        )
        return {
            **self._base(chain=chain, asset=asset),
            "operation": "pre_trade_check",
            "action": normalized_action,
            "amount_usd": amount_usd,
            "market": self._market(),
            "tokenomics": self._tokenomics(),
            "risk": self._risk(),
        }  # type: ignore[return-value]
