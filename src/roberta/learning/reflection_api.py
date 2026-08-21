"""Public Phase 8 candidate lifecycle seams.

The end-to-end authority root remains ``build_learning_candidate_bundle`` plus
``validate_learning_candidate_bundle``. These wrappers additionally require a
locally content-address-valid provisional ReflectionRecord before allowing a
standalone candidate creation or lifecycle transition, so a mutated reflection
cannot be used as provenance by the public package surface.
"""

from __future__ import annotations

from .reflection import (
    CANDIDATE_LESSON_CONTRACT,
    LEARNING_DIAGNOSIS_VERSION,
    REFLECTION_CONTRACT,
    VERIFICATION_PLAN_CONTRACT,
    CandidateLesson,
    ReflectionError,
    ReflectionRecord,
    VerificationPlan,
    _hash,
    _reflection_material,
    create_candidate_lesson as _create_candidate_lesson,
    diagnose_failure_layers,
    transition_candidate_lesson as _transition_candidate_lesson,
)


def _validate_local_reflection_integrity(
    reflection: ReflectionRecord,
) -> ReflectionRecord:
    if not isinstance(reflection, ReflectionRecord):
        raise ReflectionError("reflection must be ReflectionRecord")
    if reflection.reflection_contract != REFLECTION_CONTRACT:
        raise ReflectionError("unsupported reflection contract")
    if reflection.diagnosis_version != LEARNING_DIAGNOSIS_VERSION:
        raise ReflectionError("unsupported reflection diagnosis version")
    if reflection.status != "provisional":
        raise ReflectionError("candidate lifecycle requires a provisional reflection")
    if reflection.content_category != "generated_provisional":
        raise ReflectionError("candidate lifecycle requires generated provisional content")
    if not reflection.failure_classifications:
        raise ReflectionError("reflection must preserve at least one failure classification")
    expected_layers = diagnose_failure_layers(
        reflection.failure_classifications,
        diagnosis_version=reflection.diagnosis_version,
    )
    if reflection.diagnosed_layers != expected_layers:
        raise ReflectionError("reflection diagnosed layers do not match failure classes")
    expected_hash = _hash(_reflection_material(reflection))
    if (
        reflection.reflection_hash != expected_hash
        or reflection.reflection_id != f"refl_{expected_hash}"
    ):
        raise ReflectionError("reflection record identity/content is invalid")
    return reflection


def create_candidate_lesson(
    *,
    reflection: ReflectionRecord,
    lesson_text: str,
    rationale: str,
    created_by: str,
    producer_version: str,
    candidate_lesson_contract: str = CANDIDATE_LESSON_CONTRACT,
    candidate_version: str = "1.0.0",
    verification_plan_contract: str = VERIFICATION_PLAN_CONTRACT,
    plan_version: str = "1.0.0",
) -> tuple[CandidateLesson, VerificationPlan]:
    """Create a candidate only from an integrity-valid provisional reflection."""

    canonical = _validate_local_reflection_integrity(reflection)
    return _create_candidate_lesson(
        reflection=canonical,
        lesson_text=lesson_text,
        rationale=rationale,
        created_by=created_by,
        producer_version=producer_version,
        candidate_lesson_contract=candidate_lesson_contract,
        candidate_version=candidate_version,
        verification_plan_contract=verification_plan_contract,
        plan_version=plan_version,
    )


def transition_candidate_lesson(
    *,
    reflection: ReflectionRecord,
    candidate: CandidateLesson,
    verification_plan: VerificationPlan,
    status: str,
    reason: str,
    superseded_by_candidate_id: str | None = None,
) -> CandidateLesson:
    """Apply a Phase 8 disposition only with an integrity-valid reflection."""

    canonical = _validate_local_reflection_integrity(reflection)
    return _transition_candidate_lesson(
        reflection=canonical,
        candidate=candidate,
        verification_plan=verification_plan,
        status=status,
        reason=reason,
        superseded_by_candidate_id=superseded_by_candidate_id,
    )
