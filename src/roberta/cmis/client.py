"""Protocol boundary for the Cross-Chain Market Intelligence Service."""

from typing import Protocol

from roberta.cmis.contracts import CMISMarketReport


class CMISClient(Protocol):
    """Minimal CMIS client contract required by X1 Scout in Task 4."""

    def market_report(self, *, chain: str, asset: str) -> CMISMarketReport:
        """Return a structured market report for an explicitly named chain."""
        ...
