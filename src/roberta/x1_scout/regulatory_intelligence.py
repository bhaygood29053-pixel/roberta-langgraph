"""First-class X1 Scout projection of promoted CMIS Regulatory Evidence v1."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.cmis.regulatory_evidence import (
    SERVICE_CONTRACT_VERSION as CMIS_REGULATORY_EVIDENCE_CONTRACT,
    canonical_regulatory_evidence_from_response,
    validate_regulatory_evidence_response,
)

REGULATORY_INTELLIGENCE_CONTRACT = "x1_regulatory_intelligence/v1"


class X1RegulatoryIntelligenceContractError(ValueError):
    """CMIS output cannot satisfy the X1 Scout regulatory product."""


def build_x1_regulatory_intelligence(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, object]:
    try:
        safe = validate_regulatory_evidence_response(
            result,
            expected_request=expected_request,
        )
        canonical = canonical_regulatory_evidence_from_response(
            safe,
            expected_request=expected_request,
        )
    except Exception as exc:
        raise X1RegulatoryIntelligenceContractError(str(exc)) from exc

    data = safe["data"]
    asset = data["asset"]
    current_state = data["current_regulatory_state"]
    bridged = asset.get("representation_type") in {"bridged", "wrapped"}

    return {
        "contract_version": REGULATORY_INTELLIGENCE_CONTRACT,
        "product": "x1_regulatory_intelligence",
        "chain": "x1",
        "status": "ok",
        "requested_asset_id": expected_request["asset_id"],
        "requested_chain_asset_id": expected_request["chain_asset_id"],
        "requested_jurisdiction": expected_request["jurisdiction"],
        "requested_framework": expected_request["framework"],
        "cmis_contract_version": CMIS_REGULATORY_EVIDENCE_CONTRACT,
        "regulatory_evidence": canonical,
        "current_regulatory_state": deepcopy(current_state),
        "freshness": deepcopy(data["freshness"]),
        "observed_at": safe.get("observed_at"),
        "confidence": deepcopy(safe.get("confidence") or {}),
        "sources": deepcopy(safe.get("sources") or []),
        "warnings": deepcopy(safe.get("warnings") or []),
        "errors": deepcopy(safe.get("errors") or []),
        "evidence_receipt": deepcopy(safe.get("evidence_receipt")),
        "proof_score": deepcopy(safe.get("proof_score")),
        "bridge_custody_dependency_preserved": bridged,
        "compliance_conclusion_authorized": False,
        "legal_advice_authorized": False,
        "automatic_risk_conclusion_authorized": False,
        "risk_interpretation": None,
        "execution_authorized": False,
    }


__all__ = [
    "CMIS_REGULATORY_EVIDENCE_CONTRACT",
    "REGULATORY_INTELLIGENCE_CONTRACT",
    "X1RegulatoryIntelligenceContractError",
    "build_x1_regulatory_intelligence",
]
