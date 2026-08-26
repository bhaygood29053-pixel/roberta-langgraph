from __future__ import annotations

from dataclasses import replace

import pytest

from roberta.learning.promotion import (
    KnowledgePromotionError,
    authorize_operational_trust,
    classify_verified_learned_knowledge,
)
from roberta.learning.retention import (
    InMemoryRetentionApprovalRegistry,
    retain_verified_lesson,
)
from tests.test_learning_retention import _phase9_fixture, _prepare, _record_approval


def _retained():
    fixture = _phase9_fixture()
    store, preparation = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()
    _record_approval(preparation, registry)
    decision = retain_verified_lesson(
        preparation=preparation,
        lesson_store=store,
        approval_registry=registry,
        recorded_at="2026-08-26T12:00:00Z",
    )
    return decision


def test_verified_classification_preserves_complete_promotion_lineage() -> None:
    decision = _retained()
    record = classify_verified_learned_knowledge(
        lesson=decision.verified_lesson,
        lifecycle_state=decision.lesson_state,
        retention_decision=decision,
    )

    assert record.lesson_id == decision.verified_lesson.lesson_id
    assert record.retention_decision_id == decision.decision_id
    assert record.retention_preparation_id == decision.preparation_id
    assert record.verification_id == decision.verified_lesson.verification_id
    assert record.source_ids == decision.verified_lesson.lesson_scope.source_ids
    assert record.contradiction_snapshot_id == decision.verified_lesson.contradiction_snapshot_id
    assert record.approval_id == decision.verified_lesson.approval_id
    assert record.operational_trust_authorized is False
    assert record.source_truth_authorized is False
    assert record.live_state_authorized is False
    assert record.cmis_provider_trust_authorized is False
    assert record.governance_mutation_authorized is False
    assert record.wallet_authorized is False
    assert record.execution_authorized is False


def test_generation_memory_repetition_or_exam_success_cannot_replace_retention_lineage() -> None:
    decision = _retained()
    tampered = replace(decision, preparation_id="remembered-or-repeated")
    with pytest.raises(KnowledgePromotionError, match="retention decision is invalid"):
        classify_verified_learned_knowledge(
            lesson=decision.verified_lesson,
            lifecycle_state=decision.lesson_state,
            retention_decision=tampered,
        )


def test_operational_promotion_is_unavailable_without_separately_accepted_wrapper() -> None:
    with pytest.raises(KnowledgePromotionError, match="separately accepted"):
        authorize_operational_trust("generated", remembered=True, exam_passed=True)
