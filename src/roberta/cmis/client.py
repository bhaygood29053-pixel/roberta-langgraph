"""Typed client boundary for the Cross-Chain Market Intelligence Service."""

from typing import Protocol

from roberta.cmis.contracts import CMISEnvelope, TradeAction


class CMISClient(Protocol):
    """CMIS operations currently required by X1 Scout.

    Every call names its target chain explicitly. Provider and transport details
    stay beneath this interface.
    """

    def market_report(self, *, chain: str, asset: str) -> CMISEnvelope:
        ...

    def tokenomics(self, *, chain: str, asset: str) -> CMISEnvelope:
        ...

    def risk_check(self, *, chain: str, asset: str) -> CMISEnvelope:
        ...

    def pre_trade_check(
        self,
        *,
        chain: str,
        asset: str,
        action: TradeAction,
        amount_usd: float,
    ) -> CMISEnvelope:
        ...
