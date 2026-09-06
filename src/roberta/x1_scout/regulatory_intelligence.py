"""First-class X1 Scout Regulatory Intelligence product.

The Scout preserves the promoted CMIS regulatory evidence exactly and feeds the
already-accepted ROBERTA regulatory reasoning layer. It does not decide legal
compliance, provide legal advice, infer automatic risk, or authorize execution.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from roberta.cmis.regulatory_evidence import (
    SERVICE_CONTRACT_VERSION as CMIS_REGULATORY_EVIDENCE_CONTRACT,
    validate_regulatory_evidence_response,
)
from roberta.regulatory import build_regulatory_intelligence

X1_REGULATORY_INTELLIGENCE_CONTRACT = "x1_regulatory_intelligence/v1"

_GENIUS_ACT_SOURCE = {
    "source_id": "genius_act_public_law_119_27",
    "framework": "GENIUS Act",
    "law_id": "Public Law 119-27",
    "authority_class": "primary",
    "live_state_authority": False,
    "execution_authorized": False,
}


class X1RegulatoryIntelligenceContractError(ValueError):
    """Raised when CMIS regulatory evidence cannot be safely projected."""


def _cmis_reasoning_evidence(
    response: Mapping[str, Any],
) -> dict[str, Any]:
    data = response["data"]
    return {
        "service": response["service"],
        "contract": data["contract_version"],
        "jurisdiction": data["jurisdiction"],
        "framework": data["framework"],
        "legal": deepcopy(data["legal"]),
        "current_regulatory_state": deepcopy(
            data["current_regulatory_state"]
        ),
        "asset": deepcopy(data["asset"]),
        "issuer": deepcopy(data["issuer"]),
        "applicability": data["applicability"],
        "sources": deepcopy(data["sources"]),
        "retrieved_at": response.get("observed_at"),
        "freshness": deepcopy(data["freshness"]),
        "limitations": deepcopy(data["limitations"]),
        "read_only": True,
        "compliance_conclusion_authorized": False,
        "compliance_conclusion": None,
        "execution_authorized": False,
    }


def build_x1_regulatory_intelligence(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        accepted = validate_regulatory_evidence_response(
            response,
            expected_request=expected_request,
        )
        evidence = _cmis_reasoning_evidence(accepted)
        reasoning = build_regulatory_intelligence(
            _GENIUS_ACT_SOURCE,
            evidence,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise X1RegulatoryIntelligenceContractError(str(exc)) from exc

    data = accepted["data"]
    asset = data["asset"]
    if reasoning.get("legal_advice") is not False:
        raise X1RegulatoryIntelligenceContractError(
            "ROBERTA regulatory reasoning must preserve legal_advice=false"
        )
    if reasoning.get("execution_authorized") is not False:
        raise X1RegulatoryIntelligenceContractError(
            "ROBERTA regulatory reasoning must preserve execution=false"
        )
    judgment = reasoning.get("roberta_judgment")
    if not isinstance(judgment, Mapping):
        raise X1RegulatoryIntelligenceContractError(
            "ROBERTA regulatory reasoning judgment missing"
        )
    if judgment.get("legal_compliance") is not None:
        raise X1RegulatoryIntelligenceContractError(
            "ROBERTA regulatory reasoning cannot emit compliance conclusion"
        )

    return {
        "contract_version": X1_REGULATORY_INTELLIGENCE_CONTRACT,
        "product": "x1_regulatory_intelligence",
        "chain": "x1",
        "status": "ok",
        "requested_asset": asset["asset_id"],
        "asset": {
            "canonical_id": asset["chain_scoped_asset_id"],
            "mint": asset["chain_scoped_asset_id"],
            "asset_id": asset["asset_id"],
            "representation_type": asset["representation_type"],
        },
        "regulatory_evidence_contract": CMIS_REGULATORY_EVIDENCE_CONTRACT,
        "regulatory_evidence": deepcopy(data),
        "roberta_regulatory_intelligence": reasoning,
        "legal_compliance": None,
        "legal_advice": False,
        "automatic_risk_conclusion_authorized": False,
        "risk_interpretation": None,
        "execution_authorized": False,
    }


__all__ = [
    "X1_REGULATORY_INTELLIGENCE_CONTRACT",
    "X1RegulatoryIntelligenceContractError",
    "build_x1_regulatory_intelligence",
]
