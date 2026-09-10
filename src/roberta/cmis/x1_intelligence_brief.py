"""ROBERTA-side contract for promoted CMIS X1 Intelligence Brief inputs.

This module owns only the Chain Scout <-> CMIS request/response boundary. It
never constructs component evidence, assigns priority, invents fact times,
infers risk, or calls providers.

The promoted outer service envelope is distinct from the accepted nested
`x1_intelligence_brief_inputs/v1` factual composition. The outer envelope may
be runtime-promoted while the nested factual contract preserves its original
non-promoted foundation flags.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


SERVICE = "x1_intelligence_brief_inputs"
SERVICE_CONTRACT_VERSION = "x1_intelligence_brief_inputs/v1"
REQUEST_CONTRACT_VERSION = "x1_intelligence_brief_request/v1"
SUPPORTED_CHAIN = "x1"
SUPPORTED_COMPONENT_SERVICES = (
    "concentration_warning_intelligence",
    "discovery_intelligence",
    "large_trade_discovery",
)

_BASE58 = frozenset(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)


class CMISX1IntelligenceBriefContractError(ValueError):
    """Raised when the promoted Brief service cannot be trusted by X1 Scout."""


def _mint(value: Any) -> str:
    text = str(value or "").strip()
    if not (
        32 <= len(text) <= 44
        and all(char in _BASE58 for char in text)
    ):
        raise CMISX1IntelligenceBriefContractError(
            "X1 Intelligence Brief subjects must be exact address-shaped X1 mints."
        )
    return text


def _canonical_utc(value: Any, *, field: str) -> tuple[str, datetime]:
    text = str(value or "").strip()
    if not text.endswith("Z"):
        raise CMISX1IntelligenceBriefContractError(
            f"{field} must use canonical UTC Z notation."
        )
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise CMISX1IntelligenceBriefContractError(
            f"{field} must be a valid UTC timestamp."
        ) from exc
    if parsed.tzinfo is None:
        raise CMISX1IntelligenceBriefContractError(
            f"{field} must include UTC timezone."
        )
    parsed = parsed.astimezone(timezone.utc)
    canonical = parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
    if canonical != text:
        raise CMISX1IntelligenceBriefContractError(
            f"{field} must be canonical whole-second UTC Z text."
        )
    return text, parsed


def normalize_x1_intelligence_brief_request(
    *,
    subjects: Sequence[str],
    window_start: str,
    window_end: str,
    requested_services: Sequence[str] = SUPPORTED_COMPONENT_SERVICES,
) -> dict[str, object]:
    """Build the only caller-controlled selector set accepted by CMIS #637."""

    if isinstance(subjects, (str, bytes, bytearray, Mapping)):
        raise CMISX1IntelligenceBriefContractError("subjects must be a list.")
    normalized_subjects = [_mint(value) for value in subjects]
    if not normalized_subjects:
        raise CMISX1IntelligenceBriefContractError(
            "X1 Intelligence Brief requires at least one exact mint subject."
        )
    if len(set(normalized_subjects)) != len(normalized_subjects):
        raise CMISX1IntelligenceBriefContractError(
            "X1 Intelligence Brief subjects must be unique."
        )

    if isinstance(requested_services, (str, bytes, bytearray, Mapping)):
        raise CMISX1IntelligenceBriefContractError(
            "requested_services must be a list."
        )
    normalized_services = [
        str(value or "").strip()
        for value in requested_services
    ]
    if (
        any(not value for value in normalized_services)
        or len(set(normalized_services)) != len(normalized_services)
    ):
        raise CMISX1IntelligenceBriefContractError(
            "requested_services must contain unique normalized service names."
        )
    if sorted(normalized_services) != sorted(SUPPORTED_COMPONENT_SERVICES):
        raise CMISX1IntelligenceBriefContractError(
            "ROBERTA Daily Brief v1 requires the accepted three-service CMIS set."
        )

    start_text, start = _canonical_utc(window_start, field="window_start")
    end_text, end = _canonical_utc(window_end, field="window_end")
    duration = int((end - start).total_seconds())
    if end <= start or duration <= 0 or duration > 86400:
        raise CMISX1IntelligenceBriefContractError(
            "X1 Intelligence Brief window must be >0 and <=86400 seconds."
        )

    return {
        "contract_version": REQUEST_CONTRACT_VERSION,
        "subjects": sorted(normalized_subjects),
        "window_start": start_text,
        "window_end": end_text,
        "requested_services": sorted(normalized_services),
    }


def validate_x1_intelligence_brief_service_response(
    value: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the promoted outer CMIS service envelope without widening facts."""

    if not isinstance(value, Mapping):
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief response must be a mapping."
        )
    safe = deepcopy(dict(value))

    if safe.get("service") != SERVICE:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief service identity mismatch."
        )
    if safe.get("chain") != SUPPORTED_CHAIN:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief must remain X1-only."
        )
    if safe.get("status") not in {"ok", "partial"}:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief runtime response must be ok or partial."
        )
    if safe.get("risk") is not None:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief must not create a top-level risk conclusion."
        )

    for field, expected in (
        ("read_only", True),
        ("public_service_promoted", True),
        ("scout_reliance_promoted", True),
        ("runtime_capability_promoted", True),
        ("complete_x1_ecosystem_coverage_verified", False),
        ("execution_authorized", False),
    ):
        if safe.get(field) is not expected:
            raise CMISX1IntelligenceBriefContractError(
                f"CMIS X1 Intelligence Brief {field} must be {str(expected).lower()}."
            )

    confidence = safe.get("confidence")
    if not isinstance(confidence, Mapping):
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief confidence metadata is required."
        )
    if confidence.get("proof_score_separate_from_risk") is not True:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief must keep Proof Score separate from risk."
        )
    if confidence.get("complete_x1_ecosystem_coverage_verified") is not False:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief confidence must not claim whole-X1 coverage."
        )

    freshness = safe.get("freshness")
    if not isinstance(freshness, Mapping):
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief response freshness metadata is required."
        )
    if freshness.get("state") != "UNKNOWN":
        raise CMISX1IntelligenceBriefContractError(
            "Brief envelope freshness must remain UNKNOWN; item fact time cannot promote it."
        )
    if freshness.get("freshness_verified") is not None:
        raise CMISX1IntelligenceBriefContractError(
            "Brief envelope freshness_verified must remain unknown."
        )
    if safe.get("observed_at") is not None:
        raise CMISX1IntelligenceBriefContractError(
            "Brief envelope observed_at must remain null without separate service fact-time proof."
        )

    data = safe.get("data")
    if not isinstance(data, Mapping):
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief data payload is required."
        )
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief nested contract mismatch."
        )
    if data.get("chain") != SUPPORTED_CHAIN:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS X1 Intelligence Brief nested data must remain X1-only."
        )

    # The factual composition remains the accepted non-promoted foundation.
    for field in (
        "public_service_promoted",
        "scout_reliance_promoted",
        "complete_x1_ecosystem_coverage_verified",
        "execution_authorized",
    ):
        if data.get(field) is not False:
            raise CMISX1IntelligenceBriefContractError(
                f"Nested Brief factual contract must keep {field}=false."
            )
    if data.get("read_only") is not True:
        raise CMISX1IntelligenceBriefContractError(
            "Nested Brief factual contract must remain read_only=true."
        )

    normalized_expected = normalize_x1_intelligence_brief_request(
        subjects=expected_request.get("subjects") or [],
        window_start=str(expected_request.get("window_start") or ""),
        window_end=str(expected_request.get("window_end") or ""),
        requested_services=expected_request.get("requested_services")
        or SUPPORTED_COMPONENT_SERVICES,
    )
    if sorted(data.get("subjects") or []) != normalized_expected["subjects"]:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS Brief subjects do not match the exact requested subject set."
        )
    if sorted(data.get("requested_services") or []) != normalized_expected[
        "requested_services"
    ]:
        raise CMISX1IntelligenceBriefContractError(
            "CMIS Brief services do not match the exact requested service set."
        )
    window = data.get("window")
    if not isinstance(window, Mapping):
        raise CMISX1IntelligenceBriefContractError(
            "CMIS Brief bounded window is required."
        )
    if (
        window.get("start") != normalized_expected["window_start"]
        or window.get("end") != normalized_expected["window_end"]
        or window.get("end_exclusive") is not True
    ):
        raise CMISX1IntelligenceBriefContractError(
            "CMIS Brief window does not match the exact requested bounded window."
        )

    return safe


__all__ = [
    "CMISX1IntelligenceBriefContractError",
    "REQUEST_CONTRACT_VERSION",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "SUPPORTED_CHAIN",
    "SUPPORTED_COMPONENT_SERVICES",
    "normalize_x1_intelligence_brief_request",
    "validate_x1_intelligence_brief_service_response",
]
