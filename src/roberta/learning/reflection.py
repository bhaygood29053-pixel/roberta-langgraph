"""Provisional reflection and candidate-lesson foundation.

Phase 8 converts canonical failed Phase 7 evaluations into deterministic,
provenance-bound learning candidates. Reflection and lesson text remain
explicitly generated/provisional. Nothing in this module verifies a lesson,
writes trusted memory, changes live-state truth, mutates governance, or grants
execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

from .evaluation import (
    ANSWER_EVALUATION_CONTRACT,
    DETERMINISTIC_EVALUATOR_ADAPTER,
    EvaluationResult,
    GoldenEvaluationCase,
    evaluate_grounded_answer,
)
from .grounding import EvidencePacket, EvidenceReference, GroundedAnswerResult


REFLECTION_CONTRACT = "evaluation-reflection/v1"
CANDIDATE_LESSON_CONTRACT = "candidate-lesson/v1"
VERIFICATION_PLAN_CONTRACT = "candidate-lesson-verification-plan/v1"
LEARNING_DIAGNOSIS_VERSION = "1.0.0"
_DEFAULT_REFLECTION_VERSION = "1.0.0"
_DEFAULT_CANDIDATE_VERSION = "1.0.0"
_DEFAULT_PLAN_VERSION = "1.0.0"
_GENERATED_PROVISIONAL = "generated_provisional"
_CANDIDATE_STATUSES = frozenset({"provisional", "rejected", "superseded"})

_FAILURE_TO_LAYER = {
    "retrieval_failure": "retrieval",
    "citation_binding_failure": "citation_binding",
    "unsupported_claim_failure": "answer_support",
    "answer_correctness_failure": "answer_correctness",
    "answer_completeness_failure": "answer_completeness",
    "conflict_handling_failure": "conflict_handling",
    "insufficiency_handling_failure": "insufficiency_handling",
    "uncertainty_calibration_failure": "uncertainty_calibration",
    "instruction_compliance_failure": "instruction_compliance",
    "evaluator_unavailable": "evaluator",
    "evaluator_disagreement": "evaluator",
    "unknown": "unknown",
}

_FAILURE_TO_CHECK = {
    "retrieval_failure": (
        "retest_retrieval_against_golden_case",
        "Re-run retrieval against the approved golden case and require the labeled relevant evidence to be recovered before attributing downstream answer quality.",
    ),
    "citation_binding_failure": (
        "revalidate_phase6_packet_and_citations",
        "Rebuild the Phase 6 evidence packet and citation bindings and require exact anchor integrity before retesting the answer.",
    ),
    "unsupported_claim_failure": (
        "rerun_golden_case_unsupported_claim_check",
        "Re-run the approved golden case and require the unsupported-claim dimension to pass with no newly invented support.",
    ),
    "answer_correctness_failure": (
        "rerun_golden_case_answer_correctness",
        "Re-run the same approved golden case and require deterministic answer-correctness criteria to pass.",
    ),
    "answer_completeness_failure": (
        "rerun_golden_case_answer_completeness",
        "Re-run the same approved golden case and require all labeled required claims to be present.",
    ),
    "conflict_handling_failure": (
        "rerun_golden_conflict_case",
        "Re-run the labeled conflict case and require conflict handling to pass without silently reconciling disagreeing evidence.",
    ),
    "insufficiency_handling_failure": (
        "rerun_golden_insufficiency_case",
        "Re-run the labeled insufficiency/no-answer case and require explicit insufficiency handling to pass.",
    ),
    "uncertainty_calibration_failure": (
        "require_calibration_evaluator_before_verification",
        "Require an accepted calibrated uncertainty evaluator and labeled calibration target before this lesson can be independently verified.",
    ),
    "instruction_compliance_failure": (
        "rerun_instruction_compliance_fixture",
        "Re-run the approved instruction-compliance or prompt-injection regression fixture and require it to pass without granting source text instruction authority.",
    ),
    "evaluator_unavailable": (
        "require_evaluator_available",
        "Require the accepted evaluator to be available and rerun the evaluation before considering lesson verification.",
    ),
    "evaluator_disagreement": (
        "require_evaluator_disagreement_resolved",
        "Resolve evaluator disagreement under a separately accepted evaluation rule before considering lesson verification.",
    ),
    "unknown": (
        "require_manual_or_new_deterministic_diagnosis",
        "Require a new accepted deterministic diagnosis or explicit human review before considering lesson verification.",
    ),
}


class ReflectionError(ValueError):
    """Raised when provisional learning state cannot be constructed safely."""


@dataclass(frozen=True, slots=True)
class ReflectionDimensionSummary:
    name: str
    status: str
    score: float | None
    details: tuple[str, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class ReflectionRecord:
    reflection_id: str
    reflection_hash: str
    reflection_contract: str
    reflection_version: str
    diagnosis_version: str
    evaluation_id: str
    evaluation_hash: str
    golden_case_id: str
    packet_id: str
    grounded_result_id: str
    retrieval_id: str
    failure_classifications: tuple[str, ...]
    diagnosed_layers: tuple[str, ...]
    dimension_summaries: tuple[ReflectionDimensionSummary, ...]
    packet_chunk_ids: tuple[str, ...]
    evidence_references: tuple[EvidenceReference, ...]
    reflection_text: str
    content_category: str
    created_by: str
    producer_version: str
    status: str

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    check_id: str
    check_kind: str
    description: str
    failure_classification: str
    diagnosed_layer: str
    required_identity_refs: tuple[str, ...]
    required_outcome: str

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class VerificationPlan:
    plan_id: str
    plan_hash: str
    verification_plan_contract: str
    plan_version: str
    candidate_id: str
    reflection_id: str
    evaluation_id: str
    golden_case_id: str
    packet_id: str
    grounded_result_id: str
    retrieval_id: str
    checks: tuple[VerificationCheck, ...]
    acceptance_rule: str
    promotion_authorized: bool = False

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class CandidateLesson:
    candidate_id: str
    candidate_hash: str
    candidate_state_id: str
    candidate_state_hash: str
    candidate_lesson_contract: str
    candidate_version: str
    reflection_id: str
    evaluation_id: str
    golden_case_id: str
    packet_id: str
    grounded_result_id: str
    retrieval_id: str
    failure_classifications: tuple[str, ...]
    diagnosed_layers: tuple[str, ...]
    packet_chunk_ids: tuple[str, ...]
    evidence_references: tuple[EvidenceReference, ...]
    lesson_text: str
    rationale: str
    content_category: str
    created_by: str
    producer_version: str
    verification_plan_id: str
    status: str
    lifecycle_reason: str | None
    superseded_by_candidate_id: str | None
    previous_state_id: str | None

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False

    @property
    def verified(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class LearningCandidateBundle:
    bundle_id: str
    bundle_hash: str
    reflection: ReflectionRecord
    candidate: CandidateLesson
    verification_plan: VerificationPlan

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ReflectionError(
            "reflection material must be canonical JSON-compatible data"
        ) from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _id(prefix: str, value: Any) -> str:
    return f"{prefix}{_hash(value)}"


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ReflectionError(f"{name} must be a normalized non-empty string")
    return value


def _optional_text(name: str, value: Any) -> str | None:
    if value is None:
        return None
    return _text(name, value)


def _reference_material(reference: EvidenceReference) -> dict[str, Any]:
    return {
        "label": reference.label,
        "anchor_id": reference.anchor_id,
        "chunk_id": reference.chunk_id,
        "source_id": reference.source_id,
        "document_id": reference.document_id,
        "section_id": reference.section_id,
        "structural_path": list(reference.structural_path),
        "line_start": reference.line_start,
        "line_end": reference.line_end,
        "content_hash": reference.content_hash,
    }


def _dimension_material(summary: ReflectionDimensionSummary) -> dict[str, Any]:
    return {
        "name": summary.name,
        "status": summary.status,
        "score": summary.score,
        "details": list(summary.details),
    }


def _check_material(check: VerificationCheck) -> dict[str, Any]:
    return {
        "check_kind": check.check_kind,
        "description": check.description,
        "failure_classification": check.failure_classification,
        "diagnosed_layer": check.diagnosed_layer,
        "required_identity_refs": list(check.required_identity_refs),
        "required_outcome": check.required_outcome,
    }


def _validate_evaluation_for_reflection(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
) -> EvaluationResult:
    if not isinstance(evaluation, EvaluationResult):
        raise ReflectionError("evaluation must be EvaluationResult")
    if evaluation.answer_evaluation_contract != ANSWER_EVALUATION_CONTRACT:
        raise ReflectionError("unsupported Phase 7 evaluation contract")
    if evaluation.evaluator_adapter_id != DETERMINISTIC_EVALUATOR_ADAPTER:
        raise ReflectionError(
            "Phase 8 first slice accepts only canonical deterministic Phase 7 evaluations"
        )
    try:
        rebuilt = evaluate_grounded_answer(
            packet=packet,
            result=grounded_result,
            case=golden_case,
            answer_evaluation_contract=evaluation.answer_evaluation_contract,
            evaluator_version=evaluation.evaluator_version,
            evaluator_adapter_id=evaluation.evaluator_adapter_id,
        )
    except Exception as exc:
        raise ReflectionError("canonical Phase 7 evaluation reconstruction failed") from exc
    if rebuilt != evaluation:
        raise ReflectionError(
            "supplied EvaluationResult does not match canonical Phase 7 evaluation"
        )
    if evaluation.aggregate_status != "fail":
        raise ReflectionError(
            "Phase 8 creates reflection candidates only from failed evaluations"
        )
    if not evaluation.failure_classifications:
        raise ReflectionError("failed evaluation must include a failure classification")
    unknown = set(evaluation.failure_classifications) - set(_FAILURE_TO_LAYER)
    if unknown:
        raise ReflectionError(f"unsupported Phase 7 failure classification {sorted(unknown)!r}")
    return rebuilt


def diagnose_failure_layers(
    failure_classifications: tuple[str, ...] | list[str],
    *,
    diagnosis_version: str = LEARNING_DIAGNOSIS_VERSION,
) -> tuple[str, ...]:
    """Map accepted Phase 7 failure classes into deterministic learning layers."""

    version = _text("diagnosis_version", diagnosis_version)
    if version != LEARNING_DIAGNOSIS_VERSION:
        raise ReflectionError(f"unsupported diagnosis version {version!r}")
    if not isinstance(failure_classifications, (tuple, list)) or not failure_classifications:
        raise ReflectionError("failure_classifications must be a non-empty tuple/list")
    layers: list[str] = []
    for value in failure_classifications:
        failure = _text("failure classification", value)
        if failure not in _FAILURE_TO_LAYER:
            raise ReflectionError(f"unsupported failure classification {failure!r}")
        layer = _FAILURE_TO_LAYER[failure]
        if layer not in layers:
            layers.append(layer)
    return tuple(layers)


def _summarize_dimensions(evaluation: EvaluationResult) -> tuple[ReflectionDimensionSummary, ...]:
    summaries: list[ReflectionDimensionSummary] = []
    for dimension in evaluation.dimensions:
        if dimension.status not in {"fail", "not_evaluated"}:
            continue
        score = dimension.score
        if score is not None and (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(float(score))
        ):
            raise ReflectionError("evaluation dimension contains invalid score")
        summaries.append(
            ReflectionDimensionSummary(
                name=_text("dimension name", dimension.name),
                status=_text("dimension status", dimension.status),
                score=None if score is None else float(score),
                details=tuple(_text("dimension detail", item) for item in dimension.details),
            )
        )
    return tuple(summaries)


def _reflection_material(record: ReflectionRecord) -> dict[str, Any]:
    return {
        "reflection_contract": record.reflection_contract,
        "reflection_version": record.reflection_version,
        "diagnosis_version": record.diagnosis_version,
        "evaluation_id": record.evaluation_id,
        "evaluation_hash": record.evaluation_hash,
        "golden_case_id": record.golden_case_id,
        "packet_id": record.packet_id,
        "grounded_result_id": record.grounded_result_id,
        "retrieval_id": record.retrieval_id,
        "failure_classifications": list(record.failure_classifications),
        "diagnosed_layers": list(record.diagnosed_layers),
        "dimension_summaries": [
            _dimension_material(item) for item in record.dimension_summaries
        ],
        "packet_chunk_ids": list(record.packet_chunk_ids),
        "evidence_references": [
            _reference_material(item) for item in record.evidence_references
        ],
        "reflection_text": record.reflection_text,
        "content_category": record.content_category,
        "created_by": record.created_by,
        "producer_version": record.producer_version,
        "status": record.status,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "execution_authorized": False,
        "governance_mutation_authorized": False,
    }


def create_reflection_record(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    reflection_text: str,
    created_by: str,
    producer_version: str,
    reflection_contract: str = REFLECTION_CONTRACT,
    reflection_version: str = _DEFAULT_REFLECTION_VERSION,
    diagnosis_version: str = LEARNING_DIAGNOSIS_VERSION,
) -> ReflectionRecord:
    """Create one provisional reflection from an exact failed Phase 7 evaluation."""

    contract = _text("reflection_contract", reflection_contract)
    if contract != REFLECTION_CONTRACT:
        raise ReflectionError(f"unsupported reflection contract {contract!r}")
    version = _text("reflection_version", reflection_version)
    diagnosis = _text("diagnosis_version", diagnosis_version)
    if diagnosis != LEARNING_DIAGNOSIS_VERSION:
        raise ReflectionError(f"unsupported diagnosis version {diagnosis!r}")

    canonical = _validate_evaluation_for_reflection(
        packet=packet,
        grounded_result=grounded_result,
        golden_case=golden_case,
        evaluation=evaluation,
    )
    failures = tuple(canonical.failure_classifications)
    layers = diagnose_failure_layers(failures, diagnosis_version=diagnosis)
    packet_chunk_ids = tuple(anchor.chunk_id for anchor in packet.evidence_anchors)
    if len(set(packet_chunk_ids)) != len(packet_chunk_ids):
        raise ReflectionError("packet chunk ids must be unique")

    provisional = ReflectionRecord(
        reflection_id="",
        reflection_hash="",
        reflection_contract=contract,
        reflection_version=version,
        diagnosis_version=diagnosis,
        evaluation_id=canonical.evaluation_id,
        evaluation_hash=canonical.evaluation_hash,
        golden_case_id=canonical.golden_case_id,
        packet_id=canonical.packet_id,
        grounded_result_id=canonical.grounded_result_id,
        retrieval_id=canonical.retrieval_id,
        failure_classifications=failures,
        diagnosed_layers=layers,
        dimension_summaries=_summarize_dimensions(canonical),
        packet_chunk_ids=packet_chunk_ids,
        evidence_references=tuple(grounded_result.evidence_references),
        reflection_text=_text("reflection_text", reflection_text),
        content_category=_GENERATED_PROVISIONAL,
        created_by=_text("created_by", created_by),
        producer_version=_text("producer_version", producer_version),
        status="provisional",
    )
    digest = _hash(_reflection_material(provisional))
    return ReflectionRecord(
        reflection_id=f"refl_{digest}",
        reflection_hash=digest,
        reflection_contract=provisional.reflection_contract,
        reflection_version=provisional.reflection_version,
        diagnosis_version=provisional.diagnosis_version,
        evaluation_id=provisional.evaluation_id,
        evaluation_hash=provisional.evaluation_hash,
        golden_case_id=provisional.golden_case_id,
        packet_id=provisional.packet_id,
        grounded_result_id=provisional.grounded_result_id,
        retrieval_id=provisional.retrieval_id,
        failure_classifications=provisional.failure_classifications,
        diagnosed_layers=provisional.diagnosed_layers,
        dimension_summaries=provisional.dimension_summaries,
        packet_chunk_ids=provisional.packet_chunk_ids,
        evidence_references=provisional.evidence_references,
        reflection_text=provisional.reflection_text,
        content_category=provisional.content_category,
        created_by=provisional.created_by,
        producer_version=provisional.producer_version,
        status=provisional.status,
    )


def validate_reflection_record(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    reflection: ReflectionRecord,
) -> ReflectionRecord:
    """Rebuild a reflection from canonical inputs and require exact equality."""

    if not isinstance(reflection, ReflectionRecord):
        raise ReflectionError("reflection must be ReflectionRecord")
    rebuilt = create_reflection_record(
        packet=packet,
        grounded_result=grounded_result,
        golden_case=golden_case,
        evaluation=evaluation,
        reflection_text=reflection.reflection_text,
        created_by=reflection.created_by,
        producer_version=reflection.producer_version,
        reflection_contract=reflection.reflection_contract,
        reflection_version=reflection.reflection_version,
        diagnosis_version=reflection.diagnosis_version,
    )
    if rebuilt != reflection:
        raise ReflectionError("reflection record identity/content is invalid")
    return rebuilt


def _candidate_core_material(
    *,
    reflection: ReflectionRecord,
    lesson_text: str,
    rationale: str,
    created_by: str,
    producer_version: str,
    candidate_contract: str,
    candidate_version: str,
) -> dict[str, Any]:
    return {
        "candidate_lesson_contract": candidate_contract,
        "candidate_version": candidate_version,
        "reflection_id": reflection.reflection_id,
        "evaluation_id": reflection.evaluation_id,
        "golden_case_id": reflection.golden_case_id,
        "packet_id": reflection.packet_id,
        "grounded_result_id": reflection.grounded_result_id,
        "retrieval_id": reflection.retrieval_id,
        "failure_classifications": list(reflection.failure_classifications),
        "diagnosed_layers": list(reflection.diagnosed_layers),
        "packet_chunk_ids": list(reflection.packet_chunk_ids),
        "evidence_references": [
            _reference_material(item) for item in reflection.evidence_references
        ],
        "lesson_text": lesson_text,
        "rationale": rationale,
        "content_category": _GENERATED_PROVISIONAL,
        "created_by": created_by,
        "producer_version": producer_version,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "execution_authorized": False,
        "governance_mutation_authorized": False,
        "verified": False,
    }


def _make_check(
    *,
    failure: str,
    layer: str,
    reflection: ReflectionRecord,
    candidate_id: str,
) -> VerificationCheck:
    kind, description = _FAILURE_TO_CHECK[failure]
    refs = (
        f"candidate:{candidate_id}",
        f"reflection:{reflection.reflection_id}",
        f"evaluation:{reflection.evaluation_id}",
        f"golden_case:{reflection.golden_case_id}",
        f"packet:{reflection.packet_id}",
        f"grounded_result:{reflection.grounded_result_id}",
        f"retrieval:{reflection.retrieval_id}",
    )
    material = {
        "check_kind": kind,
        "description": description,
        "failure_classification": failure,
        "diagnosed_layer": layer,
        "required_identity_refs": list(refs),
        "required_outcome": "pass_under_separate_candidate_verification_contract",
    }
    return VerificationCheck(
        check_id=_id("vchk_", material),
        check_kind=kind,
        description=description,
        failure_classification=failure,
        diagnosed_layer=layer,
        required_identity_refs=refs,
        required_outcome="pass_under_separate_candidate_verification_contract",
    )


def _plan_material(plan: VerificationPlan) -> dict[str, Any]:
    return {
        "verification_plan_contract": plan.verification_plan_contract,
        "plan_version": plan.plan_version,
        "candidate_id": plan.candidate_id,
        "reflection_id": plan.reflection_id,
        "evaluation_id": plan.evaluation_id,
        "golden_case_id": plan.golden_case_id,
        "packet_id": plan.packet_id,
        "grounded_result_id": plan.grounded_result_id,
        "retrieval_id": plan.retrieval_id,
        "checks": [
            {"check_id": item.check_id, **_check_material(item)} for item in plan.checks
        ],
        "acceptance_rule": plan.acceptance_rule,
        "promotion_authorized": False,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "execution_authorized": False,
        "governance_mutation_authorized": False,
    }


def _build_verification_plan(
    *,
    reflection: ReflectionRecord,
    candidate_id: str,
    verification_plan_contract: str,
    plan_version: str,
) -> VerificationPlan:
    contract = _text("verification_plan_contract", verification_plan_contract)
    if contract != VERIFICATION_PLAN_CONTRACT:
        raise ReflectionError(f"unsupported verification plan contract {contract!r}")
    version = _text("plan_version", plan_version)
    checks = tuple(
        _make_check(
            failure=failure,
            layer=_FAILURE_TO_LAYER[failure],
            reflection=reflection,
            candidate_id=candidate_id,
        )
        for failure in reflection.failure_classifications
    )
    if not checks:
        raise ReflectionError("verification plan requires at least one check")
    provisional = VerificationPlan(
        plan_id="",
        plan_hash="",
        verification_plan_contract=contract,
        plan_version=version,
        candidate_id=candidate_id,
        reflection_id=reflection.reflection_id,
        evaluation_id=reflection.evaluation_id,
        golden_case_id=reflection.golden_case_id,
        packet_id=reflection.packet_id,
        grounded_result_id=reflection.grounded_result_id,
        retrieval_id=reflection.retrieval_id,
        checks=checks,
        acceptance_rule=(
            "all required checks must pass under a separate accepted "
            "candidate-lesson verification contract before any promotion"
        ),
        promotion_authorized=False,
    )
    digest = _hash(_plan_material(provisional))
    return VerificationPlan(
        plan_id=f"vplan_{digest}",
        plan_hash=digest,
        verification_plan_contract=provisional.verification_plan_contract,
        plan_version=provisional.plan_version,
        candidate_id=provisional.candidate_id,
        reflection_id=provisional.reflection_id,
        evaluation_id=provisional.evaluation_id,
        golden_case_id=provisional.golden_case_id,
        packet_id=provisional.packet_id,
        grounded_result_id=provisional.grounded_result_id,
        retrieval_id=provisional.retrieval_id,
        checks=provisional.checks,
        acceptance_rule=provisional.acceptance_rule,
        promotion_authorized=False,
    )


def _candidate_state_material(candidate: CandidateLesson) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "verification_plan_id": candidate.verification_plan_id,
        "status": candidate.status,
        "lifecycle_reason": candidate.lifecycle_reason,
        "superseded_by_candidate_id": candidate.superseded_by_candidate_id,
        "previous_state_id": candidate.previous_state_id,
        "verified": False,
        "memory_promotion_authorized": False,
    }


def _candidate_with_state(
    *,
    candidate_id: str,
    candidate_hash: str,
    candidate_lesson_contract: str,
    candidate_version: str,
    reflection: ReflectionRecord,
    lesson_text: str,
    rationale: str,
    created_by: str,
    producer_version: str,
    verification_plan_id: str,
    status: str,
    lifecycle_reason: str | None,
    superseded_by_candidate_id: str | None,
    previous_state_id: str | None,
) -> CandidateLesson:
    if status not in _CANDIDATE_STATUSES:
        raise ReflectionError(f"unsupported candidate lifecycle status {status!r}")
    if status == "provisional":
        if lifecycle_reason is not None or superseded_by_candidate_id is not None:
            raise ReflectionError("provisional candidate cannot carry terminal lifecycle fields")
    elif status == "rejected":
        if lifecycle_reason is None:
            raise ReflectionError("rejected candidate requires lifecycle_reason")
        if superseded_by_candidate_id is not None:
            raise ReflectionError("rejected candidate cannot name superseded_by_candidate_id")
    elif status == "superseded":
        if lifecycle_reason is None or superseded_by_candidate_id is None:
            raise ReflectionError(
                "superseded candidate requires lifecycle_reason and superseded_by_candidate_id"
            )
        if superseded_by_candidate_id == candidate_id:
            raise ReflectionError("candidate cannot supersede itself")

    provisional = CandidateLesson(
        candidate_id=candidate_id,
        candidate_hash=candidate_hash,
        candidate_state_id="",
        candidate_state_hash="",
        candidate_lesson_contract=candidate_lesson_contract,
        candidate_version=candidate_version,
        reflection_id=reflection.reflection_id,
        evaluation_id=reflection.evaluation_id,
        golden_case_id=reflection.golden_case_id,
        packet_id=reflection.packet_id,
        grounded_result_id=reflection.grounded_result_id,
        retrieval_id=reflection.retrieval_id,
        failure_classifications=reflection.failure_classifications,
        diagnosed_layers=reflection.diagnosed_layers,
        packet_chunk_ids=reflection.packet_chunk_ids,
        evidence_references=reflection.evidence_references,
        lesson_text=lesson_text,
        rationale=rationale,
        content_category=_GENERATED_PROVISIONAL,
        created_by=created_by,
        producer_version=producer_version,
        verification_plan_id=verification_plan_id,
        status=status,
        lifecycle_reason=lifecycle_reason,
        superseded_by_candidate_id=superseded_by_candidate_id,
        previous_state_id=previous_state_id,
    )
    state_hash = _hash(_candidate_state_material(provisional))
    return CandidateLesson(
        candidate_id=provisional.candidate_id,
        candidate_hash=provisional.candidate_hash,
        candidate_state_id=f"cstate_{state_hash}",
        candidate_state_hash=state_hash,
        candidate_lesson_contract=provisional.candidate_lesson_contract,
        candidate_version=provisional.candidate_version,
        reflection_id=provisional.reflection_id,
        evaluation_id=provisional.evaluation_id,
        golden_case_id=provisional.golden_case_id,
        packet_id=provisional.packet_id,
        grounded_result_id=provisional.grounded_result_id,
        retrieval_id=provisional.retrieval_id,
        failure_classifications=provisional.failure_classifications,
        diagnosed_layers=provisional.diagnosed_layers,
        packet_chunk_ids=provisional.packet_chunk_ids,
        evidence_references=provisional.evidence_references,
        lesson_text=provisional.lesson_text,
        rationale=provisional.rationale,
        content_category=provisional.content_category,
        created_by=provisional.created_by,
        producer_version=provisional.producer_version,
        verification_plan_id=provisional.verification_plan_id,
        status=provisional.status,
        lifecycle_reason=provisional.lifecycle_reason,
        superseded_by_candidate_id=provisional.superseded_by_candidate_id,
        previous_state_id=provisional.previous_state_id,
    )


def create_candidate_lesson(
    *,
    reflection: ReflectionRecord,
    lesson_text: str,
    rationale: str,
    created_by: str,
    producer_version: str,
    candidate_lesson_contract: str = CANDIDATE_LESSON_CONTRACT,
    candidate_version: str = _DEFAULT_CANDIDATE_VERSION,
    verification_plan_contract: str = VERIFICATION_PLAN_CONTRACT,
    plan_version: str = _DEFAULT_PLAN_VERSION,
) -> tuple[CandidateLesson, VerificationPlan]:
    """Create a provisional candidate and deterministic future verification plan."""

    if not isinstance(reflection, ReflectionRecord):
        raise ReflectionError("reflection must be ReflectionRecord")
    if reflection.status != "provisional" or reflection.content_category != _GENERATED_PROVISIONAL:
        raise ReflectionError("candidate lesson requires a provisional generated reflection")
    contract = _text("candidate_lesson_contract", candidate_lesson_contract)
    if contract != CANDIDATE_LESSON_CONTRACT:
        raise ReflectionError(f"unsupported candidate lesson contract {contract!r}")
    version = _text("candidate_version", candidate_version)
    lesson = _text("lesson_text", lesson_text)
    reason = _text("rationale", rationale)
    author = _text("created_by", created_by)
    producer = _text("producer_version", producer_version)

    core = _candidate_core_material(
        reflection=reflection,
        lesson_text=lesson,
        rationale=reason,
        created_by=author,
        producer_version=producer,
        candidate_contract=contract,
        candidate_version=version,
    )
    candidate_hash = _hash(core)
    candidate_id = f"cless_{candidate_hash}"
    plan = _build_verification_plan(
        reflection=reflection,
        candidate_id=candidate_id,
        verification_plan_contract=verification_plan_contract,
        plan_version=plan_version,
    )
    candidate = _candidate_with_state(
        candidate_id=candidate_id,
        candidate_hash=candidate_hash,
        candidate_lesson_contract=contract,
        candidate_version=version,
        reflection=reflection,
        lesson_text=lesson,
        rationale=reason,
        created_by=author,
        producer_version=producer,
        verification_plan_id=plan.plan_id,
        status="provisional",
        lifecycle_reason=None,
        superseded_by_candidate_id=None,
        previous_state_id=None,
    )
    return candidate, plan


def _validate_candidate_and_plan(
    *, reflection: ReflectionRecord, candidate: CandidateLesson, plan: VerificationPlan
) -> tuple[CandidateLesson, VerificationPlan]:
    if not isinstance(candidate, CandidateLesson) or not isinstance(plan, VerificationPlan):
        raise ReflectionError("candidate and plan must use Phase 8 typed records")
    if candidate.candidate_lesson_contract != CANDIDATE_LESSON_CONTRACT:
        raise ReflectionError("unsupported candidate lesson contract")
    core = _candidate_core_material(
        reflection=reflection,
        lesson_text=_text("lesson_text", candidate.lesson_text),
        rationale=_text("rationale", candidate.rationale),
        created_by=_text("created_by", candidate.created_by),
        producer_version=_text("producer_version", candidate.producer_version),
        candidate_contract=candidate.candidate_lesson_contract,
        candidate_version=_text("candidate_version", candidate.candidate_version),
    )
    expected_hash = _hash(core)
    if candidate.candidate_hash != expected_hash or candidate.candidate_id != f"cless_{expected_hash}":
        raise ReflectionError("candidate lesson core identity/content is invalid")

    expected_plan = _build_verification_plan(
        reflection=reflection,
        candidate_id=candidate.candidate_id,
        verification_plan_contract=plan.verification_plan_contract,
        plan_version=plan.plan_version,
    )
    if expected_plan != plan or candidate.verification_plan_id != plan.plan_id:
        raise ReflectionError("candidate verification plan identity/content is invalid")

    expected_state = _candidate_with_state(
        candidate_id=candidate.candidate_id,
        candidate_hash=candidate.candidate_hash,
        candidate_lesson_contract=candidate.candidate_lesson_contract,
        candidate_version=candidate.candidate_version,
        reflection=reflection,
        lesson_text=candidate.lesson_text,
        rationale=candidate.rationale,
        created_by=candidate.created_by,
        producer_version=candidate.producer_version,
        verification_plan_id=candidate.verification_plan_id,
        status=candidate.status,
        lifecycle_reason=candidate.lifecycle_reason,
        superseded_by_candidate_id=candidate.superseded_by_candidate_id,
        previous_state_id=candidate.previous_state_id,
    )
    if expected_state != candidate:
        raise ReflectionError("candidate lifecycle state identity/content is invalid")
    return candidate, plan


def transition_candidate_lesson(
    *,
    reflection: ReflectionRecord,
    candidate: CandidateLesson,
    verification_plan: VerificationPlan,
    status: str,
    reason: str,
    superseded_by_candidate_id: str | None = None,
) -> CandidateLesson:
    """Create an immutable rejected/superseded lifecycle revision; never verified."""

    _validate_candidate_and_plan(
        reflection=reflection, candidate=candidate, plan=verification_plan
    )
    if candidate.status != "provisional":
        raise ReflectionError("only a provisional candidate may receive a Phase 8 disposition")
    target = _text("status", status)
    if target not in {"rejected", "superseded"}:
        raise ReflectionError(
            "Phase 8 lifecycle transition supports only rejected or superseded"
        )
    return _candidate_with_state(
        candidate_id=candidate.candidate_id,
        candidate_hash=candidate.candidate_hash,
        candidate_lesson_contract=candidate.candidate_lesson_contract,
        candidate_version=candidate.candidate_version,
        reflection=reflection,
        lesson_text=candidate.lesson_text,
        rationale=candidate.rationale,
        created_by=candidate.created_by,
        producer_version=candidate.producer_version,
        verification_plan_id=candidate.verification_plan_id,
        status=target,
        lifecycle_reason=_text("reason", reason),
        superseded_by_candidate_id=(
            _optional_text("superseded_by_candidate_id", superseded_by_candidate_id)
            if target == "superseded"
            else None
        ),
        previous_state_id=candidate.candidate_state_id,
    )


def _bundle_material(bundle: LearningCandidateBundle) -> dict[str, Any]:
    return {
        "reflection_id": bundle.reflection.reflection_id,
        "candidate_id": bundle.candidate.candidate_id,
        "candidate_state_id": bundle.candidate.candidate_state_id,
        "verification_plan_id": bundle.verification_plan.plan_id,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "execution_authorized": False,
        "governance_mutation_authorized": False,
    }


def build_learning_candidate_bundle(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    reflection_text: str,
    lesson_text: str,
    rationale: str,
    created_by: str,
    producer_version: str,
    reflection_version: str = _DEFAULT_REFLECTION_VERSION,
    candidate_version: str = _DEFAULT_CANDIDATE_VERSION,
    plan_version: str = _DEFAULT_PLAN_VERSION,
) -> LearningCandidateBundle:
    """Build the complete Phase 8 provisional learning-candidate tracer bullet."""

    reflection = create_reflection_record(
        packet=packet,
        grounded_result=grounded_result,
        golden_case=golden_case,
        evaluation=evaluation,
        reflection_text=reflection_text,
        created_by=created_by,
        producer_version=producer_version,
        reflection_version=reflection_version,
    )
    candidate, plan = create_candidate_lesson(
        reflection=reflection,
        lesson_text=lesson_text,
        rationale=rationale,
        created_by=created_by,
        producer_version=producer_version,
        candidate_version=candidate_version,
        plan_version=plan_version,
    )
    provisional = LearningCandidateBundle(
        bundle_id="",
        bundle_hash="",
        reflection=reflection,
        candidate=candidate,
        verification_plan=plan,
    )
    digest = _hash(_bundle_material(provisional))
    return LearningCandidateBundle(
        bundle_id=f"lcb_{digest}",
        bundle_hash=digest,
        reflection=reflection,
        candidate=candidate,
        verification_plan=plan,
    )


def validate_learning_candidate_bundle(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    bundle: LearningCandidateBundle,
) -> LearningCandidateBundle:
    """Revalidate canonical provenance and every Phase 8 content-addressed record."""

    if not isinstance(bundle, LearningCandidateBundle):
        raise ReflectionError("bundle must be LearningCandidateBundle")
    reflection = validate_reflection_record(
        packet=packet,
        grounded_result=grounded_result,
        golden_case=golden_case,
        evaluation=evaluation,
        reflection=bundle.reflection,
    )
    _validate_candidate_and_plan(
        reflection=reflection,
        candidate=bundle.candidate,
        plan=bundle.verification_plan,
    )
    expected_hash = _hash(_bundle_material(bundle))
    if bundle.bundle_hash != expected_hash or bundle.bundle_id != f"lcb_{expected_hash}":
        raise ReflectionError("learning candidate bundle identity/content is invalid")
    return bundle
