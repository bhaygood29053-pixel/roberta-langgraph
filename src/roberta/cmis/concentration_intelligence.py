"""Fail-closed Scout-side gate for the first promoted CMIS intelligence service.

The Phase 11 intelligence foundation remains non-promoted. This module validates
only the separately promoted X1 public service introduced by CMIS contract 1.9.0.
It never interprets concentration facts, Proof Score, policy output, or risk.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    service_capability,
)

SERVICE = "concentration_change_intelligence"
MIN_CONTRACT_VERSION = "1.9.0"
SERVICE_CONTRACT_VERSION = "concentration_change_intelligence/v1"
PROMOTION_SCOPE = "cmis_owned_top_account_concentration_change_evidence_by_id"
ACCEPTED_CONCLUSION_TYPE = "top_account_concentration_change"
_ID_RE = re.compile(r"^ie_[0-9a-f]{64}$")


def normalize_intelligence_evidence_id(value: Any) -> str:
    """Mirror the canonical public identifier shape accepted by CMIS."""
    if not isinstance(value, str) or value.strip() != value or not _ID_RE.fullmatch(value):
        raise ValueError("intelligence_evidence_id must be a canonical ie_ content id")
    return value


def _semver(value: object) -> tuple[int, int, int]:
    text = str(value or "").strip()
    parts = text.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise CMISCapabilityContractError(
            f"CMIS contract_version must be numeric MAJOR.MINOR.PATCH, got {text!r}."
        )
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def require_concentration_intelligence_promotion(
    raw_manifest: Mapping[str, Any],
    *,
    chain: str,
) -> Mapping[str, Any]:
    """Require the exact 1.9 X1 promotion contract before Scout reliance."""
    normalized_chain = str(chain or "").strip().lower()
    if not normalized_chain:
        raise CMISCapabilityUnavailable(
            chain="unknown",
            service=SERVICE,
            state=None,
            limitations=["chain_required"],
        )

    if _semver(raw_manifest.get("contract_version")) < _semver(MIN_CONTRACT_VERSION):
        raise CMISCapabilityContractError(
            "CMIS concentration intelligence requires contract 1.9.0 or newer."
        )

    capability = service_capability(raw_manifest, chain=normalized_chain, service=SERVICE)
    if capability is None:
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service=SERVICE,
            state=None,
            limitations=["capability_record_missing"],
        )

    # `service_capability` returns a generic Mapping at runtime. Promotion fields
    # are validated from the raw manifest because the 1.8-compatible normalized
    # capability shape deliberately does not invent defaults for newer fields.
    chains = raw_manifest.get("chains")
    chain_record = chains.get(normalized_chain) if isinstance(chains, Mapping) else None
    services = chain_record.get("services") if isinstance(chain_record, Mapping) else None
    raw = services.get(SERVICE) if isinstance(services, Mapping) else None
    if not isinstance(raw, Mapping):
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service=SERVICE,
            state=None,
            limitations=["capability_record_missing"],
        )

    if normalized_chain != "x1":
        if (
            raw.get("state") != "unavailable"
            or raw.get("callable") is not False
            or raw.get("public_service_promoted") is not False
            or raw.get("scout_reliance_promoted") is not False
            or raw.get("execution_authorized") is not False
        ):
            raise CMISCapabilityContractError(
                f"CMIS {normalized_chain}/{SERVICE} must remain unavailable and non-promoted."
            )
        raise CMISCapabilityUnavailable(
            chain=normalized_chain,
            service=SERVICE,
            state="unavailable",
            limitations=list(raw.get("limitations") or []),
        )

    expected = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "promotion_scope": PROMOTION_SCOPE,
        "execution_authorized": False,
    }
    for field, expected_value in expected.items():
        if raw.get(field) != expected_value:
            raise CMISCapabilityContractError(
                f"CMIS {SERVICE} promotion field {field} must be {expected_value!r}."
            )

    conclusion_types = raw.get("accepted_conclusion_types")
    if conclusion_types != [ACCEPTED_CONCLUSION_TYPE]:
        raise CMISCapabilityContractError(
            "CMIS concentration intelligence accepted conclusion scope drifted."
        )

    return raw


__all__ = [
    "ACCEPTED_CONCLUSION_TYPE",
    "MIN_CONTRACT_VERSION",
    "PROMOTION_SCOPE",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "normalize_intelligence_evidence_id",
    "require_concentration_intelligence_promotion",
]
