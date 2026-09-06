from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    REGULATORY_EVIDENCE_CONTRACT_VERSION,
    REGULATORY_EVIDENCE_MIN_CMIS_CONTRACT_VERSION,
    REGULATORY_EVIDENCE_REQUIRED_LIMITATIONS,
    REGULATORY_EVIDENCE_REQUIRED_REQUIREMENTS,
    require_regulatory_evidence_capability,
    validate_capability_manifest,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.regulatory_evidence import (
    CMISRegulatoryEvidenceContractError,
    normalize_regulatory_evidence_request,
    validate_regulatory_evidence_response,
)
from roberta.x1_scout.regulatory_intelligence import (
    X1_REGULATORY_INTELLIGENCE_CONTRACT,
    build_x1_regulatory_intelligence,
)
from tests.test_cmis_http_client import _Server, _capabilities


MINT = "B69chRzqzDCmdB5WYB8NRu5Yv5ZA95ABiZcdzCgGm9Tq"
EVALUATED_AT = "2026-09-06T16:00:00Z"


def _request():
    return normalize_regulatory_evidence_request(
        jurisdiction="US",
        framework="GENIUS Act",
        asset_id="USDC.X",
        asset_mint=MINT,
        evaluated_at=EVALUATED_AT,
        max_evidence_age_seconds=86400,
    )


def _promoted_capabilities():
    value = deepcopy(_capabilities())
    value["contract_version"] = "1.26.0"
    if "regulatory_evidence" not in value["supported_services"]:
        value["supported_services"].append("regulatory_evidence")
    x1 = value["chains"]["x1"]
    x1["services"]["regulatory_evidence"] = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": REGULATORY_EVIDENCE_CONTRACT_VERSION,
        "requirements": list(REGULATORY_EVIDENCE_REQUIRED_REQUIREMENTS),
        "limitations": list(REGULATORY_EVIDENCE_REQUIRED_LIMITATIONS),
        "compliance_conclusion_authorized": False,
        "execution_authorized": False,
    }
    if "regulatory_evidence" not in x1["callable_services"]:
        x1["callable_services"].append("regulatory_evidence")
    solana = value["chains"]["solana"]
    solana["services"]["regulatory_evidence"] = {
        "state": "unavailable",
        "callable": False,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "service_contract_version": REGULATORY_EVIDENCE_CONTRACT_VERSION,
        "requirements": [],
        "limitations": ["regulatory_evidence_not_available_for_chain"],
        "compliance_conclusion_authorized": False,
        "execution_authorized": False,
    }
    return value


def _source(authority_class, title):
    return {
        "authority_class": authority_class,
        "publisher": (
            "U.S. Government Publishing Office"
            if authority_class == "primary_law"
            else "U.S. Department of the Treasury"
        ),
        "title": title,
        "url": "https://example.invalid/" + authority_class,
        "published_on": "2026-08-17",
        "retrieved_at": "2026-09-06T15:30:00Z",
    }


def _envelope():
    sources = [
        _source("primary_law", "Public Law 119-27 — GENIUS Act"),
        _source(
            "primary_regulator",
            "Treasury GENIUS Act proposed rulemaking",
        ),
    ]
    return {
        "service": "regulatory_evidence",
        "chain": "x1",
        "status": "ok",
        "asset": {"canonical_id": MINT, "mint": MINT},
        "data": {
            "contract_version": "regulatory_evidence/v1",
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "read_only": True,
            "jurisdiction": "US",
            "framework": "GENIUS Act",
            "legal": {
                "law_id": "Public Law 119-27",
                "enacted_on": "2025-07-18",
                "status": "enacted",
                "effective_date_rule": {
                    "type": "earlier_of",
                    "fixed_date": "2027-01-18",
                    "days_after_final_rules": 120,
                },
            },
            "current_regulatory_state": {
                "rulemaking_status": "proposed_rule",
                "final_rule_verified": False,
                "effective_now_verified": False,
                "status_as_of": "2026-09-06T15:30:00Z",
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
                "status_as_of": "2026-09-06T15:30:00Z",
                "evaluated_at": EVALUATED_AT,
                "age_seconds": 1800.0,
                "max_evidence_age_seconds": 86400.0,
                "freshness_verified": True,
            },
            "sources": sources,
            "limitations": [
                "Current proposed-rule status does not establish final or effective implementing regulation.",
                "Issuer licensing and compliance are not established by this record.",
                "Underlying USDC evidence does not establish USDC.X bridge, custody, liquidity, or redemption safety.",
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
                "source": item["title"],
                "publisher": item["publisher"],
                "scope": item["authority_class"],
                "observed_at": item["retrieved_at"],
            }
            for item in sources
        ],
        "observed_at": "2026-09-06T15:30:00Z",
        "warnings": [{
            "code": "regulatory_status_is_not_compliance",
            "message": "Regulatory status is not compliance.",
        }],
        "errors": [],
        "execution_authorized": False,
    }


def test_cmis_126_regulatory_capability_is_exact_and_promoted():
    manifest = validate_capability_manifest(_promoted_capabilities())
    capability = require_regulatory_evidence_capability(manifest)
    assert REGULATORY_EVIDENCE_MIN_CMIS_CONTRACT_VERSION == "1.26.0"
    assert capability["service_contract_version"] == "regulatory_evidence/v1"
    assert capability["state"] == "bounded"
    assert capability["read_only"] is True
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["compliance_conclusion_authorized"] is False
    assert capability["execution_authorized"] is False


def test_capability_rejects_missing_no_compliance_guardrail():
    raw = _promoted_capabilities()
    raw["chains"]["x1"]["services"]["regulatory_evidence"][
        "limitations"
    ].remove("no_compliant_or_non_compliant_conclusion")
    manifest = validate_capability_manifest(raw)
    with pytest.raises(
        CMISCapabilityContractError,
        match="missing accepted limitations",
    ):
        require_regulatory_evidence_capability(manifest)


def test_request_requires_exact_supported_framework_and_freshness_inputs():
    request = _request()
    assert request["asset_mint"] == MINT
    assert request["jurisdiction"] == "US"
    assert request["framework"] == "GENIUS Act"
    assert request["max_evidence_age_seconds"] == 86400.0
    with pytest.raises(
        CMISRegulatoryEvidenceContractError,
        match="US jurisdiction only",
    ):
        normalize_regulatory_evidence_request(
            jurisdiction="EU",
            framework="GENIUS Act",
            asset_id="USDC.X",
            asset_mint=MINT,
            evaluated_at=EVALUATED_AT,
            max_evidence_age_seconds=86400,
        )


def test_response_preserves_proposed_rule_exact_mint_and_bridge_dependencies():
    accepted = validate_regulatory_evidence_response(
        _envelope(),
        expected_request=_request(),
    )
    data = accepted["data"]
    assert data["current_regulatory_state"]["rulemaking_status"] == "proposed_rule"
    assert data["current_regulatory_state"]["final_rule_verified"] is False
    assert data["current_regulatory_state"]["effective_now_verified"] is False
    assert data["asset"]["chain_scoped_asset_id"] == MINT
    assert data["asset"]["bridge_dependency"] is True
    assert data["asset"]["custody_dependency"] is True
    assert data["freshness"]["freshness_verified"] is True
    assert data["compliance_conclusion"] is None
    assert accepted["risk"] is None


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda value: value["data"]["asset"].__setitem__(
                "chain_scoped_asset_id",
                "WrongMint111111111111111111111111111111111",
            ),
            "exact X1 mint identity",
        ),
        (
            lambda value: value["data"]["current_regulatory_state"].__setitem__(
                "final_rule_verified",
                True,
            ),
            "proposed rule cannot be widened",
        ),
        (
            lambda value: value["data"]["freshness"].__setitem__(
                "freshness_verified",
                False,
            ),
            "freshness must be verified",
        ),
        (
            lambda value: value["data"]["asset"].__setitem__(
                "bridge_dependency",
                False,
            ),
            "preserve bridge dependency",
        ),
        (
            lambda value: value["data"].__setitem__(
                "compliance_conclusion",
                "COMPLIANT",
            ),
            "cannot emit a compliance conclusion",
        ),
        (
            lambda value: value.__setitem__(
                "risk",
                {"level": "LOW"},
            ),
            "must not promote a risk conclusion",
        ),
    ],
)
def test_response_fails_closed_on_identity_status_freshness_or_safety_drift(
    mutator,
    match,
):
    bad = _envelope()
    mutator(bad)
    with pytest.raises(CMISRegulatoryEvidenceContractError, match=match):
        validate_regulatory_evidence_response(
            bad,
            expected_request=_request(),
        )


def test_response_requires_both_primary_law_and_primary_regulator_provenance():
    bad = _envelope()
    bad["data"]["sources"] = [
        item
        for item in bad["data"]["sources"]
        if item["authority_class"] != "primary_regulator"
    ]
    with pytest.raises(
        CMISRegulatoryEvidenceContractError,
        match="primary-regulator provenance",
    ):
        validate_regulatory_evidence_response(
            bad,
            expected_request=_request(),
        )


def test_http_client_posts_only_exact_regulatory_selectors_and_freshness():
    expected = _envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).regulatory_evidence(
            chain="x1",
            asset=MINT,
            jurisdiction="US",
            framework="GENIUS Act",
            asset_id="USDC.X",
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


def test_http_client_blocks_before_cmis_126_without_post():
    capabilities = _promoted_capabilities()
    capabilities["contract_version"] = "1.25.0"
    with _Server(_envelope(), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).regulatory_evidence(
            chain="x1",
            asset=MINT,
            jurisdiction="US",
            framework="GENIUS Act",
            asset_id="USDC.X",
            evaluated_at=EVALUATED_AT,
            max_evidence_age_seconds=86400,
        )
    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == (
        "cmis_regulatory_evidence_contract_unavailable"
    )
    assert running.requests == []


def test_x1_scout_product_feeds_existing_regulatory_reasoning_without_compliance():
    source = _envelope()
    product = build_x1_regulatory_intelligence(
        source,
        expected_request=_request(),
    )
    assert product["contract_version"] == X1_REGULATORY_INTELLIGENCE_CONTRACT
    assert product["regulatory_evidence"] == source["data"]
    assert product["asset"]["mint"] == MINT
    reasoning = product["roberta_regulatory_intelligence"]
    assert reasoning["contract"] == "roberta_regulatory_intelligence/v1"
    assert reasoning["current_evidence"]["asset"]["asset_id"] == "USDC.X"
    assert reasoning["current_evidence"]["asset"]["bridge_dependency"] is True
    assert reasoning["roberta_judgment"]["legal_compliance"] is None
    assert reasoning["roberta_judgment"]["bridge_custody_risk_preserved"] is True
    assert product["legal_advice"] is False
    assert product["automatic_risk_conclusion_authorized"] is False
    assert product["risk_interpretation"] is None
    assert product["execution_authorized"] is False


def test_public_wiring_exposes_regulatory_operation_and_exact_selectors():
    graph = Path("src/roberta/x1_scout/graph.py").read_text()
    tool = Path("src/roberta/x1_scout/tool.py").read_text()
    state = Path("src/roberta/x1_scout/state.py").read_text()
    client = Path("src/roberta/cmis/client.py").read_text()

    assert 'if operation == "regulatory_evidence":' in graph
    assert "require_regulatory_evidence_capability(" in graph
    assert "cmis_client.regulatory_evidence(" in graph
    assert 'report["x1_regulatory_intelligence"]' in graph
    assert 'report["roberta_regulatory_intelligence"]' in graph
    assert "build_x1_regulatory_intelligence(" in graph

    assert '"regulatory_evidence",' in tool
    assert "regulatory_jurisdiction: str | None = None" in tool
    assert "regulatory_framework: str | None = None" in tool
    assert "regulatory_asset_id: str | None = None" in tool
    assert "regulatory_evaluated_at: str | None = None" in tool
    assert "regulatory_max_evidence_age_seconds: float | None = None" in tool
    assert "COMPLIANT/NON_COMPLIANT" in tool
    assert "USDC.X bridge" in tool

    assert "regulatory_jurisdiction: NotRequired[str]" in state
    assert "regulatory_framework: NotRequired[str]" in state
    assert "regulatory_asset_id: NotRequired[str]" in state
    assert "regulatory_evaluated_at: NotRequired[str]" in state
    assert "regulatory_max_evidence_age_seconds: NotRequired[float]" in state
    assert "x1_regulatory_intelligence: NotRequired" in state
    assert "roberta_regulatory_intelligence: NotRequired" in state

    assert "def regulatory_evidence(" in client
    assert "max_evidence_age_seconds: float" in client
