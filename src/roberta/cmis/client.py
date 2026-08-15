"""Typed client boundary for the Cross-Chain Market Intelligence Service."""

from typing import Protocol

from roberta.cmis.contracts import (
    CMISMarketReport,
    CMISPreTradeCheck,
    CMISRiskCheck,
    CMISTokenomicsReport,
    TradeAction,
)


class CMISClient(Protocol):
    """Operations currently required by chain-specialist agents.

    Every call names the target chain explicitly. Implementations may use RPC,
    DEX integrations, indexers, scanners, or a remote CMIS service underneath
    this boundary, but those provider details stay hidden from the Scouts.
    """

    def market_report(self, *, chain: str, asset: str) -> CMISMarketReport:
        """Return market and market-risk facts for an explicitly named chain."""
        ...

    def tokenomics(self, *, chain: str, asset: str) -> CMISTokenomicsReport:
        """Return deterministic tokenomics facts for an explicitly named chain."""
        ...

    def risk_check(self, *, chain: str, asset: str) -> CMISRiskCheck:
        """Return deterministic market-risk evaluation for an asset."""
        ...

    def pre_trade_check(
        self,
        *,
        chain: str,
        asset: str,
        action: TradeAction,
        amount_usd: float,
    ) -> CMISPreTradeCheck:
        """Return a deterministic pre-trade market/tokenomics/risk check."""
        ...
