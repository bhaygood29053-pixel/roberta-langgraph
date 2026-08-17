"""Exact selector validation for persisted CMIS verification evidence."""

from __future__ import annotations


def normalize_verification_evidence_selector(
    *,
    evidence_id: str | None = None,
    fact_type: str | None = None,
    subject_id: str | None = None,
) -> dict[str, str]:
    """Return the only selector shapes CMIS accepts for persisted evidence.

    Roberta and X1 Scout may select a stable content-addressed evidence record,
    or the latest record for one exact fact identity. They may not infer a fact
    from an asset name or combine selector modes.
    """

    evidence_key = str(evidence_id or "").strip()
    fact_key = str(fact_type or "").strip()
    subject_key = str(subject_id or "").strip()

    if evidence_key:
        if fact_key or subject_key:
            raise ValueError(
                "verification_evidence accepts evidence_id OR fact_type + subject_id, not both"
            )
        return {"evidence_id": evidence_key}

    if fact_key or subject_key:
        if not fact_key or not subject_key:
            raise ValueError(
                "verification_evidence fact selection requires both fact_type and subject_id"
            )
        return {"fact_type": fact_key, "subject_id": subject_key}

    raise ValueError(
        "verification_evidence requires evidence_id OR fact_type + subject_id"
    )


__all__ = ["normalize_verification_evidence_selector"]
