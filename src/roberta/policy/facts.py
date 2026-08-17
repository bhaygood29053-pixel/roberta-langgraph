"""Explicit structured-evidence adapters for Oracle policy facts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from roberta.policy.contracts import EvidenceStatus, FreshnessStatus, PolicyFact


@dataclass(frozen=True, slots=True)
class EvidenceFrame:
    """One structured payload with caller-established evidence authority.

    The caller owns the verification decision. This adapter never infers that a
    provider/CMIS/scout payload is verified merely because fields are present.
    """

    payload: Mapping[str, Any]
    evidence_status: EvidenceStatus
    freshness: FreshnessStatus
    source: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, Mapping):
            raise TypeError("evidence frame payload must be a mapping")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("evidence frame source must be a non-empty string")
        # Reuse PolicyFact validation for the two status vocabularies.
        PolicyFact(
            value=True,
            evidence_status=self.evidence_status,
            freshness=self.freshness,
            source=self.source,
        )


@dataclass(frozen=True, slots=True)
class FactPathSpec:
    """Exact mapping path used to expose one field to deterministic policy."""

    fact_key: str
    path: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.fact_key, str) or not self.fact_key.strip():
            raise ValueError("fact_key must be a non-empty string")
        if not isinstance(self.path, tuple) or not self.path:
            raise ValueError("fact path must be a non-empty tuple")
        if any(not isinstance(part, str) or not part.strip() for part in self.path):
            raise ValueError("fact path parts must be non-empty strings")


def _read_mapping_path(payload: Mapping[str, Any], path: tuple[str, ...]) -> tuple[bool, Any]:
    current: Any = payload
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    return True, current


def extract_policy_facts(
    frame: EvidenceFrame,
    specs: Sequence[FactPathSpec],
) -> dict[str, PolicyFact]:
    """Extract only explicitly declared fields from one structured evidence frame.

    Missing paths are omitted so rules depending on them become
    ``insufficient_evidence``. Explicit nulls are retained but downgraded to
    ``insufficient_evidence`` because a null payload value is not usable proof.
    Duplicate fact keys fail closed rather than silently choosing one path.
    """

    facts: dict[str, PolicyFact] = {}
    for spec in specs:
        if spec.fact_key in facts:
            raise ValueError(f"duplicate policy fact mapping: {spec.fact_key!r}")
        found, value = _read_mapping_path(frame.payload, spec.path)
        if not found:
            continue
        status: EvidenceStatus = (
            "insufficient_evidence" if value is None else frame.evidence_status
        )
        facts[spec.fact_key] = PolicyFact(
            value=value,
            evidence_status=status,
            freshness=frame.freshness,
            source=frame.source,
        )
    return facts


def merge_policy_facts(*fact_sets: Mapping[str, PolicyFact]) -> dict[str, PolicyFact]:
    """Merge independent fact sets without allowing silent evidence replacement."""

    merged: dict[str, PolicyFact] = {}
    for fact_set in fact_sets:
        for key, fact in fact_set.items():
            if key in merged:
                raise ValueError(f"duplicate policy fact from multiple sources: {key!r}")
            if not isinstance(fact, PolicyFact):
                raise TypeError("policy fact sets must contain PolicyFact values")
            merged[key] = fact
    return merged
