"""Contract validators for ROBERTA Regulatory Intelligence v1.

ROBERTA validates the CMIS regulatory boundary and preserves source facts,
current evidence, and judgment as separate layers. It does not recreate CMIS
legal/evidence verification.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

CMIS_REGULATORY_SERVICE = "regulatory_evidence"
CMIS_REGULATORY_CONTRACT = "regulatory_evidence/v1"
ROBERTA_REGULATORY_CONTRACT = "roberta_regulatory_intelligence/v1"

APPLICABILITY_STATES = frozenset({
    "APPLICABLE",
    "NOT_APPLICABLE",
    "UNKNOWN",
    "INSUFFICIENT_EVIDENCE",
})
REPRESENTATION_TYPES = frozenset({"native", "bridged", "wrapped", "unknown"})


class RegulatoryIntelligenceContractError(ValueError):
    """Raised when incoming regulatory evidence weakens ROBERTA's boundary."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise RegulatoryIntelligenceContractError(
            f"{field} must be normalized text"
        )
    return value


def validate_cmis_regulatory_evidence(
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate only the ROBERTA-facing CMIS boundary.

    Detailed legal/source verification remains CMIS-owned. ROBERTA checks the
    exact contract and safety fields before using the evidence.
    """
    if not isinstance(evidence, Mapping):
        raise RegulatoryIntelligenceContractError(
            "CMIS regulatory evidence must be a mapping"
        )
    safe = deepcopy(dict(evidence))

    if safe.get("service") != CMIS_REGULATORY_SERVICE:
        raise RegulatoryIntelligenceContractError(
            "unexpected CMIS regulatory service"
        )
    if safe.get("contract") != CMIS_REGULATORY_CONTRACT:
        raise RegulatoryIntelligenceContractError(
            "unexpected CMIS regulatory contract"
        )
    if safe.get("read_only") is not True:
        raise RegulatoryIntelligenceContractError(
            "CMIS regulatory evidence must remain read-only"
        )
    if safe.get("execution_authorized") is not False:
        raise RegulatoryIntelligenceContractError(
            "regulatory evidence cannot authorize execution"
        )
    if safe.get("compliance_conclusion_authorized") is not False:
        raise RegulatoryIntelligenceContractError(
            "v1 cannot authorize legal-compliance conclusions"
        )
    if safe.get("compliance_conclusion") is not None:
        raise RegulatoryIntelligenceContractError(
            "v1 cannot supply a legal-compliance conclusion"
        )

    _text(safe.get("jurisdiction"), "jurisdiction")
    _text(safe.get("framework"), "framework")

    applicability = _text(safe.get("applicability"), "applicability")
    if applicability not in APPLICABILITY_STATES:
        raise RegulatoryIntelligenceContractError(
            "unsupported applicability state"
        )

    asset = safe.get("asset")
    if not isinstance(asset, Mapping):
        raise RegulatoryIntelligenceContractError("asset must be a mapping")
    _text(asset.get("asset_id"), "asset.asset_id")
    representation_type = _text(
        asset.get("representation_type"), "asset.representation_type"
    )
    if representation_type not in REPRESENTATION_TYPES:
        raise RegulatoryIntelligenceContractError(
            "unsupported representation type"
        )
    if not isinstance(asset.get("bridge_dependency"), bool):
        raise RegulatoryIntelligenceContractError(
            "asset.bridge_dependency must be boolean"
        )
    if not isinstance(asset.get("custody_dependency"), bool):
        raise RegulatoryIntelligenceContractError(
            "asset.custody_dependency must be boolean"
        )
    if representation_type in {"bridged", "wrapped"}:
        _text(asset.get("underlying_asset"), "asset.underlying_asset")
        if asset.get("bridge_dependency") is not True:
            raise RegulatoryIntelligenceContractError(
                "bridged/wrapped evidence must preserve bridge dependency"
            )

    sources = safe.get("sources")
    if (
        not isinstance(sources, Sequence)
        or isinstance(sources, (str, bytes))
        or not sources
    ):
        raise RegulatoryIntelligenceContractError(
            "CMIS regulatory evidence requires source provenance"
        )

    limitations = safe.get("limitations")
    if (
        not isinstance(limitations, Sequence)
        or isinstance(limitations, (str, bytes))
        or not limitations
    ):
        raise RegulatoryIntelligenceContractError(
            "CMIS regulatory evidence requires explicit limitations"
        )

    return safe
