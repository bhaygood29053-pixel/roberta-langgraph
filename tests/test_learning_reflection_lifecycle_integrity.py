from __future__ import annotations

from dataclasses import replace

import pytest

from roberta.learning import (
    InMemorySourceStore,
    ReflectionError,
    RetrievalCorpusItem,
    build_evidence_index,
    build_evidence_packet,
    build_learning_candidate_bundle,
    chunk_parsed_document,
    evaluate_grounded_answer,
    ingest_utf8_source,
    make_answer_candidate,
    make_answer_claim,
    make_golden_claim_criterion,
    make_golden_evaluation_case,
    parse_markdown_structure,
    retrieve_evidence,
    transition_candidate_lesson,
    validate_answer_candidate,
    validate_learning_candidate_bundle,
)
from roberta.learning.reflection import _bundle_material, _candidate_state_material, _hash


def _failed_bundle():
    store = InMemorySourceStore()
    source = ingest_utf8_source(
        store=store,
        content="# Evidence\nRoberta preserves exact evidence citations.\n",
        origin="test://reflection/lifecycle-predecessor",
        title="Lifecycle Predecessor Fixture",
        version="1",
        authority_class="internal",
        approval_status="approved",
        parser_version="utf8-source/v1",
    ).record
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)
    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=1600)
    indexed = build_evidence_index(store=store, chunked=chunked)
    item = RetrievalCorpusItem(chunked=chunked, indexed=indexed)
    retrieval = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="exact evidence citations",
        top_k=2,
    )
    packet = build_evidence_packet(store=store, corpus=(item,), result=retrieval)
    grounded = validate_answer_candidate(
        packet=packet,
        candidate=make_answer_candidate(
            packet_id=packet.packet_id,
            answer_text="Roberta preserves exact evidence citations. Extra generated claim.",
            claims=(
                make_answer_claim(
                    claim_id="claim-1",
                    text="Roberta preserves exact evidence citations.",
                    status="supported",
                    evidence_anchors=("E1",),
                ),
                make_answer_claim(
                    claim_id="claim-extra",
                    text="Extra generated claim.",
                    status="supported",
                    evidence_anchors=("E1",),
                ),
            ),
        ),
    )
    criterion = make_golden_claim_criterion(
        claim_id="claim-1",
        allowed_evidence_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        required_text_substrings=("exact evidence",),
    )
    case = make_golden_evaluation_case(
        question="What does the source say about evidence?",
        expected_behavior="answer",
        relevant_chunk_ids=(packet.evidence_anchors[0].chunk_id,),
        claim_criteria=(criterion,),
        required_answer_substrings=("exact evidence",),
        expected_packet_id=packet.packet_id,
        expected_retrieval_id=grounded.retrieval_id,
        provenance_uri="test://golden/lifecycle-predecessor",
        authored_by="test-suite",
    )
    evaluation = evaluate_grounded_answer(packet=packet, result=grounded, case=case)
    assert evaluation.aggregate_status == "fail"
    bundle = build_learning_candidate_bundle(
        packet=packet,
        grounded_result=grounded,
        golden_case=case,
        evaluation=evaluation,
        reflection_text="The answer emitted a claim outside the approved golden criteria.",
        lesson_text="Keep generated claims inside the evaluated evidence-backed claim scope.",
        rationale="The deterministic evaluator classified an unsupported claim.",
        created_by="test-reflector",
        producer_version="test-reflector/1",
    )
    return packet, grounded, case, evaluation, bundle


def _forge_terminal_predecessor(bundle, rejected, previous_state_id):
    state_seed = replace(
        rejected,
        candidate_state_id="",
        candidate_state_hash="",
        previous_state_id=previous_state_id,
    )
    state_hash = _hash(_candidate_state_material(state_seed))
    forged_candidate = replace(
        state_seed,
        candidate_state_id=f"cstate_{state_hash}",
        candidate_state_hash=state_hash,
    )
    bundle_seed = replace(
        bundle,
        bundle_id="",
        bundle_hash="",
        candidate=forged_candidate,
    )
    bundle_hash = _hash(_bundle_material(bundle_seed))
    return replace(
        bundle_seed,
        bundle_id=f"lcb_{bundle_hash}",
        bundle_hash=bundle_hash,
    )


@pytest.mark.parametrize("forged_predecessor", [None, "cstate_unrelated"])
def test_terminal_candidate_validation_reconstructs_exact_provisional_predecessor(
    forged_predecessor: str | None,
) -> None:
    packet, grounded, case, evaluation, bundle = _failed_bundle()
    rejected = transition_candidate_lesson(
        reflection=bundle.reflection,
        candidate=bundle.candidate,
        verification_plan=bundle.verification_plan,
        status="rejected",
        reason="Independent retest rejected this provisional lesson.",
    )
    assert rejected.previous_state_id == bundle.candidate.candidate_state_id

    forged_bundle = _forge_terminal_predecessor(
        bundle, rejected, forged_predecessor
    )

    with pytest.raises(
        ReflectionError,
        match="previous_state_id does not match initial provisional state",
    ):
        validate_learning_candidate_bundle(
            packet=packet,
            grounded_result=grounded,
            golden_case=case,
            evaluation=evaluation,
            bundle=forged_bundle,
        )
