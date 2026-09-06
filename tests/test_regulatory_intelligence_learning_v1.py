import copy

import pytest

from roberta.regulatory import (
    RegulatoryIntelligenceContractError,
    build_regulatory_intelligence,
)


STATIC_SOURCE = {
    "source_id": "genius_act_public_law_119_27",
    "framework": "GENIUS Act",
    "law_id": "Public Law 119-27",
    "authority_class": "primary",
    "live_state_authority": False,
    "execution_authorized": False,
}


def _cmis_usdcx():
    return {
        "service": "regulatory_evidence",
        "contract": "regulatory_evidence/v1",
        "jurisdiction": "US",
        "framework": "GENIUS Act",
        "legal": {
            "law_id": "Public Law 119-27",
            "status": "enacted",
        },
        "asset": {
            "asset_id": "USDC.X",
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
        "sources": [{
            "authority_class": "primary_law",
            "publisher": "U.S. Government Publishing Office",
            "title": "Public Law 119-27",
            "url": "https://www.govinfo.gov/app/details/PLAW-119publ27",
        }],
        "retrieved_at": "2026-09-06T15:00:00Z",
        "limitations": [
            "Current issuer licensing/compliance is not established.",
        ],
        "read_only": True,
        "compliance_conclusion_authorized": False,
        "compliance_conclusion": None,
        "execution_authorized": False,
    }


def test_missing_cmis_evidence_fails_closed_without_guessing():
    result = build_regulatory_intelligence(STATIC_SOURCE, None)
    assert result["current_evidence"]["state"] == "UNAVAILABLE"
    assert result["roberta_judgment"]["applicability"] == "INSUFFICIENT_EVIDENCE"
    assert result["roberta_judgment"]["legal_compliance"] is None
    assert result["execution_authorized"] is False


def test_usdcx_preserves_three_layers_and_bridge_risk():
    result = build_regulatory_intelligence(STATIC_SOURCE, _cmis_usdcx())
    assert result["contract"] == "roberta_regulatory_intelligence/v1"
    assert result["source_knowledge"]["law_id"] == "Public Law 119-27"
    assert result["current_evidence"]["asset"]["asset_id"] == "USDC.X"
    assert result["current_evidence"]["asset"]["underlying_asset"] == "USDC"
    assert result["roberta_judgment"]["bridge_custody_risk_preserved"] is True
    assert result["roberta_judgment"]["legal_compliance"] is None
    assert any(
        "does not erase" in item
        for item in result["roberta_judgment"]["limitations"]
    )


def test_roberta_rejects_cmis_compliance_conclusion():
    evidence = _cmis_usdcx()
    evidence["compliance_conclusion"] = "COMPLIANT"
    with pytest.raises(
        RegulatoryIntelligenceContractError,
        match="cannot supply a legal-compliance conclusion",
    ):
        build_regulatory_intelligence(STATIC_SOURCE, evidence)


def test_roberta_rejects_bridged_asset_with_erased_bridge_dependency():
    evidence = _cmis_usdcx()
    evidence["asset"]["bridge_dependency"] = False
    with pytest.raises(
        RegulatoryIntelligenceContractError,
        match="preserve bridge dependency",
    ):
        build_regulatory_intelligence(STATIC_SOURCE, evidence)


def test_roberta_rejects_static_source_framework_mismatch():
    evidence = _cmis_usdcx()
    bad_source = copy.deepcopy(STATIC_SOURCE)
    bad_source["framework"] = "Different Framework"
    with pytest.raises(
        RegulatoryIntelligenceContractError,
        match="framework identity mismatch",
    ):
        build_regulatory_intelligence(bad_source, evidence)
