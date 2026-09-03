"""Deterministic X1 Scout projection of CMIS Concentration Warning Intelligence v1.

This module preserves the accepted CMIS pull-only warning response. It does not
recompute WATCH/CLEAR, persistence, threshold policy, freshness, Evidence
Receipts, Proof Scores, risk, or delivery state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from roberta.cmis.concentration_warning import (
    DELIVERY_MODE,
    SERVICE_CONTRACT_VERSION as CMIS_WARNING_CONTRACT,
    validate_concentration_warning_response,
)


CONCENTRATION_WARNING_CONTRACT = "x1_concentration_warning_intelligence/v1"


class X1ConcentrationWarningContractError(ValueError):
    """Raised when CMIS warning output cannot satisfy the X1 Scout product."""


def _mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise X1ConcentrationWarningContractError(
            f"required Concentration Warning object missing: {key}"
        )
    return value


def _sequence(container: Mapping[str, Any], key: str) -> list[Any]:
    value = container.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, Mapping)):
        raise X1ConcentrationWarningContractError(
            f"required Concentration Warning list malformed: {key}"
        )
    return list(value)


def build_x1_concentration_warning_intelligence(
    warning_result: Mapping[str, Any],
    *,
    requested_asset: str,
) -> dict[str, object]:
    """Preserve one validated CMIS warning response without recomputation."""

    if not isinstance(warning_result, Mapping):
        raise X1ConcentrationWarningContractError(
            "CMIS Concentration Warning result must be an object"
        )
    try:
        safe = validate_concentration_warning_response(
            warning_result,
            requested_asset=requested_asset,
        )
    except Exception as exc:
        raise X1ConcentrationWarningContractError(str(exc)) from exc

    if safe.get("status") != "ok":
        raise X1ConcentrationWarningContractError(
            "X1 Concentration Warning product requires accepted CMIS ok status"
        )
    if safe.get("risk") is not None:
        raise X1ConcentrationWarningContractError(
            "X1 Concentration Warning product must not promote risk"
        )

    asset = _mapping(safe, "asset")
    data = _mapping(safe, "data")
    if data.get("contract_version") != CMIS_WARNING_CONTRACT:
        raise X1ConcentrationWarningContractError(
            "CMIS Concentration Warning service contract mismatch"
        )
    if data.get("delivery_mode") != DELIVERY_MODE:
        raise X1ConcentrationWarningContractError(
            "Concentration Warning delivery mode must remain pull_only"
        )
    if data.get("push_delivery_authorized") is not False:
        raise X1ConcentrationWarningContractError(
            "Concentration Warning push delivery must remain unauthorized"
        )
    if data.get("warning_level_is_risk_severity") is not False:
        raise X1ConcentrationWarningContractError(
            "Concentration Warning state must remain separate from risk severity"
        )
    if data.get("execution_authorized") is not False:
        raise X1ConcentrationWarningContractError(
            "Concentration Warning must preserve execution_authorized=false"
        )

    confidence = _mapping(safe, "confidence")
    sources = _sequence(safe, "sources")
    warnings = _sequence(safe, "warnings")
    errors = _sequence(safe, "errors")

    return {
        "contract_version": CONCENTRATION_WARNING_CONTRACT,
        "product": "x1_concentration_warning_intelligence",
        "chain": "x1",
        "status": "ok",
        "requested_asset": requested_asset,
        "asset": deepcopy(dict(asset)),
        "warning": deepcopy(dict(data)),
        "observed_at": safe.get("observed_at"),
        "confidence": deepcopy(dict(confidence)),
        "sources": deepcopy(sources),
        "warnings": deepcopy(warnings),
        "errors": deepcopy(errors),
        "evidence_receipt": deepcopy(safe.get("evidence_receipt")),
        "proof_score": deepcopy(safe.get("proof_score")),
        "proof_score_separate_from_risk": True,
        "delivery_mode": DELIVERY_MODE,
        "push_delivery_authorized": False,
        "warning_level_is_risk_severity": False,
        "risk_interpretation": None,
        "execution_authorized": False,
    }


__all__ = [
    "CMIS_WARNING_CONTRACT",
    "CONCENTRATION_WARNING_CONTRACT",
    "X1ConcentrationWarningContractError",
    "build_x1_concentration_warning_intelligence",
]
