"""Structured contracts for the Cross-Chain Market Intelligence Service.

These contracts model the Roberta-side service boundary. They are deliberately
provider-neutral and preserve unavailable values, confidence, warnings, source
metadata, and service errors instead of asking an LLM to infer missing facts.
"""

from typing import Literal, TypeAlias, TypedDict

CMISOperation: TypeAlias = Literal[
    "market_report",
    "tokenomics",
    "risk_check",
    "pre_trade_check",
]
DataConfidence: TypeAlias = Literal[
    "HIGH",
    "MEDIUM",
    "LOW",
    "UNAVAILABLE",
    "TEST_ONLY",
]
TradeAction: TypeAlias = Literal["BUY", "SELL"]
RiskLevel: TypeAlias = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    "UNKNOWN",
    "TEST_ONLY",
]
RiskDecision: TypeAlias = Literal[
    "ALLOW",
    "WARN",
    "BLOCK",
    "UNAVAILABLE",
    "TEST_ONLY",
]


class CMISError(TypedDict):
    code: str
    message: str
    retryable: bool
    source: str | None


class MarketSnapshot(TypedDict):
    price: float | None
    liquidity: float | None
    lp_count: int | None
    volume_24h: float | None
    volume_rank: int | None
    liquidity_rank: int | None


class TokenomicsSnapshot(TypedDict):
    supply: float | None
    mint_authority: str | None
    freeze_authority: str | None


class RiskSnapshot(TypedDict):
    score: float | None
    level: RiskLevel
    decision: RiskDecision
    flags: list[str]


class CMISBaseReport(TypedDict):
    service: Literal["cmis"]
    chain: str
    asset: str
    timestamp: str
    data_confidence: DataConfidence
    sources: list[str]
    warnings: list[str]
    errors: list[CMISError]


class CMISMarketReport(CMISBaseReport):
    operation: Literal["market_report"]
    market: MarketSnapshot
    risk: RiskSnapshot


class CMISTokenomicsReport(CMISBaseReport):
    operation: Literal["tokenomics"]
    tokenomics: TokenomicsSnapshot


class CMISRiskCheck(CMISBaseReport):
    operation: Literal["risk_check"]
    risk: RiskSnapshot


class CMISPreTradeCheck(CMISBaseReport):
    operation: Literal["pre_trade_check"]
    action: TradeAction
    amount_usd: float
    market: MarketSnapshot
    tokenomics: TokenomicsSnapshot
    risk: RiskSnapshot


CMISResult: TypeAlias = (
    CMISMarketReport | CMISTokenomicsReport | CMISRiskCheck | CMISPreTradeCheck
)
