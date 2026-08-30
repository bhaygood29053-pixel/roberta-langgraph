from __future__ import annotations

from copy import deepcopy
import json

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    INSTANT_X1_SCAN_CONTRACT_VERSION,
    INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION,
    require_instant_x1_scan_capability,
    validate_capability_manifest,
)
from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.planner import enforce_plan, select_cmis_operation
from roberta.x1_scout.tool import build_x1_scout_tool


EXACT_MINT = "11111111111111111111111111111111"


def test_instant_x1_scan_capability_requires_exact_accepted_contract() -> None:
    manifest = validate_capability_manifest(MockCMISClient().capabilities())

    capability = require_instant_x1_scan_capability(manifest, chain="x1")

    assert manifest["contract_version"] == INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION
    assert capability["state"] == "bounded"
    assert capability["callable"] is True
    assert capability["service_contract_version"] == INSTANT_X1_SCAN_CONTRACT_VERSION
    assert capability["read_only"] is True
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["execution_authorized"] is False


def test_instant_x1_scan_capability_fails_closed_on_old_or_weakened_contract() -> None:
    old = deepcopy(MockCMISClient().capabilities())
    old["contract_version"] = "1.12.0"
    with pytest.raises(CMISCapabilityContractError, match="requires contract"):
        require_instant_x1_scan_capability(
            validate_capability_manifest(old),
            chain="x1",
        )

    wrong_contract = deepcopy(MockCMISClient().capabilities())
    wrong_contract["chains"]["x1"]["services"]["instant_x1_scan"][
        "service_contract_version"
    ] = "instant_x1_scan/v0"
    with pytest.raises(CMISCapabilityContractError, match="service contract mismatch"):
        require_instant_x1_scan_capability(
            validate_capability_manifest(wrong_contract),
            chain="x1",
        )

    promoted_execution = deepcopy(MockCMISClient().capabilities())
    promoted_execution["chains"]["x1"]["services"]["instant_x1_scan"][
        "execution_authorized"
    ] = True
    with pytest.raises(CMISCapabilityContractError, match="execution_authorized=false"):
        require_instant_x1_scan_capability(
            validate_capability_manifest(promoted_execution),
            chain="x1",
        )


def test_instant_x1_scan_capability_has_no_solana_fallback() -> None:
    manifest = validate_capability_manifest(MockCMISClient().capabilities())

    with pytest.raises(CMISCapabilityUnavailable, match="solana/instant_x1_scan"):
        require_instant_x1_scan_capability(manifest, chain="solana")


@pytest.mark.parametrize(
    "objective",
    [
        "Instant X1 scan AGI",
        "quick X1 scan this token",
        "scan this asset",
    ],
)
def test_instant_scan_objectives_select_single_composition_service(
    objective: str,
) -> None:
    assert select_cmis_operation(objective) == "instant_x1_scan"

    plan = enforce_plan(
        {"asset": "AGI", "objective": objective},
        {"operations": ["market_report", "risk_check", "instant_x1_scan"]},
    )

    assert plan["operations"] == ["instant_x1_scan"]


def test_planner_cannot_silently_promote_instant_scan_for_other_objective() -> None:
    plan = enforce_plan(
        {"asset": "AGI", "objective": "assess market risk"},
        {"operations": ["instant_x1_scan"]},
    )

    assert plan["operations"] == ["risk_check"]
    assert any(
        warning
        == "planner_operation_rejected_without_instant_scan_objective: instant_x1_scan"
        for warning in plan["warnings"]
    )


def test_x1_scout_uses_single_cmis_composition_and_preserves_unknowns() -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": EXACT_MINT,
                "objective": "Instant X1 scan this asset",
            },
            "status": "running",
        }
    )

    assert [call["operation"] for call in cmis.calls] == ["instant_x1_scan"]
    report = result["report"]
    assert report["status"] == "complete"
    assert report["source"] == {"service": "cmis", "operation": "instant_x1_scan"}
    assert report["plan"]["operations"] == ["instant_x1_scan"]

    presentation = report["instant_x1_scan_presentation"]
    assert presentation["contract_version"] == INSTANT_X1_SCAN_CONTRACT_VERSION
    assert presentation["read_only"] is True
    assert presentation["execution_authorized"] is False
    holder = presentation["sections"]["holder_concentration"]
    assert holder["holders"] is None
    assert holder["holders_verified"] is False
    assert holder["top_account_concentration"]["state"] == "unavailable"
    assert holder["top_account_concentration"]["verified"] is False

    raw_data = report["findings"]["data"]
    assert raw_data["sections"]["holder_concentration"] == holder
    assert presentation["limitations"] == raw_data["limitations"]


def test_x1_scout_fails_closed_before_dispatch_when_scan_contract_is_stale() -> None:
    class OldScanCMIS(MockCMISClient):
        def capabilities(self):
            manifest = super().capabilities()
            manifest["contract_version"] = "1.12.0"
            return manifest

    cmis = OldScanCMIS()
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "Instant X1 scan AGI",
            },
            "status": "running",
        }
    )

    assert cmis.calls == []
    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "unavailable"
    assert report["findings"]["data"] == {}
    assert any(
        warning.get("code") == "cmis_instant_x1_scan_contract_unavailable"
        for warning in report["warnings"]
    )


def test_x1_scout_tool_exposes_explicit_instant_scan_without_execution_inputs() -> None:
    cmis = MockCMISClient()
    tool = build_x1_scout_tool(cmis)

    report = json.loads(
        tool.invoke(
            {
                "asset": "AGI",
                "objective": "Instant X1 scan AGI",
                "operation": "instant_x1_scan",
            }
        )
    )

    assert [call["operation"] for call in cmis.calls] == ["instant_x1_scan"]
    assert report["source"]["operation"] == "instant_x1_scan"
    assert report["instant_x1_scan_presentation"]["execution_authorized"] is False


def test_explicit_instant_scan_rejects_trade_parameters() -> None:
    tool = build_x1_scout_tool(MockCMISClient())

    with pytest.raises(ValueError, match="trade action/amount"):
        tool.invoke(
            {
                "asset": "AGI",
                "objective": "Instant X1 scan AGI",
                "operation": "instant_x1_scan",
                "action": "BUY",
                "amount_usd": 100.0,
            }
        )
