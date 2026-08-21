"""Independent candidate-lesson verification for the Roberta Learning System.

Phase 9 revalidates canonical Phase 8 candidate state and executes only the
checks already present in its deterministic VerificationPlan. Verification is
not durable-memory promotion, source truth, live-state truth, governance
mutation, or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .evaluation import EvaluationError, EvaluationResult, GoldenEvaluationCase, evaluate_grounded_answer
from .grounding import EvidencePacket, GroundedAnswerResult
from .reflection import (
    LearningCandidateBundle,
    ReflectionError,
    VerificationCheck,
    validate_learning_candidate_bundle,
)


CANDIDATE_VERIFICATION_CONTRACT = "candidate-lesson-verification/v1"
DETERMINISTIC_VERIFIER_ADAPTER = "deterministic-phase7-retest/v1"
VERIFIER_VERSION = "1.0.0"

_RESULT_STATUSES = frozenset({"verified_for_learning", "rejected", "inconclusive"})
_CHECK_STATUSES = frozenset({"pass", "fail", "inconclusive"})

_CHECK_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "retest_retrieval_against_golden_case": ("retrieval_coverage",),
    "revalidate_phase6_packet_and_citations": ("citation_correctness",),
    "rerun_golden_case_unsupported_claim_check": ("unsupported_claim_rate",),
    "rerun_golden_case_answer_correctness": (
        "answer_correctness",
        "limitation_disclosure",
    ),
    "rerun_golden_case_answer_completeness": ("answer_completeness",),
    "rerun_golden_conflict_case": ("conflict_handling",),
    "rerun_golden_insufficiency_case": ("insufficiency_handling",),
    "rerun_instruction_compliance_fixture": ("instruction_compliance",),
}

_INCONCLUSIVE_ONLY_CHECKS = frozenset(
    {
        "require_calibration_evaluator_before_verification",
        "require_evaluator_available",
        "require_evaluator_disagreement_resolved",
        "require_manual_or_new_deterministic_diagnosis",
    }
)


class VerificationError(ValueError):
    """Raised when candidate verification cannot proceed safely."""


@dataclass(frozen=True, slots=True)
class VerificationCheckResult:
    check_id: str
    check_kind: str
    failure_classification: str
    diagnosed_layer: str
    required_identity_refs: tuple[str, ...]
    status: str
    retest_packet_id: str | None
    retest_grounded_result_id: str | None
    retest_retrieval_id: str | None
    retest_evaluation_id: str | None
    details: tuple[str, ...]

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class CandidateVerificationResult:
    verification_id: str
    verification_hash: str
    candidate_verification_contract: str
    verifier_version: str
    verifier_adapter_id: str
    bundle_id: str
    candidate_id: str
    candidate_state_id: str
    reflection_id: str
    verification_plan_id: str
    original_evaluation_id: str
    golden_case_id: str
    packet_id: str
    grounded_result_id: str
    retrieval_id: str
    retest_packet_id: str | None
    retest_grounded_result_id: str | None
    retest_retrieval_id: str | None
    retest_evaluation_id: str | None
    checks: tuple[VerificationCheckResult, ...]
    status: str
    created_by: str
    producer_version: str

    @property
    def verified_for_learning(self) -> bool:
        return self.status == "verified_for_learning"

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
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
        raise VerificationError(
            "verification material must be canonical JSON-compatible data"
        ) from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise VerificationError(f"{name} must be a normalized non-empty string")
    return value


def _check_result_material(result: VerificationCheckResult) -> dict[str, Any]:
    return {
        "check_id": result.check_id,
        "check_kind": result.check_kind,
        "failure_classification": result.failure_classification,
        "diagnosed_layer": result.diagnosed_layer,
        "required_identity_refs": list(result.required_identity_refs),
        "status": result.status,
        "retest_packet_id": result.retest_packet_id,
        "retest_grounded_result_id": result.retest_grounded_result_id,
        "retest_retrieval_id": result.retest_retrieval_id,
        "retest_evaluation_id": result.retest_evaluation_id,
        "details": list(result.details),
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "governance_mutation_authorized": False,
        "execution_authorized": False,
    }


def _result_material(result: CandidateVerificationResult) -> dict[str, Any]:
    return {
        "candidate_verification_contract": result.candidate_verification_contract,
        "verifier_version": result.verifier_version,
        "verifier_adapter_id": result.verifier_adapter_id,
        "bundle_id": result.bundle_id,
        "candidate_id": result.candidate_id,
        "candidate_state_id": result.candidate_state_id,
        "reflection_id": result.reflection_id,
        "verification_plan_id": result.verification_plan_id,
        "original_evaluation_id": result.original_evaluation_id,
        "golden_case_id": result.golden_case_id,
        "packet_id": result.packet_id,
        "grounded_result_id": result.grounded_result_id,
        "retrieval_id": result.retrieval_id,
        "retest_packet_id": result.retest_packet_id,
        "retest_grounded_result_id": result.retest_grounded_result_id,
        "retest_retrieval_id": result.retest_retrieval_id,
        "retest_evaluation_id": result.retest_evaluation_id,
        "checks": [_check_result_material(item) for item in result.checks],
        "status": result.status,
        "created_by": result.created_by,
        "producer_version": result.producer_version,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "governance_mutation_authorized": False,
        "execution_authorized": False,
    }


def _canonical_phase8_bundle(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    bundle: LearningCandidateBundle,
) -> LearningCandidateBundle:
    try:
        canonical = validate_learning_candidate_bundle(
            packet=packet,
            grounded_result=grounded_result,
            golden_case=golden_case,
            evaluation=evaluation,
            bundle=bundle,
        )
    except ReflectionError as exc:
        raise VerificationError("canonical Phase 8 bundle validation failed") from exc
    if canonical.candidate.status != "provisional":
        raise VerificationError(
            "Phase 9 verifies only the exact provisional candidate lifecycle state"
        )
    return canonical


def _build_retest_evaluation(
    *,
    golden_case: GoldenEvaluationCase,
    original_evaluation: EvaluationResult,
    retest_packet: EvidencePacket | None,
    retest_grounded_result: GroundedAnswerResult | None,
) -> tuple[EvaluationResult | None, tuple[str, ...]]:
    missing: list[str] = []
    if retest_packet is None:
        missing.append("retest_packet_unavailable")
    if retest_grounded_result is None:
        missing.append("retest_grounded_result_unavailable")
    if missing:
        return None, tuple(missing)

    try:
        evaluation = evaluate_grounded_answer(
            packet=retest_packet,
            result=retest_grounded_result,
            case=golden_case,
            answer_evaluation_contract=original_evaluation.answer_evaluation_contract,
            evaluator_version=original_evaluation.evaluator_version,
            evaluator_adapter_id=original_evaluation.evaluator_adapter_id,
        )
    except EvaluationError as exc:
        raise VerificationError("canonical Phase 9 retest evaluation failed") from exc
    return evaluation, ()


def _dimension_statuses(
    evaluation: EvaluationResult, names: tuple[str, ...]
) -> tuple[tuple[str, str], ...]:
    by_name = {item.name: item for item in evaluation.dimensions}
    output: list[tuple[str, str]] = []
    for name in names:
        dimension = by_name.get(name)
        if dimension is None:
            output.append((name, "missing"))
        else:
            output.append((name, dimension.status))
    return tuple(output)


def _verify_check(
    *,
    check: VerificationCheck,
    retest_evaluation: EvaluationResult | None,
    missing_retest_details: tuple[str, ...],
    retest_packet: EvidencePacket | None,
    retest_grounded_result: GroundedAnswerResult | None,
) -> VerificationCheckResult:
    if retest_evaluation is None:
        status = "inconclusive"
        details = missing_retest_details or ("verification_evidence_unavailable",)
    elif check.check_kind in _CHECK_DIMENSIONS:
        statuses = _dimension_statuses(
            retest_evaluation, _CHECK_DIMENSIONS[check.check_kind]
        )
        details = tuple(f"dimension:{name}:{value}" for name, value in statuses)
        values = tuple(value for _, value in statuses)
        if "missing" in values:
            status = "inconclusive"
        elif "fail" in values:
            status = "fail"
        elif any(value in {"not_evaluated", "not_applicable"} for value in values):
            status = "inconclusive"
        elif values and all(value == "pass" for value in values):
            status = "pass"
        else:
            raise VerificationError("unexpected Phase 7 dimension state during verification")
    elif check.check_kind in _INCONCLUSIVE_ONLY_CHECKS:
        status = "inconclusive"
        details = (f"accepted_verification_capability_unavailable:{check.check_kind}",)
    else:
        raise VerificationError(
            f"unsupported Phase 8 verification check kind {check.check_kind!r}"
        )

    if status not in _CHECK_STATUSES:
        raise VerificationError("unsupported verification check status")
    return VerificationCheckResult(
        check_id=check.check_id,
        check_kind=check.check_kind,
        failure_classification=check.failure_classification,
        diagnosed_layer=check.diagnosed_layer,
        required_identity_refs=check.required_identity_refs,
        status=status,
        retest_packet_id=None if retest_packet is None else retest_packet.packet_id,
        retest_grounded_result_id=(
            None if retest_grounded_result is None else retest_grounded_result.result_id
        ),
        retest_retrieval_id=(
            None if retest_grounded_result is None else retest_grounded_result.retrieval_id
        ),
        retest_evaluation_id=(
            None if retest_evaluation is None else retest_evaluation.evaluation_id
        ),
        details=details,
    )


def _aggregate_status(checks: tuple[VerificationCheckResult, ...]) -> str:
    if not checks:
        raise VerificationError("candidate verification requires at least one check")
    if any(item.status == "fail" for item in checks):
        return "rejected"
    if any(item.status == "inconclusive" for item in checks):
        return "inconclusive"
    if all(item.status == "pass" for item in checks):
        return "verified_for_learning"
    raise VerificationError("candidate verification could not derive an aggregate status")


def verify_candidate_lesson(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    bundle: LearningCandidateBundle,
    retest_packet: EvidencePacket | None,
    retest_grounded_result: GroundedAnswerResult | None,
    created_by: str,
    producer_version: str,
    candidate_verification_contract: str = CANDIDATE_VERIFICATION_CONTRACT,
    verifier_version: str = VERIFIER_VERSION,
    verifier_adapter_id: str = DETERMINISTIC_VERIFIER_ADAPTER,
) -> CandidateVerificationResult:
    """Verify one exact provisional Phase 8 candidate without promoting it."""

    contract = _text("candidate_verification_contract", candidate_verification_contract)
    if contract != CANDIDATE_VERIFICATION_CONTRACT:
        raise VerificationError(f"unsupported candidate verification contract {contract!r}")
    version = _text("verifier_version", verifier_version)
    if version != VERIFIER_VERSION:
        raise VerificationError(f"unsupported verifier version {version!r}")
    adapter = _text("verifier_adapter_id", verifier_adapter_id)
    if adapter != DETERMINISTIC_VERIFIER_ADAPTER:
        raise VerificationError(f"unsupported verifier adapter {adapter!r}")

    canonical = _canonical_phase8_bundle(
        packet=packet,
        grounded_result=grounded_result,
        golden_case=golden_case,
        evaluation=evaluation,
        bundle=bundle,
    )
    retest_evaluation, missing_retest_details = _build_retest_evaluation(
        golden_case=golden_case,
        original_evaluation=evaluation,
        retest_packet=retest_packet,
        retest_grounded_result=retest_grounded_result,
    )

    checks = tuple(
        _verify_check(
            check=check,
            retest_evaluation=retest_evaluation,
            missing_retest_details=missing_retest_details,
            retest_packet=retest_packet,
            retest_grounded_result=retest_grounded_result,
        )
        for check in canonical.verification_plan.checks
    )
    status = _aggregate_status(checks)
    if status not in _RESULT_STATUSES:
        raise VerificationError("unsupported candidate verification status")

    provisional = CandidateVerificationResult(
        verification_id="",
        verification_hash="",
        candidate_verification_contract=contract,
        verifier_version=version,
        verifier_adapter_id=adapter,
        bundle_id=canonical.bundle_id,
        candidate_id=canonical.candidate.candidate_id,
        candidate_state_id=canonical.candidate.candidate_state_id,
        reflection_id=canonical.reflection.reflection_id,
        verification_plan_id=canonical.verification_plan.plan_id,
        original_evaluation_id=evaluation.evaluation_id,
        golden_case_id=golden_case.case_id,
        packet_id=packet.packet_id,
        grounded_result_id=grounded_result.result_id,
        retrieval_id=grounded_result.retrieval_id,
        retest_packet_id=None if retest_packet is None else retest_packet.packet_id,
        retest_grounded_result_id=(
            None if retest_grounded_result is None else retest_grounded_result.result_id
        ),
        retest_retrieval_id=(
            None if retest_grounded_result is None else retest_grounded_result.retrieval_id
        ),
        retest_evaluation_id=(
            None if retest_evaluation is None else retest_evaluation.evaluation_id
        ),
        checks=checks,
        status=status,
        created_by=_text("created_by", created_by),
        producer_version=_text("producer_version", producer_version),
    )
    digest = _hash(_result_material(provisional))
    return CandidateVerificationResult(
        verification_id=f"cverify_{digest}",
        verification_hash=digest,
        candidate_verification_contract=provisional.candidate_verification_contract,
        verifier_version=provisional.verifier_version,
        verifier_adapter_id=provisional.verifier_adapter_id,
        bundle_id=provisional.bundle_id,
        candidate_id=provisional.candidate_id,
        candidate_state_id=provisional.candidate_state_id,
        reflection_id=provisional.reflection_id,
        verification_plan_id=provisional.verification_plan_id,
        original_evaluation_id=provisional.original_evaluation_id,
        golden_case_id=provisional.golden_case_id,
        packet_id=provisional.packet_id,
        grounded_result_id=provisional.grounded_result_id,
        retrieval_id=provisional.retrieval_id,
        retest_packet_id=provisional.retest_packet_id,
        retest_grounded_result_id=provisional.retest_grounded_result_id,
        retest_retrieval_id=provisional.retest_retrieval_id,
        retest_evaluation_id=provisional.retest_evaluation_id,
        checks=provisional.checks,
        status=provisional.status,
        created_by=provisional.created_by,
        producer_version=provisional.producer_version,
    )


def validate_candidate_verification_result(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    bundle: LearningCandidateBundle,
    retest_packet: EvidencePacket | None,
    retest_grounded_result: GroundedAnswerResult | None,
    result: CandidateVerificationResult,
) -> CandidateVerificationResult:
    """Rebuild a Phase 9 verification result and require exact equality."""

    if not isinstance(result, CandidateVerificationResult):
        raise VerificationError("result must be CandidateVerificationResult")
    rebuilt = verify_candidate_lesson(
        packet=packet,
        grounded_result=grounded_result,
        golden_case=golden_case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=retest_packet,
        retest_grounded_result=retest_grounded_result,
        created_by=result.created_by,
        producer_version=result.producer_version,
        candidate_verification_contract=result.candidate_verification_contract,
        verifier_version=result.verifier_version,
        verifier_adapter_id=result.verifier_adapter_id,
    )
    if rebuilt != result:
        raise VerificationError("candidate verification result identity/content is invalid")
    return rebuilt
