"""Strict validator for the accepted CMIS Instant X1 Scan v1 payload.

CMIS owns the composed facts. This module validates authority/evidence contract
shape only; it never recomputes market data, proof, risk, holder semantics,
concentration, or historical coverage.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from roberta.cmis.capabilities import INSTANT_X1_SCAN_CONTRACT_VERSION
from roberta.cmis.contracts import CMISEnvelope


_REQUIRED_SECTIONS = (
    "identity",
    "market",
    "tokenomics",
    "holder_concentration",
    "history",
    "risk",
    "evidence",
)

_REQUIRED_LIMITATIONS = (
    "missing_or_unverified_fields_remain_unknown",
    "holder_count_requires_existing_verified_holder_semantics",
    "current_top_account_concentration_not_promoted_in_v1",
    "history_is_cmis_stored_verified_observations_only",
    "history_does_not_imply_complete_asset_lifetime",
    "proof_score_does_not_modify_market_facts_or_risk",
    "risk_score_remains_unavailable_until_separately_calibrated",
    "execution_authorized_false",
)


class CMISInstantX1ScanContractError(RuntimeError):
    """CMIS returned a successful scan outside the accepted v1 authority shape."""


def _mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan field {field} must be an object."
        )
    return value


def validate_instant_x1_scan_response(
    envelope: CMISEnvelope,
) -> CMISEnvelope:
    """Validate successful/partial Instant X1 Scan results without rewriting them.

    Unavailable/error envelopes are already fail-closed and may omit the product
    data contract. Every other service result must match the accepted v1 shape.
    """

    if envelope.get("service") != "instant_x1_scan":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response service identity mismatch."
        )
    if envelope.get("chain") != "x1":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response must remain X1-only."
        )

    if envelope.get("status") in {"unavailable", "error"}:
        failed_data = envelope.get("data")
        if failed_data != {}:
            raise CMISInstantX1ScanContractError(
                "Failed CMIS Instant X1 Scan responses must not expose product data."
            )
        if envelope.get("risk") is not None:
            raise CMISInstantX1ScanContractError(
                "Failed CMIS Instant X1 Scan responses must not expose risk data."
            )
        return envelope

    data = _mapping(envelope.get("data"), field="data")
    if data.get("contract_version") != INSTANT_X1_SCAN_CONTRACT_VERSION:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response contract_version mismatch."
        )
    if data.get("read_only") is not True:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response must remain read-only."
        )
    if data.get("execution_authorized") is not False:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response must preserve execution_authorized=false."
        )

    sections = _mapping(data.get("sections"), field="data.sections")
    missing_sections = [
        name for name in _REQUIRED_SECTIONS if not isinstance(sections.get(name), Mapping)
    ]
    if missing_sections:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response is missing required sections: "
            + ", ".join(missing_sections)
        )

    limitations = data.get("limitations")
    if not isinstance(limitations, list) or any(
        not isinstance(item, str) or not item.strip() for item in limitations
    ):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan limitations must be a list of non-empty strings."
        )
    missing_limitations = sorted(set(_REQUIRED_LIMITATIONS) - set(limitations))
    if missing_limitations:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response is missing accepted limitations: "
            f"{missing_limitations!r}."
        )

    evidence = _mapping(sections["evidence"], field="data.sections.evidence")
    if evidence.get("proof_score_separate_from_risk") is not True:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan must keep Proof Score separate from risk."
        )
    if evidence.get("runtime_evidence_receipt_post_processing_only") is not True:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan evidence-receipt runtime boundary mismatch."
        )

    risk = _mapping(sections["risk"], field="data.sections.risk")
    if risk.get("execution_authorized") is not False:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan risk section must preserve execution_authorized=false."
        )

    holder = _mapping(
        sections["holder_concentration"],
        field="data.sections.holder_concentration",
    )
    current_concentration = _mapping(
        holder.get("top_account_concentration"),
        field="data.sections.holder_concentration.top_account_concentration",
    )
    if (
        current_concentration.get("verified") is not False
        or current_concentration.get("state") != "unavailable"
        or current_concentration.get("value") is not None
    ):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan v1 current concentration must remain explicitly unavailable."
        )

    return envelope


__all__ = [
    "CMISInstantX1ScanContractError",
    "validate_instant_x1_scan_response",
]
