from __future__ import annotations

from dataclasses import replace

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from roberta.approval import (
    build_approval_graph,
    build_approval_resume_payload,
    start_approval,
)
from roberta.approval.runtime import resume_approval_authenticated
from roberta.learning import (
    InMemorySourceStore,
    build_learning_candidate_bundle,
    ingest_utf8_source,
    verify_candidate_lesson,
)
from roberta.learning.retention import (
    InMemoryVerifiedLessonStore,
    RetentionError,
    build_retention_proposal,
    finalize_retention,
)
from tests.test_learning_verification import _fixture


def _source_store() -> InMemorySourceStore:
    store = InMemorySourceStore()
    ingest_utf8_source(
        store=store,
        content="# Evidence\nRoberta preserves exact evidence citations.\n",
        origin="test://verification/basic",
        title="Verification Fixture",
        version="1",
        authority_class="internal",
        approval_status="approved",
        parser_version="utf8-source/v1",
    )
    return store


def _verified_fixture(*, lesson_text: str | None = None, retest_passes: bool = True):
    packet, failed_grounded, case, evaluation, bundle, corrected = _fixture()
    if lesson_text is not None:
        bundle = build_learning_candidate_bundle(
            packet=packet,
            grounded_result=failed_grounded,
            golden_case=case,
            evaluation=evaluation,
            reflection_text=bundle.reflection.reflection_text,
            lesson_text=lesson_text,
            rationale=bundle.candidate.rationale,
            created_by=bundle.candidate.created_by,
            producer_version=bundle.candidate.producer_version,
        )
    retest = corrected if retest_passes else failed_grounded
    verification = verify_candidate_lesson(
        packet=packet,
        grounded_result=failed_grounded,
        golden_case=case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=packet,
        retest_grounded_result=retest,
        created_by="test-verifier",
        producer_version="test-verifier/1",
    )
    return {
        "packet": packet,
        "grounded_result": failed_grounded,
        "golden_case": case,
        "evaluation": evaluation,
        "bundle": bundle,
        "retest_packet": packet,
        "retest_grounded_result": retest,
        "verification_result": verification,
        "source_store": _source_store(),
    }


def _build(data, retention_store, *, request_id: str):
    return build_retention_proposal(
        **data,
        retention_store=retention_store,
        approval_request_id=request_id,
    )


def _approve(request, *, thread_id: str, principal: str = "test-user:phase10"):
    graph = build_approval_graph(checkpointer=InMemorySaver())
    paused = start_approval(graph, request, thread_id=thread_id)
    assert paused["__interrupt__"]
    decision = build_approval_resume_payload(request, "approve")
    assert "human_principal_id" not in decision
    state, context = resume_approval_authenticated(
        graph,
        decision,
        thread_id=thread_id,
        human_principal_id=principal,
    )
    assert state["status"] == "approved"
    assert context.human_principal_id == principal
    return context


def _finalize(data, retention_store, proposal, approval):
    return finalize_retention(
        **data,
        retention_store=retention_store,
        proposal=proposal,
        approval=approval,
        created_by="test-retention",
        producer_version="test-retention/1",
    )


def test_verified_lesson_requires_exact_human_approval_and_preserves_authority_bounds():
    data = _verified_fixture()
    store = InMemoryVerifiedLessonStore()
    proposal = _build(data, store, request_id="retain-1")

    assert proposal.status == "approval_required"
    assert proposal.contradiction_snapshot is not None
    assert proposal.contradiction_snapshot.complete is True
    assert proposal.contradiction_snapshot.contradiction_status == "clear"
    assert len(proposal.contradiction_snapshot.source_members) == 1
    assert proposal.confidence_basis == (
        "candidate_verification_status:verified_for_learning",
        "calibrated_probability:unavailable",
    )

    approval = _approve(proposal.approval_request, thread_id="retention-thread-1")
    result = _finalize(data, store, proposal, approval)

    assert result.decision.status == "retained"
    assert result.lesson is not None
    assert result.lifecycle is not None
    assert result.lifecycle.state == "active"
    assert result.lesson.verified is True
    assert result.lesson.body_origin == "generated_candidate"
    assert ("verification_id", data["verification_result"].verification_id) in result.lesson.verification_refs
    assert result.lesson.source_truth_authorized is False
    assert result.lesson.live_state_authorized is False
    assert result.lesson.governance_mutation_authorized is False
    assert result.lesson.provider_trust_mutation_authorized is False
    assert result.lesson.external_memory_write_authorized is False
    assert result.lesson.wallet_authorized is False
    assert result.lesson.execution_authorized is False
    assert store.approval_consumed(proposal.approval_request.binding_sha256) is True
    assert store.revision == 1


def test_tampered_phase9_verification_fails_before_retention():
    data = _verified_fixture()
    data["verification_result"] = replace(
        data["verification_result"],
        verification_hash="0" * 64,
    )
    with pytest.raises(RetentionError, match="Phase 9 verification revalidation failed"):
        _build(data, InMemoryVerifiedLessonStore(), request_id="retain-tampered")


def test_only_verified_for_learning_is_retention_eligible():
    data = _verified_fixture(retest_passes=False)
    assert data["verification_result"].status == "rejected"
    proposal = _build(data, InMemoryVerifiedLessonStore(), request_id="retain-rejected")

    assert proposal.status == "rejected"
    assert proposal.approval_request is None
    assert proposal.confidence_basis[0] == "candidate_verification_status:rejected"


def test_missing_approved_source_scope_is_inconclusive_never_clear():
    data = _verified_fixture()
    data["source_store"] = InMemorySourceStore()
    proposal = _build(data, InMemoryVerifiedLessonStore(), request_id="retain-missing-source")

    assert proposal.status == "inconclusive"
    assert proposal.approval_request is None
    assert proposal.contradiction_snapshot is None
    assert "contradiction_scope_unavailable" in proposal.reasons[0]


def test_explicit_store_conflict_blocks_retention_without_human_approval():
    data = _verified_fixture()
    store = InMemoryVerifiedLessonStore()
    initial = _build(data, store, request_id="retain-conflict-seed")
    store.record_conflict_evidence(
        lesson_key=initial.lesson_key,
        evidence_id="accepted-conflict-evidence:1",
    )
    blocked = _build(data, store, request_id="retain-conflict")

    assert blocked.status == "rejected"
    assert blocked.approval_request is None
    assert blocked.contradiction_snapshot is not None
    assert blocked.contradiction_snapshot.contradiction_status == "conflict"
    result = _finalize(data, store, blocked, None)
    assert result.decision.status == "rejected"
    assert result.lesson is None


def test_exact_duplicate_does_not_create_parallel_trusted_lesson():
    data = _verified_fixture()
    store = InMemoryVerifiedLessonStore()
    first = _build(data, store, request_id="retain-first")
    first_result = _finalize(
        data,
        store,
        first,
        _approve(first.approval_request, thread_id="retention-thread-first"),
    )

    duplicate = _build(data, store, request_id="retain-duplicate")
    assert duplicate.status == "duplicate"
    assert duplicate.duplicate_lesson_id == first_result.lesson.lesson_id
    assert duplicate.approval_request is None

    duplicate_result = _finalize(data, store, duplicate, None)
    assert duplicate_result.decision.status == "duplicate"
    assert duplicate_result.lesson is None
    assert store.get_lesson(first_result.lesson.lesson_id) == first_result.lesson


def test_nonidentical_active_overlapping_lesson_fails_closed_as_inconclusive():
    first_data = _verified_fixture()
    store = InMemoryVerifiedLessonStore()
    first = _build(first_data, store, request_id="retain-overlap-first")
    _finalize(
        first_data,
        store,
        first,
        _approve(first.approval_request, thread_id="retention-thread-overlap-first"),
    )

    second_data = _verified_fixture(
        lesson_text="Answer only with claims that remain inside the exact supported evidence boundary."
    )
    second = _build(second_data, store, request_id="retain-overlap-second")
    assert second.status == "inconclusive"
    assert second.contradiction_snapshot is not None
    assert second.contradiction_snapshot.contradiction_status == "inconclusive"
    assert second.approval_request is None


def test_caller_cannot_replace_authenticated_approval_runtime_with_none_or_wrong_request():
    data = _verified_fixture()
    store = InMemoryVerifiedLessonStore()
    proposal = _build(data, store, request_id="retain-exact")

    with pytest.raises(RetentionError, match="AuthenticatedApprovalContext"):
        _finalize(data, store, proposal, None)

    other = _build(data, store, request_id="retain-other")
    wrong_approval = _approve(
        other.approval_request,
        thread_id="retention-thread-wrong",
        principal="test-user:wrong-binding",
    )
    with pytest.raises(RetentionError, match="approval request does not match"):
        _finalize(data, store, proposal, wrong_approval)


def test_approval_binding_is_one_time_and_cannot_be_replayed():
    data = _verified_fixture()
    store = InMemoryVerifiedLessonStore()
    proposal = _build(data, store, request_id="retain-once")
    approval = _approve(proposal.approval_request, thread_id="retention-thread-once")
    _finalize(data, store, proposal, approval)

    with pytest.raises(RetentionError, match="already been consumed"):
        _finalize(data, store, proposal, approval)


def test_revocation_is_immutable_auditable_and_advances_scope_revision():
    data = _verified_fixture()
    store = InMemoryVerifiedLessonStore()
    proposal = _build(data, store, request_id="retain-revoke")
    retained = _finalize(
        data,
        store,
        proposal,
        _approve(proposal.approval_request, thread_id="retention-thread-revoke"),
    )
    revision_after_retention = store.revision

    revoked = store.transition_lifecycle(
        lesson_id=retained.lesson.lesson_id,
        state="revoked",
        reason="accepted deterministic invalidation fixture",
    )

    history = store.lifecycle_history(retained.lesson.lesson_id)
    assert len(history) == 2
    assert history[0].state == "active"
    assert history[1] == revoked
    assert revoked.previous_state_id == history[0].state_id
    assert store.revision == revision_after_retention + 1

    retry = _build(data, store, request_id="retain-after-revoke")
    assert retry.status == "inconclusive"
    assert retry.reasons == ("matching_verified_lesson_is_not_active",)
