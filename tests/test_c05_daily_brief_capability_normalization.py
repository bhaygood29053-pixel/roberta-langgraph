from __future__ import annotations

from copy import deepcopy

import pytest

from roberta.cmis.capabilities import (
    CAPABILITY_SCHEMA_VERSION,
    CMISCapabilityContractError,
    INTELLIGENCE_FOUNDATION_CAPABILITIES,
    INTELLIGENCE_FOUNDATION_PHASE,
    INTELLIGENCE_PROMOTION_RULE,
    RESPONSE_FRESHNESS_CONTRACT_VERSION,
    X1_INTELLIGENCE_BRIEF_REQUIRED_LIMITATIONS,
    X1_INTELLIGENCE_BRIEF_REQUIRED_REQUIREMENTS,
    X1_INTELLIGENCE_BRIEF_SERVICE_CONTRACT_VERSION,
    X1_INTELLIGENCE_BRIEF_REQUEST_CONTRACT_VERSION,
    X1_INTELLIGENCE_BRIEF_COMPOSITION_CONTRACT_VERSION,
    require_x1_intelligence_brief_capability,
    validate_capability_manifest,
)


SERVICE = "x1_intelligence_brief_inputs"


def _foundation_capability() -> dict[str, object]:
    return {
        "state": "bounded",
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "requirements": [],
        "limitations": [],
    }


def _raw_manifest() -> dict[str, object]:
    x1_brief = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": X1_INTELLIGENCE_BRIEF_SERVICE_CONTRACT_VERSION,
        "request_contract_version": X1_INTELLIGENCE_BRIEF_REQUEST_CONTRACT_VERSION,
        "composition_contract_version": X1_INTELLIGENCE_BRIEF_COMPOSITION_CONTRACT_VERSION,
        "requirements": list(X1_INTELLIGENCE_BRIEF_REQUIRED_REQUIREMENTS),
        "limitations": list(X1_INTELLIGENCE_BRIEF_REQUIRED_LIMITATIONS),
        "complete_x1_ecosystem_coverage_verified": False,
        "execution_authorized": False,
    }
    solana_brief = {
        "state": "unavailable",
        "callable": False,
        "requirements": [],
        "limitations": ["x1_intelligence_brief_inputs_not_available_for_chain"],
    }
    return {
        "service": "cmis_gateway",
        "version": CAPABILITY_SCHEMA_VERSION,
        "schema_version": CAPABILITY_SCHEMA_VERSION,
        "contract_version": "1.30.0",
        "request_path": "/v1/cmis",
        "response_freshness": {
            "contract_version": RESPONSE_FRESHNESS_CONTRACT_VERSION,
            "required_on_every_public_response": True,
            "observation_time_alone_never_proves_provider_fact_freshness": True,
            "missing_service_specific_freshness_fails_closed": True,
        },
        "evidence_quality": {
            "evidence_receipt_schema_version": 1,
            "proof_score_schema_version": 1,
            "proof_strength_values": ["STRONG", "MODERATE", "WEAK"],
            "risk_separate_from_proof": True,
            "missing_evidence_is_unknown": True,
        },
        "intelligence_foundation": {
            "schema_version": 1,
            "phase": INTELLIGENCE_FOUNDATION_PHASE,
            "read_only": True,
            "public_service_promoted": False,
            "scout_reliance_promoted": False,
            "promotion_rule": INTELLIGENCE_PROMOTION_RULE,
            "intelligence_evidence_schema_version": 1,
            "capabilities": {
                name: _foundation_capability()
                for name in INTELLIGENCE_FOUNDATION_CAPABILITIES
            },
        },
        "supported_services": [SERVICE],
        "supported_chains": ["x1"],
        "known_chains": ["x1", "solana"],
        "chains": {
            "x1": {
                "services": {SERVICE: x1_brief},
                "callable_services": [SERVICE],
            },
            "solana": {
                "services": {SERVICE: solana_brief},
                "callable_services": [],
            },
        },
    }


def test_raw_manifest_preserves_daily_brief_contract_through_normalization():
    normalized = validate_capability_manifest(_raw_manifest())
    capability = normalized["chains"]["x1"]["services"][SERVICE]

    assert capability["service_contract_version"] == X1_INTELLIGENCE_BRIEF_SERVICE_CONTRACT_VERSION
    assert capability["request_contract_version"] == X1_INTELLIGENCE_BRIEF_REQUEST_CONTRACT_VERSION
    assert capability["composition_contract_version"] == X1_INTELLIGENCE_BRIEF_COMPOSITION_CONTRACT_VERSION
    assert capability["read_only"] is True
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["complete_x1_ecosystem_coverage_verified"] is False
    assert capability["execution_authorized"] is False

    accepted = require_x1_intelligence_brief_capability(normalized, chain="x1")
    assert accepted is capability


def test_daily_brief_normalizer_preserves_fail_closed_contract_validation():
    raw = _raw_manifest()
    raw["chains"]["x1"]["services"][SERVICE]["service_contract_version"] = "wrong/v0"
    normalized = validate_capability_manifest(raw)

    with pytest.raises(CMISCapabilityContractError, match="service contract mismatch"):
        require_x1_intelligence_brief_capability(normalized, chain="x1")


def test_daily_brief_normalizer_preserves_execution_false():
    raw = deepcopy(_raw_manifest())
    raw["chains"]["x1"]["services"][SERVICE]["execution_authorized"] = True
    normalized = validate_capability_manifest(raw)

    with pytest.raises(CMISCapabilityContractError, match="execution_authorized must be false"):
        require_x1_intelligence_brief_capability(normalized, chain="x1")
