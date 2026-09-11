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
    "trade_price_impact_intelligence",
    "large_trade_discovery",
    "wallet_relationship_intelligence",
    "regulatory_evidence",
    "instant_x1_scan",
    "x1_intelligence_brief_inputs",
    "tokenized_equity_intelligence",
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
    "trade_price_impact_intelligence",
    "large_trade_discovery",
    "wallet_relationship_intelligence",
    "instant_x1_scan",
    "x1_intelligence_brief_inputs",
    "tokenized_equity_intelligence",
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


class CMISResponseFreshness(TypedDict):
    """Top-level CMIS response-freshness contract promoted in CMIS 1.27."""

    contract_version: str
    scope: str
    state: str
    freshness_verified: bool | None
    observed_at: object | None
    details: dict[str, object]
    reason: NotRequired[str]


class CMISEvidenceCompletion(TypedDict):
    """System-wide evidence-completion metadata attached by protected CMIS."""

    contract_version: str
    state: Literal["COMPLETE", "PARTIAL", "BLOCKED"]
    primary_service: str
    service_status: str
    evidence_receipt_available: bool
    proof_score_available: bool
    receipt_freshness_checked: bool
    receipt_freshness_verified: bool | None
    verification_status: str
    unresolved_fields: list[str]
    unknown_proof_categories: list[str]
    missing_or_unavailable_evidence: list[str]
    supporting_evidence_checked: list[str]
    risk_separate_from_proof: bool
    facts_recomputed: bool
    risk_recomputed: bool
    status_rewritten: bool
    execution_authorized: bool


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
    # Required by the live HTTP client after a CMIS 1.27 capability handshake.
    # NotRequired preserves structural compatibility with older deterministic
    # fixtures/adapters that predate universal response freshness.
    freshness: NotRequired[CMISResponseFreshness]
    warnings: list[object]
    errors: list[object]
    # Added by CMIS contract >=1.7.0. NotRequired keeps legacy deterministic
    # adapters structurally usable while the live HTTP client requires and
    # validates these fields after a compatible capability handshake.
    evidence_receipt: NotRequired[dict[str, object]]
    proof_score: NotRequired[dict[str, object]]
    # Added centrally by protected CMIS after Evidence Receipt / Proof Score
    # binding. The field is metadata only: it never upgrades missing evidence,
    # rewrites risk, or authorizes execution. NotRequired retains compatibility
    # with historical fixtures until the assembled runtime is upgraded.
    evidence_completion: NotRequired[CMISEvidenceCompletion]
    # Service-specific promotion flags used by newer promoted CMIS products.
    read_only: NotRequired[bool]
    public_service_promoted: NotRequired[bool]
    scout_reliance_promoted: NotRequired[bool]
    runtime_capability_promoted: NotRequired[bool]
    complete_x1_ecosystem_coverage_verified: NotRequired[bool]
    execution_authorized: NotRequired[bool]


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
CMISTradePriceImpactIntelligence: TypeAlias = CMISEnvelope
CMISLargeTradeDiscovery: TypeAlias = CMISEnvelope
CMISWalletRelationshipIntelligence: TypeAlias = CMISEnvelope
CMISRegulatoryEvidence: TypeAlias = CMISEnvelope
CMISInstantX1Scan: TypeAlias = CMISEnvelope
CMISX1IntelligenceBrief: TypeAlias = CMISEnvelope
CMISTokenizedEquityIntelligence: TypeAlias = CMISEnvelope
