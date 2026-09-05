"""External contracts for the Cross-Chain Market Intelligence Service.

Roberta-side types mirror the CMIS HTTP service envelope. They intentionally do
not restate provider-specific market schemas; Chain Scouts preserve structured
CMIS payloads and Roberta consumes evidence metadata without inventing or
recomputing unavailable fields.
"""

from typing import Literal, NotRequired, TypeAlias, TypedDict

CMISService: TypeAlias = Literal[
    "asset_lookup",
    "market_report",
    "rank",
    "historical_compare",
    "tokenomics",
    "burn_intelligence",
    "discovery_intelligence",
    "risk_check",
    "pre_trade_check",
    "verification_evidence",
    "concentration_change_intelligence",
    "concentration_warning_intelligence",
    "bridge_to_xdex_utilization",
    "cross_chain_asset_provenance",
    "instant_x1_scan",
]
CMISOperation: TypeAlias = Literal[
    "asset_lookup",
    "market_report",
    "rank",
    "historical_compare",
    "tokenomics",
    "burn_intelligence",
    "discovery_intelligence",
    "risk_check",
    "pre_trade_check",
    "verification_evidence",
    "concentration_change_intelligence",
    "concentration_warning_intelligence",
    "bridge_to_xdex_utilization",
    "cross_chain_asset_provenance",
    "instant_x1_scan",
]
CMISStatus: TypeAlias = Literal[
    "ok",
    "partial",
    "unavailable",
    "ambiguous",
    "error",
]
TradeAction: TypeAlias = Literal["BUY", "SELL"]
HistoricalMode: TypeAlias = Literal[
    "window",
    "all_available",
    "all_available_pair",
]
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
    """Standard CMIS HTTP response envelope plus evidence-quality metadata."""

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
    # Added by CMIS contract >=1.7.0. NotRequired keeps legacy deterministic
    # adapters structurally usable while the live HTTP client requires and
    # validates these fields after a compatible capability handshake.
    evidence_receipt: NotRequired[dict[str, object]]
    proof_score: NotRequired[dict[str, object]]


CMISResult: TypeAlias = CMISEnvelope
CMISMarketReport: TypeAlias = CMISEnvelope
CMISRankReport: TypeAlias = CMISEnvelope
CMISHistoricalCompare: TypeAlias = CMISEnvelope
CMISTokenomicsReport: TypeAlias = CMISEnvelope
CMISBurnIntelligence: TypeAlias = CMISEnvelope
CMISDiscoveryIntelligence: TypeAlias = CMISEnvelope
CMISRiskCheck: TypeAlias = CMISEnvelope
CMISPreTradeCheck: TypeAlias = CMISEnvelope
CMISVerificationEvidence: TypeAlias = CMISEnvelope
CMISConcentrationChangeIntelligence: TypeAlias = CMISEnvelope
CMISConcentrationWarningIntelligence: TypeAlias = CMISEnvelope
CMISBridgeToXdexUtilization: TypeAlias = CMISEnvelope
CMISCrossChainAssetProvenance: TypeAlias = CMISEnvelope
CMISInstantX1Scan: TypeAlias = CMISEnvelope
