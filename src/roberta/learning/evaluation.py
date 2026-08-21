"""Independent answer evaluation for the Roberta Learning System.

Phase 7 scores accepted Phase 6 grounded answers against explicit approved
golden labels. Scores are measurement metadata only: never source truth,
live-state verification, durable-memory promotion, or execution authority.
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

_CLAIM_STATUSES = frozenset({"supported", "insufficient", "conflict"})
_CASE_BEHAVIORS = frozenset({"answer", "insufficient", "conflict"})
_CASE_APPROVAL = frozenset({"approved", "pending", "rejected"})
_DIMENSION_STATUSES = frozenset({"pass", "fail", "not_evaluated", "not_applicable"})
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
    """Raised when evaluation cannot be performed safely."""


@dataclass(frozen=True, slots=True)
class GoldenClaimCriterion:
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
        raise EvaluationError("evaluation material must be canonical JSON-compatible data") from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _id(prefix: str, value: Any) -> str:
    return f"{prefix}{_hash(value)}"


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise EvaluationError(f"{name} must be a normalized non-empty string")
    return value


def _optional_text(name: str, value: Any) -> str | None:
    return None if value is None else _text(name, value)


def _strings(name: str, values: Any, *, sort_values: bool = True) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise EvaluationError(f"{name} must be a tuple/list of strings")
    output: list[str] = []
    for value in values:
        item = _text(name, value)
        if item in output:
            raise EvaluationError(f"{name} must not contain duplicates")
        output.append(item)
    if sort_values:
        output.sort()
    return tuple(output)


def _match_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def _substrings(name: str, values: Any) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in _strings(name, values, sort_values=False):
        item = _match_text(value)
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
    if not isinstance(required, bool):
        raise EvaluationError("required must be bool")
    statuses = _strings("allowed claim status", allowed_statuses)
    if not statuses:
        raise EvaluationError("allowed_statuses must contain at least one status")
    unknown = set(statuses) - _CLAIM_STATUSES
    if unknown:
        raise EvaluationError(f"unsupported allowed claim statuses: {sorted(unknown)!r}")
    return GoldenClaimCriterion(
        claim_id=_text("claim_id", claim_id),
        required=required,
        allowed_statuses=statuses,
        allowed_evidence_chunk_ids=_strings(
            "allowed evidence chunk id", allowed_evidence_chunk_ids
        ),
        required_text_substrings=_substrings(
            "required claim substring", required_text_substrings
        ),
    )


def _criterion_material(value: GoldenClaimCriterion) -> dict[str, Any]:
    return {
        "claim_id": value.claim_id,
        "required": value.required,
        "allowed_statuses": list(value.allowed_statuses),
        "allowed_evidence_chunk_ids": list(value.allowed_evidence_chunk_ids),
        "required_text_substrings": list(value.required_text_substrings),
    }


def _case_material(value: GoldenEvaluationCase) -> dict[str, Any]:
    return {
        "golden_case_contract": value.golden_case_contract,
        "case_version": value.case_version,
        "question": value.question,
        "expected_behavior": value.expected_behavior,
        "expected_packet_id": value.expected_packet_id,
        "expected_retrieval_id": value.expected_retrieval_id,
        "relevant_chunk_ids": list(value.relevant_chunk_ids),
        "claim_criteria": [_criterion_material(item) for item in value.claim_criteria],
        "required_answer_substrings": list(value.required_answer_substrings),
        "required_limitations": list(value.required_limitations),
        "allowed_limitations": list(value.allowed_limitations),
        "forbidden_answer_substrings": list(value.forbidden_answer_substrings),
        "calibration_target": list(value.calibration_target) if value.calibration_target else None,
        "provenance_uri": value.provenance_uri,
        "authored_by": value.authored_by,
        "approval_status": value.approval_status,
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
    contract = _text("golden_case_contract", golden_case_contract)
    if contract != GOLDEN_CASE_CONTRACT:
        raise EvaluationError(f"unsupported golden case contract {contract!r}")
    behavior = _text("expected_behavior", expected_behavior)
    if behavior not in _CASE_BEHAVIORS:
        raise EvaluationError(f"unsupported expected behavior {behavior!r}")
    approval = _text("approval_status", approval_status)
    if approval not in _CASE_APPROVAL:
        raise EvaluationError(f"unsupported golden case approval status {approval!r}")

    if not isinstance(claim_criteria, (tuple, list)):
        raise EvaluationError("claim_criteria must be a tuple/list")
    criteria: list[GoldenClaimCriterion] = []
    seen: set[str] = set()
    for item in claim_criteria:
        if not isinstance(item, GoldenClaimCriterion):
            raise EvaluationError("claim_criteria must contain GoldenClaimCriterion")
        normalized = make_golden_claim_criterion(
            claim_id=item.claim_id,
            required=item.required,
            allowed_statuses=item.allowed_statuses,
            allowed_evidence_chunk_ids=item.allowed_evidence_chunk_ids,
            required_text_substrings=item.required_text_substrings,
        )
        if normalized.claim_id in seen:
            raise EvaluationError("golden claim ids must be unique")
        seen.add(normalized.claim_id)
        criteria.append(normalized)
    criteria.sort(key=lambda item: item.claim_id)

    required_lims = _strings("required limitation", required_limitations)
    allowed_lims = _strings("allowed limitation", allowed_limitations)
    if allowed_lims and not set(required_lims).issubset(allowed_lims):
        raise EvaluationError("required limitations must be included in allowed limitations")

    calibration: tuple[float, float] | None = None
    if calibration_target is not None:
        if (
            not isinstance(calibration_target, tuple)
            or len(calibration_target) != 2
            or any(
                isinstance(item, bool) or not isinstance(item, (int, float))
                for item in calibration_target
            )
        ):
            raise EvaluationError("calibration_target must be a numeric (low, high) tuple")
        low, high = float(calibration_target[0]), float(calibration_target[1])
        if not math.isfinite(low) or not math.isfinite(high) or not (0 <= low <= high <= 1):
            raise EvaluationError("calibration_target must satisfy 0 <= low <= high <= 1")
        calibration = (low, high)

    provisional = GoldenEvaluationCase(
        case_id="",
        case_hash="",
        golden_case_contract=contract,
        case_version=_text("case_version", case_version),
        question=_text("question", question),
        expected_behavior=behavior,
        expected_packet_id=_optional_text("expected_packet_id", expected_packet_id),
        expected_retrieval_id=_optional_text("expected_retrieval_id", expected_retrieval_id),
        relevant_chunk_ids=_strings("relevant chunk id", relevant_chunk_ids),
        claim_criteria=tuple(criteria),
        required_answer_substrings=_substrings(
            "required answer substring", required_answer_substrings
        ),
        required_limitations=required_lims,
        allowed_limitations=allowed_lims,
        forbidden_answer_substrings=_substrings(
            "forbidden answer substring", forbidden_answer_substrings
        ),
        calibration_target=calibration,
        provenance_uri=_text("provenance_uri", provenance_uri),
        authored_by=_text("authored_by", authored_by),
        approval_status=approval,
    )
    digest = _hash(_case_material(provisional))
    return GoldenEvaluationCase(
        case_id=f"gcase_{digest}",
        case_hash=digest,
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


def _validate_case(case: GoldenEvaluationCase) -> GoldenEvaluationCase:
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
    status = _text("dimension status", status)
    if status not in _DIMENSION_STATUSES:
        raise EvaluationError(f"unsupported dimension status {status!r}")
    for label, value in (("numerator", numerator), ("denominator", denominator)):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise EvaluationError(f"dimension {label} must be a non-negative integer")
    if score is not None:
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise EvaluationError("dimension score must be numeric")
        score = float(score)
        if not math.isfinite(score):
            raise EvaluationError("dimension score must be finite")
    return EvaluationDimension(
        name=_text("dimension name", name),
        status=status,
        score=score,
        numerator=numerator,
        denominator=denominator,
        details=_strings("dimension detail", details),
    )


def _ratio(
    name: str,
    numerator: int,
    denominator: int,
    *,
    details: tuple[str, ...] | list[str] = (),
) -> EvaluationDimension:
    if denominator <= 0:
        return _dimension(name, "not_applicable", details=details)
    score = numerator / denominator
    return _dimension(
        name,
        "pass" if numerator == denominator else "fail",
        numerator=numerator,
        denominator=denominator,
        score=score,
        details=details,
    )


def _cited_chunks(claim: AnswerClaim, anchor_chunks: dict[str, str]) -> tuple[str, ...]:
    output: list[str] = []
    for label in claim.evidence_anchors:
        chunk_id = anchor_chunks[label]
        if chunk_id not in output:
            output.append(chunk_id)
    return tuple(output)


def _criterion_accepts(
    criterion: GoldenClaimCriterion,
    claim: AnswerClaim,
    anchor_chunks: dict[str, str],
) -> bool:
    if claim.status not in criterion.allowed_statuses:
        return False
    cited = _cited_chunks(claim, anchor_chunks)
    if criterion.allowed_evidence_chunk_ids and not set(cited).issubset(
        set(criterion.allowed_evidence_chunk_ids)
    ):
        return False
    text = _match_text(claim.text)
    return all(value in text for value in criterion.required_text_substrings)


def _dimension_material(item: EvaluationDimension) -> dict[str, Any]:
    return {
        "name": item.name,
        "status": item.status,
        "score": item.score,
        "numerator": item.numerator,
        "denominator": item.denominator,
        "details": list(item.details),
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
    contract = _text("answer_evaluation_contract", answer_evaluation_contract)
    if contract != ANSWER_EVALUATION_CONTRACT:
        raise EvaluationError(f"unsupported answer evaluation contract {contract!r}")
    version = _text("evaluator_version", evaluator_version)
    adapter = _text("evaluator_adapter_id", evaluator_adapter_id)
    if adapter != DETERMINISTIC_EVALUATOR_ADAPTER:
        raise EvaluationError(
            "Phase 7 first slice accepts only the deterministic golden-label adapter"
        )

    result = validate_grounded_result_for_evaluation(packet=packet, result=result)
    case = _validate_case(case)
    if case.expected_packet_id is not None and case.expected_packet_id != packet.packet_id:
        raise EvaluationError("golden case expected_packet_id does not match packet")
    if case.expected_retrieval_id is not None and case.expected_retrieval_id != result.retrieval_id:
        raise EvaluationError("golden case expected_retrieval_id does not match result")

    anchors = {item.label: item for item in packet.evidence_anchors}
    anchor_chunks = {label: item.chunk_id for label, item in anchors.items()}
    packet_chunks = set(anchor_chunks.values())
    relevant = set(case.relevant_chunk_ids)
    present_relevant = relevant & packet_chunks
    missing_relevant = relevant - packet_chunks
    dimensions: list[EvaluationDimension] = []
    failures: list[str] = []

    if relevant:
        retrieval = _ratio(
            "retrieval_coverage",
            len(present_relevant),
            len(relevant),
            details=tuple(
                f"missing_relevant_chunk:{value}" for value in sorted(missing_relevant)
            ),
        )
    else:
        retrieval = _dimension("retrieval_coverage", "not_applicable")
    dimensions.append(retrieval)
    retrieval_failed = retrieval.status == "fail"
    if retrieval_failed:
        failures.append("retrieval_failure")

    references = {item.label: item for item in result.evidence_references}
    citation_integrity = all(
        label in anchors
        and reference.anchor_id == anchors[label].anchor_id
        and reference.chunk_id == anchors[label].chunk_id
        and reference.content_hash == anchors[label].content_hash
        for label, reference in references.items()
    )
    dimensions.append(
        _dimension(
            "citation_correctness",
            "pass" if citation_integrity else "fail",
            numerator=int(citation_integrity),
            denominator=1,
            score=1.0 if citation_integrity else 0.0,
        )
    )
    if not citation_integrity:
        failures.append("citation_binding_failure")

    cited_chunks = {item.chunk_id for item in result.evidence_references}
    if relevant:
        if cited_chunks:
            relevant_cited = cited_chunks & relevant
            dimensions.append(
                _dimension(
                    "citation_precision",
                    "pass" if relevant_cited == cited_chunks else "fail",
                    numerator=len(relevant_cited),
                    denominator=len(cited_chunks),
                    score=len(relevant_cited) / len(cited_chunks),
                    details=tuple(
                        f"irrelevant_cited_chunk:{value}"
                        for value in sorted(cited_chunks - relevant)
                    ),
                )
            )
        elif case.expected_behavior == "insufficient":
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
            dimensions.append(
                _ratio(
                    "citation_completeness",
                    len(cited_chunks & present_relevant),
                    len(present_relevant),
                    details=tuple(
                        f"uncited_relevant_chunk:{value}"
                        for value in sorted(present_relevant - cited_chunks)
                    ),
                )
            )
    else:
        dimensions.append(_dimension("citation_precision", "not_evaluated"))
        dimensions.append(_dimension("citation_completeness", "not_evaluated"))

    criteria = {item.claim_id: item for item in case.claim_criteria}
    claims = {item.claim_id: item for item in result.claims}
    unsupported: list[str] = []
    matched = 0
    correct = 0
    for claim in result.claims:
        criterion = criteria.get(claim.claim_id)
        if criterion is None:
            unsupported.append(claim.claim_id)
            continue
        matched += 1
        if _criterion_accepts(criterion, claim, anchor_chunks):
            correct += 1
        else:
            unsupported.append(claim.claim_id)
    unsupported_rate = len(unsupported) / len(result.claims) if result.claims else 0.0
    dimensions.append(
        _dimension(
            "unsupported_claim_rate",
            "pass" if not unsupported else "fail",
            numerator=len(unsupported),
            denominator=len(result.claims),
            score=unsupported_rate,
            details=tuple(
                f"unsupported_or_mislabeled_claim:{value}" for value in sorted(unsupported)
            ),
        )
    )
    if unsupported:
        failures.append("unsupported_claim_failure")

    normalized_answer = _match_text(result.answer_text)
    has_answer_text_criterion = bool(case.required_answer_substrings)
    answer_text_ok = all(value in normalized_answer for value in case.required_answer_substrings)
    if case.claim_criteria or has_answer_text_criterion:
        numerator = correct + int(has_answer_text_criterion and answer_text_ok)
        denominator = matched + int(has_answer_text_criterion)
        if denominator == 0:
            correctness = _dimension(
                "answer_correctness",
                "fail",
                numerator=0,
                denominator=1,
                score=0.0,
                details=("no_labeled_claims_matched",),
            )
        else:
            correctness = _ratio(
                "answer_correctness",
                numerator,
                denominator,
                details=(
                    ()
                    if (not has_answer_text_criterion or answer_text_ok)
                    else ("required_answer_substring_missing",)
                ),
            )
    else:
        correctness = _dimension("answer_correctness", "not_evaluated")
    if retrieval_failed and correctness.status == "fail":
        correctness = _dimension(
            "answer_correctness",
            "not_evaluated",
            details=("blocked_by_retrieval_failure",),
        )
    dimensions.append(correctness)
    if correctness.status == "fail":
        failures.append("answer_correctness_failure")

    required_criteria = [item for item in case.claim_criteria if item.required]
    if required_criteria:
        if retrieval_failed:
            completeness = _dimension(
                "answer_completeness",
                "not_evaluated",
                details=("blocked_by_retrieval_failure",),
            )
        else:
            present = sum(item.claim_id in claims for item in required_criteria)
            completeness = _ratio(
                "answer_completeness",
                present,
                len(required_criteria),
                details=tuple(
                    f"missing_required_claim:{item.claim_id}"
                    for item in required_criteria
                    if item.claim_id not in claims
                ),
            )
    else:
        completeness = _dimension("answer_completeness", "not_applicable")
    dimensions.append(completeness)
    if completeness.status == "fail":
        failures.append("answer_completeness_failure")

    limitations = set(result.limitations)
    missing_lims = set(case.required_limitations) - limitations
    disallowed_lims = (
        limitations - set(case.allowed_limitations) if case.allowed_limitations else set()
    )
    limitation_ok = not missing_lims and not disallowed_lims
    dimensions.append(
        _dimension(
            "limitation_disclosure",
            "pass" if limitation_ok else "fail",
            numerator=int(limitation_ok),
            denominator=1,
            score=1.0 if limitation_ok else 0.0,
            details=tuple(
                [
                    *(f"missing_required_limitation:{value}" for value in sorted(missing_lims)),
                    *(f"disallowed_limitation:{value}" for value in sorted(disallowed_lims)),
                ]
            ),
        )
    )
    if not limitation_ok:
        failures.append("answer_correctness_failure")

    expects_insufficient = case.expected_behavior == "insufficient"
    if expects_insufficient or result.status == "insufficient":
        ok = (
            expects_insufficient
            and result.status == "insufficient"
            and all(claim.status == "insufficient" for claim in result.claims)
            and "insufficient_evidence" in limitations
        )
        dimensions.append(
            _dimension(
                "insufficiency_handling",
                "pass" if ok else "fail",
                numerator=int(ok),
                denominator=1,
                score=1.0 if ok else 0.0,
            )
        )
        if not ok:
            failures.append("insufficiency_handling_failure")
    else:
        dimensions.append(_dimension("insufficiency_handling", "not_applicable"))

    has_conflict = any(claim.status == "conflict" for claim in result.claims)
    expects_conflict = case.expected_behavior == "conflict"
    if expects_conflict or has_conflict:
        ok = expects_conflict and has_conflict
        dimensions.append(
            _dimension(
                "conflict_handling",
                "pass" if ok else "fail",
                numerator=int(ok),
                denominator=1,
                score=1.0 if ok else 0.0,
            )
        )
        if not ok:
            failures.append("conflict_handling_failure")
    else:
        dimensions.append(_dimension("conflict_handling", "not_applicable"))

    forbidden_hits = [
        value
        for value in case.forbidden_answer_substrings
        if value in normalized_answer
        or any(value in _match_text(claim.text) for claim in result.claims)
    ]
    if case.forbidden_answer_substrings:
        ok = not forbidden_hits
        dimensions.append(
            _dimension(
                "instruction_compliance",
                "pass" if ok else "fail",
                numerator=int(ok),
                denominator=1,
                score=1.0 if ok else 0.0,
                details=tuple(
                    f"forbidden_answer_substring_present:{value}"
                    for value in sorted(forbidden_hits)
                ),
            )
        )
        if not ok:
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
    calibration_status = "not_applicable" if case.calibration_target is None else "not_evaluated"
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

    failures_tuple = tuple(dict.fromkeys(failures))
    if set(failures_tuple) - _FAILURE_CLASSES:
        raise EvaluationError("unsupported failure classification produced")
    aggregate_status = (
        "pass"
        if not failures_tuple and all(item.status != "fail" for item in dimensions)
        else "fail"
    )
    warnings = [
        "semantic_groundedness_not_evaluated",
        "evaluation_does_not_authorize_memory_promotion",
    ]
    if retrieval_failed:
        warnings.append("answer_dimensions_may_be_blocked_by_retrieval_failure")
    if case.calibration_target is not None:
        warnings.append("uncertainty_calibration_not_evaluated")

    material = {
        "answer_evaluation_contract": contract,
        "evaluator_version": version,
        "evaluator_adapter_id": adapter,
        "golden_case_id": case.case_id,
        "packet_id": packet.packet_id,
        "grounded_result_id": result.result_id,
        "retrieval_id": result.retrieval_id,
        "dimensions": [_dimension_material(item) for item in dimensions],
        "failure_classifications": list(failures_tuple),
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
    digest = _hash(material)
    return EvaluationResult(
        evaluation_id=f"eval_{digest}",
        evaluation_hash=digest,
        answer_evaluation_contract=contract,
        evaluator_version=version,
        evaluator_adapter_id=adapter,
        golden_case_id=case.case_id,
        packet_id=packet.packet_id,
        grounded_result_id=result.result_id,
        retrieval_id=result.retrieval_id,
        dimensions=tuple(dimensions),
        failure_classifications=failures_tuple,
        aggregate_status=aggregate_status,
        warnings=tuple(warnings),
        errors=(),
        semantic_groundedness_status="not_evaluated",
        uncertainty_calibration_status=calibration_status,
        semantic_support_verified=False,
        claim_coverage_verified=False,
    )


def _dimension_named(result: EvaluationResult, name: str) -> EvaluationDimension | None:
    return next((item for item in result.dimensions if item.name == name), None)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def aggregate_evaluation_results(
    results: tuple[EvaluationResult, ...] | list[EvaluationResult],
) -> EvaluationAggregate:
    if not isinstance(results, (tuple, list)) or not results:
        raise EvaluationError("results must contain at least one EvaluationResult")
    normalized: list[EvaluationResult] = []
    seen: set[str] = set()
    for item in results:
        if not isinstance(item, EvaluationResult):
            raise EvaluationError("results must contain EvaluationResult values")
        if item.evaluation_id in seen:
            raise EvaluationError("evaluation ids must be unique in an aggregate")
        if item.answer_evaluation_contract != ANSWER_EVALUATION_CONTRACT:
            raise EvaluationError("aggregate contains unsupported evaluation contract")
        seen.add(item.evaluation_id)
        normalized.append(item)
    normalized.sort(key=lambda item: item.evaluation_id)

    buckets: dict[str, list[float]] = {
        "citation_precision": [],
        "citation_completeness": [],
        "unsupported_claim_rate": [],
        "insufficiency_handling": [],
        "conflict_handling": [],
    }
    for result in normalized:
        for name, bucket in buckets.items():
            dimension = _dimension_named(result, name)
            if dimension is not None and dimension.score is not None:
                bucket.append(dimension.score)

    total = len(normalized)
    passed = sum(item.aggregate_status == "pass" for item in normalized)
    retrieval_failures = sum(
        "retrieval_failure" in item.failure_classifications for item in normalized
    )
    answer_classes = _FAILURE_CLASSES - {
        "retrieval_failure",
        "evaluator_unavailable",
        "evaluator_disagreement",
        "unknown",
    }
    answer_failures = sum(
        bool(set(item.failure_classifications) & answer_classes) for item in normalized
    )
    material = {
        "evaluation_ids": [item.evaluation_id for item in normalized],
        "total_cases": total,
        "passed_cases": passed,
        "case_pass_rate": passed / total,
        "mean_citation_precision": _mean(buckets["citation_precision"]),
        "mean_citation_completeness": _mean(buckets["citation_completeness"]),
        "mean_unsupported_claim_rate": _mean(buckets["unsupported_claim_rate"]),
        "insufficiency_accuracy": _mean(buckets["insufficiency_handling"]),
        "conflict_accuracy": _mean(buckets["conflict_handling"]),
        "retrieval_failure_rate": retrieval_failures / total,
        "answer_failure_rate": answer_failures / total,
    }
    return EvaluationAggregate(
        aggregate_id=_id("evalagg_", material),
        evaluation_ids=tuple(item.evaluation_id for item in normalized),
        total_cases=total,
        passed_cases=passed,
        case_pass_rate=passed / total,
        mean_citation_precision=material["mean_citation_precision"],
        mean_citation_completeness=material["mean_citation_completeness"],
        mean_unsupported_claim_rate=material["mean_unsupported_claim_rate"],
        insufficiency_accuracy=material["insufficiency_accuracy"],
        conflict_accuracy=material["conflict_accuracy"],
        retrieval_failure_rate=retrieval_failures / total,
        answer_failure_rate=answer_failures / total,
    )
