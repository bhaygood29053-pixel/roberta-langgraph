"""Deterministic Roberta-side interpretation of CMIS evidence metadata.

Roberta may explain CMIS evidence, but she may not recompute a CMIS proof score,
change a verification status, merge cross-chain provenance, or convert missing
evidence into a fact. This module validates and projects the accepted CMIS
Evidence Receipt / Proof Score contract into a small read-only interpretation
context for presentation and policy reasoning.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


EVIDENCE_RECEIPT_SCHEMA_VERSION = 1
PROOF_SCORE_SCHEMA_VERSION = 1
PROOF_STRENGTHS = frozenset({"STRONG", "MODERATE", "WEAK"})
VERIFICATION_STATUSES = frozenset(
    {"AGREEMENT", "CONFLICT", "INSUFFICIENT_EVIDENCE", "UNVERIFIED"}
)


class CMISEvidenceMetadataError(ValueError):
    """CMIS evidence metadata is missing, cross-boundary, or malformed."""


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [deepcopy(dict(item)) for item in value if isinstance(item, Mapping)]


def _risk_fields(envelope: Mapping[str, Any]) -> tuple[str, str]:
    """Return authoritative risk level and recommendation separately.

    PASS/WARN/BLOCK-style recommendation tokens are never relabeled as a risk
    level. If CMIS did not return a dedicated level, the level remains UNKNOWN.
    """

    risk = _mapping(envelope.get("risk"))
    level = _text(risk.get("level"))
    recommendation = None
    for key in ("recommendation", "outcome", "result"):
        recommendation = _text(risk.get(key))
        if recommendation:
            break
    return (
        level.upper() if level else "UNKNOWN",
        recommendation.upper() if recommendation else "UNKNOWN",
    )


def validate_evidence_metadata(
    envelope: Mapping[str, Any],
    *,
    required: bool = False,
) -> dict[str, Any] | None:
    """Validate CMIS evidence receipt/proof metadata without changing it.

    ``required=False`` keeps deterministic legacy test adapters compatible.
    Live CMIS responses can be validated with ``required=True`` after the
    capability handshake establishes the evidence-quality contract.
    """

    receipt_raw = envelope.get("evidence_receipt")
    proof_raw = envelope.get("proof_score")
    if receipt_raw is None and proof_raw is None and not required:
        return None
    if not isinstance(receipt_raw, Mapping) or not isinstance(proof_raw, Mapping):
        raise CMISEvidenceMetadataError(
            "CMIS evidence_receipt and proof_score must both be present objects."
        )

    receipt = receipt_raw
    proof = proof_raw
    if receipt.get("schema_version") != EVIDENCE_RECEIPT_SCHEMA_VERSION:
        raise CMISEvidenceMetadataError("Unsupported CMIS evidence receipt schema.")
    if proof.get("schema_version") != PROOF_SCORE_SCHEMA_VERSION:
        raise CMISEvidenceMetadataError("Unsupported CMIS proof score schema.")

    chain = _text(envelope.get("chain"))
    service = _text(envelope.get("service"))
    if not chain or not service:
        raise CMISEvidenceMetadataError("CMIS envelope chain/service is required.")
    if _text(receipt.get("chain")) != chain:
        raise CMISEvidenceMetadataError("CMIS evidence receipt chain mismatch.")
    if _text(receipt.get("service")) != service:
        raise CMISEvidenceMetadataError("CMIS evidence receipt service mismatch.")

    receipt_id = _text(receipt.get("receipt_id"))
    if receipt_id is None or not receipt_id.startswith("er_"):
        raise CMISEvidenceMetadataError("CMIS evidence receipt_id is invalid.")

    verification = _mapping(receipt.get("verification"))
    verification_status = _text(verification.get("status"))
    if verification_status not in VERIFICATION_STATUSES:
        raise CMISEvidenceMetadataError("CMIS evidence verification status is invalid.")
    if verification.get("provider_assertion_promoted") is not False:
        raise CMISEvidenceMetadataError(
            "CMIS evidence receipt may not claim provider assertion promotion."
        )

    proof_strength = _text(proof.get("proof_strength"))
    if proof_strength not in PROOF_STRENGTHS:
        raise CMISEvidenceMetadataError("CMIS proof strength is invalid.")
    if proof.get("risk_considered") is not False or proof.get("risk_separate") is not True:
        raise CMISEvidenceMetadataError(
            "CMIS proof score must remain explicitly separate from risk."
        )

    categories = proof.get("categories")
    if not isinstance(categories, Mapping):
        raise CMISEvidenceMetadataError("CMIS proof categories must be an object.")
    normalized_categories: dict[str, dict[str, Any]] = {}
    for raw_name, raw_category in categories.items():
        name = _text(raw_name)
        if not name or not isinstance(raw_category, Mapping):
            raise CMISEvidenceMetadataError("CMIS proof category is malformed.")
        score = raw_category.get("score")
        if score is not None and (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or score < 0
            or score > 100
        ):
            raise CMISEvidenceMetadataError(
                f"CMIS proof category {name!r} score is invalid."
            )
        state = _text(raw_category.get("state"))
        if state is None:
            raise CMISEvidenceMetadataError(
                f"CMIS proof category {name!r} state is required."
            )
        normalized_categories[name] = {
            "state": state,
            "score": score,
            "reasons": _string_list(raw_category.get("reasons")),
            "evidence_paths": _string_list(raw_category.get("evidence_paths")),
        }

    freshness = _mapping(receipt.get("freshness"))
    freshness_verified = freshness.get("verified")
    if freshness_verified not in {True, False, None}:
        raise CMISEvidenceMetadataError("CMIS evidence freshness state is invalid.")

    scope = _mapping(receipt.get("evidence_scope"))
    explicit_scope = scope.get("explicit_scope_available")
    if explicit_scope not in {True, False}:
        raise CMISEvidenceMetadataError("CMIS evidence scope flag is invalid.")

    risk_level, risk_recommendation = _risk_fields(envelope)
    return {
        "available": True,
        "chain": chain,
        "service": service,
        "receipt_id": receipt_id,
        "verification_status": verification_status,
        "verification_code": _text(verification.get("code")),
        "independently_verified": verification.get("independently_verified") is True,
        "proof_strength": proof_strength,
        "proof_percent": proof.get("proof_percent"),
        "category_coverage_percent": proof.get("category_coverage_percent"),
        "proof_categories": normalized_categories,
        "unknown_categories": _string_list(proof.get("unknown_categories")),
        "evidence_scope": deepcopy(dict(scope)),
        "freshness_verified": freshness_verified,
        "disagreements": _mapping_list(receipt.get("disagreements")),
        "limitations": _mapping_list(receipt.get("limitations")),
        "unresolved_fields": _string_list(receipt.get("unresolved_fields")),
        "sources": _mapping_list(receipt.get("sources")),
        "risk_level": risk_level,
        "risk_recommendation": risk_recommendation,
        "risk_separate_from_proof": True,
    }


def evidence_context(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Return a presentation-safe evidence context, including legacy fallback."""

    validated = validate_evidence_metadata(envelope, required=False)
    if validated is not None:
        return validated
    risk_level, risk_recommendation = _risk_fields(envelope)
    return {
        "available": False,
        "chain": _text(envelope.get("chain")) or "unknown",
        "service": _text(envelope.get("service")) or "unknown",
        "receipt_id": None,
        "verification_status": "UNVERIFIED",
        "verification_code": None,
        "independently_verified": False,
        "proof_strength": "WEAK",
        "proof_percent": None,
        "category_coverage_percent": 0,
        "proof_categories": {},
        "unknown_categories": ["evidence_receipt", "proof_score"],
        "evidence_scope": {},
        "freshness_verified": None,
        "disagreements": [],
        "limitations": [],
        "unresolved_fields": ["evidence_receipt", "proof_score"],
        "sources": [],
        "risk_level": risk_level,
        "risk_recommendation": risk_recommendation,
        "risk_separate_from_proof": True,
    }


def compare_chain_evidence(
    envelopes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare proof metadata across chains without comparing market values.

    Each envelope remains isolated under its own chain key. This helper reports
    only CMIS proof/evidence differences; it never computes cross-chain price,
    liquidity, volume, risk, or a synthetic safety score.
    """

    by_chain: dict[str, dict[str, Any]] = {}
    for raw_chain, envelope in envelopes.items():
        chain = str(raw_chain or "").strip().lower()
        if not chain:
            raise ValueError("cross-chain evidence key must name a chain")
        if not isinstance(envelope, Mapping):
            raise TypeError("cross-chain evidence values must be CMIS envelopes")
        envelope_chain = str(envelope.get("chain") or "").strip().lower()
        if envelope_chain != chain:
            raise CMISEvidenceMetadataError(
                f"cross-chain evidence mismatch: key={chain!r}, envelope={envelope_chain!r}"
            )
        by_chain[chain] = evidence_context(envelope)

    return {
        "chains": by_chain,
        "chain_isolation_preserved": True,
        "market_values_compared": False,
        "risk_values_recomputed": False,
        "proof_values_recomputed": False,
    }


__all__ = [
    "CMISEvidenceMetadataError",
    "EVIDENCE_RECEIPT_SCHEMA_VERSION",
    "PROOF_SCORE_SCHEMA_VERSION",
    "PROOF_STRENGTHS",
    "compare_chain_evidence",
    "evidence_context",
    "validate_evidence_metadata",
]
