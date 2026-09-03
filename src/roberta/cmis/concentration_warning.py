"""ROBERTA-side validation for CMIS 1.18 Concentration Warning Intelligence v1.

X1 Scout may consume the promoted CMIS pull-only warning service, but it must not
recompute WATCH/CLEAR, persistence, freshness, Receipt/Proof lineage, risk, or
delivery state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import re
from typing import Any


SERVICE = "concentration_warning_intelligence"
MIN_CMIS_CONTRACT_VERSION = "1.18.0"
SERVICE_CONTRACT_VERSION = "concentration_warning_intelligence/v1"
DELIVERY_MODE = "pull_only"
WARNING_SCHEMA = "cmis_persistent_concentration_warning.v1"
PERSISTENCE_MODE = "two_distinct_compatible_observations"

_ID_RE = re.compile(r"^ie_[0-9a-f]{64}$")
_WARNING_ID_RE = re.compile(r"^cw_[0-9a-f]{64}$")
_POLICY_FIELDS = frozenset(
    {"policy_id", "policy_version", "absolute_delta_threshold_bps"}
)
_ALLOWED_LEVELS = frozenset({"WATCH", "CLEAR"})
_ALLOWED_COMPARATORS = frozenset({"GT", "GTE"})


class CMISConcentrationWarningContractError(ValueError):
    """Raised when CMIS warning data violates the accepted ROBERTA boundary."""


def _mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CMISConcentrationWarningContractError(f"{name} must be a mapping")
    return value


def _list(name: str, value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise CMISConcentrationWarningContractError(f"{name} must be a list")
    return value


def _normalized_text(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise CMISConcentrationWarningContractError(
            f"{name} must be normalized non-empty text"
        )
    text = value.strip()
    if not text or text != value:
        raise CMISConcentrationWarningContractError(
            f"{name} must be normalized non-empty text"
        )
    return text


def _canonical_utc(name: str, value: Any) -> str:
    text = _normalized_text(name, value)
    if not text.endswith("Z"):
        raise CMISConcentrationWarningContractError(
            f"{name} must be canonical UTC ending in Z"
        )
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise CMISConcentrationWarningContractError(
            f"{name} must be canonical UTC ending in Z"
        ) from exc
    canonical = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if canonical != text:
        raise CMISConcentrationWarningContractError(
            f"{name} must be canonical UTC ending in Z"
        )
    return text


def _nonnegative_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CMISConcentrationWarningContractError(
            f"{name} must be a non-negative integer"
        )
    return value


def normalize_intelligence_evidence_ids(value: Any) -> tuple[str, str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CMISConcentrationWarningContractError(
            "intelligence_evidence_ids must contain exactly two canonical ids"
        )
    items = list(value)
    if len(items) != 2:
        raise CMISConcentrationWarningContractError(
            "intelligence_evidence_ids must contain exactly two canonical ids"
        )
    normalized: list[str] = []
    for item in items:
        if not isinstance(item, str) or not _ID_RE.fullmatch(item):
            raise CMISConcentrationWarningContractError(
                "intelligence_evidence_ids must contain canonical ie_ content ids"
            )
        normalized.append(item)
    if normalized[0] == normalized[1]:
        raise CMISConcentrationWarningContractError(
            "intelligence_evidence_ids must be distinct"
        )
    return normalized[0], normalized[1]


def normalize_threshold_policy(value: Any) -> dict[str, Any]:
    policy = _mapping("threshold_policy", value)
    if set(policy) != set(_POLICY_FIELDS):
        raise CMISConcentrationWarningContractError(
            "threshold_policy must contain exactly policy_id, policy_version, "
            "and absolute_delta_threshold_bps"
        )
    policy_id = _normalized_text("threshold_policy.policy_id", policy.get("policy_id"))
    policy_version = _normalized_text(
        "threshold_policy.policy_version", policy.get("policy_version")
    )
    threshold = policy.get("absolute_delta_threshold_bps")
    if threshold is None or isinstance(threshold, bool):
        raise CMISConcentrationWarningContractError(
            "threshold_policy.absolute_delta_threshold_bps is required"
        )
    return {
        "policy_id": policy_id,
        "policy_version": policy_version,
        "absolute_delta_threshold_bps": deepcopy(threshold),
    }


def normalize_warning_request(
    *,
    intelligence_evidence_ids: Any,
    threshold_policy: Any,
    threshold_unit: Any,
    comparator: Any,
    evaluated_at: Any,
    max_latest_age_seconds: Any,
    max_persistence_window_seconds: Any,
) -> dict[str, Any]:
    ids = normalize_intelligence_evidence_ids(intelligence_evidence_ids)
    policy = normalize_threshold_policy(threshold_policy)
    unit = _normalized_text("threshold_unit", threshold_unit)
    if unit != "basis_points":
        raise CMISConcentrationWarningContractError(
            "threshold_unit must be basis_points"
        )
    comparison = _normalized_text("comparator", comparator)
    if comparison not in _ALLOWED_COMPARATORS:
        raise CMISConcentrationWarningContractError("comparator must be GT or GTE")
    evaluated = _canonical_utc("evaluated_at", evaluated_at)
    latest_age = _nonnegative_int(
        "max_latest_age_seconds", max_latest_age_seconds
    )
    window = _nonnegative_int(
        "max_persistence_window_seconds", max_persistence_window_seconds
    )
    return {
        "intelligence_evidence_ids": list(ids),
        "threshold_policy": policy,
        "threshold_unit": unit,
        "comparator": comparison,
        "evaluated_at": evaluated,
        "max_latest_age_seconds": latest_age,
        "max_persistence_window_seconds": window,
    }


def validate_concentration_warning_response(
    response: Mapping[str, Any],
    *,
    requested_asset: str,
) -> dict[str, Any]:
    """Validate an accepted CMIS service response without recomputing warning truth."""

    if not isinstance(response, Mapping):
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning response must be a mapping"
        )
    safe = deepcopy(dict(response))
    if safe.get("service") != SERVICE or safe.get("chain") != "x1":
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning service/chain identity mismatch"
        )
    if safe.get("execution_authorized") is not False:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning must preserve execution_authorized=false"
        )
    if safe.get("status") != "ok":
        return safe

    asset = _mapping("asset", safe.get("asset"))
    expected_asset = _normalized_text("requested_asset", requested_asset)
    if asset.get("canonical_id") != expected_asset:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning asset identity mismatch"
        )
    if safe.get("risk") is not None:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning must not promote risk"
        )

    data = _mapping("data", safe.get("data"))
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning service contract mismatch"
        )
    if data.get("delivery_mode") != DELIVERY_MODE:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning delivery_mode must remain pull_only"
        )
    expected_flags = {
        "push_delivery_authorized": False,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "warning_level_is_risk_severity": False,
        "risk_interpretation_verified": False,
        "behavioral_interpretation_verified": False,
        "ownership_interpretation_verified": False,
        "proof_strength_separate_from_risk": True,
        "execution_authorized": False,
    }
    for field, expected in expected_flags.items():
        if data.get(field) is not expected:
            raise CMISConcentrationWarningContractError(
                f"CMIS Concentration Warning {field} must be {expected!r}"
            )
    if data.get("risk_interpretation") is not None:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning risk_interpretation must remain null"
        )

    warning_id = data.get("warning_id")
    if not isinstance(warning_id, str) or not _WARNING_ID_RE.fullmatch(warning_id):
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning warning_id must be canonical"
        )
    level = data.get("warning_level")
    if level not in _ALLOWED_LEVELS:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning level must be WATCH or CLEAR"
        )
    active = data.get("warning_active")
    if not isinstance(active, bool) or active is not (level == "WATCH"):
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning active state must match WATCH/CLEAR"
        )

    persistence = _mapping("data.persistence", data.get("persistence"))
    if persistence.get("mode") != PERSISTENCE_MODE:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning persistence mode mismatch"
        )
    if persistence.get("required_observations") != 2:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning requires exactly two observations"
        )
    evaluated_ids = normalize_intelligence_evidence_ids(
        persistence.get("evaluated_evidence_ids")
    )
    observations = _list("data.observations", data.get("observations"))
    if len(observations) != 2:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning must preserve exactly two observations"
        )
    for index, observation in enumerate(observations):
        record = _mapping(f"data.observations[{index}]", observation)
        if record.get("intelligence_evidence_id") != evaluated_ids[index]:
            raise CMISConcentrationWarningContractError(
                "CMIS Concentration Warning observation order drift"
            )
        if record.get("freshness_verified") is not True:
            raise CMISConcentrationWarningContractError(
                "CMIS Concentration Warning observation freshness must remain verified"
            )

    evidence = _mapping("data.evidence", data.get("evidence"))
    if tuple(normalize_intelligence_evidence_ids(
        evidence.get("intelligence_evidence_ids")
    )) != evaluated_ids:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning evidence identity drift"
        )
    if evidence.get("freshness_verified") is not True:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning evidence freshness must remain verified"
        )
    if _list("data.evidence.unresolved_fields", evidence.get("unresolved_fields")):
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning must not retain unresolved evidence fields"
        )

    canonical = _mapping("data.canonical_warning", data.get("canonical_warning"))
    if canonical.get("schema") != WARNING_SCHEMA:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning canonical warning schema mismatch"
        )
    if canonical.get("warning_id") != warning_id:
        raise CMISConcentrationWarningContractError(
            "CMIS Concentration Warning canonical warning id drift"
        )
    for field in (
        "warning_level",
        "warning_active",
        "policy",
        "freshness_policy",
        "persistence",
        "observations",
        "evidence",
        "limitations",
    ):
        if canonical.get(field) != data.get(field):
            raise CMISConcentrationWarningContractError(
                f"CMIS Concentration Warning {field} must preserve canonical warning exactly"
            )
    for field in (
        "public_service_promoted",
        "scout_reliance_promoted",
        "cmis_promotable",
        "delivery_authorized",
        "warning_level_is_risk_severity",
        "risk_interpretation_verified",
        "behavioral_interpretation_verified",
        "ownership_interpretation_verified",
        "execution_authorized",
    ):
        if canonical.get(field) is not False:
            raise CMISConcentrationWarningContractError(
                f"protected canonical warning must keep {field}=false"
            )
    if canonical.get("risk_interpretation") is not None:
        raise CMISConcentrationWarningContractError(
            "protected canonical warning risk interpretation must remain null"
        )
    if canonical.get("proof_strength_separate_from_risk") is not True:
        raise CMISConcentrationWarningContractError(
            "protected canonical warning must keep Proof Score separate from risk"
        )

    return safe


__all__ = [
    "CMISConcentrationWarningContractError",
    "DELIVERY_MODE",
    "MIN_CMIS_CONTRACT_VERSION",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "normalize_intelligence_evidence_ids",
    "normalize_threshold_policy",
    "normalize_warning_request",
    "validate_concentration_warning_response",
]
