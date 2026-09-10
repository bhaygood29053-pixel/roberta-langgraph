from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    X1_INTELLIGENCE_BRIEF_REQUIRED_LIMITATIONS,
    X1_INTELLIGENCE_BRIEF_REQUIRED_REQUIREMENTS,
    require_x1_intelligence_brief_capability,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.x1_intelligence_brief import (
    SERVICE,
    SUPPORTED_COMPONENT_SERVICES,
    CMISX1IntelligenceBriefContractError,
    normalize_x1_intelligence_brief_request,
)
from roberta.x1_scout.daily_intelligence_brief_runtime import (
    X1_DAILY_BRIEF_RUNTIME_CONTRACT,
    build_x1_daily_intelligence_brief_runtime,
)


MINT = "7SXmUpcBGSAwW5LmtzQVF9jHswZ7xzmdKqWa4nDgL3ER"


def capability_manifest(version="1.28.0"):
    brief = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": "x1_intelligence_brief_inputs/v1",
        "request_contract_version": "x1_intelligence_brief_request/v1",
        "composition_contract_version": "x1_intelligence_brief_inputs/v1",
        "requirements": list(X1_INTELLIGENCE_BRIEF_REQUIRED_REQUIREMENTS),
        "limitations": list(X1_INTELLIGENCE_BRIEF_REQUIRED_LIMITATIONS),
        "complete_x1_ecosystem_coverage_verified": False,
        "execution_authorized": False,
    }
    return {
        "contract_version": version,
        "chains": {
            "x1": {"services": {SERVICE: brief}},
            "solana": {
                "services": {
                    SERVICE: {
                        "state": "unavailable",
                        "callable": False,
                        "read_only": True,
                        "public_service_promoted": False,
                        "scout_reliance_promoted": False,
                        "requirements": [],
                        "limitations": [
                            "x1_intelligence_brief_inputs_not_available_for_chain"
                        ],
                        "complete_x1_ecosystem_coverage_verified": False,
                        "execution_authorized": False,
                    }
                }
            },
        },
    }


def foundation():
    return {
        "brief_inputs_id": "xib_runtime_test",
        "contract_version": "x1_intelligence_brief_inputs/v1",
        "chain": "x1",
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "subjects": [MINT],
        "requested_services": sorted(SUPPORTED_COMPONENT_SERVICES),
        "window": {
            "start": "2026-09-09T00:00:00Z",
            "end": "2026-09-10T00:00:00Z",
            "end_exclusive": True,
            "duration_seconds": 86400,
        },
        "items": [],
        "component_evaluations": [],
        "coverage": {
            "requested_subject_count": 1,
            "resolved_subject_count": 1,
            "requested_service_count": 3,
            "input_service_classes_requested": sorted(
                SUPPORTED_COMPONENT_SERVICES
            ),
            "input_service_classes_evaluated": sorted(
                SUPPORTED_COMPONENT_SERVICES
            ),
            "partial_service_classes": [],
            "unavailable_service_classes": [],
            "error_or_ambiguous_service_classes": [],
            "component_response_matrix_complete": True,
            "duplicate_exact_component_responses_collapsed": 0,
            "included_item_count": 0,
            "outside_window_item_count": 0,
            "window_start": "2026-09-09T00:00:00Z",
            "window_end": "2026-09-10T00:00:00Z",
            "window_end_exclusive": True,
            "earliest_included_fact_time": None,
            "latest_included_fact_time": None,
            "complete_x1_ecosystem_coverage_verified": False,
        },
        "priority_is_risk_severity": False,
        "proof_score_separate_from_risk": True,
        "missing_evidence_zero_filled": False,
        "complete_x1_ecosystem_coverage_verified": False,
        "execution_authorized": False,
    }


def envelope():
    return {
        "service": SERVICE,
        "chain": "x1",
        "status": "ok",
        "asset": {},
        "data": foundation(),
        "risk": None,
        "confidence": {
            "basis": "deterministic_bounded_cmis_component_composition",
            "proof_score_separate_from_risk": True,
            "complete_x1_ecosystem_coverage_verified": False,
        },
        "sources": [
            {
                "component_service": name,
                "component_contract_version": f"{name}/v1",
            }
            for name in SUPPORTED_COMPONENT_SERVICES
        ],
        "observed_at": None,
        "freshness": {
            "contract_version": "cmis_response_freshness/v1",
            "scope": f"{SERVICE}.response",
            "state": "UNKNOWN",
            "freshness_verified": None,
            "observed_at": None,
            "details": {},
        },
        "warnings": [],
        "errors": [],
        "evidence_receipt": {"receipt_id": "er_runtime"},
        "proof_score": {"proof_strength": "MODERATE"},
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "runtime_capability_promoted": True,
        "complete_x1_ecosystem_coverage_verified": False,
        "execution_authorized": False,
    }


def expected_request():
    return normalize_x1_intelligence_brief_request(
        subjects=[MINT],
        window_start="2026-09-09T00:00:00Z",
        window_end="2026-09-10T00:00:00Z",
        requested_services=list(SUPPORTED_COMPONENT_SERVICES),
    )


def test_requires_exact_cmis_128_promoted_capability():
    capability = require_x1_intelligence_brief_capability(
        capability_manifest(),
        chain="x1",
    )

    assert capability["state"] == "bounded"
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["complete_x1_ecosystem_coverage_verified"] is False
    assert capability["execution_authorized"] is False

    with pytest.raises(CMISCapabilityContractError, match="requires contract"):
        require_x1_intelligence_brief_capability(
            capability_manifest("1.27.0"),
            chain="x1",
        )


def test_missing_claim_integrity_limitation_fails_capability_handshake():
    manifest = capability_manifest()
    manifest["chains"]["x1"]["services"][SERVICE]["limitations"].remove(
        "sequence_or_activity_is_not_causality"
    )

    with pytest.raises(CMISCapabilityContractError, match="missing accepted limitations"):
        require_x1_intelligence_brief_capability(manifest, chain="x1")


def test_builds_live_wrapper_without_mutating_nested_typed_brief():
    upstream = envelope()
    before = deepcopy(upstream)

    runtime = build_x1_daily_intelligence_brief_runtime(
        upstream,
        expected_request=expected_request(),
    )

    assert runtime["contract_version"] == X1_DAILY_BRIEF_RUNTIME_CONTRACT
    assert runtime["product"] == "x1_daily_intelligence_brief_runtime"
    assert runtime["runtime_reliance_authorized"] is True
    assert runtime["public_service_promoted"] is True
    assert runtime["scout_reliance_promoted"] is True
    assert runtime["complete_x1_ecosystem_coverage_verified"] is False
    assert runtime["provider_truth_certified"] is False
    assert runtime["execution_authorized"] is False

    typed = runtime["daily_brief"]
    assert typed["contract_version"] == "x1_daily_intelligence_brief/v1"
    assert typed["runtime_reliance_authorized"] is False
    assert typed["complete_x1_ecosystem_coverage_verified"] is False
    assert typed["execution_authorized"] is False
    assert upstream == before


def test_nested_fact_contract_cannot_self_promote():
    upstream = envelope()
    upstream["data"]["public_service_promoted"] = True

    with pytest.raises(
        Exception,
        match="Nested Brief factual contract must keep public_service_promoted=false",
    ):
        build_x1_daily_intelligence_brief_runtime(
            upstream,
            expected_request=expected_request(),
        )


def test_outer_service_must_be_promoted_and_freshness_stays_unknown():
    upstream = envelope()
    upstream["runtime_capability_promoted"] = False

    with pytest.raises(Exception, match="runtime_capability_promoted"):
        build_x1_daily_intelligence_brief_runtime(
            upstream,
            expected_request=expected_request(),
        )

    upstream = envelope()
    upstream["freshness"]["state"] = "VERIFIED"
    upstream["freshness"]["freshness_verified"] = True

    with pytest.raises(Exception, match="freshness must remain UNKNOWN"):
        build_x1_daily_intelligence_brief_runtime(
            upstream,
            expected_request=expected_request(),
        )


class CapturingClient(CMISHTTPClient):
    def __init__(self):
        super().__init__(base_url="http://cmis.invalid")
        self.sent = None

    def capabilities(self):
        return capability_manifest()

    def _send_payload(self, **kwargs):
        self.sent = kwargs
        return envelope()


def test_http_call_uses_selector_only_payload_without_top_level_asset():
    client = CapturingClient()

    result = client.x1_intelligence_brief_inputs(
        chain="x1",
        subjects=[MINT],
        window_start="2026-09-09T00:00:00Z",
        window_end="2026-09-10T00:00:00Z",
        requested_services=list(SUPPORTED_COMPONENT_SERVICES),
    )

    assert result["service"] == SERVICE
    payload = client.sent["payload"]
    assert set(payload) == {"service", "chain", "params"}
    assert "asset" not in payload
    assert payload["service"] == SERVICE
    assert payload["chain"] == "x1"
    assert payload["params"] == expected_request()


def test_request_is_exact_three_service_bounded_scope():
    with pytest.raises(
        CMISX1IntelligenceBriefContractError,
        match="accepted three-service",
    ):
        normalize_x1_intelligence_brief_request(
            subjects=[MINT],
            window_start="2026-09-09T00:00:00Z",
            window_end="2026-09-10T00:00:00Z",
            requested_services=["large_trade_discovery"],
        )

    with pytest.raises(
        CMISX1IntelligenceBriefContractError,
        match="<=86400",
    ):
        normalize_x1_intelligence_brief_request(
            subjects=[MINT],
            window_start="2026-09-09T00:00:00Z",
            window_end="2026-09-10T00:00:01Z",
            requested_services=list(SUPPORTED_COMPONENT_SERVICES),
        )


def test_x1_scout_runtime_route_is_explicit_only_and_reported():
    planner = Path("src/roberta/x1_scout/planner.py").read_text(encoding="utf-8")
    graph = Path("src/roberta/x1_scout/graph.py").read_text(encoding="utf-8")
    state = Path("src/roberta/x1_scout/state.py").read_text(encoding="utf-8")

    assert '"x1_intelligence_brief_inputs"' not in planner.split(
        "AUTONOMOUS_OPERATIONS", 1
    )[1].split(")", 1)[0]
    assert 'if operation == "x1_intelligence_brief_inputs":' in planner
    assert 'if operation == "x1_intelligence_brief_inputs":' in graph
    assert "build_x1_daily_intelligence_brief_runtime" in graph
    assert "x1_daily_intelligence_brief_runtime" in graph
    assert "daily_brief_subjects" in state
    assert "x1_daily_intelligence_brief_runtime" in state
