from __future__ import annotations

from dataclasses import replace
import inspect

import pytest

from roberta.approval import ApprovalDecision, resolve_approval_decision
from roberta.learning import (
    InMemoryRetentionApprovalRegistry,
    InMemorySourceStore,
    InMemoryVerifiedLessonStore,
    RetentionError,
    build_evidence_index,
    build_evidence_packet,
    build_learning_candidate_bundle,
    chunk_parsed_document,
    ingest_utf8_source,
    make_answer_candidate,
    make_answer_claim,
    make_golden_claim_criterion,
    make_golden_evaluation_case,
    make_lesson_scope,
    parse_markdown_structure,
    prepare_verified_lesson_retention,
    retain_verified_lesson,
    retrieve_evidence,
    transition_verified_lesson_state,
    validate_answer_candidate,
    verify_candidate_lesson,
)
from roberta.learning.evaluation import evaluate_grounded_answer
from roberta.learning.indexing import IndexedDocument
from roberta.learning.retrieval import RetrievalCorpusItem
import roberta.learning.retention as retention_module


LESSON = "Keep generated claims inside the evaluated evidence-backed claim scope."
OTHER_LESSON = "Do not add generated claims outside the accepted evidence-backed scope."


def _phase9_fixture(
    *,
    lesson_text: str = LESSON,
    origin: str = "test://retention/source-a",
    corrected: bool = True,
):
    source_store = InMemorySourceStore()
    source = ingest_utf8_source(
        store=source_store,
        content=lesson_text + "\n",
        origin=origin,
        title="Retention procedural source",
        version="1",
        authority_class="internal",
        approval_status="approved",
        parser_version="utf8-source/v1",
    ).record
    parsed = parse_markdown_structure(store=source_store, source_id=source.source_id)
    chunked = chunk_parsed_document(store=source_store, parsed=parsed, max_chars=1600)
    indexed: IndexedDocument = build_evidence_index(store=source_store, chunked=chunked)
    item = RetrievalCorpusItem(chunked=chunked, indexed=indexed)
    retrieval = retrieve_evidence(
        store=source_store,
        corpus=(item,),
        text="generated claims evidence-backed scope",
        top_k=2,
    )
    packet = build_evidence_packet(store=source_store, corpus=(item,), result=retrieval)

    supported = make_answer_claim(
        claim_id="claim-1",
        text=lesson_text,
        status="supported",
        evidence_anchors=("E1",),
    )
    extra = make_answer_claim(
        claim_id="claim-extra",
        text="An extra generated claim.",
        status="supported",
        evidence_anchors=("E1",),
    )
    failed_grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text=f"{lesson_text} An extra generated claim.",
            claims=(supported, extra),
        ),
    )
    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        allowed_evidence_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        required_text_substrings=("evidence-backed",),
    )
    case = make_golden_evaluation_case(
        question="What procedural rule does the source state?",
        expected_behavior="answer",
        relevant_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        claim_criteria=(criterion,),
        required_answer_substrings=("evidence-backed",),
        expected_packet_id=packet.packet_id,
        expected_retrieval_id=failed_grounded.retrieval_id,
        provenance_uri=origin + "/golden",
        authored_by="test-suite",
    )
    evaluation = evaluate_grounded_answer(
        packet=packet,
        result=failed_grounded,
        case=case,
    )
    assert evaluation.failure_classifications == ("unsupported_claim_failure",)

    bundle = build_learning_candidate_bundle(
        packet=packet,
        grounded_result=failed_grounded,
        golden_case=case,
        evaluation=evaluation,
        reflection_text="The answer added a generated claim outside the accepted claim criteria.",
        lesson_text=lesson_text,
        rationale="The canonical evaluator classified an unsupported structured claim.",
        created_by="test-reflector",
        producer_version="test-reflector/1",
    )
    corrected_grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text=lesson_text,
            claims=(supported,),
        ),
    )
    retest = corrected_grounded if corrected else failed_grounded
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
        "source_store": source_store,
        "source": source,
        "packet": packet,
        "failed_grounded": failed_grounded,
        "case": case,
        "evaluation": evaluation,
        "bundle": bundle,
        "retest_grounded": retest,
        "verification": verification,
    }


def _scope(fixture: dict, *, lesson_key: str = "unsupported-claim-discipline"):
    return make_lesson_scope(
        lesson_key=lesson_key,
        domain="learning-system",
        task="grounded-answer-generation",
        source_ids=(fixture["source"].source_id,),
    )


def _prepare(
    fixture: dict,
    *,
    lesson_store: InMemoryVerifiedLessonStore | None = None,
    scope=None,
    lesson_type: str = "procedural",
    approval_attempt: int = 1,
):
    lesson_store = lesson_store or InMemoryVerifiedLessonStore()
    scope = scope or _scope(fixture)
    result = prepare_verified_lesson_retention(
        packet=fixture["packet"],
        grounded_result=fixture["failed_grounded"],
        golden_case=fixture["case"],
        evaluation=fixture["evaluation"],
        bundle=fixture["bundle"],
        retest_packet=fixture["packet"],
        retest_grounded_result=fixture["retest_grounded"],
        verification_result=fixture["verification"],
        source_store=fixture["source_store"],
        lesson_store=lesson_store,
        lesson_type=lesson_type,
        lesson_scope=scope,
        approval_attempt=approval_attempt,
        created_by="test-curator",
        producer_version="test-curator/1",
    )
    return lesson_store, result


def _record_approval(preparation, registry, *, principal="human:user-1", thread="retention-thread-1"):
    request = preparation.approval_request
    assert request is not None
    decision = ApprovalDecision.from_resume(
        {
            "request_id": request.request_id,
            "proposal_sha256": request.proposal_sha256,
            "binding_sha256": request.binding_sha256,
            "decision": "approve",
        },
        request=request,
    )
    outcome = resolve_approval_decision(request, decision)
    return registry.record_application_approval(
        request=request,
        outcome=outcome,
        thread_id=thread,
        human_principal_id=principal,
    )


def test_canonical_phase9_result_is_revalidated_before_retention() -> None:
    fixture = _phase9_fixture()
    tampered = replace(fixture["verification"], status="rejected")

    with pytest.raises(RetentionError, match="canonical Phase 9 verification"):
        prepare_verified_lesson_retention(
            packet=fixture["packet"],
            grounded_result=fixture["failed_grounded"],
            golden_case=fixture["case"],
            evaluation=fixture["evaluation"],
            bundle=fixture["bundle"],
            retest_packet=fixture["packet"],
            retest_grounded_result=fixture["retest_grounded"],
            verification_result=tampered,
            source_store=fixture["source_store"],
            lesson_store=InMemoryVerifiedLessonStore(),
            lesson_type="procedural",
            lesson_scope=_scope(fixture),
            approval_attempt=1,
            created_by="test-curator",
            producer_version="1",
        )


def test_only_verified_for_learning_is_retention_eligible() -> None:
    fixture = _phase9_fixture(corrected=False)
    assert fixture["verification"].status == "rejected"

    with pytest.raises(RetentionError, match="verified_for_learning"):
        _prepare(fixture)


def test_unsupported_lesson_type_fails_closed() -> None:
    fixture = _phase9_fixture()
    with pytest.raises(RetentionError, match="lesson_type"):
        _prepare(fixture, lesson_type="semantic")


def test_complete_source_snapshot_is_provider_built_and_content_addressed() -> None:
    fixture = _phase9_fixture()
    _, first = _prepare(fixture)
    _, second = _prepare(fixture)

    assert first.status == "approval_required"
    assert first.contradiction_snapshot == second.contradiction_snapshot
    snapshot = first.contradiction_snapshot
    assert snapshot.source_count == 1
    assert snapshot.active_lesson_count == 0
    assert snapshot.source_ids == (fixture["source"].source_id,)
    assert snapshot.source_snapshot_complete is True
    assert snapshot.lesson_snapshot_complete is True
    assert snapshot.status == "clear"
    assert snapshot.snapshot_id.startswith("rcs_")


def test_caller_selected_source_subset_fails_closed() -> None:
    fixture = _phase9_fixture()
    scope = make_lesson_scope(
        lesson_key="unsupported-claim-discipline",
        domain="learning-system",
        task="grounded-answer-generation",
        source_ids=("src_missing",),
    )
    with pytest.raises(RetentionError, match="complete canonical Phase 8 evidence source scope"):
        _prepare(fixture, scope=scope)


def test_source_must_exactly_support_first_slice_procedural_lesson() -> None:
    fixture = _phase9_fixture()
    fixture["source_store"]._artifacts[fixture["source"].artifact_ref] = b"Different source text.\n"

    with pytest.raises(RetentionError, match="canonical source artifact"):
        _prepare(fixture)


def test_conflicting_active_lesson_blocks_retention() -> None:
    first_fixture = _phase9_fixture(lesson_text=LESSON, origin="test://retention/conflict-a")
    lesson_store, first = _prepare(first_fixture)
    registry = InMemoryRetentionApprovalRegistry()
    _record_approval(first, registry)
    retained = retain_verified_lesson(
        preparation=first,
        lesson_store=lesson_store,
        approval_registry=registry,
        recorded_at="2026-08-21T14:00:00Z",
    )
    assert retained.status == "retained"

    second_fixture = _phase9_fixture(
        lesson_text=OTHER_LESSON,
        origin="test://retention/conflict-b",
    )
    second_scope = make_lesson_scope(
        lesson_key="unsupported-claim-discipline",
        domain="learning-system",
        task="grounded-answer-generation",
        source_ids=(second_fixture["source"].source_id,),
    )
    _, blocked = _prepare(second_fixture, lesson_store=lesson_store, scope=second_scope)

    assert blocked.status == "rejected"
    assert blocked.approval_request is None
    assert blocked.contradiction_snapshot.status == "conflict"
    assert retained.verified_lesson.lesson_id in blocked.contradiction_snapshot.active_lesson_ids


def test_exact_duplicate_does_not_create_second_trusted_lesson() -> None:
    fixture = _phase9_fixture()
    lesson_store, first = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()
    _record_approval(first, registry)
    retained = retain_verified_lesson(
        preparation=first,
        lesson_store=lesson_store,
        approval_registry=registry,
        recorded_at="2026-08-21T14:00:00Z",
    )

    _, duplicate = _prepare(fixture, lesson_store=lesson_store, approval_attempt=2)
    assert duplicate.status == "duplicate"
    assert duplicate.approval_request is None
    assert duplicate.existing_lesson_id == retained.verified_lesson.lesson_id
    assert len(lesson_store.list_active()) == 1
    assert lesson_store.get_preparation(duplicate.preparation_id) == duplicate
    assert lesson_store.get_preparation(duplicate.preparation_id).verification_id == fixture["verification"].verification_id


def test_confidence_basis_never_invents_numeric_probability() -> None:
    fixture = _phase9_fixture()
    _, preparation = _prepare(fixture)

    assert preparation.confidence_level == "verification_passed_uncalibrated"
    assert preparation.confidence_score is None
    assert "calibrated_probability_unavailable" in preparation.confidence_basis


def test_preparation_builds_exact_human_retention_approval_request() -> None:
    fixture = _phase9_fixture()
    _, preparation = _prepare(fixture)
    request = preparation.approval_request

    assert preparation.status == "approval_required"
    assert request is not None
    assert request.action_type == "retain_verified_lesson"
    assert "verified-lesson-retention/v1" in request.scope
    assert preparation.preparation_id in request.proposal["preparation_id"]
    assert request.proposal["verification_id"] == fixture["verification"].verification_id
    assert request.proposal["source_truth_authorized"] is False
    assert request.proposal["execution_authorized"] is False


def test_only_trusted_human_application_approval_can_retain() -> None:
    fixture = _phase9_fixture()
    lesson_store, preparation = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()

    with pytest.raises(RetentionError, match="trusted human retention approval"):
        retain_verified_lesson(
            preparation=preparation,
            lesson_store=lesson_store,
            approval_registry=registry,
            recorded_at="2026-08-21T14:00:00Z",
        )

    with pytest.raises(RetentionError, match="human_principal_id"):
        _record_approval(preparation, registry, principal="")

    trusted = _record_approval(preparation, registry)
    result = retain_verified_lesson(
        preparation=preparation,
        lesson_store=lesson_store,
        approval_registry=registry,
        recorded_at="2026-08-21T14:00:00Z",
    )
    assert trusted.authority == "human_review/v1"
    assert result.status == "retained"
    assert result.verified_lesson.approval_principal_id == "human:user-1"
    assert result.verified_lesson.approval_thread_id == "retention-thread-1"


def test_changed_preparation_cannot_borrow_existing_approval() -> None:
    fixture = _phase9_fixture()
    lesson_store, preparation = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()
    _record_approval(preparation, registry)
    tampered = replace(preparation, confidence_level="calibrated_high")

    with pytest.raises(RetentionError, match="preparation identity/content"):
        retain_verified_lesson(
            preparation=tampered,
            lesson_store=lesson_store,
            approval_registry=registry,
            recorded_at="2026-08-21T14:00:00Z",
        )


def test_consumed_approval_binding_cannot_be_replayed() -> None:
    fixture = _phase9_fixture()
    lesson_store, preparation = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()
    _record_approval(preparation, registry)
    retain_verified_lesson(
        preparation=preparation,
        lesson_store=lesson_store,
        approval_registry=registry,
        recorded_at="2026-08-21T14:00:00Z",
    )

    with pytest.raises(RetentionError, match="already consumed"):
        retain_verified_lesson(
            preparation=preparation,
            lesson_store=lesson_store,
            approval_registry=registry,
            recorded_at="2026-08-21T14:00:00Z",
        )


def test_retained_record_preserves_phase8_phase9_and_gate_provenance() -> None:
    fixture = _phase9_fixture()
    lesson_store, preparation = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()
    _record_approval(preparation, registry)
    result = retain_verified_lesson(
        preparation=preparation,
        lesson_store=lesson_store,
        approval_registry=registry,
        recorded_at="2026-08-21T14:00:00Z",
    )
    lesson = result.verified_lesson

    assert lesson.verification_id == fixture["verification"].verification_id
    assert lesson.bundle_id == fixture["bundle"].bundle_id
    assert lesson.candidate_id == fixture["bundle"].candidate.candidate_id
    assert lesson.reflection_id == fixture["bundle"].reflection.reflection_id
    assert lesson.verification_plan_id == fixture["bundle"].verification_plan.plan_id
    assert lesson.original_evaluation_id == fixture["evaluation"].evaluation_id
    assert lesson.retest_evaluation_id == fixture["verification"].retest_evaluation_id
    assert lesson.contradiction_snapshot_id == preparation.contradiction_snapshot.snapshot_id
    assert lesson.confidence_level == preparation.confidence_level
    assert lesson.approval_binding_sha256 == preparation.approval_request.binding_sha256


def test_verified_lesson_identity_is_reproducible_and_tamper_sensitive() -> None:
    fixture = _phase9_fixture()
    lesson_store, preparation = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()
    _record_approval(preparation, registry)
    first = retain_verified_lesson(
        preparation=preparation,
        lesson_store=lesson_store,
        approval_registry=registry,
        recorded_at="2026-08-21T14:00:00Z",
    )
    lesson = first.verified_lesson
    assert lesson.lesson_id.startswith("vl_")
    assert lesson.lesson_id == f"vl_{lesson.lesson_hash}"

    tampered = replace(lesson, lesson_body="Tampered body")
    with pytest.raises(RetentionError, match="verified lesson identity/content"):
        lesson_store.validate_lesson(tampered)


def test_verified_lesson_lifecycle_requires_exact_active_predecessor() -> None:
    fixture = _phase9_fixture()
    lesson_store, preparation = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()
    _record_approval(preparation, registry)
    retained = retain_verified_lesson(
        preparation=preparation,
        lesson_store=lesson_store,
        approval_registry=registry,
        recorded_at="2026-08-21T14:00:00Z",
    )
    active = retained.lesson_state

    revoked = transition_verified_lesson_state(
        store=lesson_store,
        lesson_id=retained.verified_lesson.lesson_id,
        previous_state_id=active.state_id,
        status="revoked",
        reason="Later deterministic evidence invalidated the procedure.",
        evidence_ids=(fixture["verification"].verification_id,),
        transition_decision_id="retention-lifecycle-decision:revoke-1",
    )
    assert revoked.previous_state_id == active.state_id
    assert revoked.status == "revoked"
    assert lesson_store.get_active_state(retained.verified_lesson.lesson_id) is None

    with pytest.raises(RetentionError, match="exact active predecessor"):
        transition_verified_lesson_state(
            store=lesson_store,
            lesson_id=retained.verified_lesson.lesson_id,
            previous_state_id="vls_unrelated",
            status="revoked",
            reason="Invalid replay.",
            evidence_ids=(fixture["verification"].verification_id,),
            transition_decision_id="retention-lifecycle-decision:replay",
        )


def test_all_phase10_records_deny_external_truth_governance_wallet_and_execution_authority() -> None:
    fixture = _phase9_fixture()
    lesson_store, preparation = _prepare(fixture)
    registry = InMemoryRetentionApprovalRegistry()
    trusted = _record_approval(preparation, registry)
    retained = retain_verified_lesson(
        preparation=preparation,
        lesson_store=lesson_store,
        approval_registry=registry,
        recorded_at="2026-08-21T14:00:00Z",
    )

    records = (
        preparation,
        preparation.contradiction_snapshot,
        trusted,
        retained,
        retained.verified_lesson,
        retained.lesson_state,
    )
    for record in records:
        assert record.source_truth_authorized is False
        assert record.live_state_authorized is False
        assert record.governance_mutation_authorized is False
        assert record.cmis_provider_trust_authorized is False
        assert record.wallet_authorized is False
        assert record.execution_authorized is False


def test_phase10_module_has_no_hxmp_write_dependency() -> None:
    source = inspect.getsource(retention_module).lower()
    assert "roberta.memory.hxmp" not in source
    assert "write-soul" not in source
    assert "execute_prepared_write" not in source
