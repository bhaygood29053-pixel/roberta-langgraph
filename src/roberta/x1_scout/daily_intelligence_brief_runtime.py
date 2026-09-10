"""Live X1 Scout adoption wrapper for ROBERTA Daily Intelligence Brief.

This module does not replace the accepted typed Daily Brief foundation. It
validates a promoted CMIS service envelope, reuses the accepted
`x1_daily_intelligence_brief/v1` projection, and wraps it in a live-reliance
contract only after the CMIS runtime promotion handshake succeeds.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.cmis.x1_intelligence_brief import (
    SERVICE,
    SERVICE_CONTRACT_VERSION,
    validate_x1_intelligence_brief_service_response,
)
from roberta.x1_scout.daily_intelligence_brief import (
    X1_DAILY_BRIEF_CONTRACT,
    build_x1_daily_intelligence_brief,
    validate_cmis_brief_inputs_foundation,
)


X1_DAILY_BRIEF_RUNTIME_CONTRACT = "x1_daily_intelligence_brief_runtime/v1"


class X1DailyIntelligenceBriefRuntimeContractError(ValueError):
    """Raised when live CMIS reliance cannot satisfy ROBERTA #412."""


def build_x1_daily_intelligence_brief_runtime(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the live Scout wrapper without mutating the accepted typed brief."""

    try:
        safe = validate_x1_intelligence_brief_service_response(
            response,
            expected_request=expected_request,
        )
        foundation = validate_cmis_brief_inputs_foundation(safe["data"])
        typed_brief = build_x1_daily_intelligence_brief(foundation)
    except Exception as exc:
        raise X1DailyIntelligenceBriefRuntimeContractError(str(exc)) from exc

    if typed_brief.get("contract_version") != X1_DAILY_BRIEF_CONTRACT:
        raise X1DailyIntelligenceBriefRuntimeContractError(
            "typed Daily Brief contract mismatch"
        )
    if typed_brief.get("runtime_reliance_authorized") is not False:
        raise X1DailyIntelligenceBriefRuntimeContractError(
            "accepted typed Daily Brief foundation must remain non-runtime"
        )
    if typed_brief.get("execution_authorized") is not False:
        raise X1DailyIntelligenceBriefRuntimeContractError(
            "accepted typed Daily Brief foundation attempted execution authority"
        )

    return {
        "contract_version": X1_DAILY_BRIEF_RUNTIME_CONTRACT,
        "product": "x1_daily_intelligence_brief_runtime",
        "chain": "x1",
        "status": typed_brief.get("status"),
        "cmis_service": SERVICE,
        "cmis_service_contract_version": SERVICE_CONTRACT_VERSION,
        "requested_subjects": deepcopy(list(expected_request.get("subjects") or [])),
        "requested_window": {
            "start": expected_request.get("window_start"),
            "end": expected_request.get("window_end"),
            "end_exclusive": True,
        },
        "requested_services": deepcopy(
            list(expected_request.get("requested_services") or [])
        ),
        "daily_brief": deepcopy(typed_brief),
        "cmis_status": safe.get("status"),
        "confidence": deepcopy(dict(safe.get("confidence") or {})),
        "freshness": deepcopy(dict(safe.get("freshness") or {})),
        "sources": deepcopy(list(safe.get("sources") or [])),
        "warnings": deepcopy(list(safe.get("warnings") or [])),
        "errors": deepcopy(list(safe.get("errors") or [])),
        "evidence_receipt": deepcopy(safe.get("evidence_receipt")),
        "proof_score": deepcopy(safe.get("proof_score")),
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "runtime_reliance_authorized": True,
        "complete_x1_ecosystem_coverage_verified": False,
        "nested_typed_brief_runtime_reliance_authorized": False,
        "provider_truth_certified": False,
        "execution_authorized": False,
    }


__all__ = [
    "X1_DAILY_BRIEF_RUNTIME_CONTRACT",
    "X1DailyIntelligenceBriefRuntimeContractError",
    "build_x1_daily_intelligence_brief_runtime",
]
