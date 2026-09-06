"""ROBERTA-side validation for promoted CMIS Regulatory Evidence v1.

This adapter validates selectors, exact X1 mint identity, provenance, rulemaking
state, freshness, and safety boundaries. It does not decide legal compliance,
recompute law/regulator state, infer risk, or authorize execution.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from typing import Any

SERVICE = "regulatory_evidence"
SERVICE_CONTRACT_VERSION = "regulatory_evidence/v1"
SUPPORTED_JURISDICTION = "US"
SUPPORTED_FRAMEWORK = "GENIUS Act"
CURRENT_RULEMAKING_STATUSES = frozenset({
    "proposed_rule",
    "final_rule",
    "effective",
    "unknown",
})
APPLICABILITY_STATES = frozenset({
    "APPLICABLE",
    "NOT_APPLICABLE",
    "UNKNOWN",
    "INSUFFICIENT_EVIDENCE",
})


class CMISRegulatoryEvidenceContractError(ValueError):
    """Raised when promoted regulatory evidence violates the Scout boundary."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CMISRegulatoryEvidenceContractError(
            f"{field} must be normalized text"
        )
    return value


def _timestamp(value: Any, field: str) -> str:
    text = _text(value, field)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CMISRegulatoryEvidenceContractError(
            f"{field} must be ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise CMISRegulatoryEvidenceContractError(
            f"{field} must include timezone"
        )
    return text


def _positive_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise CMISRegulatoryEvidenceContractError(f"{field} must be positive")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CMISRegulatoryEvidenceContractError(
            f"{field} must be positive"
        ) from exc
    if parsed <= 0:
        raise CMISRegulatoryEvidenceContractError(f"{field} must be positive")
    return parsed


def _mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise CMISRegulatoryEvidenceContractError(
            f"required regulatory object missing: {key}"
        )
    return value


def _sequence(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, Mapping)):
        raise CMISRegulatoryEvidenceContractError(
            f"required regulatory list malformed: {key}"
        )
    return list(value)


def normalize_regulatory_evidence_request(
    *,
    jurisdiction: Any,
    framework: Any,
    asset_id: Any,
    asset_mint: Any,
    evaluated_at: Any,
    max_evidence_age_seconds: Any,
) -> dict[str, object]:
    normalized_jurisdiction = _text(jurisdiction, "jurisdiction")
    normalized_framework = _text(framework, "framework")
    normalized_asset_id = _text(asset_id, "asset_id")
    normalized_mint = _text(asset_mint, "asset_mint")
    normalized_evaluated_at = _timestamp(evaluated_at, "evaluated_at")
    max_age = _positive_number(
        max_evidence_age_seconds,
        "max_evidence_age_seconds",
    )
    if normalized_jurisdiction != SUPPORTED_JURISDICTION:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence v1 supports US jurisdiction only"
        )
    if normalized_framework != SUPPORTED_FRAMEWORK:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence v1 supports GENIUS Act only"
        )
    return {
        "jurisdiction": normalized_jurisdiction,
        "framework": normalized_framework,
        "asset_id": normalized_asset_id,
        "asset_mint": normalized_mint,
        "evaluated_at": normalized_evaluated_at,
        "max_evidence_age_seconds": max_age,
    }


def validate_regulatory_evidence_response(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CMISRegulatoryEvidenceContractError(
            "CMIS regulatory evidence response must be an object"
        )
    safe = deepcopy(dict(response))
    if safe.get("service") != SERVICE:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence service mismatch"
        )
    if safe.get("chain") != "x1":
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence chain must remain x1"
        )
    if safe.get("status") != "ok":
        raise CMISRegulatoryEvidenceContractError(
            "promoted regulatory evidence requires CMIS ok status"
        )
    if safe.get("risk") is not None:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence must not promote a risk conclusion"
        )
    if safe.get("execution_authorized") not in (None, False):
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence must preserve execution_authorized=false"
        )

    expected = normalize_regulatory_evidence_request(
        jurisdiction=expected_request.get("jurisdiction"),
        framework=expected_request.get("framework"),
        asset_id=expected_request.get("asset_id"),
        asset_mint=expected_request.get("asset_mint"),
        evaluated_at=expected_request.get("evaluated_at"),
        max_evidence_age_seconds=expected_request.get(
            "max_evidence_age_seconds"
        ),
    )

    asset_identity = _mapping(safe, "asset")
    if asset_identity.get("canonical_id") != expected["asset_mint"]:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence canonical asset id must match exact X1 mint"
        )
    if asset_identity.get("mint") != expected["asset_mint"]:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence mint must match exact request"
        )

    data = _mapping(safe, "data")
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence contract mismatch"
        )
    for field, expected_flag in (
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("read_only", True),
        ("compliance_conclusion_authorized", False),
        ("legal_advice_authorized", False),
        ("execution_authorized", False),
    ):
        if data.get(field) is not expected_flag:
            raise CMISRegulatoryEvidenceContractError(
                f"regulatory evidence {field} boundary drift"
            )
    if data.get("compliance_conclusion") is not None:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence cannot emit a compliance conclusion"
        )
    if data.get("jurisdiction") != expected["jurisdiction"]:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory jurisdiction identity mismatch"
        )
    if data.get("framework") != expected["framework"]:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory framework identity mismatch"
        )

    regulatory_asset = _mapping(data, "asset")
    if regulatory_asset.get("asset_id") != expected["asset_id"]:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory asset identity mismatch"
        )
    if regulatory_asset.get("chain") != "x1":
        raise CMISRegulatoryEvidenceContractError(
            "regulatory asset must remain X1 scoped"
        )
    if regulatory_asset.get("asset_id_kind") != "mint":
        raise CMISRegulatoryEvidenceContractError(
            "regulatory X1 identity must use exact mint"
        )
    if regulatory_asset.get("chain_scoped_asset_id") != expected["asset_mint"]:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory exact X1 mint identity mismatch"
        )
    representation = _text(
        regulatory_asset.get("representation_type"),
        "data.asset.representation_type",
    )
    if representation in {"bridged", "wrapped"}:
        if regulatory_asset.get("bridge_dependency") is not True:
            raise CMISRegulatoryEvidenceContractError(
                "bridged regulatory evidence must preserve bridge dependency"
            )
        if regulatory_asset.get("custody_dependency") is not True:
            raise CMISRegulatoryEvidenceContractError(
                "bridged regulatory evidence must preserve custody dependency"
            )
        _text(
            regulatory_asset.get("underlying_asset"),
            "data.asset.underlying_asset",
        )

    applicability = _text(data.get("applicability"), "data.applicability")
    if applicability not in APPLICABILITY_STATES:
        raise CMISRegulatoryEvidenceContractError(
            "unsupported regulatory applicability state"
        )

    state = _mapping(data, "current_regulatory_state")
    rulemaking = _text(
        state.get("rulemaking_status"),
        "data.current_regulatory_state.rulemaking_status",
    )
    if rulemaking not in CURRENT_RULEMAKING_STATUSES:
        raise CMISRegulatoryEvidenceContractError(
            "unsupported current rulemaking status"
        )
    final_verified = state.get("final_rule_verified")
    effective_verified = state.get("effective_now_verified")
    if not isinstance(final_verified, bool) or not isinstance(
        effective_verified, bool
    ):
        raise CMISRegulatoryEvidenceContractError(
            "current rulemaking verification flags must be boolean"
        )
    if rulemaking == "proposed_rule" and (
        final_verified is not False or effective_verified is not False
    ):
        raise CMISRegulatoryEvidenceContractError(
            "proposed rule cannot be widened to final or effective"
        )
    if rulemaking == "final_rule" and (
        final_verified is not True or effective_verified is not False
    ):
        raise CMISRegulatoryEvidenceContractError(
            "final-rule verification state mismatch"
        )
    if rulemaking == "effective" and (
        final_verified is not True or effective_verified is not True
    ):
        raise CMISRegulatoryEvidenceContractError(
            "effective-rule verification state mismatch"
        )
    if rulemaking == "unknown" and (
        final_verified is not False or effective_verified is not False
    ):
        raise CMISRegulatoryEvidenceContractError(
            "unknown rulemaking state cannot imply final/effective"
        )
    _timestamp(
        state.get("status_as_of"),
        "data.current_regulatory_state.status_as_of",
    )

    freshness = _mapping(data, "freshness")
    if freshness.get("freshness_verified") is not True:
        raise CMISRegulatoryEvidenceContractError(
            "current regulatory evidence freshness must be verified"
        )
    if freshness.get("evaluated_at") != expected["evaluated_at"]:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evaluated_at must match exact request"
        )
    try:
        returned_max_age = float(freshness.get("max_evidence_age_seconds"))
    except (TypeError, ValueError) as exc:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory freshness max age must be numeric"
        ) from exc
    if returned_max_age != expected["max_evidence_age_seconds"]:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory freshness bound must match exact request"
        )

    data_sources = _sequence(data, "sources")
    authority_classes = {
        item.get("authority_class")
        for item in data_sources
        if isinstance(item, Mapping)
    }
    if "primary_law" not in authority_classes:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence requires primary-law provenance"
        )
    if "primary_regulator" not in authority_classes:
        raise CMISRegulatoryEvidenceContractError(
            "current regulatory state requires primary-regulator provenance"
        )
    _sequence(data, "limitations")

    return safe


__all__ = [
    "APPLICABILITY_STATES",
    "CMISRegulatoryEvidenceContractError",
    "CURRENT_RULEMAKING_STATUSES",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "SUPPORTED_FRAMEWORK",
    "SUPPORTED_JURISDICTION",
    "normalize_regulatory_evidence_request",
    "validate_regulatory_evidence_response",
]
