"""External contracts for the Cross-Chain Market Intelligence Service.

Roberta-side types mirror the CMIS HTTP service envelope. They intentionally do
not restate provider-specific market schemas; X1 Scout preserves the structured
CMIS payload and interprets it without inventing unavailable fields.
"""

from typing import Literal, TypeAlias, TypedDict

CMISService: TypeAlias = Literal[
    "asset_lookup",
    "market_report",
    "rank",
    "historical_compare",
    "tokenomics",
    "risk_check",
    "pre_trade_check",
    "verification_evidence",
]
CMISOperation: TypeAlias = Literal[
    "market_report",
    "rank",
    "historical_compare",
    "tokenomics",
    "risk_check",
    "pre_trade_check",
    "verification_evidence",
]
CMISStatus: TypeAlias = Literal[
    "ok",
    "partial",
    "unavailable",
    "ambiguous",
    "error",
]
TradeAction: TypeAlias = Literal["BUY", "SELL"]
RankMetric: TypeAlias = Literal[
    "volume",
    "liquidity",
    "holders",
    "safety",
    "gainers",
    "losers",
    "trending",
]


class CMISEnvelope(TypedDict):
    """Standard CMIS HTTP response envelope."""

    service: CMISService
    chain: str
    status: CMISStatus
    asset: dict[str, object]
    data: dict[str, object]
    risk: dict[str, object] | None
    confidence: dict[str, object]
    sources: list[object]
    observed_at: object | None
    warnings: list[object]
    errors: list[object]


CMISResult: TypeAlias = CMISEnvelope
CMISMarketReport: TypeAlias = CMISEnvelope
CMISRankReport: TypeAlias = CMISEnvelope
CMISHistoricalCompare: TypeAlias = CMISEnvelope
CMISTokenomicsReport: TypeAlias = CMISEnvelope
CMISRiskCheck: TypeAlias = CMISEnvelope
CMISPreTradeCheck: TypeAlias = CMISEnvelope
CMISVerificationEvidence: TypeAlias = CMISEnvelope
