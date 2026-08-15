"""Structured CMIS contracts used by chain-specialist agents.

Task 4 intentionally models only the market_report operation needed to prove
Roberta -> X1 Scout -> CMIS layering. Additional CMIS operations are added
incrementally after this boundary is stable.
"""

from typing import Literal, TypedDict


class MarketSnapshot(TypedDict):
    price: None
    liquidity: None
    volume_24h: None


class RiskSnapshot(TypedDict):
    level: Literal["TEST_ONLY"]
    flags: list[str]


class CMISMarketReport(TypedDict):
    service: Literal["cmis"]
    operation: Literal["market_report"]
    chain: Literal["x1"]
    asset: str
    data_confidence: Literal["TEST_ONLY"]
    market: MarketSnapshot
    risk: RiskSnapshot
    warnings: list[str]
