"""Evidence-bounded ROBERTA regulatory reasoning."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.regulatory.models import (
    ROBERTA_REGULATORY_CONTRACT,
    RegulatoryIntelligenceContractError,
    validate_cmis_regulatory_evidence,
)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise RegulatoryIntelligenceContractError(
            f"{field} must be normalized text"
        )
    return value


def _validate_static_source(source: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(source, Mapping):
        raise RegulatoryIntelligenceContractError(
            "static regulatory source must be a mapping"
        )
    safe = deepcopy(dict(source))
    _text(safe.get("source_id"), "source_id")
    _text(safe.get("framework"), "framework")
    _text(safe.get("law_id"), "law_id")
    authority = _text(safe.get("authority_class"), "authority_class")
    if authority != "primary":
        raise RegulatoryIntelligenceContractError(
            "v1 regulatory learning requires a primary static source"
        )
    if safe.get("live_state_authority") is not False:
        raise RegulatoryIntelligenceContractError(
            "static source cannot claim live-state authority"
        )
    if safe.get("execution_authorized") is not False:
        raise RegulatoryIntelligenceContractError(
            "static source cannot authorize execution"
        )
    return safe


def build_regulatory_intelligence(
    static_source: Mapping[str, Any],
    cmis_evidence: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build the three-layer ROBERTA regulatory view.

    Static source knowledge can explain the law. Current applicability and
    current asset/issuer/bridge facts require CMIS evidence. Missing CMIS
    evidence fails closed to INSUFFICIENT_EVIDENCE.
    """
    source = _validate_static_source(static_source)

    if cmis_evidence is None:
        return {
            "contract": ROBERTA_REGULATORY_CONTRACT,
            "source_knowledge": source,
            "current_evidence": {
                "state": "UNAVAILABLE",
                "reason": "cmis_regulatory_evidence_unavailable",
            },
            "roberta_judgment": {
                "applicability": "INSUFFICIENT_EVIDENCE",
                "legal_compliance": None,
                "bridge_custody_risk_preserved": None,
                "evidence_quality": "INSUFFICIENT",
                "limitations": [
                    "Static law knowledge does not prove current asset, issuer, bridge, or licensing state.",
                    "No compliance conclusion is authorized.",
                ],
            },
            "legal_advice": False,
            "execution_authorized": False,
        }

    evidence = validate_cmis_regulatory_evidence(cmis_evidence)
    if evidence["framework"] != source["framework"]:
        raise RegulatoryIntelligenceContractError(
            "static source and CMIS framework identity mismatch"
        )

    asset = evidence["asset"]
    bridged = asset["representation_type"] in {"bridged", "wrapped"}

    limitations = list(evidence["limitations"])
    if bridged:
        limitations.append(
            "Regulatory evidence about the underlying asset does not erase "
            "representation-specific bridge, custody, liquidity, or redemption risk."
        )

    return {
        "contract": ROBERTA_REGULATORY_CONTRACT,
        "source_knowledge": source,
        "current_evidence": {
            "state": "CMIS_VERIFIED_BOUNDARY",
            "service": evidence["service"],
            "contract": evidence["contract"],
            "jurisdiction": evidence["jurisdiction"],
            "framework": evidence["framework"],
            "legal": deepcopy(evidence.get("legal")),
            "asset": deepcopy(asset),
            "issuer": deepcopy(evidence.get("issuer")),
            "sources": deepcopy(evidence["sources"]),
            "retrieved_at": evidence.get("retrieved_at"),
        },
        "roberta_judgment": {
            "applicability": evidence["applicability"],
            "legal_compliance": None,
            "bridge_custody_risk_preserved": bridged,
            "evidence_quality": (
                "SUFFICIENT_FOR_BOUNDED_APPLICABILITY"
                if evidence["applicability"] in {"APPLICABLE", "NOT_APPLICABLE"}
                else "INSUFFICIENT_FOR_APPLICABILITY"
            ),
            "limitations": limitations,
        },
        "legal_advice": False,
        "execution_authorized": False,
    }
