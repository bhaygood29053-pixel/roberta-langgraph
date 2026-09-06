from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    REGULATORY_EVIDENCE_MIN_CMIS_CONTRACT_VERSION,
    REGULATORY_EVIDENCE_REQUIRED_LIMITATIONS,
    REGULATORY_EVIDENCE_REQUIRED_REQUIREMENTS,
    require_regulatory_evidence_capability,
    validate_capability_manifest,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.regulatory_evidence import (
    CMISRegulatoryEvidenceContractError,
    SERVICE_CONTRACT_VERSION,
    canonical_regulatory_evidence_from_response,
    normalize_regulatory_evidence_request,
    validate_regulatory_evidence_response,
)
from roberta.regulatory import build_regulatory_intelligence
from roberta.x1_scout.regulatory_intelligence import (
    REGULATORY_INTELLIGENCE_CONTRACT,
    build_x1_regulatory_intelligence,
)
from tests.test_cmis_http_client import _Server, _capabilities


MINT = "B69chRzqzDCmdB5WYB8NRu5Yv5ZA95ABiZcdzCgGm9Tq"
EVALUATED_AT = "2026-09-06T16:00:00Z"
STATUS_AS_OF = "2026-09-06T15:30:00Z"


STATIC_SOURCE = {
    "source_id": "genius-act-public-law-119-27",
    "framework": "GENIUS Act",
    "law_id": "Public Law 119-27",
    "authority_class": "primary",
    "live_state_authority": False,
    "execution_authorized": False,
}


def _promoted_capabilities():
    value = deepcopy(_capabilities())
    value["contract_version"] = "1.26.0"
    value["supported_services"].append("regulatory_evidence")

    x1 = value["chains"]["x1"]
    x1["services"]["regulatory_evidence"] = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "requirements": list(REGULATORY_EVIDENCE_REQUIRED_REQUIREMENTS),
        "limitations": list(REGULATORY_EVIDENCE_REQUIRED_LIMITATIONS),
        "compliance_conclusion_authorized": False,
        "execution_authorized": False,
    }
    x1["callable_services"].append("regulatory_evidence")

    solana = value["chains"]["solana"]
    solana["services"]["regulatory_evidence"] = {
        "state": "unavailable",
        "callable": False,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "requirements": [],
        "limitations": ["regulatory_evidence_not_available_for_chain"],
        "compliance_conclusion_authorized": False,
        "execution_authorized": False,
    }
    return value


def _request():
    return normalize_regulatory_evidence_request(
        jurisdiction="US",
        framework="GENIUS Act",
        asset_id="USDC.X",
        chain_asset_id=MINT,
        evaluated_at=EVALUATED_AT,
        max_evidence_age_seconds=86400,
    )


def _envelope():
    data_sources = [
        {
            "authority_class": "primary_law",
            "publisher": "U.S. Government Publishing Office",
            "title": "Public Law 119-27 — GENIUS Act",
            "url": "https://www.govinfo.gov/app/details/PLAW-119publ27",
            "published_on": "2025-07-18",
            "retrieved_at": STATUS_AS_OF,
        },
        {
            "authority_class": "primary_regulator",
            "publisher": "U.S. Department of the Treasury",
            "title": "Treasury Seeks Public Comment on GENIUS Act Proposed Rulemaking",
            "url": "https://home.treasury.gov/news/press-releases/sb0605",
            "published_on": "2026-08-17",
            "retrieved_at": STATUS_AS_OF,
        },
    ]
    return {
        "service": "regulatory_evidence",
        "chain": "x1",
        "status": "ok",
        "asset": {"canonical_id": MINT, "mint": MINT},
        "data": {
            "contract_version": SERVICE_CONTRACT_VERSION,
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "read_only": True,
            "jurisdiction": "US",
            "framework": "GENIUS Act",
            "legal": {
                "law_id": "Public Law 119-27",
                "enacted_on": "2025-07-18",
                "status": "enacted",
            },
            "current_regulatory_state": {
                "rulemaking_status": "proposed_rule",
                "final_rule_verified": False,
                "effective_now_verified": False,
                "status_as_of": STATUS_AS_OF,
            },
            "asset": {
                "asset_id": "USDC.X",
                "chain": "x1",
                "asset_id_kind": "mint",
                "chain_scoped_asset_id": MINT,
                "representation_type": "bridged",
                "underlying_asset": "USDC",
                "bridge_dependency": True,
                "custody_dependency": True,
            },
            "issuer": {
                "name": "Circle",
                "identity_status": "PROVIDER_REPORTED",
            },
            "applicability": "INSUFFICIENT_EVIDENCE",
            "freshness": {
                "status_as_of": STATUS_AS_OF,
                "evaluated_at": EVALUATED_AT,
                "age_seconds": 1800.0,
                "max_evidence_age_seconds": 86400.0,
                "freshness_verified": True,
            },
            "sources": data_sources,
            "limitations": [
                "Current proposed-rule status does not establish final regulation.",
                "Issuer licensing and compliance are not established.",
                "Underlying USDC evidence does not establish USDC.X bridge or custody safety.",
            ],
            "compliance_conclusion_authorized": False,
            "compliance_conclusion": None,
            "legal_advice_authorized": False,
            "execution_authorized": False,
        },
        "risk": None,
        "confidence": {
            "canonical_regulatory_record_validated": True,
            "exact_x1_mint_identity_verified": True,
            "primary_law_provenance_present": True,
            "primary_regulator_provenance_present": True,
            "freshness_verified": True,
        },
        "sources": [
            {
                "source": source["title"],
                "publisher": source["publisher"],
                "scope": source["authority_class"],
                "observed_at": source["retrieved_at"],
            }
            for source in data_sources
        ],
        "observed_at": STATUS_AS_OF,
        "warnings": [
            {
                "code": "regulatory_status_is_not_compliance",
                "message": "Regulatory status is not compliance.",
            }
        ],
        "errors": [],
        "execution_authorized": False,
    }


def test_cmis_126_regulatory_capability_is_exact_and_bounded():
    manifest = validate_capability_manifest(_promoted_capabilities())
    capability = require_regulatory_evidence_capability(manifest)
    assert REGULATORY_EVIDENCE_MIN_CMIS_CONTRACT_VERSION == "1.26.0"
    assert capability["service_contract_version"] == SERVICE_CONTRACT_VERSION
    assert capability["state"] == "bounded"
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["compliance_conclusion_authorized"] is False
    assert capability["execution_authorized"] is False


def test_regulatory_capability_rejects_guardrail_drift():
    raw = _promoted_capabilities()
    raw["chains"]["x1"]["services"]["regulatory_evidence"]["limitations"].remove(
        "proposed_rule_is_not_final_rule"
    )
    manifest = validate_capability_manifest(raw)
    with pytest.raises(CMISCapabilityContractError, match="missing accepted limitations"):
        require_regulatory_evidence_capability(manifest)


def test_response_preserves_proposed_rule_freshness_and_exact_mint():
    accepted = validate_regulatory_evidence_response(
        _envelope(),
        expected_request=_request(),
    )
    assert accepted["data"]["asset"]["chain_scoped_asset_id"] == MINT
    assert accepted["data"]["current_regulatory_state"]["rulemaking_status"] == (
        "proposed_rule"
    )
    assert accepted["data"]["freshness"]["freshness_verified"] is True
    assert accepted["risk"] is None


def test_response_rejects_proposed_rule_promoted_as_final():
    bad = _envelope()
    bad["data"]["current_regulatory_state"]["final_rule_verified"] = True
    with pytest.raises(
        CMISRegulatoryEvidenceContractError,
        match="proposed rule cannot be promoted",
    ):
        validate_regulatory_evidence_response(bad, expected_request=_request())


def test_response_rejects_exact_mint_mismatch():
    bad = _envelope()
    bad["data"]["asset"]["chain_scoped_asset_id"] = "different-mint"
    with pytest.raises(
        CMISRegulatoryEvidenceContractError,
        match="exact X1 mint mismatch",
    ):
        validate_regulatory_evidence_response(bad, expected_request=_request())


def test_http_client_posts_only_selectors_and_freshness_inputs():
    expected = _envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).regulatory_evidence(
            chain="x1",
            jurisdiction="US",
            framework="GENIUS Act",
            asset_id="USDC.X",
            chain_asset_id=MINT,
            evaluated_at=EVALUATED_AT,
            max_evidence_age_seconds=86400,
        )

    assert result == expected
    assert running.requests == [{
        "service": "regulatory_evidence",
        "chain": "x1",
        "asset": MINT,
        "params": _request(),
    }]


def test_http_client_blocks_regulatory_service_before_cmis_126_without_post():
    capabilities = _promoted_capabilities()
    capabilities["contract_version"] = "1.25.0"
    with _Server(_envelope(), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).regulatory_evidence(
            chain="x1",
            jurisdiction="US",
            framework="GENIUS Act",
            asset_id="USDC.X",
            chain_asset_id=MINT,
            evaluated_at=EVALUATED_AT,
            max_evidence_age_seconds=86400,
        )
    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == (
        "cmis_regulatory_evidence_contract_unavailable"
    )
    assert running.requests == []


def test_x1_regulatory_product_preserves_cmis_projection_and_no_compliance():
    product = build_x1_regulatory_intelligence(
        _envelope(),
        expected_request=_request(),
    )
    assert product["contract_version"] == REGULATORY_INTELLIGENCE_CONTRACT
    assert product["requested_chain_asset_id"] == MINT
    assert product["current_regulatory_state"]["rulemaking_status"] == "proposed_rule"
    assert product["compliance_conclusion_authorized"] is False
    assert product["legal_advice_authorized"] is False
    assert product["automatic_risk_conclusion_authorized"] is False
    assert product["risk_interpretation"] is None
    assert product["execution_authorized"] is False


def test_promoted_cmis_evidence_feeds_existing_roberta_regulatory_reasoning():
    canonical = canonical_regulatory_evidence_from_response(
        _envelope(),
        expected_request=_request(),
    )
    view = build_regulatory_intelligence(STATIC_SOURCE, canonical)
    assert view["contract"] == "roberta_regulatory_intelligence/v1"
    assert view["current_evidence"]["state"] == "CMIS_VERIFIED_BOUNDARY"
    assert view["current_evidence"]["asset"]["chain_scoped_asset_id"] == MINT
    assert view["roberta_judgment"]["legal_compliance"] is None
    assert view["roberta_judgment"]["bridge_custody_risk_preserved"] is True
    assert view["legal_advice"] is False
    assert view["execution_authorized"] is False


def test_public_x1_scout_wiring_is_explicit_and_first_class():
    graph = Path("src/roberta/x1_scout/graph.py").read_text(encoding="utf-8")
    tool = Path("src/roberta/x1_scout/tool.py").read_text(encoding="utf-8")
    assert 'operation == "regulatory_evidence"' in graph
    assert "cmis_client.regulatory_evidence(" in graph
    assert 'report["x1_regulatory_intelligence"]' in graph
    assert "build_x1_regulatory_intelligence(" in graph
    assert '"regulatory_evidence",' in tool
    assert "regulatory_chain_asset_id" in tool
    assert "regulatory_max_evidence_age_seconds" in tool
