"""Strict validator for the accepted CMIS Instant X1 Scan v1 payload.

CMIS owns the composed facts. This module validates authority/evidence contract
shape only; it never recomputes market data, proof, risk, holder semantics,
concentration, or historical coverage.
"""

from __future__ import annotations

from collections.abc import Mapping
import math
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


def _validate_rationale_list(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field} must be a list of non-empty strings."
        )
    return value


def _validate_outer_envelope(envelope: Mapping[str, Any]) -> None:
    for field in ("asset", "data", "confidence"):
        _mapping(envelope.get(field), field=field)
    for field in ("sources", "warnings", "errors"):
        if not isinstance(envelope.get(field), list):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan field {field} must be a list."
            )
    if "observed_at" not in envelope:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan field observed_at is required."
        )
    if "risk" not in envelope:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan field risk is required."
        )
    for field in ("evidence_receipt", "proof_score"):
        if field in envelope and not isinstance(envelope.get(field), Mapping):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan field {field} must be an object when present."
            )


def _validate_score(value: object, *, verified: object, field: str) -> None:
    if not isinstance(verified, bool):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field}_verified must be boolean."
        )
    if value is None:
        if verified is True:
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan {field} cannot be verified when unavailable."
            )
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field} must be a finite JSON number or null."
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field} must be finite."
        )


def _validate_risk_projection(
    value: object,
    *,
    field: str,
    require_execution_false: bool,
) -> Mapping[str, Any]:
    risk = _mapping(value, field=field)
    recommendation = risk.get("recommendation")
    if recommendation is not None and (
        not isinstance(recommendation, str) or not recommendation.strip()
    ):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field}.recommendation must be non-empty text or null."
        )

    _validate_rationale_list(risk.get("flags"), field=f"{field}.flags")
    _validate_rationale_list(risk.get("reasons"), field=f"{field}.reasons")

    for object_field in ("confidence", "policy"):
        if not isinstance(risk.get(object_field), Mapping):
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan {field}.{object_field} must be an object."
            )

    _validate_score(
        risk.get("score"),
        verified=risk.get("score_verified"),
        field=f"{field}.score",
    )

    score_reason = risk.get("score_reason")
    if score_reason is not None and (
        not isinstance(score_reason, str) or not score_reason.strip()
    ):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field}.score_reason must be non-empty text or null."
        )

    if require_execution_false:
        if risk.get("execution_authorized") is not False:
            raise CMISInstantX1ScanContractError(
                f"CMIS Instant X1 Scan {field} must preserve execution_authorized=false."
            )
    elif (
        "execution_authorized" in risk
        and risk.get("execution_authorized") is not False
    ):
        raise CMISInstantX1ScanContractError(
            f"CMIS Instant X1 Scan {field} must not authorize execution."
        )
    return risk


def validate_instant_x1_scan_response(
    envelope: CMISEnvelope,
) -> CMISEnvelope:
    """Validate Instant X1 Scan results without rewriting CMIS facts.

    Only ok/partial envelopes may carry the product contract. Ambiguous,
    unavailable, and error envelopes must remain fail-closed with empty product
    data and no risk payload.
    """

    if envelope.get("service") != "instant_x1_scan":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response service identity mismatch."
        )
    if envelope.get("chain") != "x1":
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response must remain X1-only."
        )

    _validate_outer_envelope(envelope)

    status = envelope.get("status")
    if not isinstance(status, str):
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response status must be text."
        )
    if status in {"ambiguous", "unavailable", "error"}:
        failed_data = envelope.get("data")
        if not isinstance(failed_data, Mapping):
            raise CMISInstantX1ScanContractError(
                "Failed CMIS Instant X1 Scan data must be an object."
            )
        if failed_data:
            allowed_keys = {"upstream_service"}
            if set(failed_data) != allowed_keys:
                raise CMISInstantX1ScanContractError(
                    "Failed CMIS Instant X1 Scan responses may expose only "
                    "upstream_service diagnostic data."
                )
            upstream_service = failed_data.get("upstream_service")
            if not isinstance(upstream_service, str) or not upstream_service.strip():
                raise CMISInstantX1ScanContractError(
                    "Failed CMIS Instant X1 Scan upstream_service must be non-empty text."
                )
        if envelope.get("risk") is not None:
            raise CMISInstantX1ScanContractError(
                "Failed CMIS Instant X1 Scan responses must not expose risk data."
            )
        return envelope

    if status not in {"ok", "partial"}:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan response status must be one of "
            "ok, partial, ambiguous, unavailable, error."
        )

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

    risk = _validate_risk_projection(
        sections["risk"],
        field="data.sections.risk",
        require_execution_false=True,
    )
    nested_flags = risk["flags"]
    nested_reasons = risk["reasons"]

    envelope_risk = envelope.get("risk")
    if envelope_risk is None:
        raise CMISInstantX1ScanContractError(
            "Successful CMIS Instant X1 Scan responses must expose envelope risk."
        )
    top_risk = _validate_risk_projection(
        envelope_risk,
        field="risk",
        require_execution_false=False,
    )
    top_flags = top_risk["flags"]
    top_reasons = top_risk["reasons"]

    shared_fields = (
        ("recommendation", risk.get("recommendation"), top_risk.get("recommendation")),
        ("flags", nested_flags, top_flags),
        ("reasons", nested_reasons, top_reasons),
        ("confidence", risk.get("confidence"), top_risk.get("confidence")),
        ("score", risk.get("score"), top_risk.get("score")),
        (
            "score_verified",
            risk.get("score_verified"),
            top_risk.get("score_verified"),
        ),
        ("score_reason", risk.get("score_reason"), top_risk.get("score_reason")),
        ("policy", risk.get("policy"), top_risk.get("policy")),
    )
    mismatched = [
        name for name, nested_value, top_value in shared_fields
        if nested_value != top_value
    ]
    if mismatched:
        raise CMISInstantX1ScanContractError(
            "CMIS Instant X1 Scan envelope risk does not match the nested "
            "risk projection for fields: "
            + ", ".join(mismatched)
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
