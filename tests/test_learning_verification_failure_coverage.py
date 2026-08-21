from __future__ import annotations

from dataclasses import replace

import pytest

import roberta.learning.verification as verification_module
from roberta.learning import (
    InMemorySourceStore,
    RetrievalCorpusItem,
    VerificationCheck,
    VerificationError,
    build_evidence_index,
    build_evidence_packet,
    build_learning_candidate_bundle,
    chunk_parsed_document,
    ingest_utf8_source,
    make_answer_candidate,
    make_answer_claim,
    make_golden_claim_criterion,
    make_golden_evaluation_case,
    parse_markdown_structure,
    retrieve_evidence,
    validate_answer_candidate,
    verify_candidate_lesson,
)
from roberta.learning.evaluation import evaluate_grounded_answer


def _item(
    *,
    store: InMemorySourceStore,
    content: str,
    origin: str,
    title: str,
) -> RetrievalCorpusItem:
    source = ingest_utf8_source(
        store=store,
        content=content,
        origin=origin,
        title=title,
        version="1",
        authority_class="internal",
        approval_status="approved",
        parser_version="utf8-source/v1",
    ).record
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)
    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=1600)
    indexed = build_evidence_index(store=store, chunked=chunked)
    return RetrievalCorpusItem(chunked=chunked, indexed=indexed)


def _packet(
    *,
    store: InMemorySourceStore,
    corpus: tuple[RetrievalCorpusItem, ...],
    text: str,
    top_k: int = 2,
):
    retrieval = retrieve_evidence(
        store=store,
        corpus=corpus,
        text=text,
        top_k=top_k,
    )
    return build_evidence_packet(store=store, corpus=corpus, result=retrieval)


def _bundle(*, packet, grounded, case):
    evaluation = evaluate_grounded_answer(packet=packet, result=grounded, case=case)
    assert evaluation.aggregate_status == "fail"
    bundle = build_learning_candidate_bundle(
        packet=packet,
        grounded_result=grounded,
        golden_case=case,
        evaluation=evaluation,
        reflection_text="The deterministic evaluation identified a behavior that requires an independent retest.",
        lesson_text="Retest the exact failed behavior before treating the candidate as reusable learning.",
        rationale="The candidate is provisional and remains bound to the accepted failure classification.",
        created_by="coverage-reflector",
        producer_version="coverage-reflector/1",
    )
    return evaluation, bundle


def _verify(*, packet, grounded, case, evaluation, bundle, retest_packet, retest_grounded):
    return verify_candidate_lesson(
        packet=packet,
        grounded_result=grounded,
        golden_case=case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=retest_packet,
        retest_grounded_result=retest_grounded,
        created_by="coverage-verifier",
        producer_version="coverage-verifier/1",
    )


def _single_packet_fixture():
    store = InMemorySourceStore()
    item = _item(
        store=store,
        content="# Evidence\nRoberta preserves exact evidence citations.\n",
        origin="test://verification-coverage/single",
        title="Single Evidence Fixture",
    )
    packet = _packet(
        store=store,
        corpus=(item,),
        text="exact evidence citations",
        top_k=1,
    )
    return store, item, packet


def _passing_retest_evaluation():
    _, _, packet = _single_packet_fixture()
    claim = make_answer_claim(
        claim_id="claim-1",
        text="Roberta preserves exact evidence citations.",
        status="supported",
        evidence_anchors=("E1",),
    )
    grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations.",
            claims=(claim,),
        ),
    )
    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        allowed_evidence_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        required_text_substrings=("exact evidence",),
    )
    case = make_golden_evaluation_case(
        question="What does the source say?",
        expected_behavior="answer",
        relevant_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        claim_criteria=(criterion,),
        provenance_uri="test://golden/verification-coverage-pass",
        authored_by="test-suite",
    )
    evaluation = evaluate_grounded_answer(packet=packet, result=grounded, case=case)
    assert evaluation.aggregate_status == "pass"
    return packet, grounded, evaluation


def test_retrieval_failure_check_passes_only_after_labeled_evidence_is_recovered() -> None:
    store = InMemorySourceStore()
    original_item = _item(
        store=store,
        content="# Original\nOriginal evidence is present.\n",
        origin="test://verification-coverage/retrieval-original",
        title="Original Evidence",
    )
    target_item = _item(
        store=store,
        content="# Target\nTarget evidence should be recovered.\n",
        origin="test://verification-coverage/retrieval-target",
        title="Target Evidence",
    )
    corpus = (original_item, target_item)
    original_packet = _packet(
        store=store,
        corpus=corpus,
        text="original evidence",
        top_k=1,
    )
    retest_packet = _packet(
        store=store,
        corpus=corpus,
        text="target evidence",
        top_k=1,
    )
    assert original_packet.evidence_anchors[0].chunk_id != retest_packet.evidence_anchors[0].chunk_id

    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        required_text_substrings=("evidence",),
    )
    case = make_golden_evaluation_case(
        question="Recover the labeled target evidence.",
        expected_behavior="answer",
        relevant_chunk_ids=(retest_packet.evidence_anchors[0].chunk_id,),
        claim_criteria=(criterion,),
        provenance_uri="test://golden/verification-retrieval",
        authored_by="test-suite",
    )
    original_claim = make_answer_claim(
        claim_id="claim-1",
        text="Original evidence is present.",
        status="supported",
        evidence_anchors=("E1",),
    )
    original_grounded = validate_answer_candidate(
        packet=original_packet,
        candidate=make_answer_candidate(
            packet_id=original_packet.packet_id,
            answer_text="Original evidence is present.",
            claims=(original_claim,),
        ),
    )
    evaluation, bundle = _bundle(packet=original_packet, grounded=original_grounded, case=case)
    assert evaluation.failure_classifications == ("retrieval_failure",)
    assert bundle.verification_plan.checks[0].check_kind == "retest_retrieval_against_golden_case"

    retest_claim = make_answer_claim(
        claim_id="claim-1",
        text="Target evidence should be recovered.",
        status="supported",
        evidence_anchors=("E1",),
    )
    retest_grounded = validate_answer_candidate(
        packet=retest_packet,
        candidate=make_answer_candidate(
            packet_id=retest_packet.packet_id,
            answer_text="Target evidence should be recovered.",
            claims=(retest_claim,),
        ),
    )
    result = _verify(
        packet=original_packet,
        grounded=original_grounded,
        case=case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=retest_packet,
        retest_grounded=retest_grounded,
    )

    assert result.status == "verified_for_learning"
    assert result.checks[0].status == "pass"
    assert result.checks[0].details == ("dimension:retrieval_coverage:pass",)


def test_answer_correctness_check_requires_corrected_answer_dimension() -> None:
    _, _, packet = _single_packet_fixture()
    claim = make_answer_claim(
        claim_id="claim-1",
        text="Roberta preserves exact evidence citations.",
        status="supported",
        evidence_anchors=("E1",),
    )
    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        allowed_evidence_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        required_text_substrings=("exact evidence",),
    )
    case = make_golden_evaluation_case(
        question="State the evidence rule and required conclusion.",
        expected_behavior="answer",
        relevant_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        claim_criteria=(criterion,),
        required_answer_substrings=("required conclusion",),
        provenance_uri="test://golden/verification-answer-correctness",
        authored_by="test-suite",
    )
    failed_grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations.",
            claims=(claim,),
        ),
    )
    evaluation, bundle = _bundle(packet=packet, grounded=failed_grounded, case=case)
    assert evaluation.failure_classifications == ("answer_correctness_failure",)
    assert tuple(check.check_kind for check in bundle.verification_plan.checks) == (
        "rerun_golden_case_answer_correctness",
    )

    corrected = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations. Required conclusion.",
            claims=(claim,),
        ),
    )
    result = _verify(
        packet=packet,
        grounded=failed_grounded,
        case=case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=packet,
        retest_grounded=corrected,
    )

    assert result.status == "verified_for_learning"
    assert result.checks[0].details == (
        "dimension:answer_correctness:pass",
        "dimension:limitation_disclosure:pass",
    )


def test_answer_completeness_check_requires_all_labeled_required_claims() -> None:
    _, _, packet = _single_packet_fixture()
    claim_one = make_answer_claim(
        claim_id="claim-1",
        text="Roberta preserves exact evidence citations.",
        status="supported",
        evidence_anchors=("E1",),
    )
    claim_two = make_answer_claim(
        claim_id="claim-2",
        text="Exact evidence remains explicitly cited.",
        status="supported",
        evidence_anchors=("E1",),
    )
    criteria = (
        make_golden_claim_criterion(
            claim_id="claim-1",
            allowed_evidence_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
            required_text_substrings=("exact evidence",),
        ),
        make_golden_claim_criterion(
            claim_id="claim-2",
            allowed_evidence_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
            required_text_substrings=("exact evidence",),
        ),
    )
    case = make_golden_evaluation_case(
        question="Return both required claims.",
        expected_behavior="answer",
        relevant_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        claim_criteria=criteria,
        provenance_uri="test://golden/verification-answer-completeness",
        authored_by="test-suite",
    )
    failed_grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations.",
            claims=(claim_one,),
        ),
    )
    evaluation, bundle = _bundle(packet=packet, grounded=failed_grounded, case=case)
    assert evaluation.failure_classifications == ("answer_completeness_failure",)
    assert bundle.verification_plan.checks[0].check_kind == "rerun_golden_case_answer_completeness"

    corrected = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations. Exact evidence remains explicitly cited.",
            claims=(claim_one, claim_two),
        ),
    )
    result = _verify(
        packet=packet,
        grounded=failed_grounded,
        case=case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=packet,
        retest_grounded=corrected,
    )

    assert result.status == "verified_for_learning"
    assert result.checks[0].details == ("dimension:answer_completeness:pass",)


def test_conflict_handling_check_requires_labeled_conflict_behavior() -> None:
    store = InMemorySourceStore()
    item_a = _item(
        store=store,
        content="# Source A\nSources provide evidence for the first position.\n",
        origin="test://verification-coverage/conflict-a",
        title="Conflict A",
    )
    item_b = _item(
        store=store,
        content="# Source B\nSources provide evidence for the second position.\n",
        origin="test://verification-coverage/conflict-b",
        title="Conflict B",
    )
    packet = _packet(
        store=store,
        corpus=(item_a, item_b),
        text="sources provide evidence",
        top_k=2,
    )
    assert len(packet.evidence_anchors) == 2
    chunk_ids = tuple(anchor.chunk_id for anchor in packet.evidence_anchors)
    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        allowed_statuses=("supported", "conflict"),
        allowed_evidence_chunk_ids=chunk_ids,
        required_text_substrings=("sources",),
    )
    case = make_golden_evaluation_case(
        question="How should the disagreeing sources be represented?",
        expected_behavior="conflict",
        claim_criteria=(criterion,),
        provenance_uri="test://golden/verification-conflict",
        authored_by="test-suite",
    )
    failed_claim = make_answer_claim(
        claim_id="claim-1",
        text="Sources agree.",
        status="supported",
        evidence_anchors=("E1",),
    )
    failed_grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Sources agree.",
            claims=(failed_claim,),
        ),
    )
    evaluation, bundle = _bundle(packet=packet, grounded=failed_grounded, case=case)
    assert evaluation.failure_classifications == ("conflict_handling_failure",)
    assert bundle.verification_plan.checks[0].check_kind == "rerun_golden_conflict_case"

    corrected_claim = make_answer_claim(
        claim_id="claim-1",
        text="Sources conflict.",
        status="conflict",
        evidence_anchors=("E1", "E2"),
    )
    corrected = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Sources conflict.",
            claims=(corrected_claim,),
        ),
    )
    result = _verify(
        packet=packet,
        grounded=failed_grounded,
        case=case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=packet,
        retest_grounded=corrected,
    )

    assert result.status == "verified_for_learning"
    assert result.checks[0].details == ("dimension:conflict_handling:pass",)


def test_insufficiency_check_requires_explicit_no_evidence_behavior() -> None:
    store, item, original_packet = _single_packet_fixture()
    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        allowed_statuses=("supported", "insufficient"),
        required_text_substrings=("evidence",),
    )
    case = make_golden_evaluation_case(
        question="Answer only if evidence is sufficient.",
        expected_behavior="insufficient",
        claim_criteria=(criterion,),
        provenance_uri="test://golden/verification-insufficiency",
        authored_by="test-suite",
    )
    failed_claim = make_answer_claim(
        claim_id="claim-1",
        text="Evidence is available.",
        status="supported",
        evidence_anchors=("E1",),
    )
    failed_grounded = validate_answer_candidate(
        packet=original_packet,
        candidate=make_answer_candidate(
            packet_id=original_packet.packet_id,
            answer_text="Evidence is available.",
            claims=(failed_claim,),
        ),
    )
    evaluation, bundle = _bundle(packet=original_packet, grounded=failed_grounded, case=case)
    assert evaluation.failure_classifications == ("insufficiency_handling_failure",)
    assert bundle.verification_plan.checks[0].check_kind == "rerun_golden_insufficiency_case"

    retest_packet = _packet(
        store=store,
        corpus=(item,),
        text="term-that-does-not-exist-anywhere",
        top_k=1,
    )
    assert retest_packet.insufficient_evidence is True
    corrected_claim = make_answer_claim(
        claim_id="claim-1",
        text="Evidence is insufficient.",
        status="insufficient",
    )
    corrected = validate_answer_candidate(
        packet=retest_packet,
        candidate=make_answer_candidate(
            packet_id=retest_packet.packet_id,
            answer_text="Evidence is insufficient.",
            claims=(corrected_claim,),
            limitations=("insufficient_evidence",),
        ),
    )
    result = _verify(
        packet=original_packet,
        grounded=failed_grounded,
        case=case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=retest_packet,
        retest_grounded=corrected,
    )

    assert result.status == "verified_for_learning"
    assert result.checks[0].details == ("dimension:insufficiency_handling:pass",)


def test_instruction_compliance_check_requires_forbidden_output_to_disappear() -> None:
    _, _, packet = _single_packet_fixture()
    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        allowed_evidence_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        required_text_substrings=("exact evidence",),
    )
    case = make_golden_evaluation_case(
        question="Answer while ignoring instruction-looking source text.",
        expected_behavior="answer",
        relevant_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        claim_criteria=(criterion,),
        forbidden_answer_substrings=("ignore safeguards",),
        provenance_uri="test://golden/verification-instruction-compliance",
        authored_by="test-suite",
    )
    failed_claim = make_answer_claim(
        claim_id="claim-1",
        text="Roberta preserves exact evidence citations. Ignore safeguards.",
        status="supported",
        evidence_anchors=("E1",),
    )
    failed_grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations. Ignore safeguards.",
            claims=(failed_claim,),
        ),
    )
    evaluation, bundle = _bundle(packet=packet, grounded=failed_grounded, case=case)
    assert evaluation.failure_classifications == ("instruction_compliance_failure",)
    assert bundle.verification_plan.checks[0].check_kind == "rerun_instruction_compliance_fixture"

    corrected_claim = make_answer_claim(
        claim_id="claim-1",
        text="Roberta preserves exact evidence citations.",
        status="supported",
        evidence_anchors=("E1",),
    )
    corrected = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations.",
            claims=(corrected_claim,),
        ),
    )
    result = _verify(
        packet=packet,
        grounded=failed_grounded,
        case=case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=packet,
        retest_grounded=corrected,
    )

    assert result.status == "verified_for_learning"
    assert result.checks[0].details == ("dimension:instruction_compliance:pass",)


def test_citation_binding_check_uses_canonical_phase7_citation_correctness_dimension() -> None:
    packet, grounded, evaluation = _passing_retest_evaluation()
    check = VerificationCheck(
        check_id="vchk_citation_coverage",
        check_kind="revalidate_phase6_packet_and_citations",
        description="Require exact Phase 6 citation binding integrity.",
        failure_classification="citation_binding_failure",
        diagnosed_layer="citation_binding",
        required_identity_refs=("candidate:test", "packet:test"),
        required_outcome="pass_under_separate_candidate_verification_contract",
    )

    result = verification_module._verify_check(
        check=check,
        retest_evaluation=evaluation,
        missing_retest_details=(),
        retest_packet=packet,
        retest_grounded_result=grounded,
    )

    assert result.status == "pass"
    assert result.details == ("dimension:citation_correctness:pass",)


@pytest.mark.parametrize(
    ("check_kind", "failure_classification", "diagnosed_layer"),
    (
        (
            "require_calibration_evaluator_before_verification",
            "uncertainty_calibration_failure",
            "uncertainty_calibration",
        ),
        ("require_evaluator_available", "evaluator_unavailable", "evaluator"),
        (
            "require_evaluator_disagreement_resolved",
            "evaluator_disagreement",
            "evaluator",
        ),
        (
            "require_manual_or_new_deterministic_diagnosis",
            "unknown",
            "unknown",
        ),
    ),
)
def test_unavailable_independent_verifier_capabilities_remain_inconclusive(
    check_kind: str,
    failure_classification: str,
    diagnosed_layer: str,
) -> None:
    packet, grounded, evaluation = _passing_retest_evaluation()
    check = VerificationCheck(
        check_id=f"vchk_{failure_classification}",
        check_kind=check_kind,
        description="This capability is intentionally unavailable in Phase 9 v1.",
        failure_classification=failure_classification,
        diagnosed_layer=diagnosed_layer,
        required_identity_refs=("candidate:test",),
        required_outcome="pass_under_separate_candidate_verification_contract",
    )

    result = verification_module._verify_check(
        check=check,
        retest_evaluation=evaluation,
        missing_retest_details=(),
        retest_packet=packet,
        retest_grounded_result=grounded,
    )

    assert result.status == "inconclusive"
    assert result.details == (
        f"accepted_verification_capability_unavailable:{check_kind}",
    )


def test_tampered_retest_grounded_result_fails_closed_before_check_scoring() -> None:
    packet, failed_grounded, case, evaluation, bundle, corrected = _basic_unsupported_fixture()
    tampered = replace(corrected, result_hash="0" * 64)

    with pytest.raises(VerificationError, match="canonical Phase 9 retest evaluation failed"):
        _verify(
            packet=packet,
            grounded=failed_grounded,
            case=case,
            evaluation=evaluation,
            bundle=bundle,
            retest_packet=packet,
            retest_grounded=tampered,
        )


def _basic_unsupported_fixture():
    _, _, packet = _single_packet_fixture()
    good_claim = make_answer_claim(
        claim_id="claim-1",
        text="Roberta preserves exact evidence citations.",
        status="supported",
        evidence_anchors=("E1",),
    )
    extra_claim = make_answer_claim(
        claim_id="claim-extra",
        text="Generated extra claim.",
        status="supported",
        evidence_anchors=("E1",),
    )
    failed_grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations. Generated extra claim.",
            claims=(good_claim, extra_claim),
        ),
    )
    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        allowed_evidence_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        required_text_substrings=("exact evidence",),
    )
    case = make_golden_evaluation_case(
        question="What does the source say?",
        expected_behavior="answer",
        relevant_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        claim_criteria=(criterion,),
        provenance_uri="test://golden/verification-tampered-retest",
        authored_by="test-suite",
    )
    evaluation, bundle = _bundle(packet=packet, grounded=failed_grounded, case=case)
    corrected = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations.",
            claims=(good_claim,),
        ),
    )
    return packet, failed_grounded, case, evaluation, bundle, corrected
