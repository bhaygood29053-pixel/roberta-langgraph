"""ROBERTA/X1 Scout contract for promoted CMIS Regulatory Evidence v1."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from typing import Any

SERVICE = "regulatory_evidence"
SERVICE_CONTRACT_VERSION = "regulatory_evidence/v1"
SUPPORTED_CHAIN = "x1"
RULEMAKING_STATUSES = frozenset({"proposed_rule", "final_rule", "effective", "unknown"})


class CMISRegulatoryEvidenceContractError(ValueError):
    """Raised when promoted CMIS regulatory evidence violates the Scout contract."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise CMISRegulatoryEvidenceContractError(f"{field} must be normalized text")
    return value


def _positive_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise CMISRegulatoryEvidenceContractError(f"{field} must be positive")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CMISRegulatoryEvidenceContractError(f"{field} must be positive") from exc
    if parsed <= 0:
        raise CMISRegulatoryEvidenceContractError(f"{field} must be positive")
    return parsed


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
        raise CMISRegulatoryEvidenceContractError(f"{field} must include timezone")
    return text


def normalize_regulatory_evidence_request(
    *,
    jurisdiction: str,
    framework: str,
    asset_id: str,
    chain_asset_id: str,
    evaluated_at: str,
    max_evidence_age_seconds: float,
) -> dict[str, object]:
    """Normalize selector/freshness inputs without accepting legal trust material."""

    return {
        "jurisdiction": _text(jurisdiction, "jurisdiction"),
        "framework": _text(framework, "framework"),
        "asset_id": _text(asset_id, "asset_id"),
        "chain_asset_id": _text(chain_asset_id, "chain_asset_id"),
        "evaluated_at": _timestamp(evaluated_at, "evaluated_at"),
        "max_evidence_age_seconds": _positive_number(
            max_evidence_age_seconds,
            "max_evidence_age_seconds",
        ),
    }


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CMISRegulatoryEvidenceContractError(f"{field} must be a mapping")
    return value


def _sequence(value: Any, field: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CMISRegulatoryEvidenceContractError(f"{field} must be a sequence")
    return value


def validate_regulatory_evidence_response(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate promoted CMIS regulatory output without widening its authority."""

    if not isinstance(result, Mapping):
        raise CMISRegulatoryEvidenceContractError("CMIS response must be a mapping")
    safe = deepcopy(dict(result))

    if safe.get("service") != SERVICE or safe.get("chain") != SUPPORTED_CHAIN:
        raise CMISRegulatoryEvidenceContractError("CMIS regulatory service identity mismatch")
    if safe.get("status") != "ok":
        raise CMISRegulatoryEvidenceContractError("promoted regulatory response must be ok")
    if safe.get("risk") is not None:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence must not promote risk"
        )
    if safe.get("execution_authorized") is not False:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence cannot authorize execution"
        )

    data = _mapping(safe.get("data"), "data")
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISRegulatoryEvidenceContractError(
            "CMIS regulatory evidence contract mismatch"
        )
    for field, expected in (
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("read_only", True),
        ("compliance_conclusion_authorized", False),
        ("legal_advice_authorized", False),
        ("execution_authorized", False),
    ):
        if data.get(field) is not expected:
            raise CMISRegulatoryEvidenceContractError(
                f"CMIS regulatory {field} must be {str(expected).lower()}"
            )
    if data.get("compliance_conclusion") is not None:
        raise CMISRegulatoryEvidenceContractError(
            "CMIS regulatory evidence cannot supply a compliance conclusion"
        )

    for field in ("jurisdiction", "framework"):
        if data.get(field) != expected_request.get(field):
            raise CMISRegulatoryEvidenceContractError(
                f"CMIS regulatory {field} selector mismatch"
            )

    asset = _mapping(data.get("asset"), "data.asset")
    if asset.get("asset_id") != expected_request.get("asset_id"):
        raise CMISRegulatoryEvidenceContractError(
            "CMIS regulatory logical asset selector mismatch"
        )
    if asset.get("chain") != "x1" or asset.get("asset_id_kind") != "mint":
        raise CMISRegulatoryEvidenceContractError(
            "CMIS regulatory asset must preserve exact X1 mint identity"
        )
    if asset.get("chain_scoped_asset_id") != expected_request.get("chain_asset_id"):
        raise CMISRegulatoryEvidenceContractError(
            "CMIS regulatory exact X1 mint mismatch"
        )
    representation = _text(asset.get("representation_type"), "data.asset.representation_type")
    if representation in {"bridged", "wrapped"}:
        _text(asset.get("underlying_asset"), "data.asset.underlying_asset")
        if asset.get("bridge_dependency") is not True:
            raise CMISRegulatoryEvidenceContractError(
                "bridged/wrapped evidence must preserve bridge dependency"
            )
        if asset.get("custody_dependency") is not True:
            raise CMISRegulatoryEvidenceContractError(
                "bridged/wrapped evidence must preserve custody dependency"
            )

    state = _mapping(data.get("current_regulatory_state"), "data.current_regulatory_state")
    status = _text(state.get("rulemaking_status"), "rulemaking_status")
    if status not in RULEMAKING_STATUSES:
        raise CMISRegulatoryEvidenceContractError(
            "unsupported current regulatory rulemaking status"
        )
    final_rule = state.get("final_rule_verified")
    effective_now = state.get("effective_now_verified")
    if not isinstance(final_rule, bool) or not isinstance(effective_now, bool):
        raise CMISRegulatoryEvidenceContractError(
            "current regulatory final/effective flags must be boolean"
        )
    if status == "proposed_rule" and (final_rule or effective_now):
        raise CMISRegulatoryEvidenceContractError(
            "proposed rule cannot be promoted as final or effective"
        )
    if status == "final_rule" and (final_rule is not True or effective_now is not False):
        raise CMISRegulatoryEvidenceContractError(
            "final-rule state must preserve final=true/effective=false"
        )
    if status == "effective" and (final_rule is not True or effective_now is not True):
        raise CMISRegulatoryEvidenceContractError(
            "effective state must preserve final=true/effective=true"
        )
    if status == "unknown" and (final_rule or effective_now):
        raise CMISRegulatoryEvidenceContractError(
            "unknown state cannot promote final/effective regulation"
        )

    freshness = _mapping(data.get("freshness"), "data.freshness")
    if freshness.get("freshness_verified") is not True:
        raise CMISRegulatoryEvidenceContractError(
            "current regulatory evidence freshness must be verified"
        )
    if freshness.get("evaluated_at") != expected_request.get("evaluated_at"):
        raise CMISRegulatoryEvidenceContractError(
            "CMIS regulatory evaluated_at mismatch"
        )
    requested_max_age = float(expected_request["max_evidence_age_seconds"])
    if float(freshness.get("max_evidence_age_seconds")) != requested_max_age:
        raise CMISRegulatoryEvidenceContractError(
            "CMIS regulatory freshness bound mismatch"
        )
    _timestamp(freshness.get("status_as_of"), "data.freshness.status_as_of")

    sources = _sequence(data.get("sources"), "data.sources")
    authority_classes = {
        source.get("authority_class")
        for source in sources
        if isinstance(source, Mapping)
    }
    if "primary_law" not in authority_classes:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence requires primary-law provenance"
        )
    if "primary_regulator" not in authority_classes:
        raise CMISRegulatoryEvidenceContractError(
            "current regulatory state requires primary-regulator provenance"
        )

    limitations = _sequence(data.get("limitations"), "data.limitations")
    if not limitations:
        raise CMISRegulatoryEvidenceContractError(
            "regulatory evidence must preserve explicit limitations"
        )
    _mapping(safe.get("confidence"), "confidence")
    _sequence(safe.get("sources"), "sources")
    _sequence(safe.get("warnings"), "warnings")
    _sequence(safe.get("errors"), "errors")
    return safe


def canonical_regulatory_evidence_from_response(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the promoted envelope into the existing ROBERTA regulatory boundary."""

    safe = validate_regulatory_evidence_response(
        result,
        expected_request=expected_request,
    )
    data = safe["data"]
    freshness = data["freshness"]
    return {
        "service": SERVICE,
        "contract": SERVICE_CONTRACT_VERSION,
        "jurisdiction": data["jurisdiction"],
        "framework": data["framework"],
        "legal": deepcopy(data.get("legal")),
        "current_regulatory_state": deepcopy(data["current_regulatory_state"]),
        "asset": deepcopy(data["asset"]),
        "issuer": deepcopy(data.get("issuer")),
        "applicability": data["applicability"],
        "sources": deepcopy(data["sources"]),
        "retrieved_at": freshness["evaluated_at"],
        "limitations": deepcopy(data["limitations"]),
        "read_only": True,
        "compliance_conclusion_authorized": False,
        "compliance_conclusion": None,
        "execution_authorized": False,
    }


__all__ = [
    "CMISRegulatoryEvidenceContractError",
    "RULEMAKING_STATUSES",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "SUPPORTED_CHAIN",
    "canonical_regulatory_evidence_from_response",
    "normalize_regulatory_evidence_request",
    "validate_regulatory_evidence_response",
]
