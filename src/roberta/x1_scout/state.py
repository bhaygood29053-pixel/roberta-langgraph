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


class X1ScoutReport(TypedDict):
    specialist: Literal["x1_scout"]
    chain: Literal["x1"]
    requested_asset: str
    asset: dict[str, object]
    objective: str
    status: Literal["complete", "error"]
    cmis_status: CMISStatus
    observed_at: object | None
    observed_at_iso: str | None
    findings: dict[str, object]
    confidence: dict[str, object]
    risk_help: dict[str, object] | None
    source: dict[str, str]
    sources: list[object]
    warnings: list[object]
    errors: list[object]


class X1ScoutState(TypedDict):
    request: X1ScoutRequest
    status: Literal["running", "complete", "error"]
    cmis_result: NotRequired[CMISEnvelope]
    report: NotRequired[X1ScoutReport]
