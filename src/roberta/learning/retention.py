"""Deterministic verified-lesson retention for the Roberta Learning System.

Phase 10 consumes only an exact canonical Phase 9 ``verified_for_learning``
result. The first slice is deliberately narrow: procedural lessons, exact
approved-source support, complete provider-built contradiction snapshots,
exact-duplicate handling, evidence-bound uncalibrated confidence, explicit
human review through Roberta's existing approval contract, and an in-memory
provider-neutral lesson store.

Retention never grants source-truth, live-state, protected-governance,
CMIS/provider-trust, wallet, or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Any, Mapping, Protocol

from roberta.approval import ApprovalOutcome, ApprovalRequest

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
RETENTION_VERSION = "1.0.0"
RETENTION_APPROVAL_ACTION = "retain_verified_lesson"
RETENTION_APPROVAL_AUTHORITY = "human_review/v1"
CONTRADICTION_SNAPSHOT_CONTRACT = "retention-contradiction-snapshot/v1"

_ALLOWED_LESSON_TYPES = frozenset({"procedural"})
_PREPARATION_STATUSES = frozenset(
    {"approval_required", "duplicate", "rejected", "inconclusive"}
)
_CONTRADICTION_STATUSES = frozenset({"clear", "conflict", "inconclusive"})
_LIFECYCLE_STATUSES = frozenset({"active", "superseded", "revoked"})


class RetentionError(ValueError):
    """Raised when a retention boundary cannot be satisfied safely."""


class _NoExternalAuthority:
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
    def cmis_provider_trust_authorized(self) -> bool:
        return False

    @property
    def wallet_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class LessonScope(_NoExternalAuthority):
    scope_id: str
    scope_hash: str
    lesson_key: str
    domain: str
    task: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RetentionSourceEntry(_NoExternalAuthority):
    source_id: str
    content_hash: str
    artifact_ref: str
    approval_status: str
    source_status: str
    exact_lesson_body_match: bool


@dataclass(frozen=True, slots=True)
class RetentionLessonEntry(_NoExternalAuthority):
    lesson_id: str
    lesson_hash: str
    state_id: str
    lesson_type: str
    scope_id: str
    lesson_key: str
    domain: str
    task: str
    lesson_body_hash: str


@dataclass(frozen=True, slots=True)
class RetentionContradictionSnapshot(_NoExternalAuthority):
    snapshot_id: str
    snapshot_hash: str
    snapshot_contract: str
    retention_version: str
    lesson_type: str
    lesson_scope_id: str
    proposed_lesson_body_hash: str
    source_entries: tuple[RetentionSourceEntry, ...]
    active_lesson_entries: tuple[RetentionLessonEntry, ...]
    source_ids: tuple[str, ...]
    active_lesson_ids: tuple[str, ...]
    source_count: int
    active_lesson_count: int
    source_snapshot_complete: bool
    lesson_snapshot_complete: bool
    exact_support_source_ids: tuple[str, ...]
    conflict_lesson_ids: tuple[str, ...]
    exact_duplicate_lesson_ids: tuple[str, ...]
    status: str
    details: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RetentionPreparation(_NoExternalAuthority):
    preparation_id: str
    preparation_hash: str
    retention_contract: str
    retention_version: str
    verification_id: str
    bundle_id: str
    candidate_id: str
    candidate_state_id: str
    reflection_id: str
    verification_plan_id: str
    original_evaluation_id: str
    retest_evaluation_id: str
    lesson_type: str
    lesson_scope: LessonScope
    lesson_body: str
    lesson_body_origin: str
    contradiction_snapshot: RetentionContradictionSnapshot
    status: str
    existing_lesson_id: str | None
    confidence_level: str
    confidence_score: float | None
    confidence_basis: tuple[str, ...]
    approval_attempt: int
    approval_request: ApprovalRequest | None
    created_by: str
    producer_version: str


@dataclass(frozen=True, slots=True)
class TrustedRetentionApproval(_NoExternalAuthority):
    approval_id: str
    approval_hash: str
    authority: str
    request_id: str
    proposal_sha256: str
    binding_sha256: str
    thread_id: str
    human_principal_id: str
    outcome_status: str


@dataclass(frozen=True, slots=True)
class VerifiedLessonRecord(_NoExternalAuthority):
    lesson_id: str
    lesson_hash: str
    verified_lesson_contract: str
    retention_contract: str
    retention_version: str
    lesson_type: str
    lesson_scope: LessonScope
    lesson_body: str
    lesson_body_origin: str
    verification_id: str
    bundle_id: str
    candidate_id: str
    candidate_state_id: str
    reflection_id: str
    verification_plan_id: str
    original_evaluation_id: str
    retest_evaluation_id: str
    contradiction_snapshot_id: str
    confidence_level: str
    confidence_score: float | None
    confidence_basis: tuple[str, ...]
    approval_id: str
    approval_request_id: str
    approval_proposal_sha256: str
    approval_binding_sha256: str
    approval_thread_id: str
    approval_principal_id: str
    recorded_at: str
    created_by: str
    producer_version: str

    @property
    def retained_for_learning(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class VerifiedLessonState(_NoExternalAuthority):
    state_id: str
    state_hash: str
    lesson_id: str
    status: str
    previous_state_id: str | None
    superseded_by_lesson_id: str | None
    reason: str
    evidence_ids: tuple[str, ...]
    transition_decision_id: str | None


@dataclass(frozen=True, slots=True)
class RetentionDecision(_NoExternalAuthority):
    decision_id: str
    decision_hash: str
    retention_contract: str
    retention_version: str
    preparation_id: str
    status: str
    verified_lesson: VerifiedLessonRecord
    lesson_state: VerifiedLessonState
    trusted_approval_id: str


class RetentionApprovalRegistry(Protocol):
    def get_application_approval(self, request_id: str) -> TrustedRetentionApproval | None: ...


class InMemoryRetentionApprovalRegistry:
    """Trusted application/session adapter used by deterministic tests.

    Production code must populate this boundary only after the existing
    LangGraph approval runtime has authenticated the human session and resolved
    the exact paused request. Phase 10 never accepts principal or thread
    identity from candidate/source/model text.
    """

    def __init__(self) -> None:
        self._records: dict[str, TrustedRetentionApproval] = {}

    def record_application_approval(
        self,
        *,
        request: ApprovalRequest,
        outcome: ApprovalOutcome,
        thread_id: str,
        human_principal_id: str,
    ) -> TrustedRetentionApproval:
        if not isinstance(request, ApprovalRequest):
            raise RetentionError("request must be ApprovalRequest")
        if request.action_type != RETENTION_APPROVAL_ACTION:
            raise RetentionError("approval request action_type is not a retention review")
        if not isinstance(outcome, ApprovalOutcome):
            raise RetentionError("outcome must be ApprovalOutcome")
        thread = _text("thread_id", thread_id)
        principal = _text("human_principal_id", human_principal_id)
        if outcome.status != "approved":
            raise RetentionError("trusted retention approval requires an approved outcome")
        if outcome.request_id != request.request_id:
            raise RetentionError("approval outcome request does not match retention request")
        if outcome.original_proposal_sha256 != request.proposal_sha256:
            raise RetentionError("approval outcome proposal does not match retention request")
        if outcome.approval_binding_sha256 != request.binding_sha256:
            raise RetentionError("approval outcome binding does not match retention request")
        if outcome.reviewed_proposal_sha256 != request.proposal_sha256:
            raise RetentionError("approved reviewed proposal differs from retention proposal")
        if tuple(outcome.scope) != request.scope:
            raise RetentionError("approval outcome scope differs from retention request")
        if _mapping_json(outcome.reviewed_proposal) != _mapping_json(request.proposal):
            raise RetentionError("approved reviewed proposal content differs from request")

        material = _trusted_approval_material_values(
            authority=RETENTION_APPROVAL_AUTHORITY,
            request_id=request.request_id,
            proposal_sha256=request.proposal_sha256,
            binding_sha256=request.binding_sha256,
            thread_id=thread,
            human_principal_id=principal,
            outcome_status=outcome.status,
        )
        digest = _hash(material)
        record = TrustedRetentionApproval(
            approval_id=f"rha_{digest}",
            approval_hash=digest,
            authority=RETENTION_APPROVAL_AUTHORITY,
            request_id=request.request_id,
            proposal_sha256=request.proposal_sha256,
            binding_sha256=request.binding_sha256,
            thread_id=thread,
            human_principal_id=principal,
            outcome_status=outcome.status,
        )
        _validate_trusted_approval(record)
        existing = self._records.get(request.request_id)
        if existing is not None and existing != record:
            raise RetentionError("conflicting trusted approval for retention request")
        self._records[request.request_id] = record
        return record

    def get_application_approval(self, request_id: str) -> TrustedRetentionApproval | None:
        record = self._records.get(request_id)
        if record is not None:
            _validate_trusted_approval(record)
        return record


class InMemoryVerifiedLessonStore:
    """Provider-neutral deterministic Phase 10 store; not external persistence."""

    def __init__(self) -> None:
        self._lessons: dict[str, VerifiedLessonRecord] = {}
        self._states: dict[str, VerifiedLessonState] = {}
        self._current_state: dict[str, str] = {}
        self._consumed_approval_bindings: set[str] = set()
        self._preparations: dict[str, RetentionPreparation] = {}

    def get_preparation(self, preparation_id: str) -> RetentionPreparation | None:
        """Return the immutable audit record for every retention outcome."""

        preparation = self._preparations.get(preparation_id)
        if preparation is not None:
            _validate_preparation(preparation)
        return preparation

    def record_preparation(self, preparation: RetentionPreparation) -> None:
        """Preserve Phase 8/9 and gate provenance even when no lesson is retained."""

        validated = _validate_preparation(preparation)
        existing = self._preparations.get(validated.preparation_id)
        if existing is not None and existing != validated:
            raise RetentionError("conflicting immutable retention preparation")
        self._preparations.setdefault(validated.preparation_id, validated)

    def get_lesson(self, lesson_id: str) -> VerifiedLessonRecord | None:
        return self._lessons.get(lesson_id)

    def get_state(self, state_id: str) -> VerifiedLessonState | None:
        return self._states.get(state_id)

    def get_active_state(self, lesson_id: str) -> VerifiedLessonState | None:
        state_id = self._current_state.get(lesson_id)
        if state_id is None:
            return None
        state = self._states.get(state_id)
        if state is None or state.status != "active":
            return None
        _validate_state_record(state)
        return state

    def list_active(self) -> tuple[VerifiedLessonRecord, ...]:
        output: list[VerifiedLessonRecord] = []
        for lesson_id in sorted(self._lessons):
            if self.get_active_state(lesson_id) is not None:
                lesson = self._lessons[lesson_id]
                self.validate_lesson(lesson)
                output.append(lesson)
        return tuple(output)

    def list_active_applicable(
        self,
        *,
        lesson_type: str,
        scope: LessonScope,
    ) -> tuple[tuple[VerifiedLessonRecord, VerifiedLessonState], ...]:
        """Enumerate every active lesson in the same v1 procedural task boundary.

        ``lesson_key`` is intentionally not used to exclude records: a caller
        cannot hide a potentially conflicting procedure merely by minting a new
        key. The first-slice applicability boundary is exact lesson type + domain
        + task, which is conservative and deterministic.
        """

        output: list[tuple[VerifiedLessonRecord, VerifiedLessonState]] = []
        for lesson in self.list_active():
            if lesson.lesson_type != lesson_type:
                continue
            if (
                lesson.lesson_scope.domain != scope.domain
                or lesson.lesson_scope.task != scope.task
            ):
                continue
            state = self.get_active_state(lesson.lesson_id)
            assert state is not None
            output.append((lesson, state))
        output.sort(key=lambda item: item[0].lesson_id)
        return tuple(output)

    def validate_lesson(self, lesson: VerifiedLessonRecord) -> VerifiedLessonRecord:
        if not isinstance(lesson, VerifiedLessonRecord):
            raise RetentionError("lesson must be VerifiedLessonRecord")
        if lesson.verified_lesson_contract != VERIFIED_LESSON_CONTRACT:
            raise RetentionError("verified lesson contract is invalid")
        if lesson.retention_contract != RETENTION_CONTRACT:
            raise RetentionError("verified lesson retention contract is invalid")
        if lesson.retention_version != RETENTION_VERSION:
            raise RetentionError("verified lesson retention version is invalid")
        _validate_scope(lesson.lesson_scope)
        material = _verified_lesson_material(lesson)
        digest = _hash(material)
        if lesson.lesson_hash != digest or lesson.lesson_id != f"vl_{digest}":
            raise RetentionError("verified lesson identity/content is invalid")
        return lesson

    def approval_binding_consumed(self, binding_sha256: str) -> bool:
        return binding_sha256 in self._consumed_approval_bindings

    def commit_retention(
        self,
        *,
        lesson: VerifiedLessonRecord,
        state: VerifiedLessonState,
        approval_binding_sha256: str,
    ) -> None:
        self.validate_lesson(lesson)
        _validate_state_record(state)
        if state.lesson_id != lesson.lesson_id or state.status != "active":
            raise RetentionError("initial lesson state must be active and bind exact lesson")
        if approval_binding_sha256 in self._consumed_approval_bindings:
            raise RetentionError("retention approval binding was already consumed")
        if lesson.lesson_id in self._lessons:
            raise RetentionError("verified lesson already exists in retention store")
        self._lessons[lesson.lesson_id] = lesson
        self._states[state.state_id] = state
        self._current_state[lesson.lesson_id] = state.state_id
        self._consumed_approval_bindings.add(approval_binding_sha256)

    def transition_state(self, state: VerifiedLessonState) -> None:
        _validate_state_record(state)
        current_id = self._current_state.get(state.lesson_id)
        current = None if current_id is None else self._states.get(current_id)
        if current is None or current.status != "active":
            raise RetentionError("verified lesson has no exact active predecessor")
        if state.previous_state_id != current.state_id:
            raise RetentionError("lifecycle transition requires exact active predecessor")
        if state.status not in {"superseded", "revoked"}:
            raise RetentionError("active lesson can transition only to superseded or revoked")
        if state.state_id in self._states and self._states[state.state_id] != state:
            raise RetentionError("conflicting immutable verified lesson state")
        self._states[state.state_id] = state
        self._current_state[state.lesson_id] = state.state_id


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
        raise RetentionError("retention material must be canonical JSON-compatible data") from exc


def _mapping_json(value: Mapping[str, Any]) -> str:
    def thaw(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {str(key): thaw(nested) for key, nested in item.items()}
        if isinstance(item, tuple):
            return [thaw(nested) for nested in item]
        return item

    return _canonical_json(thaw(value))


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise RetentionError(f"{name} must be a normalized non-empty string")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _body_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_recorded_at(value: str) -> str:
    text = _text("recorded_at", value)
    if not text.endswith("Z"):
        raise RetentionError("recorded_at must be a canonical UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise RetentionError("recorded_at must be a valid UTC timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise RetentionError("recorded_at must be UTC")
    return text


def make_lesson_scope(
    *,
    lesson_key: str,
    domain: str,
    task: str,
    source_ids: tuple[str, ...],
) -> LessonScope:
    key = _text("lesson_key", lesson_key)
    normalized_domain = _text("domain", domain)
    normalized_task = _text("task", task)
    if not isinstance(source_ids, tuple) or not source_ids:
        raise RetentionError("source_ids must be a non-empty tuple")
    normalized_sources = tuple(sorted({_text("source_id", item) for item in source_ids}))
    if len(normalized_sources) != len(source_ids):
        raise RetentionError("source_ids must be unique")
    material = {
        "lesson_key": key,
        "domain": normalized_domain,
        "task": normalized_task,
        "source_ids": list(normalized_sources),
    }
    digest = _hash(material)
    return LessonScope(
        scope_id=f"lscope_{digest}",
        scope_hash=digest,
        lesson_key=key,
        domain=normalized_domain,
        task=normalized_task,
        source_ids=normalized_sources,
    )


def _validate_scope(scope: LessonScope) -> LessonScope:
    if not isinstance(scope, LessonScope):
        raise RetentionError("lesson_scope must be LessonScope")
    rebuilt = make_lesson_scope(
        lesson_key=scope.lesson_key,
        domain=scope.domain,
        task=scope.task,
        source_ids=scope.source_ids,
    )
    if rebuilt != scope:
        raise RetentionError("lesson scope identity/content is invalid")
    return rebuilt


def _validate_source_record_identity(record: SourceRecord) -> None:
    identity = {
        "origin": record.origin,
        "title": record.title,
        "version": record.version,
        "content_hash": record.content_hash,
    }
    expected_id = "src_" + _hash(identity)
    if record.source_id != expected_id:
        raise RetentionError("trusted source store returned non-canonical source identity")
    if record.artifact_ref != f"artifact_sha256:{record.content_hash}":
        raise RetentionError("canonical source artifact reference is invalid")


def _source_entry(
    *,
    source_store: SourceStore,
    source_id: str,
    lesson_body: str,
) -> tuple[RetentionSourceEntry | None, tuple[str, ...]]:
    try:
        record = source_store.get_source(source_id)
    except Exception as exc:
        return None, (f"source_lookup_failed:{type(exc).__name__}:{source_id}",)
    if record is None:
        return None, (f"missing_source:{source_id}",)
    if not isinstance(record, SourceRecord) or record.source_id != source_id:
        raise RetentionError("trusted source store returned non-canonical source identity")
    _validate_source_record_identity(record)
    try:
        artifact = source_store.get_artifact(record.artifact_ref)
    except Exception as exc:
        return None, (f"source_artifact_lookup_failed:{type(exc).__name__}:{source_id}",)
    if artifact is None:
        return None, (f"missing_source_artifact:{source_id}",)
    if _sha256_bytes(artifact) != record.content_hash:
        raise RetentionError("canonical source artifact content hash is invalid")
    try:
        text = artifact.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RetentionError("canonical source artifact is not valid UTF-8") from exc
    exact = text.rstrip("\r\n") == lesson_body
    entry = RetentionSourceEntry(
        source_id=record.source_id,
        content_hash=record.content_hash,
        artifact_ref=record.artifact_ref,
        approval_status=record.approval_status,
        source_status=record.status,
        exact_lesson_body_match=exact,
    )
    details: list[str] = []
    if record.approval_status != "approved" or record.status != "approved":
        details.append(f"source_not_active_approved:{source_id}")
    if not exact:
        details.append(f"source_exact_support_unavailable:{source_id}")
    return entry, tuple(details)


def _lesson_entry(
    lesson: VerifiedLessonRecord, state: VerifiedLessonState
) -> RetentionLessonEntry:
    return RetentionLessonEntry(
        lesson_id=lesson.lesson_id,
        lesson_hash=lesson.lesson_hash,
        state_id=state.state_id,
        lesson_type=lesson.lesson_type,
        scope_id=lesson.lesson_scope.scope_id,
        lesson_key=lesson.lesson_scope.lesson_key,
        domain=lesson.lesson_scope.domain,
        task=lesson.lesson_scope.task,
        lesson_body_hash=_body_hash(lesson.lesson_body),
    )


def _source_entry_material(entry: RetentionSourceEntry) -> dict[str, Any]:
    return {
        "source_id": entry.source_id,
        "content_hash": entry.content_hash,
        "artifact_ref": entry.artifact_ref,
        "approval_status": entry.approval_status,
        "source_status": entry.source_status,
        "exact_lesson_body_match": entry.exact_lesson_body_match,
    }


def _lesson_entry_material(entry: RetentionLessonEntry) -> dict[str, Any]:
    return {
        "lesson_id": entry.lesson_id,
        "lesson_hash": entry.lesson_hash,
        "state_id": entry.state_id,
        "lesson_type": entry.lesson_type,
        "scope_id": entry.scope_id,
        "lesson_key": entry.lesson_key,
        "domain": entry.domain,
        "task": entry.task,
        "lesson_body_hash": entry.lesson_body_hash,
    }


def _build_contradiction_snapshot(
    *,
    source_store: SourceStore,
    lesson_store: InMemoryVerifiedLessonStore,
    lesson_type: str,
    scope: LessonScope,
    lesson_body: str,
    source_conflict_detected: bool,
) -> RetentionContradictionSnapshot:
    source_entries: list[RetentionSourceEntry] = []
    source_details: list[str] = []
    source_complete = True
    for source_id in scope.source_ids:
        entry, details = _source_entry(
            source_store=source_store,
            source_id=source_id,
            lesson_body=lesson_body,
        )
        source_details.extend(details)
        if entry is None:
            source_complete = False
        else:
            source_entries.append(entry)
            if entry.approval_status != "approved" or entry.source_status != "approved":
                source_complete = False

    active_pairs = lesson_store.list_active_applicable(
        lesson_type=lesson_type,
        scope=scope,
    )
    lesson_entries = tuple(_lesson_entry(lesson, state) for lesson, state in active_pairs)
    lesson_complete = True

    body_hash = _body_hash(lesson_body)
    duplicate_ids: list[str] = []
    conflict_ids: list[str] = []
    for lesson, _state in active_pairs:
        if lesson.lesson_scope == scope and lesson.lesson_body == lesson_body:
            duplicate_ids.append(lesson.lesson_id)
        elif lesson.lesson_body != lesson_body:
            conflict_ids.append(lesson.lesson_id)

    source_tuple = tuple(source_entries)
    active_ids = tuple(entry.lesson_id for entry in lesson_entries)
    exact_support_ids = tuple(
        entry.source_id for entry in source_tuple if entry.exact_lesson_body_match
    )
    all_declared_sources_exactly_support = (
        source_complete
        and len(source_tuple) == len(scope.source_ids)
        and len(exact_support_ids) == len(scope.source_ids)
    )

    if not source_complete or not lesson_complete or not all_declared_sources_exactly_support:
        status = "inconclusive"
    elif source_conflict_detected or conflict_ids:
        status = "conflict"
    else:
        status = "clear"
    if status not in _CONTRADICTION_STATUSES:
        raise RetentionError("unsupported contradiction snapshot status")

    if source_conflict_detected:
        source_details.append("canonical_evidence_packet_reports_source_conflict")
    details = tuple(source_details)
    material = {
        "snapshot_contract": CONTRADICTION_SNAPSHOT_CONTRACT,
        "retention_version": RETENTION_VERSION,
        "lesson_type": lesson_type,
        "lesson_scope_id": scope.scope_id,
        "proposed_lesson_body_hash": body_hash,
        "source_entries": [_source_entry_material(item) for item in source_tuple],
        "active_lesson_entries": [_lesson_entry_material(item) for item in lesson_entries],
        "source_ids": list(scope.source_ids),
        "active_lesson_ids": list(active_ids),
        "source_count": len(source_tuple),
        "active_lesson_count": len(lesson_entries),
        "source_snapshot_complete": source_complete,
        "lesson_snapshot_complete": lesson_complete,
        "exact_support_source_ids": list(exact_support_ids),
        "conflict_lesson_ids": sorted(conflict_ids),
        "exact_duplicate_lesson_ids": sorted(duplicate_ids),
        "status": status,
        "details": list(details),
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "cmis_provider_trust_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }
    digest = _hash(material)
    return RetentionContradictionSnapshot(
        snapshot_id=f"rcs_{digest}",
        snapshot_hash=digest,
        snapshot_contract=CONTRADICTION_SNAPSHOT_CONTRACT,
        retention_version=RETENTION_VERSION,
        lesson_type=lesson_type,
        lesson_scope_id=scope.scope_id,
        proposed_lesson_body_hash=body_hash,
        source_entries=source_tuple,
        active_lesson_entries=lesson_entries,
        source_ids=scope.source_ids,
        active_lesson_ids=active_ids,
        source_count=len(source_tuple),
        active_lesson_count=len(lesson_entries),
        source_snapshot_complete=source_complete,
        lesson_snapshot_complete=lesson_complete,
        exact_support_source_ids=exact_support_ids,
        conflict_lesson_ids=tuple(sorted(conflict_ids)),
        exact_duplicate_lesson_ids=tuple(sorted(duplicate_ids)),
        status=status,
        details=details,
    )


def _snapshot_material(snapshot: RetentionContradictionSnapshot) -> dict[str, Any]:
    return {
        "snapshot_contract": snapshot.snapshot_contract,
        "retention_version": snapshot.retention_version,
        "lesson_type": snapshot.lesson_type,
        "lesson_scope_id": snapshot.lesson_scope_id,
        "proposed_lesson_body_hash": snapshot.proposed_lesson_body_hash,
        "source_entries": [_source_entry_material(item) for item in snapshot.source_entries],
        "active_lesson_entries": [
            _lesson_entry_material(item) for item in snapshot.active_lesson_entries
        ],
        "source_ids": list(snapshot.source_ids),
        "active_lesson_ids": list(snapshot.active_lesson_ids),
        "source_count": snapshot.source_count,
        "active_lesson_count": snapshot.active_lesson_count,
        "source_snapshot_complete": snapshot.source_snapshot_complete,
        "lesson_snapshot_complete": snapshot.lesson_snapshot_complete,
        "exact_support_source_ids": list(snapshot.exact_support_source_ids),
        "conflict_lesson_ids": list(snapshot.conflict_lesson_ids),
        "exact_duplicate_lesson_ids": list(snapshot.exact_duplicate_lesson_ids),
        "status": snapshot.status,
        "details": list(snapshot.details),
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "cmis_provider_trust_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def _validate_snapshot(snapshot: RetentionContradictionSnapshot) -> None:
    if not isinstance(snapshot, RetentionContradictionSnapshot):
        raise RetentionError("contradiction_snapshot must be RetentionContradictionSnapshot")
    if snapshot.snapshot_contract != CONTRADICTION_SNAPSHOT_CONTRACT:
        raise RetentionError("contradiction snapshot contract is invalid")
    if snapshot.retention_version != RETENTION_VERSION:
        raise RetentionError("contradiction snapshot retention version is invalid")
    if snapshot.status not in _CONTRADICTION_STATUSES:
        raise RetentionError("contradiction snapshot status is invalid")
    if snapshot.source_count != len(snapshot.source_entries):
        raise RetentionError("contradiction source count is invalid")
    if snapshot.active_lesson_count != len(snapshot.active_lesson_entries):
        raise RetentionError("contradiction lesson count is invalid")
    if snapshot.active_lesson_ids != tuple(
        item.lesson_id for item in snapshot.active_lesson_entries
    ):
        raise RetentionError("contradiction active lesson identities are invalid")
    digest = _hash(_snapshot_material(snapshot))
    if snapshot.snapshot_hash != digest or snapshot.snapshot_id != f"rcs_{digest}":
        raise RetentionError("contradiction snapshot identity/content is invalid")


def _preparation_material(preparation: RetentionPreparation) -> dict[str, Any]:
    return {
        "retention_contract": preparation.retention_contract,
        "retention_version": preparation.retention_version,
        "verification_id": preparation.verification_id,
        "bundle_id": preparation.bundle_id,
        "candidate_id": preparation.candidate_id,
        "candidate_state_id": preparation.candidate_state_id,
        "reflection_id": preparation.reflection_id,
        "verification_plan_id": preparation.verification_plan_id,
        "original_evaluation_id": preparation.original_evaluation_id,
        "retest_evaluation_id": preparation.retest_evaluation_id,
        "lesson_type": preparation.lesson_type,
        "lesson_scope_id": preparation.lesson_scope.scope_id,
        "lesson_body": preparation.lesson_body,
        "lesson_body_origin": preparation.lesson_body_origin,
        "contradiction_snapshot_id": preparation.contradiction_snapshot.snapshot_id,
        "status": preparation.status,
        "existing_lesson_id": preparation.existing_lesson_id,
        "confidence_level": preparation.confidence_level,
        "confidence_score": preparation.confidence_score,
        "confidence_basis": list(preparation.confidence_basis),
        "approval_attempt": preparation.approval_attempt,
        "created_by": preparation.created_by,
        "producer_version": preparation.producer_version,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "cmis_provider_trust_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def _approval_scope(preparation: RetentionPreparation) -> tuple[str, ...]:
    return (
        RETENTION_CONTRACT,
        f"lesson_type:{preparation.lesson_type}",
        f"lesson_scope:{preparation.lesson_scope.scope_id}",
        f"approval_attempt:{preparation.approval_attempt}",
    )


def _approval_proposal(preparation: RetentionPreparation) -> dict[str, Any]:
    return {
        "preparation_id": preparation.preparation_id,
        "retention_contract": preparation.retention_contract,
        "retention_version": preparation.retention_version,
        "verification_id": preparation.verification_id,
        "bundle_id": preparation.bundle_id,
        "candidate_id": preparation.candidate_id,
        "candidate_state_id": preparation.candidate_state_id,
        "reflection_id": preparation.reflection_id,
        "verification_plan_id": preparation.verification_plan_id,
        "original_evaluation_id": preparation.original_evaluation_id,
        "retest_evaluation_id": preparation.retest_evaluation_id,
        "lesson_type": preparation.lesson_type,
        "lesson_scope_id": preparation.lesson_scope.scope_id,
        "lesson_body_hash": _body_hash(preparation.lesson_body),
        "contradiction_snapshot_id": preparation.contradiction_snapshot.snapshot_id,
        "contradiction_status": preparation.contradiction_snapshot.status,
        "existing_lesson_id": preparation.existing_lesson_id,
        "confidence_level": preparation.confidence_level,
        "confidence_score": preparation.confidence_score,
        "confidence_basis": list(preparation.confidence_basis),
        "approval_attempt": preparation.approval_attempt,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "cmis_provider_trust_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def _build_approval_request(preparation: RetentionPreparation) -> ApprovalRequest:
    return ApprovalRequest(
        request_id=f"retainreq_{preparation.preparation_hash}",
        action_type=RETENTION_APPROVAL_ACTION,
        summary="Retain one exact verified procedural lesson in the Phase 10 retention store.",
        scope=_approval_scope(preparation),
        proposal=_approval_proposal(preparation),
        policy_reasons=(
            "phase9_verified_for_learning_revalidated",
            "phase10_contradiction_and_dedup_gates_passed",
            "explicit_human_retention_approval_required",
        ),
        evidence_summary=(
            preparation.verification_id,
            preparation.contradiction_snapshot.snapshot_id,
        ),
    )


def _validate_preparation(preparation: RetentionPreparation) -> RetentionPreparation:
    if not isinstance(preparation, RetentionPreparation):
        raise RetentionError("preparation must be RetentionPreparation")
    _validate_scope(preparation.lesson_scope)
    _validate_snapshot(preparation.contradiction_snapshot)
    if preparation.retention_contract != RETENTION_CONTRACT:
        raise RetentionError("retention preparation contract is invalid")
    if preparation.retention_version != RETENTION_VERSION:
        raise RetentionError("retention preparation version is invalid")
    if preparation.status not in _PREPARATION_STATUSES:
        raise RetentionError("unsupported retention preparation status")
    if preparation.lesson_type not in _ALLOWED_LESSON_TYPES:
        raise RetentionError("retention preparation lesson type is invalid")
    digest = _hash(_preparation_material(preparation))
    if (
        preparation.preparation_hash != digest
        or preparation.preparation_id != f"rprep_{digest}"
    ):
        raise RetentionError("retention preparation identity/content is invalid")
    if preparation.status == "approval_required":
        if preparation.approval_request is None:
            raise RetentionError("approval-required preparation is missing ApprovalRequest")
        rebuilt = _build_approval_request(preparation)
        if rebuilt != preparation.approval_request:
            raise RetentionError("retention approval request identity/content is invalid")
    elif preparation.approval_request is not None:
        raise RetentionError("non-eligible retention preparation cannot carry approval request")
    return preparation


def prepare_verified_lesson_retention(
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
    lesson_store: InMemoryVerifiedLessonStore,
    lesson_type: str,
    lesson_scope: LessonScope,
    approval_attempt: int,
    created_by: str,
    producer_version: str,
    retention_contract: str = RETENTION_CONTRACT,
    retention_version: str = RETENTION_VERSION,
) -> RetentionPreparation:
    """Build an auditable Phase 10 retention preparation without retaining it."""

    contract = _text("retention_contract", retention_contract)
    if contract != RETENTION_CONTRACT:
        raise RetentionError(f"unsupported retention contract {contract!r}")
    version = _text("retention_version", retention_version)
    if version != RETENTION_VERSION:
        raise RetentionError(f"unsupported retention version {version!r}")
    normalized_type = _text("lesson_type", lesson_type)
    if normalized_type not in _ALLOWED_LESSON_TYPES:
        raise RetentionError("lesson_type is not supported by Phase 10 v1")
    scope = _validate_scope(lesson_scope)
    if not isinstance(approval_attempt, int) or isinstance(approval_attempt, bool) or approval_attempt < 1:
        raise RetentionError("approval_attempt must be a positive integer")
    if not isinstance(lesson_store, InMemoryVerifiedLessonStore):
        raise RetentionError("Phase 10 v1 requires the provider-neutral in-memory lesson store")

    try:
        canonical_verification = validate_candidate_verification_result(
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
        raise RetentionError("canonical Phase 9 verification validation failed") from exc
    if canonical_verification.status != "verified_for_learning":
        raise RetentionError(
            "Phase 10 retention requires exact verified_for_learning Phase 9 state"
        )
    if canonical_verification.retest_evaluation_id is None:
        raise RetentionError("verified_for_learning result must bind a retest evaluation")

    lesson_body = _text("lesson_body", bundle.candidate.lesson_text)
    packet_source_ids = tuple(
        sorted({anchor.source_id for anchor in packet.evidence_anchors})
    )
    candidate_source_ids = tuple(
        sorted({reference.source_id for reference in bundle.candidate.evidence_references})
    )
    if not packet_source_ids or packet_source_ids != candidate_source_ids:
        raise RetentionError(
            "canonical Phase 8 packet/candidate source scope is incomplete or inconsistent"
        )
    if scope.source_ids != packet_source_ids:
        raise RetentionError(
            "lesson scope must equal the complete canonical Phase 8 evidence source scope"
        )
    snapshot = _build_contradiction_snapshot(
        source_store=source_store,
        lesson_store=lesson_store,
        lesson_type=normalized_type,
        scope=scope,
        lesson_body=lesson_body,
        source_conflict_detected=packet.has_conflicting_sources,
    )

    duplicate_ids = snapshot.exact_duplicate_lesson_ids
    existing_lesson_id = duplicate_ids[0] if duplicate_ids else None
    if snapshot.status == "inconclusive":
        status = "inconclusive"
    elif snapshot.status == "conflict":
        status = "rejected"
    elif duplicate_ids:
        status = "duplicate"
    else:
        status = "approval_required"

    confidence_basis = (
        "phase9_all_required_checks_passed",
        "calibrated_probability_unavailable",
    )
    provisional = RetentionPreparation(
        preparation_id="",
        preparation_hash="",
        retention_contract=contract,
        retention_version=version,
        verification_id=canonical_verification.verification_id,
        bundle_id=bundle.bundle_id,
        candidate_id=bundle.candidate.candidate_id,
        candidate_state_id=bundle.candidate.candidate_state_id,
        reflection_id=bundle.reflection.reflection_id,
        verification_plan_id=bundle.verification_plan.plan_id,
        original_evaluation_id=evaluation.evaluation_id,
        retest_evaluation_id=canonical_verification.retest_evaluation_id,
        lesson_type=normalized_type,
        lesson_scope=scope,
        lesson_body=lesson_body,
        lesson_body_origin="generated_provisional",
        contradiction_snapshot=snapshot,
        status=status,
        existing_lesson_id=existing_lesson_id,
        confidence_level="verification_passed_uncalibrated",
        confidence_score=None,
        confidence_basis=confidence_basis,
        approval_attempt=approval_attempt,
        approval_request=None,
        created_by=_text("created_by", created_by),
        producer_version=_text("producer_version", producer_version),
    )
    digest = _hash(_preparation_material(provisional))
    identified = RetentionPreparation(
        preparation_id=f"rprep_{digest}",
        preparation_hash=digest,
        retention_contract=provisional.retention_contract,
        retention_version=provisional.retention_version,
        verification_id=provisional.verification_id,
        bundle_id=provisional.bundle_id,
        candidate_id=provisional.candidate_id,
        candidate_state_id=provisional.candidate_state_id,
        reflection_id=provisional.reflection_id,
        verification_plan_id=provisional.verification_plan_id,
        original_evaluation_id=provisional.original_evaluation_id,
        retest_evaluation_id=provisional.retest_evaluation_id,
        lesson_type=provisional.lesson_type,
        lesson_scope=provisional.lesson_scope,
        lesson_body=provisional.lesson_body,
        lesson_body_origin=provisional.lesson_body_origin,
        contradiction_snapshot=provisional.contradiction_snapshot,
        status=provisional.status,
        existing_lesson_id=provisional.existing_lesson_id,
        confidence_level=provisional.confidence_level,
        confidence_score=provisional.confidence_score,
        confidence_basis=provisional.confidence_basis,
        approval_attempt=provisional.approval_attempt,
        approval_request=None,
        created_by=provisional.created_by,
        producer_version=provisional.producer_version,
    )
    request = _build_approval_request(identified) if status == "approval_required" else None
    final = RetentionPreparation(
        preparation_id=identified.preparation_id,
        preparation_hash=identified.preparation_hash,
        retention_contract=identified.retention_contract,
        retention_version=identified.retention_version,
        verification_id=identified.verification_id,
        bundle_id=identified.bundle_id,
        candidate_id=identified.candidate_id,
        candidate_state_id=identified.candidate_state_id,
        reflection_id=identified.reflection_id,
        verification_plan_id=identified.verification_plan_id,
        original_evaluation_id=identified.original_evaluation_id,
        retest_evaluation_id=identified.retest_evaluation_id,
        lesson_type=identified.lesson_type,
        lesson_scope=identified.lesson_scope,
        lesson_body=identified.lesson_body,
        lesson_body_origin=identified.lesson_body_origin,
        contradiction_snapshot=identified.contradiction_snapshot,
        status=identified.status,
        existing_lesson_id=identified.existing_lesson_id,
        confidence_level=identified.confidence_level,
        confidence_score=identified.confidence_score,
        confidence_basis=identified.confidence_basis,
        approval_attempt=identified.approval_attempt,
        approval_request=request,
        created_by=identified.created_by,
        producer_version=identified.producer_version,
    )
    validated = _validate_preparation(final)
    lesson_store.record_preparation(validated)
    return validated


def _validate_lesson_snapshot_current(
    preparation: RetentionPreparation,
    lesson_store: InMemoryVerifiedLessonStore,
) -> None:
    current = lesson_store.list_active_applicable(
        lesson_type=preparation.lesson_type,
        scope=preparation.lesson_scope,
    )
    current_entries = tuple(_lesson_entry(lesson, state) for lesson, state in current)
    if current_entries != preparation.contradiction_snapshot.active_lesson_entries:
        raise RetentionError(
            "active verified-lesson snapshot changed; prepare and approve retention again"
        )


def _trusted_approval_material_values(
    *,
    authority: str,
    request_id: str,
    proposal_sha256: str,
    binding_sha256: str,
    thread_id: str,
    human_principal_id: str,
    outcome_status: str,
) -> dict[str, Any]:
    return {
        "authority": authority,
        "request_id": request_id,
        "proposal_sha256": proposal_sha256,
        "binding_sha256": binding_sha256,
        "thread_id": thread_id,
        "human_principal_id": human_principal_id,
        "outcome_status": outcome_status,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "cmis_provider_trust_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def _validate_trusted_approval(
    approval: TrustedRetentionApproval,
) -> TrustedRetentionApproval:
    if not isinstance(approval, TrustedRetentionApproval):
        raise RetentionError("trusted approval record type is invalid")
    if approval.authority != RETENTION_APPROVAL_AUTHORITY:
        raise RetentionError("trusted retention approval authority is invalid")
    _text("approval_thread_id", approval.thread_id)
    _text("approval_principal_id", approval.human_principal_id)
    if approval.outcome_status != "approved":
        raise RetentionError("trusted retention approval is not approved")
    material = _trusted_approval_material_values(
        authority=approval.authority,
        request_id=approval.request_id,
        proposal_sha256=approval.proposal_sha256,
        binding_sha256=approval.binding_sha256,
        thread_id=approval.thread_id,
        human_principal_id=approval.human_principal_id,
        outcome_status=approval.outcome_status,
    )
    digest = _hash(material)
    if approval.approval_hash != digest or approval.approval_id != f"rha_{digest}":
        raise RetentionError("trusted retention approval identity/content is invalid")
    return approval


def _verified_lesson_material(lesson: VerifiedLessonRecord) -> dict[str, Any]:
    return {
        "verified_lesson_contract": lesson.verified_lesson_contract,
        "retention_contract": lesson.retention_contract,
        "retention_version": lesson.retention_version,
        "lesson_type": lesson.lesson_type,
        "lesson_scope_id": lesson.lesson_scope.scope_id,
        "lesson_body": lesson.lesson_body,
        "lesson_body_origin": lesson.lesson_body_origin,
        "verification_id": lesson.verification_id,
        "bundle_id": lesson.bundle_id,
        "candidate_id": lesson.candidate_id,
        "candidate_state_id": lesson.candidate_state_id,
        "reflection_id": lesson.reflection_id,
        "verification_plan_id": lesson.verification_plan_id,
        "original_evaluation_id": lesson.original_evaluation_id,
        "retest_evaluation_id": lesson.retest_evaluation_id,
        "contradiction_snapshot_id": lesson.contradiction_snapshot_id,
        "confidence_level": lesson.confidence_level,
        "confidence_score": lesson.confidence_score,
        "confidence_basis": list(lesson.confidence_basis),
        "approval_id": lesson.approval_id,
        "approval_request_id": lesson.approval_request_id,
        "approval_proposal_sha256": lesson.approval_proposal_sha256,
        "approval_binding_sha256": lesson.approval_binding_sha256,
        "approval_thread_id": lesson.approval_thread_id,
        "approval_principal_id": lesson.approval_principal_id,
        "recorded_at": lesson.recorded_at,
        "created_by": lesson.created_by,
        "producer_version": lesson.producer_version,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "cmis_provider_trust_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def _state_material(state: VerifiedLessonState) -> dict[str, Any]:
    return {
        "lesson_id": state.lesson_id,
        "status": state.status,
        "previous_state_id": state.previous_state_id,
        "superseded_by_lesson_id": state.superseded_by_lesson_id,
        "reason": state.reason,
        "evidence_ids": list(state.evidence_ids),
        "transition_decision_id": state.transition_decision_id,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "cmis_provider_trust_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def _build_state(
    *,
    lesson_id: str,
    status: str,
    previous_state_id: str | None,
    superseded_by_lesson_id: str | None,
    reason: str,
    evidence_ids: tuple[str, ...],
    transition_decision_id: str | None,
) -> VerifiedLessonState:
    if status not in _LIFECYCLE_STATUSES:
        raise RetentionError("unsupported verified lesson lifecycle status")
    normalized_lesson = _text("lesson_id", lesson_id)
    if not isinstance(evidence_ids, tuple) or not evidence_ids:
        raise RetentionError("verified lesson lifecycle requires evidence_ids")
    normalized_evidence = tuple(_text("evidence_id", item) for item in evidence_ids)

    replacement: str | None
    if status == "superseded":
        replacement = _text("superseded_by_lesson_id", superseded_by_lesson_id)
        if replacement == normalized_lesson:
            raise RetentionError("verified lesson cannot supersede itself")
    else:
        if superseded_by_lesson_id is not None:
            raise RetentionError("superseded_by_lesson_id is valid only for superseded state")
        replacement = None
    if status == "active" and previous_state_id is not None:
        raise RetentionError("initial active lesson state cannot have previous_state_id")
    if status in {"superseded", "revoked"} and previous_state_id is None:
        raise RetentionError("terminal lesson state requires previous_state_id")

    if status == "active":
        if transition_decision_id is not None:
            raise RetentionError("initial active state cannot bind a transition decision")
        decision_id = None
    else:
        decision_id = _text("transition_decision_id", transition_decision_id)

    provisional = VerifiedLessonState(
        state_id="",
        state_hash="",
        lesson_id=normalized_lesson,
        status=status,
        previous_state_id=previous_state_id,
        superseded_by_lesson_id=replacement,
        reason=_text("reason", reason),
        evidence_ids=normalized_evidence,
        transition_decision_id=decision_id,
    )
    digest = _hash(_state_material(provisional))
    return VerifiedLessonState(
        state_id=f"vls_{digest}",
        state_hash=digest,
        lesson_id=provisional.lesson_id,
        status=provisional.status,
        previous_state_id=provisional.previous_state_id,
        superseded_by_lesson_id=provisional.superseded_by_lesson_id,
        reason=provisional.reason,
        evidence_ids=provisional.evidence_ids,
        transition_decision_id=provisional.transition_decision_id,
    )


def _validate_state_record(state: VerifiedLessonState) -> VerifiedLessonState:
    if not isinstance(state, VerifiedLessonState):
        raise RetentionError("state must be VerifiedLessonState")
    if state.status not in _LIFECYCLE_STATUSES:
        raise RetentionError("verified lesson lifecycle status is invalid")
    if state.status == "superseded":
        if state.superseded_by_lesson_id is None:
            raise RetentionError("superseded state must bind replacement lesson")
        if state.superseded_by_lesson_id == state.lesson_id:
            raise RetentionError("verified lesson cannot supersede itself")
    elif state.superseded_by_lesson_id is not None:
        raise RetentionError("non-superseded state cannot bind replacement lesson")
    if state.status == "active" and state.previous_state_id is not None:
        raise RetentionError("active state previous_state_id is invalid")
    if state.status in {"superseded", "revoked"} and state.previous_state_id is None:
        raise RetentionError("terminal state previous_state_id is required")
    if state.status == "active" and state.transition_decision_id is not None:
        raise RetentionError("active state transition_decision_id is invalid")
    if state.status in {"superseded", "revoked"} and state.transition_decision_id is None:
        raise RetentionError("terminal state must bind a transition decision")
    digest = _hash(_state_material(state))
    if state.state_hash != digest or state.state_id != f"vls_{digest}":
        raise RetentionError("verified lesson lifecycle state identity/content is invalid")
    return state


def _decision_material(decision: RetentionDecision) -> dict[str, Any]:
    return {
        "retention_contract": decision.retention_contract,
        "retention_version": decision.retention_version,
        "preparation_id": decision.preparation_id,
        "status": decision.status,
        "verified_lesson_id": decision.verified_lesson.lesson_id,
        "lesson_state_id": decision.lesson_state.state_id,
        "trusted_approval_id": decision.trusted_approval_id,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "governance_mutation_authorized": False,
        "cmis_provider_trust_authorized": False,
        "wallet_authorized": False,
        "execution_authorized": False,
    }


def validate_retention_decision(decision: RetentionDecision) -> RetentionDecision:
    """Validate a retained decision and its content-addressed nested records."""

    if not isinstance(decision, RetentionDecision):
        raise RetentionError("decision must be RetentionDecision")
    if decision.retention_contract != RETENTION_CONTRACT:
        raise RetentionError("retention decision contract is invalid")
    if decision.retention_version != RETENTION_VERSION:
        raise RetentionError("retention decision version is invalid")
    if decision.status != "retained":
        raise RetentionError("Phase 10 v1 final retention decision must be retained")
    _validate_scope(decision.verified_lesson.lesson_scope)
    digest_lesson = _hash(_verified_lesson_material(decision.verified_lesson))
    if (
        decision.verified_lesson.lesson_hash != digest_lesson
        or decision.verified_lesson.lesson_id != f"vl_{digest_lesson}"
    ):
        raise RetentionError("verified lesson identity/content is invalid")
    _validate_state_record(decision.lesson_state)
    if decision.lesson_state.lesson_id != decision.verified_lesson.lesson_id:
        raise RetentionError("retention decision lesson state does not bind verified lesson")
    digest = _hash(_decision_material(decision))
    if decision.decision_hash != digest or decision.decision_id != f"rdec_{digest}":
        raise RetentionError("retention decision identity/content is invalid")
    return decision


def retain_verified_lesson(
    *,
    preparation: RetentionPreparation,
    lesson_store: InMemoryVerifiedLessonStore,
    approval_registry: RetentionApprovalRegistry,
    recorded_at: str,
) -> RetentionDecision:
    """Consume one exact trusted human approval and retain one verified lesson."""

    prepared = _validate_preparation(preparation)
    if prepared.status != "approval_required" or prepared.approval_request is None:
        raise RetentionError("retention preparation is not eligible for human-approved retention")
    if not isinstance(lesson_store, InMemoryVerifiedLessonStore):
        raise RetentionError("Phase 10 v1 requires the in-memory verified lesson store")

    request = prepared.approval_request
    trusted = approval_registry.get_application_approval(request.request_id)
    if trusted is None:
        raise RetentionError("trusted human retention approval is unavailable")
    _validate_trusted_approval(trusted)
    if trusted.request_id != request.request_id:
        raise RetentionError("trusted retention approval request identity mismatch")
    if trusted.proposal_sha256 != request.proposal_sha256:
        raise RetentionError("trusted retention approval proposal mismatch")
    if trusted.binding_sha256 != request.binding_sha256:
        raise RetentionError("trusted retention approval binding mismatch")
    if lesson_store.approval_binding_consumed(trusted.binding_sha256):
        raise RetentionError("retention approval binding was already consumed")

    # Active lesson state is mutable Phase 10 store state. Recheck it after the
    # exact human approval is resolved and before committing the lesson. Source
    # records/artifacts used by this v1 snapshot are immutable Phase 1 identities.
    _validate_lesson_snapshot_current(prepared, lesson_store)

    timestamp = _canonical_recorded_at(recorded_at)
    provisional_lesson = VerifiedLessonRecord(
        lesson_id="",
        lesson_hash="",
        verified_lesson_contract=VERIFIED_LESSON_CONTRACT,
        retention_contract=prepared.retention_contract,
        retention_version=prepared.retention_version,
        lesson_type=prepared.lesson_type,
        lesson_scope=prepared.lesson_scope,
        lesson_body=prepared.lesson_body,
        lesson_body_origin=prepared.lesson_body_origin,
        verification_id=prepared.verification_id,
        bundle_id=prepared.bundle_id,
        candidate_id=prepared.candidate_id,
        candidate_state_id=prepared.candidate_state_id,
        reflection_id=prepared.reflection_id,
        verification_plan_id=prepared.verification_plan_id,
        original_evaluation_id=prepared.original_evaluation_id,
        retest_evaluation_id=prepared.retest_evaluation_id,
        contradiction_snapshot_id=prepared.contradiction_snapshot.snapshot_id,
        confidence_level=prepared.confidence_level,
        confidence_score=prepared.confidence_score,
        confidence_basis=prepared.confidence_basis,
        approval_id=trusted.approval_id,
        approval_request_id=trusted.request_id,
        approval_proposal_sha256=trusted.proposal_sha256,
        approval_binding_sha256=trusted.binding_sha256,
        approval_thread_id=trusted.thread_id,
        approval_principal_id=trusted.human_principal_id,
        recorded_at=timestamp,
        created_by=prepared.created_by,
        producer_version=prepared.producer_version,
    )
    lesson_digest = _hash(_verified_lesson_material(provisional_lesson))
    lesson = VerifiedLessonRecord(
        lesson_id=f"vl_{lesson_digest}",
        lesson_hash=lesson_digest,
        verified_lesson_contract=provisional_lesson.verified_lesson_contract,
        retention_contract=provisional_lesson.retention_contract,
        retention_version=provisional_lesson.retention_version,
        lesson_type=provisional_lesson.lesson_type,
        lesson_scope=provisional_lesson.lesson_scope,
        lesson_body=provisional_lesson.lesson_body,
        lesson_body_origin=provisional_lesson.lesson_body_origin,
        verification_id=provisional_lesson.verification_id,
        bundle_id=provisional_lesson.bundle_id,
        candidate_id=provisional_lesson.candidate_id,
        candidate_state_id=provisional_lesson.candidate_state_id,
        reflection_id=provisional_lesson.reflection_id,
        verification_plan_id=provisional_lesson.verification_plan_id,
        original_evaluation_id=provisional_lesson.original_evaluation_id,
        retest_evaluation_id=provisional_lesson.retest_evaluation_id,
        contradiction_snapshot_id=provisional_lesson.contradiction_snapshot_id,
        confidence_level=provisional_lesson.confidence_level,
        confidence_score=provisional_lesson.confidence_score,
        confidence_basis=provisional_lesson.confidence_basis,
        approval_id=provisional_lesson.approval_id,
        approval_request_id=provisional_lesson.approval_request_id,
        approval_proposal_sha256=provisional_lesson.approval_proposal_sha256,
        approval_binding_sha256=provisional_lesson.approval_binding_sha256,
        approval_thread_id=provisional_lesson.approval_thread_id,
        approval_principal_id=provisional_lesson.approval_principal_id,
        recorded_at=provisional_lesson.recorded_at,
        created_by=provisional_lesson.created_by,
        producer_version=provisional_lesson.producer_version,
    )
    state = _build_state(
        lesson_id=lesson.lesson_id,
        status="active",
        previous_state_id=None,
        superseded_by_lesson_id=None,
        reason="initial_verified_retention",
        evidence_ids=(prepared.verification_id, prepared.contradiction_snapshot.snapshot_id),
        transition_decision_id=None,
    )
    lesson_store.commit_retention(
        lesson=lesson,
        state=state,
        approval_binding_sha256=trusted.binding_sha256,
    )

    provisional_decision = RetentionDecision(
        decision_id="",
        decision_hash="",
        retention_contract=prepared.retention_contract,
        retention_version=prepared.retention_version,
        preparation_id=prepared.preparation_id,
        status="retained",
        verified_lesson=lesson,
        lesson_state=state,
        trusted_approval_id=trusted.approval_id,
    )
    decision_digest = _hash(_decision_material(provisional_decision))
    decision = RetentionDecision(
        decision_id=f"rdec_{decision_digest}",
        decision_hash=decision_digest,
        retention_contract=provisional_decision.retention_contract,
        retention_version=provisional_decision.retention_version,
        preparation_id=provisional_decision.preparation_id,
        status=provisional_decision.status,
        verified_lesson=provisional_decision.verified_lesson,
        lesson_state=provisional_decision.lesson_state,
        trusted_approval_id=provisional_decision.trusted_approval_id,
    )
    return validate_retention_decision(decision)


def transition_verified_lesson_state(
    *,
    store: InMemoryVerifiedLessonStore,
    lesson_id: str,
    previous_state_id: str,
    status: str,
    reason: str,
    evidence_ids: tuple[str, ...],
    transition_decision_id: str,
    superseded_by_lesson_id: str | None = None,
) -> VerifiedLessonState:
    """Create one immutable superseded/revoked revision from the exact active state."""

    if not isinstance(store, InMemoryVerifiedLessonStore):
        raise RetentionError("Phase 10 v1 requires the in-memory verified lesson store")
    current = store.get_active_state(lesson_id)
    if current is None or current.state_id != previous_state_id:
        raise RetentionError("lifecycle transition requires exact active predecessor")
    if status not in {"superseded", "revoked"}:
        raise RetentionError("Phase 10 lifecycle transition must be superseded or revoked")
    state = _build_state(
        lesson_id=lesson_id,
        status=status,
        previous_state_id=previous_state_id,
        superseded_by_lesson_id=superseded_by_lesson_id,
        reason=reason,
        evidence_ids=evidence_ids,
        transition_decision_id=transition_decision_id,
    )
    store.transition_state(state)
    return state
