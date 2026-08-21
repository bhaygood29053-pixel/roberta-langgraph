"""Independent answer-evaluation foundation for the Roberta Learning System.

Phase 7 evaluates accepted Phase 6 grounded-answer records against explicit,
versioned golden labels. Evaluation output is measurement metadata only: it is
not source truth, live-state verification, durable-memory promotion, or
execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import unicodedata
from typing import Any

from .grounding import (
    ANSWER_CONTRACT,
    AnswerClaim,
    EvidencePacket,
    GroundedAnswerResult,
    GroundingError,
    make_answer_candidate,
    validate_answer_candidate,
)


ANSWER_EVALUATION_CONTRACT = "grounded-answer-evaluation/v1"
GOLDEN_CASE_CONTRACT = "grounded-answer-golden-case/v1"
DETERMINISTIC_EVALUATOR_ADAPTER = "deterministic-golden-label/v1"
EVALUATOR_VERSION = "1.0.0"

_ALLOWED_CLAIM_STATUSES = frozenset({"supported", "insufficient", "conflict"})
_ALLOWED_CASE_BEHAVIORS = frozenset({"answer", "insufficient", "conflict"})
_ALLOWED_CASE_APPROVAL = frozenset({"approved", "pending", "rejected"})
_ALLOWED_DIMENSION_STATUSES = frozenset(
    {"pass", "fail", "not_evaluated", "not_applicable"}
)
_FAILURE_CLASSES = frozenset(
    {
        "retrieval_failure",
        "citation_binding_failure",
        "unsupported_claim_failure",
        "answer_correctness_failure",
        "answer_completeness_failure",
        "conflict_handling_failure",
        "insufficiency_handling_failure",
        "uncertainty_calibration_failure",
        "instruction_compliance_failure",
        "evaluator_unavailable",
        "evaluator_disagreement",
        "unknown",
    }
)


class EvaluationError(ValueError):
    """Raised when answer evaluation cannot be performed safely."""


@dataclass(frozen=True, slots=True)
class GoldenClaimCriterion:
    """Explicit deterministic labels for one structured answer claim."""

    claim_id: str
    required: bool
    allowed_statuses: tuple[str, ...]
    allowed_evidence_chunk_ids: tuple[str, ...]
    required_text_substrings: tuple[str, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class GoldenEvaluationCase:
    """Immutable content-addressed evaluation labels for one answer case."""

    case_id: str
    case_hash: str
    golden_case_contract: str
    case_version: str
    question: str
    expected_behavior: str
    expected_packet_id: str | None
    expected_retrieval_id: str | None
    relevant_chunk_ids: tuple[str, ...]
    claim_criteria: tuple[GoldenClaimCriterion, ...]
    required_answer_substrings: tuple[str, ...]
    required_limitations: tuple[str, ...]
    allowed_limitations: tuple[str, ...]
    forbidden_answer_substrings: tuple[str, ...]
    calibration_target: tuple[float, float] | None
    provenance_uri: str
    authored_by: str
    approval_status: str

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class EvaluationDimension:
    name: str
    status: str
    score: float | None
    numerator: int | None
    denominator: int | None
    details: tuple[str, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    evaluation_id: str
    evaluation_hash: str
    answer_evaluation_contract: str
    evaluator_version: str
    evaluator_adapter_id: str
    golden_case_id: str
    packet_id: str
    grounded_result_id: str
    retrieval_id: str
    dimensions: tuple[EvaluationDimension, ...]
    failure_classifications: tuple[str, ...]
    aggregate_status: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    semantic_groundedness_status: str
    uncertainty_calibration_status: str
    semantic_support_verified: bool = False
    claim_coverage_verified: bool = False

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class EvaluationAggregate:
    aggregate_id: str
    evaluation_ids: tuple[str, ...]
    total_cases: int
    passed_cases: int
    case_pass_rate: float
    mean_citation_precision: float | None
    mean_citation_completeness: float | None
    mean_unsupported_claim_rate: float | None
    insufficiency_accuracy: float | None
    conflict_accuracy: float | None
    retrieval_failure_rate: float
    answer_failure_rate: float

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def memory_promotion_authorized(self) -> bool:
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
        raise EvaluationError(
            "evaluation material must be canonical JSON-compatible data"
        ) from exc


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _content_id(prefix: str, value: Any) -> str:
    return f"{prefix}{_content_hash(value)}"


def _normalized_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise EvaluationError(f"{name} must be a normalized non-empty string")
    return value


def _normalized_optional_text(name: str, value: Any) -> str | None:
    if value is None:
        return None
    return _normalized_text(name, value)


def _normalized_unique_strings(
    name: str, values: Any, *, sort_values: bool = True
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise EvaluationError(f"{name} must be a tuple/list of strings")
    items: list[str] = []
    for value in values:
        item = _normalized_text(name, value)
        if item in items:
            raise EvaluationError(f"{name} must not contain duplicates")
        items.append(item)
    if sort_values:
        items.sort()
    return tuple(items)


def _normalized_match_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _normalized_substrings(name: str, values: Any) -> tuple[str, ...]:
    raw = _normalized_unique_strings(name, values, sort_values=False)
    normalized: list[str] = []
    for value in raw:
        item = _normalized_match_text(value)
        if not item.strip():
            raise EvaluationError(f"{name} cannot normalize to empty text")
        if item in normalized:
            raise EvaluationError(f"{name} must remain unique after normalization")
        normalized.append(item)
    normalized.sort()
    return tuple(normalized)


def make_golden_claim_criterion(
    *,
    claim_id: str,
    required: bool = True,
    allowed_statuses: tuple[str, ...] | list[str] = ("supported",),
    allowed_evidence_chunk_ids: tuple[str, ...] | list[str] = (),
    required_text_substrings: tuple[str, ...] | list[str] = (),
) -> GoldenClaimCriterion:
    """Create one deterministic claim label for a golden evaluation case."""

    if not isinstance(required, bool):
        raise EvaluationError("required must be bool")
    statuses = _normalized_unique_strings("allowed claim status", allowed_statuses)
    if not statuses:
        raise EvaluationError("allowed_statuses must contain at least one status")
    unknown = set(statuses) - _ALLOWED_CLAIM_STATUSES
    if unknown:
        raise EvaluationError(f"unsupported allowed claim statuses: {sorted(unknown)!r}")
    return GoldenClaimCriterion(
        claim_id=_normalized_text("claim_id", claim_id),
        required=required,
        allowed_statuses=statuses,
        allowed_evidence_chunk_ids=_normalized_unique_strings(
            "allowed evidence chunk id", allowed_evidence_chunk_ids
        ),
        required_text_substrings=_normalized_substrings(
            "required claim substring", required_text_substrings
        ),
    )


def _criterion_material(criterion: GoldenClaimCriterion) -> dict[str, Any]:
    return {
        "claim_id": criterion.claim_id,
        "required": criterion.required,
        "allowed_statuses": list(criterion.allowed_statuses),
        "allowed_evidence_chunk_ids": list(criterion.allowed_evidence_chunk_ids),
        "required_text_substrings": list(criterion.required_text_substrings),
    }


def _case_material(case: GoldenEvaluationCase) -> dict[str, Any]:
    return {
        "golden_case_contract": case.golden_case_contract,
        "case_version": case.case_version,
        "question": case.question,
        "expected_behavior": case.expected_behavior,
        "expected_packet_id": case.expected_packet_id,
        "expected_retrieval_id": case.expected_retrieval_id,
        "relevant_chunk_ids": list(case.relevant_chunk_ids),
        "claim_criteria": [
            _criterion_material(criterion) for criterion in case.claim_criteria
        ],
        "required_answer_substrings": list(case.required_answer_substrings),
        "required_limitations": list(case.required_limitations),
        "allowed_limitations": list(case.allowed_limitations),
        "forbidden_answer_substrings": list(case.forbidden_answer_substrings),
        "calibration_target": (
            list(case.calibration_target)
            if case.calibration_target is not None
            else None
        ),
        "provenance_uri": case.provenance_uri,
        "authored_by": case.authored_by,
        "approval_status": case.approval_status,
    }


def make_golden_evaluation_case(
    *,
    question: str,
    expected_behavior: str,
    relevant_chunk_ids: tuple[str, ...] | list[str] = (),
    claim_criteria: tuple[GoldenClaimCriterion, ...] | list[GoldenClaimCriterion] = (),
    required_answer_substrings: tuple[str, ...] | list[str] = (),
    required_limitations: tuple[str, ...] | list[str] = (),
    allowed_limitations: tuple[str, ...] | list[str] = (),
    forbidden_answer_substrings: tuple[str, ...] | list[str] = (),
    expected_packet_id: str | None = None,
    expected_retrieval_id: str | None = None,
    calibration_target: tuple[float, float] | None = None,
    provenance_uri: str,
    authored_by: str,
    approval_status: str = "approved",
    golden_case_contract: str = GOLDEN_CASE_CONTRACT,
    case_version: str = "1.0.0",
) -> GoldenEvaluationCase:
    """Create an immutable content-addressed golden evaluation case."""

    contract = _normalized_text("golden_case_contract", golden_case_contract)
    if contract != GOLDEN_CASE_CONTRACT:
        raise EvaluationError(f"unsupported golden case contract {contract!r}")
    behavior = _normalized_text("expected_behavior", expected_behavior)
    if behavior not in _ALLOWED_CASE_BEHAVIORS:
        raise EvaluationError(f"unsupported expected behavior {behavior!r}")
    approval = _normalized_text("approval_status", approval_status)
    if approval not in _ALLOWED_CASE_APPROVAL:
        raise EvaluationError(f"unsupported golden case approval status {approval!r}")

    if not isinstance(claim_criteria, (tuple, list)):
        raise EvaluationError("claim_criteria must be a tuple/list")
    normalized_criteria: list[GoldenClaimCriterion] = []
    claim_ids: set[str] = set()
    for criterion in claim_criteria:
        if not isinstance(criterion, GoldenClaimCriterion):
            raise EvaluationError("claim_criteria must contain GoldenClaimCriterion")
        normalized = make_golden_claim_criterion(
            claim_id=criterion.claim_id,
            required=criterion.required,
            allowed_statuses=criterion.allowed_statuses,
            allowed_evidence_chunk_ids=criterion.allowed_evidence_chunk_ids,
            required_text_substrings=criterion.required_text_substrings,
        )
        if normalized.claim_id in claim_ids:
            raise EvaluationError("golden claim ids must be unique")
        claim_ids.add(normalized.claim_id)
        normalized_criteria.append(normalized)
    normalized_criteria.sort(key=lambda item: item.claim_id)

    required_lims = _normalized_unique_strings("required limitation", required_limitations)
    allowed_lims = _normalized_unique_strings("allowed limitation", allowed_limitations)
    if allowed_lims and not set(required_lims).issubset(allowed_lims):
        raise EvaluationError("required limitations must be included in allowed limitations")

    normalized_calibration: tuple[float, float] | None = None
    if calibration_target is not None:
        if (
            not isinstance(calibration_target, tuple)
            or len(calibration_target) != 2
            or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in calibration_target)
        ):
            raise EvaluationError("calibration_target must be a numeric (low, high) tuple")
        low, high = (float(calibration_target[0]), float(calibration_target[1]))
        if not math.isfinite(low) or not math.isfinite(high) or not (0.0 <= low <= high <= 1.0):
            raise EvaluationError("calibration_target must satisfy 0 <= low <= high <= 1")
        normalized_calibration = (low, high)

    provisional = GoldenEvaluationCase(
        case_id="",
        case_hash="",
        golden_case_contract=contract,
        case_version=_normalized_text("case_version", case_version),
        question=_normalized_text("question", question),
        expected_behavior=behavior,
        expected_packet_id=_normalized_optional_text("expected_packet_id", expected_packet_id),
        expected_retrieval_id=_normalized_optional_text(
            "expected_retrieval_id", expected_retrieval_id
        ),
        relevant_chunk_ids=_normalized_unique_strings(
            "relevant chunk id", relevant_chunk_ids
        ),
        claim_criteria=tuple(normalized_criteria),
        required_answer_substrings=_normalized_substrings(
            "required answer substring", required_answer_substrings
        ),
        required_limitations=required_lims,
        allowed_limitations=allowed_lims,
        forbidden_answer_substrings=_normalized_substrings(
            "forbidden answer substring", forbidden_answer_substrings
        ),
        calibration_target=normalized_calibration,
        provenance_uri=_normalized_text("provenance_uri", provenance_uri),
        authored_by=_normalized_text("authored_by", authored_by),
        approval_status=approval,
    )
    case_hash = _content_hash(_case_material(provisional))
    return GoldenEvaluationCase(
        case_id=f"gcase_{case_hash}",
        case_hash=case_hash,
        golden_case_contract=provisional.golden_case_contract,
        case_version=provisional.case_version,
        question=provisional.question,
        expected_behavior=provisional.expected_behavior,
        expected_packet_id=provisional.expected_packet_id,
        expected_retrieval_id=provisional.expected_retrieval_id,
        relevant_chunk_ids=provisional.relevant_chunk_ids,
        claim_criteria=provisional.claim_criteria,
        required_answer_substrings=provisional.required_answer_substrings,
        required_limitations=provisional.required_limitations,
        allowed_limitations=provisional.allowed_limitations,
        forbidden_answer_substrings=provisional.forbidden_answer_substrings,
        calibration_target=provisional.calibration_target,
        provenance_uri=provisional.provenance_uri,
        authored_by=provisional.authored_by,
        approval_status=provisional.approval_status,
    )


def _validate_golden_case(case: GoldenEvaluationCase) -> GoldenEvaluationCase:
    if not isinstance(case, GoldenEvaluationCase):
        raise EvaluationError("case must be GoldenEvaluationCase")
    rebuilt = make_golden_evaluation_case(
        question=case.question,
        expected_behavior=case.expected_behavior,
        relevant_chunk_ids=case.relevant_chunk_ids,
        claim_criteria=case.claim_criteria,
        required_answer_substrings=case.required_answer_substrings,
        required_limitations=case.required_limitations,
        allowed_limitations=case.allowed_limitations,
        forbidden_answer_substrings=case.forbidden_answer_substrings,
        expected_packet_id=case.expected_packet_id,
        expected_retrieval_id=case.expected_retrieval_id,
        calibration_target=case.calibration_target,
        provenance_uri=case.provenance_uri,
        authored_by=case.authored_by,
        approval_status=case.approval_status,
        golden_case_contract=case.golden_case_contract,
        case_version=case.case_version,
    )
    if rebuilt != case:
        raise EvaluationError("golden evaluation case identity/content is invalid")
    if case.approval_status != "approved":
        raise EvaluationError("only approved golden evaluation cases may be scored")
    return case


def validate_grounded_result_for_evaluation(
    *, packet: EvidencePacket, result: GroundedAnswerResult
) -> GroundedAnswerResult:
    """Reconstruct and exactly validate one Phase 6 result before evaluation."""

    if not isinstance(result, GroundedAnswerResult):
        raise EvaluationError("result must be GroundedAnswerResult")
    if result.answer_contract != ANSWER_CONTRACT:
        raise EvaluationError("unsupported grounded answer contract")
    try:
        candidate = make_answer_candidate(
            packet_id=result.packet_id,
            answer_text=result.answer_text,
            claims=result.claims,
            limitations=result.limitations,
            answer_contract=result.answer_contract,
            answer_version=result.answer_version,
        )
        rebuilt = validate_answer_candidate(packet=packet, candidate=candidate)
    except GroundingError as exc:
        raise EvaluationError("canonical Phase 6 grounded-answer reconstruction failed") from exc
    if rebuilt != result:
        raise EvaluationError(
            "supplied GroundedAnswerResult does not match canonical Phase 6 validation"
        )
    return rebuilt


def _dimension(
    name: str,
    status: str,
    *,
    numerator: int | None = None,
    denominator: int | None = None,
    score: float | None = None,
    details: tuple[str, ...] | list[str] = (),
) -> EvaluationDimension:
    normalized_status = _normalized_text("dimension status", status)
    if normalized_status not in _ALLOWED_DIMENSION_STATUSES:
        raise EvaluationError(f"unsupported dimension status {normalized_status!r}")
    if numerator is not None and (isinstance(numerator, bool) or not isinstance(numerator, int) or numerator < 0):
        raise EvaluationError("dimension numerator must be a non-negative integer")
    if denominator is not None and (isinstance(denominator, bool) or not isinstance(denominator, int) or denominator < 0):
        raise EvaluationError("dimension denominator must be a non-negative integer")
    if score is not None:
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(float(score)):
            raise EvaluationError("dimension score must be finite numeric")
        score = float(score)
    return EvaluationDimension(
        name=_normalized_text("dimension name", name),
        status=normalized_status,
        score=score,
        numerator=numerator,
        denominator=denominator,
        details=_normalized_unique_strings("dimension detail", details),
    )


def _ratio_dimension(
    name: str,
    numerator: int,
    denominator: int,
    *,
    pass_when_equal: bool = True,
    details: tuple[str, ...] | list[str] = (),
) -> EvaluationDimension:
    if denominator <= 0:
        return _dimension(name, "not_applicable", details=details)
    score = numerator / denominator
    status = "pass" if (not pass_when_equal or numerator == denominator) else "fail"
    return _dimension(
        name,
        status,
        numerator=numerator,
        denominator=denominator,
        score=score,
        details=details,
    )


def _claim_cited_chunk_ids(
    *, claim: AnswerClaim, anchor_chunk_by_label: dict[str, str]
) -> tuple[str, ...]:
    chunks: list[str] = []
    for label in claim.evidence_anchors:
        chunk_id = anchor_chunk_by_label[label]
        if chunk_id not in chunks:
            chunks.append(chunk_id)
    return tuple(chunks)


def _criterion_accepts_claim(
    *,
    criterion: GoldenClaimCriterion,
    claim: AnswerClaim,
    anchor_chunk_by_label: dict[str, str],
) -> bool:
    if claim.status not in criterion.allowed_statuses:
        return False
    cited_chunks = _claim_cited_chunk_ids(
        claim=claim, anchor_chunk_by_label=anchor_chunk_by_label
    )
    if criterion.allowed_evidence_chunk_ids and not set(cited_chunks).issubset(
        set(criterion.allowed_evidence_chunk_ids)
    ):
        return False
    normalized_claim_text = _normalized_match_text(claim.text)
    return all(
        substring in normalized_claim_text
        for substring in criterion.required_text_substrings
    )


def _dimension_material(dimension: EvaluationDimension) -> dict[str, Any]:
    return {
        "name": dimension.name,
        "status": dimension.status,
        "score": dimension.score,
        "numerator": dimension.numerator,
        "denominator": dimension.denominator,
        "details": list(dimension.details),
    }


def evaluate_grounded_answer(
    *,
    packet: EvidencePacket,
    result: GroundedAnswerResult,
    case: GoldenEvaluationCase,
    answer_evaluation_contract: str = ANSWER_EVALUATION_CONTRACT,
    evaluator_version: str = EVALUATOR_VERSION,
    evaluator_adapter_id: str = DETERMINISTIC_EVALUATOR_ADAPTER,
) -> EvaluationResult:
    """Evaluate one accepted Phase 6 result against deterministic golden labels."""

    contract = _normalized_text(
        "answer_evaluation_contract", answer_evaluation_contract
    )
    if contract != ANSWER_EVALUATION_CONTRACT:
        raise EvaluationError(f"unsupported answer evaluation contract {contract!r}")
    version = _normalized_text("evaluator_version", evaluator_version)
    adapter = _normalized_text("evaluator_adapter_id", evaluator_adapter_id)
    if adapter != DETERMINISTIC_EVALUATOR_ADAPTER:
        raise EvaluationError(
            "Phase 7 first slice accepts only the deterministic golden-label adapter"
        )

    canonical_result = validate_grounded_result_for_evaluation(
        packet=packet, result=result
    )
    canonical_case = _validate_golden_case(case)

    if canonical_case.expected_packet_id is not None and canonical_case.expected_packet_id != packet.packet_id:
        raise EvaluationError("golden case expected_packet_id does not match packet")
    if canonical_case.expected_retrieval_id is not None and canonical_case.expected_retrieval_id != canonical_result.retrieval_id:
        raise EvaluationError("golden case expected_retrieval_id does not match result")

    anchors_by_label = {anchor.label: anchor for anchor in packet.evidence_anchors}
    anchor_chunk_by_label = {
        label: anchor.chunk_id for label, anchor in anchors_by_label.items()
    }
    packet_chunk_ids = {anchor.chunk_id for anchor in packet.evidence_anchors}
    relevant_chunk_ids = set(canonical_case.relevant_chunk_ids)
    present_relevant = relevant_chunk_ids & packet_chunk_ids
    missing_relevant = relevant_chunk_ids - packet_chunk_ids

    dimensions: list[EvaluationDimension] = []
    failures: list[str] = []

    if relevant_chunk_ids:
        retrieval_dimension = _ratio_dimension(
            "retrieval_coverage",
            len(present_relevant),
            len(relevant_chunk_ids),
            details=tuple(
                f"missing_relevant_chunk:{chunk_id}" for chunk_id in sorted(missing_relevant)
            ),
        )
    else:
        retrieval_dimension = _dimension("retrieval_coverage", "not_applicable")
    dimensions.append(retrieval_dimension)
    retrieval_failed = retrieval_dimension.status == "fail"
    if retrieval_failed:
        failures.append("retrieval_failure")

    reference_by_label = {
        reference.label: reference for reference in canonical_result.evidence_references
    }
    citation_integrity_ok = all(
        label in anchors_by_label
        and reference.anchor_id == anchors_by_label[label].anchor_id
        and reference.chunk_id == anchors_by_label[label].chunk_id
        and reference.content_hash == anchors_by_label[label].content_hash
        for label, reference in reference_by_label.items()
    )
    dimensions.append(
        _dimension(
            "citation_correctness",
            "pass" if citation_integrity_ok else "fail",
            numerator=int(citation_integrity_ok),
            denominator=1,
            score=1.0 if citation_integrity_ok else 0.0,
        )
    )
    if not citation_integrity_ok:
        failures.append("citation_binding_failure")

    cited_chunk_ids = {
        reference.chunk_id for reference in canonical_result.evidence_references
    }
    if relevant_chunk_ids:
        if cited_chunk_ids:
            relevant_citations = cited_chunk_ids & relevant_chunk_ids
            precision = len(relevant_citations) / len(cited_chunk_ids)
            dimensions.append(
                _dimension(
                    "citation_precision",
                    "pass" if len(relevant_citations) == len(cited_chunk_ids) else "fail",
                    numerator=len(relevant_citations),
                    denominator=len(cited_chunk_ids),
                    score=precision,
                    details=tuple(
                        f"irrelevant_cited_chunk:{chunk_id}"
                        for chunk_id in sorted(cited_chunk_ids - relevant_chunk_ids)
                    ),
                )
            )
        elif canonical_case.expected_behavior == "insufficient":
            dimensions.append(_dimension("citation_precision", "not_applicable"))
        else:
            dimensions.append(
                _dimension(
                    "citation_precision",
                    "fail",
                    numerator=0,
                    denominator=1,
                    score=0.0,
                    details=("no_citations_for_answer_case",),
                )
            )

        if retrieval_failed and not present_relevant:
            dimensions.append(
                _dimension(
                    "citation_completeness",
                    "not_evaluated",
                    details=("blocked_by_retrieval_failure",),
                )
            )
        else:
            completeness_denominator = len(present_relevant)
            dimensions.append(
                _ratio_dimension(
                    "citation_completeness",
                    len(cited_chunk_ids & present_relevant),
                    completeness_denominator,
                    details=tuple(
                        f"uncited_relevant_chunk:{chunk_id}"
                        for chunk_id in sorted(present_relevant - cited_chunk_ids)
                    ),
                )
            )
    else:
        dimensions.append(_dimension("citation_precision", "not_evaluated"))
        dimensions.append(_dimension("citation_completeness", "not_evaluated"))

    criteria_by_claim_id = {
        criterion.claim_id: criterion for criterion in canonical_case.claim_criteria
    }
    claims_by_id = {claim.claim_id: claim for claim in canonical_result.claims}
    unsupported_claim_ids: list[str] = []
    matched_claims = 0
    correct_matched_claims = 0
    for claim in canonical_result.claims:
        criterion = criteria_by_claim_id.get(claim.claim_id)
        if criterion is None:
            unsupported_claim_ids.append(claim.claim_id)
            continue
        matched_claims += 1
        if _criterion_accepts_claim(
            criterion=criterion,
            claim=claim,
            anchor_chunk_by_label=anchor_chunk_by_label,
        ):
            correct_matched_claims += 1
        else:
            unsupported_claim_ids.append(claim.claim_id)

    unsupported_rate = (
        len(unsupported_claim_ids) / len(canonical_result.claims)
        if canonical_result.claims
        else 0.0
    )
    dimensions.append(
        _dimension(
            "unsupported_claim_rate",
            "pass" if not unsupported_claim_ids else "fail",
            numerator=len(unsupported_claim_ids),
            denominator=len(canonical_result.claims),
            score=unsupported_rate,
            details=tuple(
                f"unsupported_or_mislabeled_claim:{claim_id}"
                for claim_id in sorted(unsupported_claim_ids)
            ),
        )
    )
    if unsupported_claim_ids:
        failures.append("unsupported_claim_failure")

    normalized_answer_text = _normalized_match_text(canonical_result.answer_text)
    answer_text_ok = all(
        substring in normalized_answer_text
        for substring in canonical_case.required_answer_substrings
    )
    if canonical_case.claim_criteria or canonical_case.required_answer_substrings:
        correctness_numerator = correct_matched_claims + int(answer_text_ok)
        correctness_denominator = matched_claims + int(
            bool(canonical_case.required_answer_substrings)
        )
        if correctness_denominator == 0:
            correctness_dimension = _dimension(
                "answer_correctness",
                "fail",
                numerator=0,
                denominator=1,
                score=0.0,
                details=("no_labeled_claims_matched",),
            )
        else:
            correctness_dimension = _ratio_dimension(
                "answer_correctness",
                correctness_numerator,
                correctness_denominator,
                details=(
                    ()
                    if answer_text_ok
                    else ("required_answer_substring_missing",)
                ),
            )
    else:
        correctness_dimension = _dimension("answer_correctness", "not_evaluated")
    if retrieval_failed and correctness_dimension.status == "fail":
        correctness_dimension = _dimension(
            "answer_correctness",
            "not_evaluated",
            details=("blocked_by_retrieval_failure",),
        )
    dimensions.append(correctness_dimension)
    if correctness_dimension.status == "fail":
        failures.append("answer_correctness_failure")

    required_criteria = [
        criterion for criterion in canonical_case.claim_criteria if criterion.required
    ]
    if required_criteria:
        present_required = sum(
            1 for criterion in required_criteria if criterion.claim_id in claims_by_id
        )
        if retrieval_failed:
            completeness_dimension = _dimension(
                "answer_completeness",
                "not_evaluated",
                details=("blocked_by_retrieval_failure",),
            )
        else:
            completeness_dimension = _ratio_dimension(
                "answer_completeness",
                present_required,
                len(required_criteria),
                details=tuple(
                    f"missing_required_claim:{criterion.claim_id}"
                    for criterion in required_criteria
                    if criterion.claim_id not in claims_by_id
                ),
            )
    else:
        completeness_dimension = _dimension("answer_completeness", "not_applicable")
    dimensions.append(completeness_dimension)
    if completeness_dimension.status == "fail":
        failures.append("answer_completeness_failure")

    limitation_set = set(canonical_result.limitations)
    required_limitations = set(canonical_case.required_limitations)
    missing_limitations = required_limitations - limitation_set
    disallowed_limitations = (
        limitation_set - set(canonical_case.allowed_limitations)
        if canonical_case.allowed_limitations
        else set()
    )
    limitation_ok = not missing_limitations and not disallowed_limitations
    dimensions.append(
        _dimension(
            "limitation_disclosure",
            "pass" if limitation_ok else "fail",
            numerator=int(limitation_ok),
            denominator=1,
            score=1.0 if limitation_ok else 0.0,
            details=tuple(
                [
                    *(f"missing_required_limitation:{value}" for value in sorted(missing_limitations)),
                    *(f"disallowed_limitation:{value}" for value in sorted(disallowed_limitations)),
                ]
            ),
        )
    )
    if not limitation_ok:
        failures.append("answer_correctness_failure")

    expects_insufficient = canonical_case.expected_behavior == "insufficient"
    if expects_insufficient or canonical_result.status == "insufficient":
        insufficiency_ok = (
            expects_insufficient
            and canonical_result.status == "insufficient"
            and all(claim.status == "insufficient" for claim in canonical_result.claims)
            and "insufficient_evidence" in limitation_set
        )
        dimensions.append(
            _dimension(
                "insufficiency_handling",
                "pass" if insufficiency_ok else "fail",
                numerator=int(insufficiency_ok),
                denominator=1,
                score=1.0 if insufficiency_ok else 0.0,
            )
        )
        if not insufficiency_ok:
            failures.append("insufficiency_handling_failure")
    else:
        dimensions.append(_dimension("insufficiency_handling", "not_applicable"))

    has_conflict_claim = any(
        claim.status == "conflict" for claim in canonical_result.claims
    )
    expects_conflict = canonical_case.expected_behavior == "conflict"
    if expects_conflict or has_conflict_claim:
        conflict_ok = expects_conflict and has_conflict_claim
        dimensions.append(
            _dimension(
                "conflict_handling",
                "pass" if conflict_ok else "fail",
                numerator=int(conflict_ok),
                denominator=1,
                score=1.0 if conflict_ok else 0.0,
            )
        )
        if not conflict_ok:
            failures.append("conflict_handling_failure")
    else:
        dimensions.append(_dimension("conflict_handling", "not_applicable"))

    forbidden_hits = [
        substring
        for substring in canonical_case.forbidden_answer_substrings
        if substring in normalized_answer_text
        or any(
            substring in _normalized_match_text(claim.text)
            for claim in canonical_result.claims
        )
    ]
    if canonical_case.forbidden_answer_substrings:
        instruction_ok = not forbidden_hits
        dimensions.append(
            _dimension(
                "instruction_compliance",
                "pass" if instruction_ok else "fail",
                numerator=int(instruction_ok),
                denominator=1,
                score=1.0 if instruction_ok else 0.0,
                details=tuple(
                    f"forbidden_answer_substring_present:{value}"
                    for value in sorted(forbidden_hits)
                ),
            )
        )
        if not instruction_ok:
            failures.append("instruction_compliance_failure")
    else:
        dimensions.append(_dimension("instruction_compliance", "not_evaluated"))

    dimensions.append(
        _dimension(
            "semantic_groundedness",
            "not_evaluated",
            details=("no_accepted_semantic_evaluator_adapter",),
        )
    )
    if canonical_case.calibration_target is None:
        calibration_status = "not_applicable"
    else:
        calibration_status = "not_evaluated"
    dimensions.append(
        _dimension(
            "uncertainty_calibration",
            calibration_status,
            details=(
                ()
                if calibration_status == "not_applicable"
                else ("grounded_answer_contract_has_no_calibrated_confidence_field",)
            ),
        )
    )

    failure_tuple = tuple(dict.fromkeys(failures))
    unknown_failures = set(failure_tuple) - _FAILURE_CLASSES
    if unknown_failures:
        raise EvaluationError(f"unsupported failure classification {unknown_failures!r}")

    blocking_statuses = {
        dimension.status for dimension in dimensions if dimension.status == "fail"
    }
    aggregate_status = "pass" if not blocking_statuses and not failure_tuple else "fail"
    warnings: list[str] = [
        "semantic_groundedness_not_evaluated",
        "evaluation_does_not_authorize_memory_promotion",
    ]
    if retrieval_failed:
        warnings.append("answer_dimensions_may_be_blocked_by_retrieval_failure")
    if canonical_case.calibration_target is not None:
        warnings.append("uncertainty_calibration_not_evaluated")

    evaluation_material = {
        "answer_evaluation_contract": contract,
        "evaluator_version": version,
        "evaluator_adapter_id": adapter,
        "golden_case_id": canonical_case.case_id,
        "packet_id": packet.packet_id,
        "grounded_result_id": canonical_result.result_id,
        "retrieval_id": canonical_result.retrieval_id,
        "dimensions": [_dimension_material(item) for item in dimensions],
        "failure_classifications": list(failure_tuple),
        "aggregate_status": aggregate_status,
        "warnings": warnings,
        "errors": [],
        "semantic_groundedness_status": "not_evaluated",
        "uncertainty_calibration_status": calibration_status,
        "semantic_support_verified": False,
        "claim_coverage_verified": False,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "execution_authorized": False,
    }
    evaluation_hash = _content_hash(evaluation_material)
    return EvaluationResult(
        evaluation_id=f"eval_{evaluation_hash}",
        evaluation_hash=evaluation_hash,
        answer_evaluation_contract=contract,
        evaluator_version=version,
        evaluator_adapter_id=adapter,
        golden_case_id=canonical_case.case_id,
        packet_id=packet.packet_id,
        grounded_result_id=canonical_result.result_id,
        retrieval_id=canonical_result.retrieval_id,
        dimensions=tuple(dimensions),
        failure_classifications=failure_tuple,
        aggregate_status=aggregate_status,
        warnings=tuple(warnings),
        errors=(),
        semantic_groundedness_status="not_evaluated",
        uncertainty_calibration_status=calibration_status,
        semantic_support_verified=False,
        claim_coverage_verified=False,
    )


def _dimension_by_name(result: EvaluationResult, name: str) -> EvaluationDimension | None:
    return next((item for item in result.dimensions if item.name == name), None)


def _mean(scores: list[float]) -> float | None:
    return sum(scores) / len(scores) if scores else None


def aggregate_evaluation_results(
    results: tuple[EvaluationResult, ...] | list[EvaluationResult],
) -> EvaluationAggregate:
    """Aggregate deterministic Phase 7 metrics without changing their authority."""

    if not isinstance(results, (tuple, list)) or not results:
        raise EvaluationError("results must contain at least one EvaluationResult")
    normalized: list[EvaluationResult] = []
    seen_ids: set[str] = set()
    for result in results:
        if not isinstance(result, EvaluationResult):
            raise EvaluationError("results must contain EvaluationResult values")
        if result.evaluation_id in seen_ids:
            raise EvaluationError("evaluation ids must be unique in an aggregate")
        if result.answer_evaluation_contract != ANSWER_EVALUATION_CONTRACT:
            raise EvaluationError("aggregate contains unsupported evaluation contract")
        seen_ids.add(result.evaluation_id)
        normalized.append(result)
    normalized.sort(key=lambda item: item.evaluation_id)

    citation_precision_scores: list[float] = []
    citation_completeness_scores: list[float] = []
    unsupported_rates: list[float] = []
    insufficiency_scores: list[float] = []
    conflict_scores: list[float] = []

    for result in normalized:
        for name, target in (
            ("citation_precision", citation_precision_scores),
            ("citation_completeness", citation_completeness_scores),
            ("unsupported_claim_rate", unsupported_rates),
            ("insufficiency_handling", insufficiency_scores),
            ("conflict_handling", conflict_scores),
        ):
            dimension = _dimension_by_name(result, name)
            if dimension is not None and dimension.score is not None:
                target.append(dimension.score)

    total = len(normalized)
    passed = sum(result.aggregate_status == "pass" for result in normalized)
    retrieval_failures = sum(
        "retrieval_failure" in result.failure_classifications for result in normalized
    )
    answer_failure_classes = _FAILURE_CLASSES - {
        "retrieval_failure",
        "evaluator_unavailable",
        "evaluator_disagreement",
        "unknown",
    }
    answer_failures = sum(
        bool(set(result.failure_classifications) & answer_failure_classes)
        for result in normalized
    )

    material = {
        "evaluation_ids": [result.evaluation_id for result in normalized],
        "total_cases": total,
        "passed_cases": passed,
        "case_pass_rate": passed / total,
        "mean_citation_precision": _mean(citation_precision_scores),
        "mean_citation_completeness": _mean(citation_completeness_scores),
        "mean_unsupported_claim_rate": _mean(unsupported_rates),
        "insufficiency_accuracy": _mean(insufficiency_scores),
        "conflict_accuracy": _mean(conflict_scores),
        "retrieval_failure_rate": retrieval_failures / total,
        "answer_failure_rate": answer_failures / total,
    }
    aggregate_id = _content_id("evalagg_", material)
    return EvaluationAggregate(
        aggregate_id=aggregate_id,
        evaluation_ids=tuple(result.evaluation_id for result in normalized),
        total_cases=total,
        passed_cases=passed,
        case_pass_rate=passed / total,
        mean_citation_precision=_mean(citation_precision_scores),
        mean_citation_completeness=_mean(citation_completeness_scores),
        mean_unsupported_claim_rate=_mean(unsupported_rates),
        insufficiency_accuracy=_mean(insufficiency_scores),
        conflict_accuracy=_mean(conflict_scores),
        retrieval_failure_rate=retrieval_failures / total,
        answer_failure_rate=answer_failures / total,
    )
