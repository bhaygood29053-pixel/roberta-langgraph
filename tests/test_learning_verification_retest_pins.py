from __future__ import annotations

from roberta.learning import (
    InMemorySourceStore,
    RetrievalCorpusItem,
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
):
    retrieval = retrieve_evidence(
        store=store,
        corpus=corpus,
        text=text,
        top_k=1,
    )
    return build_evidence_packet(store=store, corpus=corpus, result=retrieval)


def test_retrieval_retest_rebinds_original_golden_evidence_pins() -> None:
    store = InMemorySourceStore()
    original_item = _item(
        store=store,
        content="# Original\nOriginal evidence is present.\n",
        origin="test://verification-pins/original",
        title="Original Evidence",
    )
    target_item = _item(
        store=store,
        content="# Target\nTarget evidence should be recovered.\n",
        origin="test://verification-pins/target",
        title="Target Evidence",
    )
    corpus = (original_item, target_item)
    original_packet = _packet(
        store=store,
        corpus=corpus,
        text="original evidence",
    )
    retest_packet = _packet(
        store=store,
        corpus=corpus,
        text="target evidence",
    )
    assert original_packet.packet_id != retest_packet.packet_id
    assert original_packet.retrieval_id != retest_packet.retrieval_id

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

    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        required_text_substrings=("evidence",),
    )
    golden_case = make_golden_evaluation_case(
        question="Recover the labeled target evidence.",
        expected_behavior="answer",
        relevant_chunk_ids=(retest_packet.evidence_anchors[0].chunk_id,),
        claim_criteria=(criterion,),
        expected_packet_id=original_packet.packet_id,
        expected_retrieval_id=original_grounded.retrieval_id,
        provenance_uri="test://golden/verification-pinned-retrieval",
        authored_by="test-suite",
    )
    evaluation = evaluate_grounded_answer(
        packet=original_packet,
        result=original_grounded,
        case=golden_case,
    )
    assert evaluation.failure_classifications == ("retrieval_failure",)

    bundle = build_learning_candidate_bundle(
        packet=original_packet,
        grounded_result=original_grounded,
        golden_case=golden_case,
        evaluation=evaluation,
        reflection_text="The original retrieval missed the labeled target evidence.",
        lesson_text="Recover the labeled evidence before evaluating downstream answer quality.",
        rationale="Retrieval coverage failed against the approved golden evidence label.",
        created_by="test-reflector",
        producer_version="test-reflector/1",
    )

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

    result = verify_candidate_lesson(
        packet=original_packet,
        grounded_result=original_grounded,
        golden_case=golden_case,
        evaluation=evaluation,
        bundle=bundle,
        retest_packet=retest_packet,
        retest_grounded_result=retest_grounded,
        created_by="test-verifier",
        producer_version="test-verifier/1",
    )

    assert result.status == "verified_for_learning"
    assert result.golden_case_id == golden_case.case_id
    assert result.retest_golden_case_id is not None
    assert result.retest_golden_case_id != golden_case.case_id
    assert result.retest_packet_id == retest_packet.packet_id
    assert result.retest_retrieval_id == retest_grounded.retrieval_id
    assert result.checks[0].status == "pass"
    assert result.checks[0].retest_golden_case_id == result.retest_golden_case_id
    assert result.checks[0].details == ("dimension:retrieval_coverage:pass",)
