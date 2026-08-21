from __future__ import annotations

from dataclasses import replace

import pytest

from roberta.learning import (
    DeterministicHashEmbeddingProvider,
    IndexedDocument,
    InMemorySourceStore,
    QueryVector,
    RetrievalCorpusItem,
    RetrievalError,
    RetrievalFilters,
    build_evidence_index,
    chunk_parsed_document,
    evaluate_retrieval,
    ingest_utf8_source,
    make_query_vector,
    normalize_retrieval_filters,
    parse_markdown_structure,
    retrieve_evidence,
)


def _item(
    *,
    store: InMemorySourceStore,
    content: str,
    origin: str,
    title: str,
    max_chars: int = 1600,
    embedding_provider=None,
):
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
    chunked = chunk_parsed_document(
        store=store,
        parsed=parsed,
        max_chars=max_chars,
    )
    indexed = build_evidence_index(
        store=store,
        chunked=chunked,
        embedding_provider=embedding_provider,
    )
    return source, RetrievalCorpusItem(chunked=chunked, indexed=indexed)


def test_exact_term_retrieval_is_deterministic_and_preserves_exact_evidence() -> None:
    store = InMemorySourceStore()
    source, item = _item(
        store=store,
        content="# Alpha\nRoberta preserves provenance anchors.\n\n# Beta\nOther material.\n",
        origin="test://retrieval/exact",
        title="Exact",
    )

    first = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="PROVENANCE anchors",
        top_k=2,
    )
    second = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="PROVENANCE anchors",
        top_k=2,
    )

    assert second == first
    assert first.status == "ok"
    assert first.retrieval_id == f"ret_{first.retrieval_hash}"
    assert first.query.query_id.startswith("qry_")
    assert first.query.normalized_tokens == ("provenance", "anchors")
    assert len(first.candidates) == 1
    candidate = first.candidates[0]
    assert candidate.source_id == source.source_id
    assert candidate.chunk_id == item.chunked.chunks[0].chunk_id
    assert candidate.text == "Roberta preserves provenance anchors.\n"
    assert candidate.lexical_matched_terms == ("provenance", "anchors")
    assert candidate.lexical_phrase_match is True
    assert candidate.vector_rank is None
    assert candidate.channel_count == 1


def test_unicode_query_normalization_matches_phase4_analyzer_semantics() -> None:
    store = InMemorySourceStore()
    _, item = _item(
        store=store,
        content="# H\nStraße CAFÉ ΚαληΜΈΡΑ ＡＢＣ\n",
        origin="test://retrieval/unicode",
        title="Unicode",
    )

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="STRASSE café καλημέρα abc",
        top_k=1,
    )

    assert result.query.normalized_tokens == (
        "strasse",
        "café",
        "καλημέρα",
        "abc",
    )
    assert result.candidates[0].lexical_matched_term_count == 4


def test_filters_are_canonical_exact_and_never_silently_widened() -> None:
    store = InMemorySourceStore()
    source_a, item_a = _item(
        store=store,
        content="preamble needle\n\n# A\nneedle alpha\n\n- needle list\n",
        origin="test://retrieval/filter-a",
        title="Filter A",
    )
    _, item_b = _item(
        store=store,
        content="# B\nneedle beta\n",
        origin="test://retrieval/filter-b",
        title="Filter B",
    )
    section_id = item_a.chunked.chunks[0].section_id
    assert section_id is None

    filters = RetrievalFilters(
        source_ids=(source_a.source_id, source_a.source_id),
        section_ids=(None,),
        source_authority_classes=("internal",),
        source_approval_statuses=("approved",),
        chunk_kinds=("prose",),
    )
    normalized = normalize_retrieval_filters(filters)
    assert normalized.source_ids == (source_a.source_id,)
    assert normalized.section_ids == (None,)

    result = retrieve_evidence(
        store=store,
        corpus=(item_b, item_a),
        text="needle",
        filters=filters,
        top_k=5,
    )

    assert result.status == "ok"
    assert result.candidates
    assert all(candidate.source_id == source_a.source_id for candidate in result.candidates)
    assert all(candidate.section_id is None for candidate in result.candidates)
    assert all(candidate.chunk_kind == "prose" for candidate in result.candidates)


def test_no_match_is_explicit_and_returns_no_fabricated_evidence() -> None:
    store = InMemorySourceStore()
    _, item = _item(
        store=store,
        content="# H\nalpha beta\n",
        origin="test://retrieval/no-match",
        title="No Match",
    )

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="completely absent phrase",
        top_k=3,
    )

    assert result.status == "no_match"
    assert result.candidates == ()
    assert result.errors == ()


def test_cross_source_conflicting_text_remains_visible_not_reconciled() -> None:
    store = InMemorySourceStore()
    source_a, item_a = _item(
        store=store,
        content="# Claim\nlaunch window is Monday\n",
        origin="test://retrieval/conflict-a",
        title="Conflict A",
    )
    source_b, item_b = _item(
        store=store,
        content="# Claim\nlaunch window is Friday\n",
        origin="test://retrieval/conflict-b",
        title="Conflict B",
    )

    result = retrieve_evidence(
        store=store,
        corpus=(item_a, item_b),
        text="launch window",
        top_k=2,
    )

    assert result.status == "ok"
    assert len(result.candidates) == 2
    assert {candidate.source_id for candidate in result.candidates} == {
        source_a.source_id,
        source_b.source_id,
    }
    assert {candidate.text for candidate in result.candidates} == {
        "launch window is Monday\n",
        "launch window is Friday\n",
    }


def test_corpus_order_does_not_change_query_or_retrieval_identity() -> None:
    store = InMemorySourceStore()
    _, item_a = _item(
        store=store,
        content="# A\nalpha one\n",
        origin="test://retrieval/order-a",
        title="Order A",
    )
    _, item_b = _item(
        store=store,
        content="# B\nalpha two\n",
        origin="test://retrieval/order-b",
        title="Order B",
    )

    first = retrieve_evidence(
        store=store,
        corpus=(item_a, item_b),
        text="alpha",
        top_k=2,
    )
    second = retrieve_evidence(
        store=store,
        corpus=(item_b, item_a),
        text="alpha",
        top_k=2,
    )

    assert second == first


def test_local_context_diversity_defers_adjacent_chunk_for_independent_source() -> None:
    store = InMemorySourceStore()
    _, item_a = _item(
        store=store,
        content="# A\nalpha alpha one\nalpha alpha two\n",
        origin="test://retrieval/diversity-a",
        title="Diversity A",
        max_chars=17,
    )
    source_b, item_b = _item(
        store=store,
        content="# B\nalpha other\n",
        origin="test://retrieval/diversity-b",
        title="Diversity B",
    )
    assert len(item_a.chunked.chunks) == 2

    result = retrieve_evidence(
        store=store,
        corpus=(item_a, item_b),
        text="alpha",
        top_k=2,
    )

    assert len(result.candidates) == 2
    assert any(
        chunk_id in result.diversity_deferred_chunk_ids
        for chunk_id in (
            item_a.chunked.chunks[0].chunk_id,
            item_a.chunked.chunks[1].chunk_id,
        )
    )
    assert source_b.source_id in {candidate.source_id for candidate in result.candidates}


def test_tampered_lexical_index_fails_canonical_phase4_validation() -> None:
    store = InMemorySourceStore()
    _, item = _item(
        store=store,
        content="# H\nalpha beta\n",
        origin="test://retrieval/tamper-lexical",
        title="Tamper Lexical",
    )
    bad_entry = replace(item.indexed.lexical_entries[0], tokens=("forged",))
    tampered = RetrievalCorpusItem(
        chunked=item.chunked,
        indexed=IndexedDocument(
            manifest=item.indexed.manifest,
            lexical_entries=(bad_entry, *item.indexed.lexical_entries[1:]),
            embedding_entries=item.indexed.embedding_entries,
        ),
    )

    with pytest.raises(RetrievalError, match="lexical index"):
        retrieve_evidence(
            store=store,
            corpus=(tampered,),
            text="alpha",
        )


def test_tampered_embedding_vector_fails_integrity_validation() -> None:
    store = InMemorySourceStore()
    provider = DeterministicHashEmbeddingProvider(dimension=4)
    _, item = _item(
        store=store,
        content="# H\nalpha beta\n",
        origin="test://retrieval/tamper-vector",
        title="Tamper Vector",
        embedding_provider=provider,
    )
    entry = item.indexed.embedding_entries[0]
    assert entry.vector is not None
    forged_vector = (entry.vector[0] + 0.1, *entry.vector[1:])
    bad_entry = replace(entry, vector=forged_vector)
    tampered = RetrievalCorpusItem(
        chunked=item.chunked,
        indexed=IndexedDocument(
            manifest=item.indexed.manifest,
            lexical_entries=item.indexed.lexical_entries,
            embedding_entries=(bad_entry, *item.indexed.embedding_entries[1:]),
        ),
    )

    with pytest.raises(RetrievalError, match="fingerprint"):
        retrieve_evidence(
            store=store,
            corpus=(tampered,),
            text="alpha",
        )


def test_exact_embedding_space_query_can_retrieve_vector_only_candidate() -> None:
    store = InMemorySourceStore()
    provider = DeterministicHashEmbeddingProvider(dimension=6)
    _, item = _item(
        store=store,
        content="# A\nfirst content\n\n# B\nsecond content\n",
        origin="test://retrieval/vector",
        title="Vector",
        embedding_provider=provider,
    )
    target_entry = item.indexed.embedding_entries[1]
    assert target_entry.vector is not None
    manifest = item.indexed.manifest
    query_vector = make_query_vector(
        provider_id=manifest.embedding_provider_id,
        model_id=manifest.embedding_model_id,
        model_version=manifest.embedding_model_version,
        dimension=manifest.embedding_dimension,
        vector=target_entry.vector,
    )

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="???",
        query_vector=query_vector,
        top_k=1,
    )

    assert result.status == "ok"
    assert result.query.normalized_tokens == ()
    assert result.vector_eligible_index_ids == (manifest.index_id,)
    assert result.vector_ineligible_index_ids == ()
    assert result.candidates[0].chunk_id == target_entry.chunk_id
    assert result.candidates[0].vector_rank == 1
    assert result.candidates[0].vector_similarity == pytest.approx(1.0)
    assert result.candidates[0].lexical_rank is None


def test_embedding_space_mismatch_is_partial_and_does_not_fake_vector_candidates() -> None:
    store = InMemorySourceStore()
    provider = DeterministicHashEmbeddingProvider(dimension=4)
    _, item = _item(
        store=store,
        content="# H\nalpha beta\n",
        origin="test://retrieval/vector-mismatch",
        title="Vector Mismatch",
        embedding_provider=provider,
    )
    wrong_space = make_query_vector(
        provider_id="other-provider",
        model_id="other-model",
        model_version="1",
        dimension=4,
        vector=(1.0, 0.0, 0.0, 0.0),
    )

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="alpha",
        query_vector=wrong_space,
        top_k=1,
    )

    assert result.status == "partial"
    assert result.vector_eligible_index_ids == ()
    assert result.vector_ineligible_index_ids == (item.indexed.manifest.index_id,)
    assert result.candidates[0].lexical_rank == 1
    assert result.candidates[0].vector_rank is None
    assert any("vector_space_ineligible" in warning for warning in result.warnings)


@pytest.mark.parametrize(
    "vector",
    [
        QueryVector(
            provider_id="p",
            model_id="m",
            model_version="1",
            dimension=2,
            vector=(1.0, float("nan")),
            vector_fingerprint="forged",
        ),
        QueryVector(
            provider_id="p",
            model_id="m",
            model_version="1",
            dimension=3,
            vector=(1.0, 0.0),
            vector_fingerprint="forged",
        ),
    ],
)
def test_malformed_query_vectors_fail_closed(vector: QueryVector) -> None:
    store = InMemorySourceStore()
    _, item = _item(
        store=store,
        content="# H\nalpha\n",
        origin="test://retrieval/bad-query-vector",
        title="Bad Query Vector",
    )

    with pytest.raises(RetrievalError):
        retrieve_evidence(
            store=store,
            corpus=(item,),
            text="alpha",
            query_vector=vector,
        )


def test_duplicate_corpus_chunk_ids_are_rejected_to_prevent_score_inflation() -> None:
    store = InMemorySourceStore()
    _, item = _item(
        store=store,
        content="# H\nalpha\n",
        origin="test://retrieval/duplicate",
        title="Duplicate",
    )

    with pytest.raises(
        RetrievalError,
        match="corpus index ids must be unique|duplicate canonical chunk_id",
    ):
        retrieve_evidence(
            store=store,
            corpus=(item, item),
            text="alpha",
        )


def test_golden_metrics_report_recall_precision_rr_ndcg_diversity_and_filters() -> None:
    store = InMemorySourceStore()
    source_a, item_a = _item(
        store=store,
        content="# A\nalpha target\n",
        origin="test://retrieval/metric-a",
        title="Metric A",
    )
    _, item_b = _item(
        store=store,
        content="# B\nalpha distractor\n",
        origin="test://retrieval/metric-b",
        title="Metric B",
    )
    result = retrieve_evidence(
        store=store,
        corpus=(item_a, item_b),
        text="alpha target",
        filters=RetrievalFilters(source_ids=(source_a.source_id,)),
        top_k=2,
    )
    target = item_a.chunked.chunks[0].chunk_id

    metrics = evaluate_retrieval(
        result=result,
        relevant_chunk_ids=(target,),
    )

    assert metrics.recall_at_k == 1.0
    assert metrics.precision_at_k == 1.0
    assert metrics.reciprocal_rank == 1.0
    assert metrics.ndcg_at_k == 1.0
    assert metrics.evidence_coverage == 1.0
    assert metrics.redundancy_rate == 0.0
    assert metrics.source_diversity == 1.0
    assert metrics.filter_correct is True
    assert metrics.retrieved_count == 1
    assert metrics.relevant_count == 1
    assert metrics.hit_count == 1


def test_negative_golden_case_keeps_undefined_relevance_metrics_explicit() -> None:
    store = InMemorySourceStore()
    _, item = _item(
        store=store,
        content="# H\nalpha\n",
        origin="test://retrieval/negative-metric",
        title="Negative Metric",
    )
    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="absent",
    )
    metrics = evaluate_retrieval(result=result, relevant_chunk_ids=())

    assert result.status == "no_match"
    assert metrics.recall_at_k is None
    assert metrics.precision_at_k is None
    assert metrics.reciprocal_rank is None
    assert metrics.ndcg_at_k is None
    assert metrics.evidence_coverage is None
    assert metrics.retrieved_count == 0


def test_all_retrieval_records_deny_live_state_authority() -> None:
    store = InMemorySourceStore()
    _, item = _item(
        store=store,
        content="# H\nalpha\n",
        origin="test://retrieval/authority",
        title="Authority",
    )
    vector = make_query_vector(
        provider_id="p",
        model_id="m",
        model_version="1",
        dimension=2,
        vector=(1.0, 0.0),
    )
    filters = RetrievalFilters(chunk_kinds=("prose",))

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="alpha",
        filters=filters,
        top_k=1,
    )
    metrics = evaluate_retrieval(
        result=result,
        relevant_chunk_ids=(result.candidates[0].chunk_id,),
    )

    assert item.live_state_authorized is False
    assert filters.live_state_authorized is False
    assert vector.live_state_authorized is False
    assert result.live_state_authorized is False
    assert result.query.live_state_authorized is False
    assert metrics.live_state_authorized is False
    assert all(candidate.live_state_authorized is False for candidate in result.candidates)


def test_query_contract_and_bounds_fail_closed() -> None:
    store = InMemorySourceStore()
    _, item = _item(
        store=store,
        content="# H\nalpha\n",
        origin="test://retrieval/bounds",
        title="Bounds",
    )

    with pytest.raises(RetrievalError, match="candidate_limit"):
        retrieve_evidence(
            store=store,
            corpus=(item,),
            text="alpha",
            top_k=3,
            candidate_limit=2,
        )
    with pytest.raises(RetrievalError, match="retrieval_contract"):
        retrieve_evidence(
            store=store,
            corpus=(item,),
            text="alpha",
            retrieval_contract="other/v1",
        )
    with pytest.raises(RetrievalError, match="fusion_contract"):
        retrieve_evidence(
            store=store,
            corpus=(item,),
            text="alpha",
            fusion_contract="other/v1",
        )
    with pytest.raises(RetrievalError, match="no lexical tokens"):
        retrieve_evidence(
            store=store,
            corpus=(item,),
            text="???",
        )
