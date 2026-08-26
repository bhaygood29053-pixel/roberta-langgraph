"""Fail-closed Learning Plane knowledge classification and promotion boundary.

Generated, remembered, repeated, or exam-passing content is never trusted by
itself.  This module can classify an exact active Phase 10 lesson as verified
learned knowledge while preserving its complete retention lineage.  It does not
provide an operational-trust promotion wrapper; that requires a separately
accepted contract and remains unavailable here.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .retention import (
    RETENTION_CONTRACT,
    RetentionDecision,
    VerifiedLessonRecord,
    VerifiedLessonState,
    validate_retention_decision,
)


LEARNING_KNOWLEDGE_CLASSIFICATION_CONTRACT = "learning-knowledge-classification/v1"
VERIFIED_LEARNED_KNOWLEDGE = "verified_learned_knowledge"


class KnowledgePromotionError(ValueError):
    """Raised when learned knowledge cannot cross a trust boundary safely."""


@dataclass(frozen=True, slots=True)
class VerifiedKnowledgeClassification:
    classification_id: str
    classification_hash: str
    contract: str
    classification: str
    lesson_id: str
    lesson_hash: str
    lifecycle_state_id: str
    retention_decision_id: str
    retention_preparation_id: str
    verification_id: str
    source_ids: tuple[str, ...]
    contradiction_snapshot_id: str
    approval_id: str
    operational_trust_authorized: bool = False

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def cmis_provider_trust_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False

    @property
    def wallet_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise KnowledgePromotionError("classification material must be canonical JSON") from exc


def _material(record: VerifiedKnowledgeClassification) -> dict[str, Any]:
    return {
        "contract": record.contract,
        "classification": record.classification,
        "lesson_id": record.lesson_id,
        "lesson_hash": record.lesson_hash,
        "lifecycle_state_id": record.lifecycle_state_id,
        "retention_decision_id": record.retention_decision_id,
        "retention_preparation_id": record.retention_preparation_id,
        "verification_id": record.verification_id,
        "source_ids": list(record.source_ids),
        "contradiction_snapshot_id": record.contradiction_snapshot_id,
        "approval_id": record.approval_id,
        "operational_trust_authorized": False,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "cmis_provider_trust_authorized": False,
        "governance_mutation_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def classify_verified_learned_knowledge(
    *,
    lesson: VerifiedLessonRecord,
    lifecycle_state: VerifiedLessonState,
    retention_decision: RetentionDecision,
) -> VerifiedKnowledgeClassification:
    """Classify one exact active retained lesson without operational promotion."""

    if not isinstance(lesson, VerifiedLessonRecord):
        raise KnowledgePromotionError("lesson must be a verified Phase 10 lesson")
    if not isinstance(lifecycle_state, VerifiedLessonState):
        raise KnowledgePromotionError("lifecycle_state must be a Phase 10 state")
    try:
        decision = validate_retention_decision(retention_decision)
    except ValueError as exc:
        raise KnowledgePromotionError("retention decision is invalid") from exc
    if decision.retention_contract != RETENTION_CONTRACT:
        raise KnowledgePromotionError("retention contract is not accepted")
    if decision.status != "retained" or decision.verified_lesson != lesson:
        raise KnowledgePromotionError("classification requires the exact retained lesson decision")
    if decision.lesson_state != lifecycle_state:
        raise KnowledgePromotionError("classification requires the exact decision lifecycle state")
    if lifecycle_state.lesson_id != lesson.lesson_id or lifecycle_state.status != "active":
        raise KnowledgePromotionError("only the exact active retained lesson is classifiable")
    if not lesson.lesson_scope.source_ids or not lesson.verification_id:
        raise KnowledgePromotionError("lesson provenance is incomplete")

    provisional = VerifiedKnowledgeClassification(
        classification_id="",
        classification_hash="",
        contract=LEARNING_KNOWLEDGE_CLASSIFICATION_CONTRACT,
        classification=VERIFIED_LEARNED_KNOWLEDGE,
        lesson_id=lesson.lesson_id,
        lesson_hash=lesson.lesson_hash,
        lifecycle_state_id=lifecycle_state.state_id,
        retention_decision_id=decision.decision_id,
        retention_preparation_id=decision.preparation_id,
        verification_id=lesson.verification_id,
        source_ids=lesson.lesson_scope.source_ids,
        contradiction_snapshot_id=lesson.contradiction_snapshot_id,
        approval_id=lesson.approval_id,
    )
    digest = hashlib.sha256(_canonical_json(_material(provisional)).encode()).hexdigest()
    return VerifiedKnowledgeClassification(
        classification_id=f"vkc_{digest}",
        classification_hash=digest,
        contract=provisional.contract,
        classification=provisional.classification,
        lesson_id=provisional.lesson_id,
        lesson_hash=provisional.lesson_hash,
        lifecycle_state_id=provisional.lifecycle_state_id,
        retention_decision_id=provisional.retention_decision_id,
        retention_preparation_id=provisional.retention_preparation_id,
        verification_id=provisional.verification_id,
        source_ids=provisional.source_ids,
        contradiction_snapshot_id=provisional.contradiction_snapshot_id,
        approval_id=provisional.approval_id,
    )


def authorize_operational_trust(*_args: object, **_kwargs: object) -> None:
    """Deny operational promotion until a separate accepted wrapper exists."""

    raise KnowledgePromotionError(
        "operational trust requires a separately accepted promotion wrapper"
    )
