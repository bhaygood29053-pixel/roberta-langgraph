"""LangGraph state for the X1 Scout specialist subgraph."""

from typing import Literal, NotRequired, TypedDict

from roberta.cmis.contracts import (
    CMISError,
    CMISOperation,
    CMISResult,
    DataConfidence,
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
    asset: str
    objective: str
    status: Literal["complete", "error"]
    timestamp: str
    data_confidence: DataConfidence
    findings: dict[str, object]
    source: dict[str, str]
    sources: list[str]
    warnings: list[str]
    errors: list[CMISError]


class X1ScoutState(TypedDict):
    request: X1ScoutRequest
    status: Literal["running", "complete", "error"]
    cmis_result: NotRequired[CMISResult]
    report: NotRequired[X1ScoutReport]
