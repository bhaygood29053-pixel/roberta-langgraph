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
    assert capability["composition_only"] is True
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

    broadened = deepcopy(MockCMISClient().capabilities())
    broadened["chains"]["x1"]["services"]["instant_x1_scan"]["state"] = "supported"
    with pytest.raises(CMISCapabilityContractError, match="state must remain bounded"):
        require_instant_x1_scan_capability(
            validate_capability_manifest(broadened),
            chain="x1",
        )

    non_composition = deepcopy(MockCMISClient().capabilities())
    non_composition["chains"]["x1"]["services"]["instant_x1_scan"][
        "composition_only"
    ] = False
    with pytest.raises(CMISCapabilityContractError, match="composition-only"):
        require_instant_x1_scan_capability(
            validate_capability_manifest(non_composition),
            chain="x1",
        )

    missing_composition = deepcopy(MockCMISClient().capabilities())
    del missing_composition["chains"]["x1"]["services"]["instant_x1_scan"][
        "composition_only"
    ]
    with pytest.raises(CMISCapabilityContractError, match="composition_only must be boolean"):
        validate_capability_manifest(missing_composition)

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
        "scan AGI",
        "scan XNT",
        "scan token AGI",
        "please scan AGI",
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


@pytest.mark.parametrize("bad_envelope", [None, [], ["not", "an", "object"]])
def test_x1_scout_rejects_non_object_scan_envelope(
    bad_envelope: object,
) -> None:
    class NonObjectCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            self.calls.append(
                {"operation": "instant_x1_scan", "chain": chain, "asset": asset}
            )
            return bad_envelope

    result = build_x1_scout_graph(NonObjectCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["findings"]["risk"] is None
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"


def test_x1_scout_rejects_malformed_successful_scan_payload() -> None:
    class MalformedScanCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["data"]["read_only"] = False
            result["data"]["execution_authorized"] = True
            return result

    cmis = MalformedScanCMIS()
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

    assert [call["operation"] for call in cmis.calls] == ["instant_x1_scan"]
    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"
    assert "instant_x1_scan_presentation" not in report


@pytest.mark.parametrize("field,bad_value", [
    ("flags", 7),
    ("reasons", {"reason": "bad shape"}),
])
def test_x1_scout_rejects_malformed_scan_risk_collections(
    field: str,
    bad_value: object,
) -> None:
    class MalformedRiskCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["data"]["sections"]["risk"][field] = bad_value
            return result

    result = build_x1_scout_graph(MalformedRiskCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"
    assert "instant_x1_scan_presentation" not in report


@pytest.mark.parametrize(
    "mutation",
    [
        lambda risk: risk.__setitem__("flags", 7),
        lambda risk: risk.__setitem__("reasons", {"reason": "bad shape"}),
        lambda risk: risk.__setitem__("execution_authorized", True),
        lambda risk: risk.__setitem__("recommendation", "DIFFERENT"),
    ],
)
def test_x1_scout_rejects_malformed_or_inconsistent_envelope_risk(
    mutation,
) -> None:
    class MalformedEnvelopeRiskCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            mutation(result["risk"])
            return result

    result = build_x1_scout_graph(MalformedEnvelopeRiskCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["findings"]["risk"] is None
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"
    assert "instant_x1_scan_presentation" not in report


@pytest.mark.parametrize(
    "bad_status",
    [None, "", "complete", "success", "OK", " partial ", [], {}, ["ok"]],
)
def test_x1_scout_rejects_unsupported_scan_status(
    bad_status: object,
) -> None:
    class BadStatusCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["status"] = bad_status
            return result

    result = build_x1_scout_graph(BadStatusCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["findings"]["risk"] is None
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"
    assert "instant_x1_scan_presentation" not in report


@pytest.mark.parametrize(
    "score,score_verified",
    [
        ("high", True),
        (float("nan"), True),
        (float("inf"), True),
        (None, True),
        (1.0, "true"),
    ],
)
def test_x1_scout_rejects_malformed_or_incoherent_risk_score(
    score: object,
    score_verified: object,
) -> None:
    class MalformedScoreCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            for risk in (
                result["risk"],
                result["data"]["sections"]["risk"],
            ):
                risk["score"] = score
                risk["score_verified"] = score_verified
            return result

    result = build_x1_scout_graph(MalformedScoreCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["findings"]["risk"] is None
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"


def test_x1_scout_rejects_failed_scan_with_incomplete_outer_envelope() -> None:
    class MissingObservedAtCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["status"] = "unavailable"
            result["data"] = {}
            result["risk"] = None
            del result["observed_at"]
            return result

    result = build_x1_scout_graph(MissingObservedAtCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["findings"]["risk"] is None
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"


@pytest.mark.parametrize(
    "holders,holders_verified",
    [
        (None, True),
        (12, "true"),
        (12, False),
        (-1, True),
        (True, True),
    ],
)
def test_x1_scout_rejects_incoherent_holder_count_verification(
    holders: object,
    holders_verified: object,
) -> None:
    class IncoherentHoldersCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            holder = result["data"]["sections"]["holder_concentration"]
            holder["holders"] = holders
            holder["holders_verified"] = holders_verified
            return result

    result = build_x1_scout_graph(IncoherentHoldersCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["findings"]["risk"] is None
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"
    assert "instant_x1_scan_presentation" not in report


def test_x1_scout_accepts_verified_nonnegative_holder_count() -> None:
    class VerifiedHoldersCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            holder = result["data"]["sections"]["holder_concentration"]
            holder["holders"] = 12
            holder["holders_verified"] = True
            return result

    result = build_x1_scout_graph(VerifiedHoldersCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "complete"
    holder = report["instant_x1_scan_presentation"]["sections"][
        "holder_concentration"
    ]
    assert holder["holders"] == 12
    assert holder["holders_verified"] is True


def test_x1_scout_rejects_promoted_current_concentration_in_v1() -> None:
    class PromotedConcentrationCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            concentration = result["data"]["sections"]["holder_concentration"][
                "top_account_concentration"
            ]
            concentration["state"] = "available"
            concentration["verified"] = True
            concentration["value"] = 0.42
            return result

    result = build_x1_scout_graph(PromotedConcentrationCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "Instant X1 scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"


def test_x1_scout_accepts_canonical_ambiguous_upstream_diagnostic_without_product_view() -> None:
    class CanonicalAmbiguousCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["status"] = "ambiguous"
            result["data"] = {"upstream_service": "asset_lookup"}
            result["risk"] = None
            result["warnings"] = [{
                "code": "asset_ambiguous",
                "message": "Asset identity is ambiguous.",
            }]
            return result

    result = build_x1_scout_graph(CanonicalAmbiguousCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "ambiguous"
    assert report["findings"]["data"] == {"upstream_service": "asset_lookup"}
    assert report["findings"]["risk"] is None
    assert "instant_x1_scan_presentation" not in report
    assert report["warnings"][0]["code"] == "asset_ambiguous"


def test_x1_scout_rejects_extra_product_fields_on_failed_scan_diagnostic() -> None:
    class InvalidFailedDiagnosticCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["status"] = "ambiguous"
            result["data"] = {
                "upstream_service": "asset_lookup",
                "sections": {"market": {"price_usd": 1.0}},
            }
            result["risk"] = None
            return result

    result = build_x1_scout_graph(InvalidFailedDiagnosticCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert report["findings"]["risk"] is None
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"


def test_x1_scout_rejects_ambiguous_scan_that_carries_product_data() -> None:
    class AmbiguousScanWithDataCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["status"] = "ambiguous"
            return result

    result = build_x1_scout_graph(AmbiguousScanWithDataCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "Instant X1 scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert "instant_x1_scan_presentation" not in report
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"


@pytest.mark.parametrize("scenario, expected_status", [
    ("unavailable", "unavailable"),
    ("error", "error"),
])
def test_mock_failed_scan_scenarios_are_data_free_and_preserve_status(
    scenario: str,
    expected_status: str,
) -> None:
    cmis = MockCMISClient(scenario=scenario)
    result = build_x1_scout_graph(cmis).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "Instant X1 scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["cmis_status"] == expected_status
    assert report["findings"]["data"] == {}
    assert report["findings"]["risk"] is None
    assert "instant_x1_scan_presentation" not in report


def test_x1_scout_rejects_failed_scan_that_carries_product_data() -> None:
    class FailedScanWithDataCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["status"] = "unavailable"
            result["warnings"] = [{
                "code": "provider_unavailable",
                "message": "provider unavailable",
            }]
            return result

    result = build_x1_scout_graph(FailedScanWithDataCMIS()).invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "Instant X1 scan AGI",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["status"] == "error"
    assert report["cmis_status"] == "error"
    assert report["findings"]["data"] == {}
    assert "instant_x1_scan_presentation" not in report
    assert report["errors"][0]["code"] == "invalid_cmis_instant_x1_scan_response"


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
