"""Deterministic Phase 10 verified-lesson retention for Roberta.

This module proves a narrow, provider-neutral retention contract. It accepts only
canonical Phase 9 ``verified_for_learning`` results, builds complete store/source
snapshots for a procedural answer-quality scope, requires an authenticated human
approval produced by Roberta's existing approval runtime, and stores only
in-memory Phase 10 records. It has no HXMP, wallet, transaction, source-truth,
governance, CMIS/provider-trust, or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from roberta.approval.contracts import ApprovalRequest
from roberta.approval.runtime import AuthenticatedApprovalContext

from .evaluation import EvaluationResult, GoldenEvaluationCase
from .grounding import EvidencePacket, GroundedAnswerResult
from .reflection import LearningCandidateBundle
from .source_ingestion import SourceRecord, SourceStore
from .verification import (
    CandidateVerificationResult,
    VerificationError,
    validate_candidate_verification_result,
)


RETENTION_CONTRACT = "verified-lesson-retention/v1"
VERIFIED_LESSON_CONTRACT = "verified-lesson/v1"
CONTRADICTION_SCOPE_CONTRACT = "verified-lesson-contradiction-scope/v1"
RETENTION_VERSION = "1.0.0"
RETENTION_APPROVAL_ACTION = "retain_verified_lesson"
PROCEDURAL_LESSON_TYPE = "procedural_answer_quality"
PROCEDURAL_LESSON_DOMAIN = "roberta_learning_system"

_PROPOSAL_STATUSES = frozenset(
    {"approval_required", "duplicate", "rejected", "inconclusive"}
)
_DECISION_STATUSES = frozenset({"retained", "duplicate", "rejected", "inconclusive"})
_LIFECYCLE_STATES = frozenset({"active", "superseded", "revoked"})


class RetentionError(ValueError):
    """Raised when Phase 10 retention material fails closed."""


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
        raise RetentionError(
            "retention material must be canonical JSON-compatible data"
        ) from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise RetentionError(f"{name} must be a normalized non-empty string")
    return value


def _sha256_hex(name: str, value: Any) -> str:
    text = _text(name, value).lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise RetentionError(f"{name} must be a 64-character hex digest")
    return text


@dataclass(frozen=True, slots=True)
class ProceduralLessonScope:
    scope_id: str
    scope_hash: str
    lesson_type: str
    domain: str
    failure_classifications: tuple[str, ...]
    diagnosed_layers: tuple[str, ...]
    source_ids: tuple[str, ...]

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SourceScopeMember:
    source_id: str
    version: str
    content_hash: str
    artifact_ref: str
    authority_class: str
    approval_status: str
    status: str


@dataclass(frozen=True, slots=True)
class RetentionContradictionSnapshot:
    snapshot_id: str
    snapshot_hash: str
    contradiction_scope_contract: str
    retention_version: str
    store_revision: int
    scope_id: str
    source_members: tuple[SourceScopeMember, ...]
    active_lesson_ids: tuple[str, ...]
    active_lesson_hashes: tuple[str, ...]
    active_lifecycle_state_ids: tuple[str, ...]
    conflict_evidence_ids: tuple[str, ...]
    contradiction_status: str
    complete: bool

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class VerifiedLessonLifecycleState:
    state_id: str
    state_hash: str
    lesson_id: str
    state: str
    previous_state_id: str | None
    reason: str
    superseded_by_lesson_id: str | None

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class VerifiedLessonRecord:
    lesson_id: str
    lesson_hash: str
    verified_lesson_contract: str
    retention_version: str
    lesson_key: str
    lesson_type: str
    scope_id: str
    failure_classifications: tuple[str, ...]
    diagnosed_layers: tuple[str, ...]
    source_ids: tuple[str, ...]
    lesson_body: str
    body_origin: str
    verification_refs: tuple[tuple[str, str | None], ...]
    verification_checks: tuple[tuple[str, str, str], ...]
    contradiction_snapshot_id: str
    confidence_basis: tuple[str, ...]
    approval_request_id: str
    approval_proposal_sha256: str
    approval_binding_sha256: str
    approval_thread_id: str
    human_principal_id: str
    initial_lifecycle_state_id: str
    created_by: str
    producer_version: str

    @property
    def verified(self) -> bool:
        return True

    @property
    def trusted_within_recorded_scope(self) -> bool:
        return True

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def live_state_authorized(self) -> bool:
        return False

    @property
    def governance_mutation_authorized(self) -> bool:
        return False

    @property
    def provider_trust_mutation_authorized(self) -> bool:
        return False

    @property
    def external_memory_write_authorized(self) -> bool:
        return False

    @property
    def wallet_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RetentionProposal:
    proposal_id: str
    proposal_hash: str
    retention_contract: str
    retention_version: str
    status: str
    lesson_id: str
    lesson_key: str
    scope: ProceduralLessonScope
    contradiction_snapshot: RetentionContradictionSnapshot | None
    duplicate_lesson_id: str | None
    confidence_basis: tuple[str, ...]
    verification_id: str
    approval_request: ApprovalRequest | None
    reasons: tuple[str, ...]

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def external_memory_write_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RetentionDecision:
    decision_id: str
    decision_hash: str
    retention_contract: str
    retention_version: str
    proposal_id: str
    status: str
    lesson_id: str | None
    duplicate_lesson_id: str | None
    contradiction_snapshot_id: str | None
    approval_binding_sha256: str | None
    approval_thread_id: str | None
    human_principal_id: str | None
    reasons: tuple[str, ...]
    created_by: str
    producer_version: str

    @property
    def source_truth_authorized(self) -> bool:
        return False

    @property
    def external_memory_write_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RetentionResult:
    decision: RetentionDecision
    lesson: VerifiedLessonRecord | None
    lifecycle: VerifiedLessonLifecycleState | None


def _scope_material(scope: ProceduralLessonScope) -> dict[str, Any]:
    return {
        "lesson_type": scope.lesson_type,
        "domain": scope.domain,
        "failure_classifications": list(scope.failure_classifications),
        "diagnosed_layers": list(scope.diagnosed_layers),
        "source_ids": list(scope.source_ids),
    }


def _make_scope(bundle: LearningCandidateBundle) -> ProceduralLessonScope:
    candidate = bundle.candidate
    failures = tuple(sorted(set(candidate.failure_classifications)))
    layers = tuple(sorted(set(candidate.diagnosed_layers)))
    source_ids = tuple(sorted({ref.source_id for ref in candidate.evidence_references}))
    if not failures:
        raise RetentionError("procedural retention requires failure classifications")
    if not layers:
        raise RetentionError("procedural retention requires diagnosed layers")
    if not source_ids:
        raise RetentionError("procedural retention requires exact source identities")
    material = {
        "lesson_type": PROCEDURAL_LESSON_TYPE,
        "domain": PROCEDURAL_LESSON_DOMAIN,
        "failure_classifications": list(failures),
        "diagnosed_layers": list(layers),
        "source_ids": list(source_ids),
    }
    digest = _hash(material)
    return ProceduralLessonScope(
        scope_id=f"lscope_{digest}",
        scope_hash=digest,
        lesson_type=PROCEDURAL_LESSON_TYPE,
        domain=PROCEDURAL_LESSON_DOMAIN,
        failure_classifications=failures,
        diagnosed_layers=layers,
        source_ids=source_ids,
    )


def _source_member(store: SourceStore, source_id: str) -> SourceScopeMember:
    record = store.get_source(source_id)
    if not isinstance(record, SourceRecord):
        raise RetentionError(f"required source {source_id!r} is unavailable")
    if record.approval_status != "approved" or record.status != "approved":
        raise RetentionError(
            f"required source {source_id!r} is not an active approved source"
        )
    artifact = store.get_artifact(record.artifact_ref)
    if artifact is None:
        raise RetentionError(f"required source artifact {record.artifact_ref!r} is unavailable")
    observed = hashlib.sha256(bytes(artifact)).hexdigest()
    if observed != record.content_hash:
        raise RetentionError(f"required source {source_id!r} failed artifact hash validation")
    return SourceScopeMember(
        source_id=record.source_id,
        version=record.version,
        content_hash=record.content_hash,
        artifact_ref=record.artifact_ref,
        authority_class=record.authority_class,
        approval_status=record.approval_status,
        status=record.status,
    )


def _source_member_material(member: SourceScopeMember) -> dict[str, Any]:
    return {
        "source_id": member.source_id,
        "version": member.version,
        "content_hash": member.content_hash,
        "artifact_ref": member.artifact_ref,
        "authority_class": member.authority_class,
        "approval_status": member.approval_status,
        "status": member.status,
    }


def _lesson_key(scope: ProceduralLessonScope, lesson_body: str) -> str:
    body = _text("lesson_body", lesson_body)
    return _hash(
        {
            "lesson_type": scope.lesson_type,
            "scope_id": scope.scope_id,
            "lesson_body": body,
        }
    )


def _scopes_overlap(record: VerifiedLessonRecord, scope: ProceduralLessonScope) -> bool:
    if record.lesson_type != scope.lesson_type:
        return False
    return bool(set(record.diagnosed_layers).intersection(scope.diagnosed_layers))


def _lifecycle_material(
    *,
    lesson_id: str,
    state: str,
    previous_state_id: str | None,
    reason: str,
    superseded_by_lesson_id: str | None,
) -> dict[str, Any]:
    return {
        "lesson_id": lesson_id,
        "state": state,
        "previous_state_id": previous_state_id,
        "reason": reason,
        "superseded_by_lesson_id": superseded_by_lesson_id,
    }


def _make_lifecycle_state(
    *,
    lesson_id: str,
    state: str,
    previous_state_id: str | None,
    reason: str,
    superseded_by_lesson_id: str | None = None,
) -> VerifiedLessonLifecycleState:
    if state not in _LIFECYCLE_STATES:
        raise RetentionError(f"unsupported lesson lifecycle state {state!r}")
    normalized_reason = _text("lifecycle reason", reason)
    if state == "superseded":
        if superseded_by_lesson_id is None:
            raise RetentionError("superseded lifecycle state requires superseding lesson id")
        _text("superseded_by_lesson_id", superseded_by_lesson_id)
    elif superseded_by_lesson_id is not None:
        raise RetentionError("superseded_by_lesson_id is valid only for superseded state")
    material = _lifecycle_material(
        lesson_id=_text("lesson_id", lesson_id),
        state=state,
        previous_state_id=previous_state_id,
        reason=normalized_reason,
        superseded_by_lesson_id=superseded_by_lesson_id,
    )
    digest = _hash(material)
    return VerifiedLessonLifecycleState(
        state_id=f"lstate_{digest}",
        state_hash=digest,
        lesson_id=lesson_id,
        state=state,
        previous_state_id=previous_state_id,
        reason=normalized_reason,
        superseded_by_lesson_id=superseded_by_lesson_id,
    )


class InMemoryVerifiedLessonStore:
    """Provider-neutral Phase 10 store; intentionally not durable persistence."""

    def __init__(self) -> None:
        self._lessons: dict[str, VerifiedLessonRecord] = {}
        self._latest_lifecycle: dict[str, VerifiedLessonLifecycleState] = {}
        self._lifecycle_history: dict[str, list[VerifiedLessonLifecycleState]] = {}
        self._decisions: dict[str, RetentionDecision] = {}
        self._consumed_approvals: set[str] = set()
        self._conflicts: dict[str, set[str]] = {}
        self._revision = 0

    @property
    def revision(self) -> int:
        return self._revision

    def get_lesson(self, lesson_id: str) -> VerifiedLessonRecord | None:
        return self._lessons.get(lesson_id)

    def get_latest_lifecycle(
        self, lesson_id: str
    ) -> VerifiedLessonLifecycleState | None:
        return self._latest_lifecycle.get(lesson_id)

    def lifecycle_history(
        self, lesson_id: str
    ) -> tuple[VerifiedLessonLifecycleState, ...]:
        return tuple(self._lifecycle_history.get(lesson_id, ()))

    def get_decision(self, decision_id: str) -> RetentionDecision | None:
        return self._decisions.get(decision_id)

    def approval_consumed(self, binding_sha256: str) -> bool:
        return binding_sha256 in self._consumed_approvals

    def active_lessons_for_scope(
        self, scope: ProceduralLessonScope
    ) -> tuple[tuple[VerifiedLessonRecord, VerifiedLessonLifecycleState], ...]:
        output: list[tuple[VerifiedLessonRecord, VerifiedLessonLifecycleState]] = []
        for lesson_id, record in self._lessons.items():
            state = self._latest_lifecycle.get(lesson_id)
            if state is None or state.state != "active":
                continue
            if _scopes_overlap(record, scope):
                output.append((record, state))
        return tuple(sorted(output, key=lambda item: item[0].lesson_id))

    def record_conflict_evidence(self, *, lesson_key: str, evidence_id: str) -> None:
        """Record blocking contradiction evidence; this can never authorize retention."""

        key = _sha256_hex("lesson_key", lesson_key)
        evidence = _text("evidence_id", evidence_id)
        values = self._conflicts.setdefault(key, set())
        if evidence not in values:
            values.add(evidence)
            self._revision += 1

    def conflict_evidence_for(self, lesson_key: str) -> tuple[str, ...]:
        return tuple(sorted(self._conflicts.get(lesson_key, ())))

    def record_nonretained_decision(self, decision: RetentionDecision) -> None:
        if decision.status == "retained":
            raise RetentionError("retained decisions require atomic lesson commit")
        existing = self._decisions.get(decision.decision_id)
        if existing is not None and existing != decision:
            raise RetentionError("conflicting immutable retention decision")
        self._decisions.setdefault(decision.decision_id, decision)

    def commit_retention(
        self,
        *,
        lesson: VerifiedLessonRecord,
        lifecycle: VerifiedLessonLifecycleState,
        decision: RetentionDecision,
    ) -> None:
        if decision.status != "retained":
            raise RetentionError("atomic retention commit requires retained decision")
        if decision.lesson_id != lesson.lesson_id:
            raise RetentionError("retention decision/lesson identity mismatch")
        if lifecycle.lesson_id != lesson.lesson_id or lifecycle.state != "active":
            raise RetentionError("retention commit requires exact initial active lifecycle")
        if lifecycle.state_id != lesson.initial_lifecycle_state_id:
            raise RetentionError("lesson/lifecycle identity mismatch")
        if decision.approval_binding_sha256 is None:
            raise RetentionError("retained decision requires approval binding")
        if self.approval_consumed(decision.approval_binding_sha256):
            raise RetentionError("retention approval binding has already been consumed")
        if lesson.lesson_id in self._lessons:
            raise RetentionError("verified lesson identity already exists")
        if decision.decision_id in self._decisions:
            raise RetentionError("retention decision identity already exists")

        self._lessons[lesson.lesson_id] = lesson
        self._latest_lifecycle[lesson.lesson_id] = lifecycle
        self._lifecycle_history[lesson.lesson_id] = [lifecycle]
        self._decisions[decision.decision_id] = decision
        self._consumed_approvals.add(decision.approval_binding_sha256)
        self._revision += 1

    def transition_lifecycle(
        self,
        *,
        lesson_id: str,
        state: str,
        reason: str,
        superseded_by_lesson_id: str | None = None,
    ) -> VerifiedLessonLifecycleState:
        record = self._lessons.get(lesson_id)
        current = self._latest_lifecycle.get(lesson_id)
        if record is None or current is None:
            raise RetentionError("verified lesson is unavailable for lifecycle transition")
        if current.state != "active":
            raise RetentionError("only an active verified lesson may transition lifecycle")
        if state not in {"superseded", "revoked"}:
            raise RetentionError("Phase 10 lifecycle transition must supersede or revoke")
        if state == "superseded":
            if superseded_by_lesson_id == lesson_id:
                raise RetentionError("a verified lesson cannot supersede itself")
            if self._lessons.get(str(superseded_by_lesson_id)) is None:
                raise RetentionError("superseding verified lesson must already exist")
        next_state = _make_lifecycle_state(
            lesson_id=lesson_id,
            state=state,
            previous_state_id=current.state_id,
            reason=reason,
            superseded_by_lesson_id=superseded_by_lesson_id,
        )
        self._latest_lifecycle[lesson_id] = next_state
        self._lifecycle_history[lesson_id].append(next_state)
        self._revision += 1
        return next_state


def build_contradiction_snapshot(
    *,
    store: InMemoryVerifiedLessonStore,
    source_store: SourceStore,
    scope: ProceduralLessonScope,
    lesson_key: str,
) -> RetentionContradictionSnapshot:
    """Build a complete provider-owned snapshot for the exact proposed lesson scope."""

    if not isinstance(store, InMemoryVerifiedLessonStore):
        raise RetentionError("Phase 10 v1 requires InMemoryVerifiedLessonStore")
    if not isinstance(scope, ProceduralLessonScope):
        raise RetentionError("scope must be ProceduralLessonScope")
    key = _sha256_hex("lesson_key", lesson_key)

    source_members = tuple(_source_member(source_store, sid) for sid in scope.source_ids)
    if tuple(member.source_id for member in source_members) != scope.source_ids:
        raise RetentionError("source scope enumeration is incomplete or out of order")

    active = store.active_lessons_for_scope(scope)
    active_ids = tuple(record.lesson_id for record, _ in active)
    active_hashes = tuple(record.lesson_hash for record, _ in active)
    lifecycle_ids = tuple(state.state_id for _, state in active)
    conflicts = store.conflict_evidence_for(key)

    nonidentical_overlap = any(record.lesson_key != key for record, _ in active)
    if conflicts:
        contradiction_status = "conflict"
    elif nonidentical_overlap:
        contradiction_status = "inconclusive"
    else:
        contradiction_status = "clear"

    material = {
        "contradiction_scope_contract": CONTRADICTION_SCOPE_CONTRACT,
        "retention_version": RETENTION_VERSION,
        "store_revision": store.revision,
        "scope_id": scope.scope_id,
        "source_members": [_source_member_material(item) for item in source_members],
        "active_lesson_ids": list(active_ids),
        "active_lesson_hashes": list(active_hashes),
        "active_lifecycle_state_ids": list(lifecycle_ids),
        "conflict_evidence_ids": list(conflicts),
        "contradiction_status": contradiction_status,
        "complete": True,
    }
    digest = _hash(material)
    return RetentionContradictionSnapshot(
        snapshot_id=f"csnap_{digest}",
        snapshot_hash=digest,
        contradiction_scope_contract=CONTRADICTION_SCOPE_CONTRACT,
        retention_version=RETENTION_VERSION,
        store_revision=store.revision,
        scope_id=scope.scope_id,
        source_members=source_members,
        active_lesson_ids=active_ids,
        active_lesson_hashes=active_hashes,
        active_lifecycle_state_ids=lifecycle_ids,
        conflict_evidence_ids=conflicts,
        contradiction_status=contradiction_status,
        complete=True,
    )


def _verification_refs(
    result: CandidateVerificationResult,
) -> tuple[tuple[str, str | None], ...]:
    return (
        ("verification_id", result.verification_id),
        ("bundle_id", result.bundle_id),
        ("candidate_id", result.candidate_id),
        ("candidate_state_id", result.candidate_state_id),
        ("reflection_id", result.reflection_id),
        ("verification_plan_id", result.verification_plan_id),
        ("original_evaluation_id", result.original_evaluation_id),
        ("golden_case_id", result.golden_case_id),
        ("packet_id", result.packet_id),
        ("grounded_result_id", result.grounded_result_id),
        ("retrieval_id", result.retrieval_id),
        ("retest_golden_case_id", result.retest_golden_case_id),
        ("retest_packet_id", result.retest_packet_id),
        ("retest_grounded_result_id", result.retest_grounded_result_id),
        ("retest_retrieval_id", result.retest_retrieval_id),
        ("retest_evaluation_id", result.retest_evaluation_id),
    )


def _approval_payload(
    *,
    bundle: LearningCandidateBundle,
    verification: CandidateVerificationResult,
    scope: ProceduralLessonScope,
    lesson_id: str,
    lesson_key: str,
    snapshot: RetentionContradictionSnapshot,
    confidence_basis: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "retention_contract": RETENTION_CONTRACT,
        "retention_version": RETENTION_VERSION,
        "verified_lesson_contract": VERIFIED_LESSON_CONTRACT,
        "lesson_id": lesson_id,
        "lesson_key": lesson_key,
        "lesson_type": scope.lesson_type,
        "scope_id": scope.scope_id,
        "scope": _scope_material(scope),
        "lesson_body": bundle.candidate.lesson_text,
        "lesson_body_origin": "generated_candidate",
        "verification_refs": [[name, value] for name, value in _verification_refs(verification)],
        "verification_checks": [
            [item.check_id, item.check_kind, item.status] for item in verification.checks
        ],
        "contradiction_snapshot_id": snapshot.snapshot_id,
        "contradiction_result": snapshot.contradiction_status,
        "duplicate_result": "none",
        "confidence_basis": list(confidence_basis),
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "provider_trust_mutation_authorized": False,
        "external_memory_write_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def _proposal_material(
    *,
    status: str,
    lesson_id: str,
    lesson_key: str,
    scope: ProceduralLessonScope,
    snapshot: RetentionContradictionSnapshot | None,
    duplicate_lesson_id: str | None,
    confidence_basis: tuple[str, ...],
    verification_id: str,
    approval_request: ApprovalRequest | None,
    reasons: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "retention_contract": RETENTION_CONTRACT,
        "retention_version": RETENTION_VERSION,
        "status": status,
        "lesson_id": lesson_id,
        "lesson_key": lesson_key,
        "scope_id": scope.scope_id,
        "contradiction_snapshot_id": None if snapshot is None else snapshot.snapshot_id,
        "duplicate_lesson_id": duplicate_lesson_id,
        "confidence_basis": list(confidence_basis),
        "verification_id": verification_id,
        "approval_request": (
            None
            if approval_request is None
            else {
                "request_id": approval_request.request_id,
                "action_type": approval_request.action_type,
                "scope": list(approval_request.scope),
                "proposal_sha256": approval_request.proposal_sha256,
                "binding_sha256": approval_request.binding_sha256,
            }
        ),
        "reasons": list(reasons),
    }


def _make_proposal(
    *,
    status: str,
    lesson_id: str,
    lesson_key: str,
    scope: ProceduralLessonScope,
    snapshot: RetentionContradictionSnapshot | None,
    duplicate_lesson_id: str | None,
    confidence_basis: tuple[str, ...],
    verification_id: str,
    approval_request: ApprovalRequest | None,
    reasons: tuple[str, ...],
) -> RetentionProposal:
    if status not in _PROPOSAL_STATUSES:
        raise RetentionError(f"unsupported retention proposal status {status!r}")
    material = _proposal_material(
        status=status,
        lesson_id=lesson_id,
        lesson_key=lesson_key,
        scope=scope,
        snapshot=snapshot,
        duplicate_lesson_id=duplicate_lesson_id,
        confidence_basis=confidence_basis,
        verification_id=verification_id,
        approval_request=approval_request,
        reasons=reasons,
    )
    digest = _hash(material)
    return RetentionProposal(
        proposal_id=f"rprop_{digest}",
        proposal_hash=digest,
        retention_contract=RETENTION_CONTRACT,
        retention_version=RETENTION_VERSION,
        status=status,
        lesson_id=lesson_id,
        lesson_key=lesson_key,
        scope=scope,
        contradiction_snapshot=snapshot,
        duplicate_lesson_id=duplicate_lesson_id,
        confidence_basis=confidence_basis,
        verification_id=verification_id,
        approval_request=approval_request,
        reasons=reasons,
    )


def build_retention_proposal(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    bundle: LearningCandidateBundle,
    retest_packet: EvidencePacket | None,
    retest_grounded_result: GroundedAnswerResult | None,
    verification_result: CandidateVerificationResult,
    source_store: SourceStore,
    retention_store: InMemoryVerifiedLessonStore,
    approval_request_id: str,
) -> RetentionProposal:
    """Revalidate Phase 8/9 and build the exact proposal a human may review."""

    if not isinstance(retention_store, InMemoryVerifiedLessonStore):
        raise RetentionError("Phase 10 v1 requires InMemoryVerifiedLessonStore")
    request_id = _text("approval_request_id", approval_request_id)

    try:
        verification = validate_candidate_verification_result(
            packet=packet,
            grounded_result=grounded_result,
            golden_case=golden_case,
            evaluation=evaluation,
            bundle=bundle,
            retest_packet=retest_packet,
            retest_grounded_result=retest_grounded_result,
            result=verification_result,
        )
    except VerificationError as exc:
        raise RetentionError("canonical Phase 9 verification revalidation failed") from exc

    scope = _make_scope(bundle)
    key = _lesson_key(scope, bundle.candidate.lesson_text)
    lesson_id = f"vlesson_{key}"
    confidence_basis = (
        f"candidate_verification_status:{verification.status}",
        "calibrated_probability:unavailable",
    )

    if verification.status != "verified_for_learning":
        return _make_proposal(
            status="rejected",
            lesson_id=lesson_id,
            lesson_key=key,
            scope=scope,
            snapshot=None,
            duplicate_lesson_id=None,
            confidence_basis=confidence_basis,
            verification_id=verification.verification_id,
            approval_request=None,
            reasons=(f"candidate_verification_status:{verification.status}",),
        )

    try:
        snapshot = build_contradiction_snapshot(
            store=retention_store,
            source_store=source_store,
            scope=scope,
            lesson_key=key,
        )
    except RetentionError as exc:
        return _make_proposal(
            status="inconclusive",
            lesson_id=lesson_id,
            lesson_key=key,
            scope=scope,
            snapshot=None,
            duplicate_lesson_id=None,
            confidence_basis=confidence_basis,
            verification_id=verification.verification_id,
            approval_request=None,
            reasons=(f"contradiction_scope_unavailable:{exc}",),
        )

    existing = retention_store.get_lesson(lesson_id)
    if existing is not None:
        lifecycle = retention_store.get_latest_lifecycle(lesson_id)
        if lifecycle is not None and lifecycle.state == "active":
            return _make_proposal(
                status="duplicate",
                lesson_id=lesson_id,
                lesson_key=key,
                scope=scope,
                snapshot=snapshot,
                duplicate_lesson_id=lesson_id,
                confidence_basis=confidence_basis,
                verification_id=verification.verification_id,
                approval_request=None,
                reasons=("exact_active_verified_lesson_duplicate",),
            )
        return _make_proposal(
            status="inconclusive",
            lesson_id=lesson_id,
            lesson_key=key,
            scope=scope,
            snapshot=snapshot,
            duplicate_lesson_id=lesson_id,
            confidence_basis=confidence_basis,
            verification_id=verification.verification_id,
            approval_request=None,
            reasons=("matching_verified_lesson_is_not_active",),
        )

    if snapshot.contradiction_status == "conflict":
        return _make_proposal(
            status="rejected",
            lesson_id=lesson_id,
            lesson_key=key,
            scope=scope,
            snapshot=snapshot,
            duplicate_lesson_id=None,
            confidence_basis=confidence_basis,
            verification_id=verification.verification_id,
            approval_request=None,
            reasons=("explicit_contradiction_evidence_present",),
        )
    if snapshot.contradiction_status != "clear":
        return _make_proposal(
            status="inconclusive",
            lesson_id=lesson_id,
            lesson_key=key,
            scope=scope,
            snapshot=snapshot,
            duplicate_lesson_id=None,
            confidence_basis=confidence_basis,
            verification_id=verification.verification_id,
            approval_request=None,
            reasons=("nonidentical_active_scope_requires_future_contradiction_capability",),
        )

    approval_payload = _approval_payload(
        bundle=bundle,
        verification=verification,
        scope=scope,
        lesson_id=lesson_id,
        lesson_key=key,
        snapshot=snapshot,
        confidence_basis=confidence_basis,
    )
    request = ApprovalRequest(
        request_id=request_id,
        action_type=RETENTION_APPROVAL_ACTION,
        summary="Retain one exact verified procedural learning lesson in the Phase 10 in-memory store.",
        scope=(
            f"retention_contract:{RETENTION_CONTRACT}",
            f"lesson_type:{scope.lesson_type}",
            f"scope_id:{scope.scope_id}",
        ),
        proposal=approval_payload,
        policy_reasons=(
            "Phase 9 verification alone does not authorize retention.",
            "Phase 10 requires exact human review of the content-bound retention proposal.",
        ),
        evidence_summary=(
            f"verification_id:{verification.verification_id}",
            f"contradiction_snapshot_id:{snapshot.snapshot_id}",
        ),
    )
    return _make_proposal(
        status="approval_required",
        lesson_id=lesson_id,
        lesson_key=key,
        scope=scope,
        snapshot=snapshot,
        duplicate_lesson_id=None,
        confidence_basis=confidence_basis,
        verification_id=verification.verification_id,
        approval_request=request,
        reasons=("all_deterministic_retention_gates_passed_pending_human_approval",),
    )


def _decision_material(
    *,
    proposal: RetentionProposal,
    status: str,
    lesson_id: str | None,
    approval_binding_sha256: str | None,
    approval_thread_id: str | None,
    human_principal_id: str | None,
    reasons: tuple[str, ...],
    created_by: str,
    producer_version: str,
    lesson_hash: str | None = None,
) -> dict[str, Any]:
    return {
        "retention_contract": RETENTION_CONTRACT,
        "retention_version": RETENTION_VERSION,
        "proposal_id": proposal.proposal_id,
        "status": status,
        "lesson_id": lesson_id,
        "lesson_hash": lesson_hash,
        "duplicate_lesson_id": proposal.duplicate_lesson_id,
        "contradiction_snapshot_id": (
            None
            if proposal.contradiction_snapshot is None
            else proposal.contradiction_snapshot.snapshot_id
        ),
        "approval_binding_sha256": approval_binding_sha256,
        "approval_thread_id": approval_thread_id,
        "human_principal_id": human_principal_id,
        "reasons": list(reasons),
        "created_by": created_by,
        "producer_version": producer_version,
    }


def _make_decision(
    *,
    proposal: RetentionProposal,
    status: str,
    lesson_id: str | None,
    approval_binding_sha256: str | None,
    approval_thread_id: str | None,
    human_principal_id: str | None,
    reasons: tuple[str, ...],
    created_by: str,
    producer_version: str,
    lesson_hash: str | None = None,
) -> RetentionDecision:
    if status not in _DECISION_STATUSES:
        raise RetentionError(f"unsupported retention decision status {status!r}")
    author = _text("created_by", created_by)
    producer = _text("producer_version", producer_version)
    material = _decision_material(
        proposal=proposal,
        status=status,
        lesson_id=lesson_id,
        approval_binding_sha256=approval_binding_sha256,
        approval_thread_id=approval_thread_id,
        human_principal_id=human_principal_id,
        reasons=reasons,
        created_by=author,
        producer_version=producer,
        lesson_hash=lesson_hash,
    )
    digest = _hash(material)
    return RetentionDecision(
        decision_id=f"rdec_{digest}",
        decision_hash=digest,
        retention_contract=RETENTION_CONTRACT,
        retention_version=RETENTION_VERSION,
        proposal_id=proposal.proposal_id,
        status=status,
        lesson_id=lesson_id,
        duplicate_lesson_id=proposal.duplicate_lesson_id,
        contradiction_snapshot_id=(
            None
            if proposal.contradiction_snapshot is None
            else proposal.contradiction_snapshot.snapshot_id
        ),
        approval_binding_sha256=approval_binding_sha256,
        approval_thread_id=approval_thread_id,
        human_principal_id=human_principal_id,
        reasons=reasons,
        created_by=author,
        producer_version=producer,
    )


def _lesson_record_material(
    *,
    proposal: RetentionProposal,
    bundle: LearningCandidateBundle,
    verification: CandidateVerificationResult,
    approval: AuthenticatedApprovalContext,
    lifecycle: VerifiedLessonLifecycleState,
    created_by: str,
    producer_version: str,
) -> dict[str, Any]:
    request = approval.request
    return {
        "verified_lesson_contract": VERIFIED_LESSON_CONTRACT,
        "retention_version": RETENTION_VERSION,
        "lesson_id": proposal.lesson_id,
        "lesson_key": proposal.lesson_key,
        "lesson_type": proposal.scope.lesson_type,
        "scope_id": proposal.scope.scope_id,
        "failure_classifications": list(proposal.scope.failure_classifications),
        "diagnosed_layers": list(proposal.scope.diagnosed_layers),
        "source_ids": list(proposal.scope.source_ids),
        "lesson_body": bundle.candidate.lesson_text,
        "body_origin": "generated_candidate",
        "verification_refs": [[name, value] for name, value in _verification_refs(verification)],
        "verification_checks": [
            [item.check_id, item.check_kind, item.status] for item in verification.checks
        ],
        "contradiction_snapshot_id": proposal.contradiction_snapshot.snapshot_id,
        "confidence_basis": list(proposal.confidence_basis),
        "approval_request_id": request.request_id,
        "approval_proposal_sha256": request.proposal_sha256,
        "approval_binding_sha256": request.binding_sha256,
        "approval_thread_id": approval.thread_id,
        "human_principal_id": approval.human_principal_id,
        "initial_lifecycle_state_id": lifecycle.state_id,
        "created_by": created_by,
        "producer_version": producer_version,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "provider_trust_mutation_authorized": False,
        "external_memory_write_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def finalize_retention(
    *,
    packet: EvidencePacket,
    grounded_result: GroundedAnswerResult,
    golden_case: GoldenEvaluationCase,
    evaluation: EvaluationResult,
    bundle: LearningCandidateBundle,
    retest_packet: EvidencePacket | None,
    retest_grounded_result: GroundedAnswerResult | None,
    verification_result: CandidateVerificationResult,
    source_store: SourceStore,
    retention_store: InMemoryVerifiedLessonStore,
    proposal: RetentionProposal,
    approval: AuthenticatedApprovalContext | None,
    created_by: str,
    producer_version: str,
) -> RetentionResult:
    """Rebuild every gate and finalize at most one exact in-memory verified lesson."""

    if not isinstance(proposal, RetentionProposal):
        raise RetentionError("proposal must be RetentionProposal")
    if (
        proposal.approval_request is not None
        and retention_store.approval_consumed(proposal.approval_request.binding_sha256)
    ):
        raise RetentionError("retention approval binding has already been consumed")
    request_id = (
        proposal.approval_request.request_id
        if proposal.approval_request is not None
        else f"blocked-{proposal.proposal_id}"
    )
    rebuilt = build_retention_proposal(
        packet=packet,
        grounded_result=grounded_result,
        golden_case=golden_case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=retest_packet,
        retest_grounded_result=retest_grounded_result,
        verification_result=verification_result,
        source_store=source_store,
        retention_store=retention_store,
        approval_request_id=request_id,
    )
    if rebuilt != proposal:
        raise RetentionError("retention proposal no longer matches exact current gate state")

    author = _text("created_by", created_by)
    producer = _text("producer_version", producer_version)

    if proposal.status != "approval_required":
        if approval is not None:
            raise RetentionError("blocked/nonretained proposal must not consume approval")
        decision_status = proposal.status
        if decision_status not in {"duplicate", "rejected", "inconclusive"}:
            raise RetentionError("invalid nonretained proposal state")
        decision = _make_decision(
            proposal=proposal,
            status=decision_status,
            lesson_id=None,
            approval_binding_sha256=None,
            approval_thread_id=None,
            human_principal_id=None,
            reasons=proposal.reasons,
            created_by=author,
            producer_version=producer,
        )
        retention_store.record_nonretained_decision(decision)
        return RetentionResult(decision=decision, lesson=None, lifecycle=None)

    if not isinstance(approval, AuthenticatedApprovalContext):
        raise RetentionError(
            "trusted retention requires AuthenticatedApprovalContext from approval runtime"
        )
    if approval.authority != "human_review/v1":
        raise RetentionError("unsupported retention approval authority")
    request = proposal.approval_request
    if request is None:
        raise RetentionError("approval-required proposal is missing exact approval request")
    if approval.request != request:
        raise RetentionError("human approval request does not match exact retention proposal")
    if request.action_type != RETENTION_APPROVAL_ACTION:
        raise RetentionError("approval request action type is not retention-authorizing")
    if approval.outcome.status != "approved":
        raise RetentionError("retention requires an explicit approved human outcome")
    if approval.outcome.request_id != request.request_id:
        raise RetentionError("approval outcome request identity mismatch")
    if approval.outcome.original_proposal_sha256 != request.proposal_sha256:
        raise RetentionError("approval outcome proposal hash mismatch")
    if approval.outcome.reviewed_proposal_sha256 != request.proposal_sha256:
        raise RetentionError("approved proposal changed during review")
    if approval.outcome.approval_binding_sha256 != request.binding_sha256:
        raise RetentionError("approval outcome binding mismatch")
    if approval.outcome.scope != request.scope:
        raise RetentionError("approval outcome scope mismatch")
    _text("approval_thread_id", approval.thread_id)
    _text("human_principal_id", approval.human_principal_id)

    try:
        verification = validate_candidate_verification_result(
            packet=packet,
            grounded_result=grounded_result,
            golden_case=golden_case,
            evaluation=evaluation,
            bundle=bundle,
            retest_packet=retest_packet,
            retest_grounded_result=retest_grounded_result,
            result=verification_result,
        )
    except VerificationError as exc:
        raise RetentionError("canonical Phase 9 verification changed before commit") from exc
    if verification.status != "verified_for_learning":
        raise RetentionError("only verified_for_learning may create a verified lesson")
    if proposal.contradiction_snapshot is None:
        raise RetentionError("retention commit requires complete contradiction snapshot")
    if proposal.contradiction_snapshot.contradiction_status != "clear":
        raise RetentionError("retention commit requires clear contradiction result")

    lifecycle = _make_lifecycle_state(
        lesson_id=proposal.lesson_id,
        state="active",
        previous_state_id=None,
        reason="retained_after_exact_phase10_gates",
    )
    record_material = _lesson_record_material(
        proposal=proposal,
        bundle=bundle,
        verification=verification,
        approval=approval,
        lifecycle=lifecycle,
        created_by=author,
        producer_version=producer,
    )
    record_hash = _hash(record_material)
    lesson = VerifiedLessonRecord(
        lesson_id=proposal.lesson_id,
        lesson_hash=record_hash,
        verified_lesson_contract=VERIFIED_LESSON_CONTRACT,
        retention_version=RETENTION_VERSION,
        lesson_key=proposal.lesson_key,
        lesson_type=proposal.scope.lesson_type,
        scope_id=proposal.scope.scope_id,
        failure_classifications=proposal.scope.failure_classifications,
        diagnosed_layers=proposal.scope.diagnosed_layers,
        source_ids=proposal.scope.source_ids,
        lesson_body=bundle.candidate.lesson_text,
        body_origin="generated_candidate",
        verification_refs=_verification_refs(verification),
        verification_checks=tuple(
            (item.check_id, item.check_kind, item.status) for item in verification.checks
        ),
        contradiction_snapshot_id=proposal.contradiction_snapshot.snapshot_id,
        confidence_basis=proposal.confidence_basis,
        approval_request_id=request.request_id,
        approval_proposal_sha256=request.proposal_sha256,
        approval_binding_sha256=request.binding_sha256,
        approval_thread_id=approval.thread_id,
        human_principal_id=approval.human_principal_id,
        initial_lifecycle_state_id=lifecycle.state_id,
        created_by=author,
        producer_version=producer,
    )
    decision = _make_decision(
        proposal=proposal,
        status="retained",
        lesson_id=lesson.lesson_id,
        approval_binding_sha256=request.binding_sha256,
        approval_thread_id=approval.thread_id,
        human_principal_id=approval.human_principal_id,
        reasons=("all_phase10_gates_passed_and_exact_human_approval_consumed",),
        created_by=author,
        producer_version=producer,
        lesson_hash=lesson.lesson_hash,
    )
    retention_store.commit_retention(
        lesson=lesson,
        lifecycle=lifecycle,
        decision=decision,
    )
    return RetentionResult(decision=decision, lesson=lesson, lifecycle=lifecycle)
