"""LangGraph state for the Solana Scout specialist subgraph."""

from typing import Literal, NotRequired, TypedDict

from roberta.cmis.contracts import CMISEnvelope, CMISOperation, CMISStatus, TradeAction


class SolanaScoutRequest(TypedDict):
    asset: str
    objective: str
    operation: NotRequired[CMISOperation]
    action: NotRequired[TradeAction]
    amount_usd: NotRequired[float]


class SolanaScoutPlanProposal(TypedDict):
    operations: list[str]


class SolanaScoutPlan(TypedDict):
    operations: list[CMISOperation]
    source: Literal["explicit", "model", "deterministic"]
    warnings: list[str]


class SolanaScoutInvestigation(TypedDict):
    operation: str
    cmis_status: CMISStatus
    cmis_status_help: dict[str, object] | None
    observed_at: object | None
    observed_at_iso: str | None
    observed_at_display: str | None
    findings: dict[str, object]
    confidence: dict[str, object]
    risk_help: dict[str, object] | None
    component_status_table: str | None
    sources: list[object]
    warnings: list[object]
    errors: list[object]


class SolanaScoutReport(TypedDict):
    specialist: Literal["solana_scout"]
    chain: Literal["solana"]
    requested_asset: str
    asset: dict[str, object]
    objective: str
    status: Literal["complete", "unavailable", "error"]
    plan: SolanaScoutPlan
    investigations: list[SolanaScoutInvestigation]
    cmis_status: CMISStatus
    cmis_status_help: dict[str, object] | None
    observed_at: object | None
    observed_at_iso: str | None
    observed_at_display: str | None
    findings: dict[str, object]
    confidence: dict[str, object]
    risk_help: dict[str, object] | None
    component_status_table: str | None
    source: dict[str, str]
    sources: list[object]
    warnings: list[object]
    errors: list[object]


class SolanaScoutState(TypedDict):
    request: SolanaScoutRequest
    status: Literal["running", "complete", "unavailable", "error"]
    plan_proposal: NotRequired[SolanaScoutPlanProposal | None]
    planner_error: NotRequired[str | None]
    plan: NotRequired[SolanaScoutPlan]
    cmis_results: NotRequired[list[CMISEnvelope]]
    cmis_result: NotRequired[CMISEnvelope]
    report: NotRequired[SolanaScoutReport]
