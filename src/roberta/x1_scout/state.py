"""LangGraph state for the X1 Scout specialist subgraph."""

from typing import Literal, NotRequired, TypedDict

from roberta.cmis.contracts import CMISMarketReport


class X1ScoutRequest(TypedDict):
    asset: str
    objective: str


class X1ScoutReport(TypedDict):
    specialist: Literal["x1_scout"]
    chain: Literal["x1"]
    asset: str
    objective: str
    status: Literal["complete"]
    data_confidence: Literal["TEST_ONLY"]
    findings: dict[str, object]
    source: dict[str, str]
    warnings: list[str]


class X1ScoutState(TypedDict):
    request: X1ScoutRequest
    status: Literal["running", "complete", "error"]
    cmis_result: NotRequired[CMISMarketReport]
    report: NotRequired[X1ScoutReport]
