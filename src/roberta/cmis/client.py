"""Typed client boundary for the Cross-Chain Market Intelligence Service."""

from typing import Protocol

from roberta.cmis.capabilities import CMISCapabilities
from roberta.cmis.contracts import CMISEnvelope, HistoricalMode, RankMetric, TradeAction


class CMISClient(Protocol):
    """CMIS operations currently required by Chain Scouts.

    Every call names its target chain explicitly. Provider and transport details
    stay beneath this interface. Capability discovery is consumed by Scouts, not
    by Roberta directly.
    """

    def capabilities(self) -> CMISCapabilities:
        ...

    def asset_lookup(self, *, chain: str, asset: str) -> CMISEnvelope:
        ...

    def market_report(self, *, chain: str, asset: str) -> CMISEnvelope:
        ...

    def instant_x1_scan(self, *, chain: str, asset: str) -> CMISEnvelope:
        ...

    def rank(
        self,
        *,
        chain: str,
        metric: RankMetric = "volume",
        limit: int = 10,
    ) -> CMISEnvelope:
        ...

    def historical_compare(
        self,
        *,
        chain: str,
        asset: str,
        question: str | None = None,
        mode: HistoricalMode = "window",
        compare_asset: str | None = None,
        provider_history_backfill: bool | None = None,
        onchain_max_signatures: int | None = None,
    ) -> CMISEnvelope:
        ...

    def tokenomics(self, *, chain: str, asset: str) -> CMISEnvelope:
        ...

    def burn_intelligence(self, *, chain: str, asset: str) -> CMISEnvelope:
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

    def verification_evidence(
        self,
        *,
        chain: str,
        evidence_id: str | None = None,
        fact_type: str | None = None,
        subject_id: str | None = None,
    ) -> CMISEnvelope:
        ...

    def concentration_change_intelligence(
        self,
        *,
        chain: str,
        asset: str,
        intelligence_evidence_id: str,
    ) -> CMISEnvelope:
        ...
