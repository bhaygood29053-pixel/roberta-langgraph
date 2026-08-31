"""LangGraph state for the X1 Scout specialist subgraph."""

from typing import Literal, NotRequired, TypedDict

from roberta.cmis.contracts import (
    CMISEnvelope,
    CMISOperation,
    CMISStatus,
    TradeAction,
)


class X1ScoutRequest(TypedDict):
    asset: str
    objective: str
    operation: NotRequired[CMISOperation]
    action: NotRequired[TradeAction]
    amount_usd: NotRequired[float]
    evidence_id: NotRequired[str]
    fact_type: NotRequired[str]
    subject_id: NotRequired[str]
    intelligence_evidence_id: NotRequired[str]
    compare_asset: NotRequired[str]


class X1ScoutPlanProposal(TypedDict):
    operations: list[str]


class X1ScoutPlan(TypedDict):
    operations: list[CMISOperation]
    source: Literal["explicit", "model", "deterministic"]
    warnings: list[str]


class X1ScoutInvestigation(TypedDict):
    """One CMIS result preserved inside a multi-step Scout report."""

    operation: str
    asset: dict[str, object]
    cmis_status: CMISStatus
    cmis_status_help: dict[str, object] | None
    observed_at: object | None
    observed_at_iso: str | None
    observed_at_display: str | None
    findings: dict[str, object]
    confidence: dict[str, object]
    evidence_context: dict[str, object]
    risk_help: dict[str, object] | None
    component_status_table: str | None
    pretrade_presentation: dict[str, object] | None
    historical_coverage_presentation: NotRequired[dict[str, object]]
    instant_x1_scan_presentation: NotRequired[dict[str, object]]
    sources: list[object]
    warnings: list[object]
    errors: list[object]


class X1ScoutReport(TypedDict):
    specialist: Literal["x1_scout"]
    chain: Literal["x1"]
    requested_asset: str
    requested_compare_asset: NotRequired[str]
    asset: dict[str, object]
    normalized_asset_identity: NotRequired[dict[str, object]]
    asset_identity_reconciliation: NotRequired[dict[str, object]]
    asset_identity_status: NotRequired[CMISStatus]
    objective: str
    status: Literal["complete", "error"]
    plan: X1ScoutPlan
    investigations: list[X1ScoutInvestigation]
    cmis_status: CMISStatus
    cmis_status_help: dict[str, object] | None
    observed_at: object | None
    observed_at_iso: str | None
    observed_at_display: str | None
    findings: dict[str, object]
    confidence: dict[str, object]
    evidence_context: dict[str, object]
    risk_help: dict[str, object] | None
    component_status_table: str | None
    pretrade_presentation: dict[str, object] | None
    historical_coverage_presentation: NotRequired[dict[str, object]]
    instant_x1_scan_presentation: NotRequired[dict[str, object]]
    instant_x1_scan_product_view: NotRequired[dict[str, object]]
    instant_x1_scan_product_text: NotRequired[str]
    source: dict[str, str]
    sources: list[object]
    warnings: list[object]
    errors: list[object]


class X1ScoutState(TypedDict):
    request: X1ScoutRequest
    status: Literal["running", "complete", "error"]
    plan_proposal: NotRequired[X1ScoutPlanProposal | None]
    planner_error: NotRequired[str | None]
    plan: NotRequired[X1ScoutPlan]
    cmis_results: NotRequired[list[CMISEnvelope]]
    cmis_result: NotRequired[CMISEnvelope]
    cmis_identity_result: NotRequired[CMISEnvelope | None]
    report: NotRequired[X1ScoutReport]
