from __future__ import annotations

from roberta.learning import (
    InMemorySourceStore,
    RetrievalCorpusItem,
    build_evidence_index,
    chunk_parsed_document,
    ingest_utf8_source,
    parse_markdown_structure,
    retrieve_evidence,
)
from roberta.learning.pyramid_provenance_containment import (
    _line_contained,
    install_strict_provenance_containment,
)
from roberta.learning.pyramid_provenance_scoped_reconstruction import (
    ProvenanceScopedRetrievalFilters,
)


def _single_prose_chunk():
    store = InMemorySourceStore()
    source = ingest_utf8_source(
        store=store,
        content=(
            "# Chapter 1\n"
            "outside-before boundary text\n"
            "inside target provenance text\n"
            "outside-after boundary text\n"
        ),
        origin="test://pyramid/provenance-containment",
        title="Provenance containment fixture",
        version="1",
        authority_class="internal",
        approval_status="approved",
        parser_version="utf8-source/v1",
    ).record
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)
    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=1600)
    indexed = build_evidence_index(
        store=store,
        chunked=chunked,
        embedding_provider=None,
    )
    chunk = next(
        item for item in chunked.chunks if "inside target provenance text" in item.text
    )
    assert chunk.line_start < 3 < chunk.line_end
    return store, RetrievalCorpusItem(chunked=chunked, indexed=indexed), chunk


def test_line_containment_rejects_boundary_straddling_span() -> None:
    assert _line_contained(10, 20, ((10, 20),)) is True
    assert _line_contained(11, 19, ((10, 20),)) is True
    assert _line_contained(9, 20, ((10, 20),)) is False
    assert _line_contained(10, 21, ((10, 20),)) is False
    assert _line_contained(9, 21, ((10, 20),)) is False


def test_boundary_straddling_chunk_is_excluded_before_ranking() -> None:
    install_strict_provenance_containment()
    store, item, chunk = _single_prose_chunk()

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="inside target provenance text",
        filters=ProvenanceScopedRetrievalFilters(
            source_ids=(chunk.source_id,),
            source_approval_statuses=("approved",),
            line_ranges=((3, 3),),
            scope_binding="strict-containment-subrange",
        ),
        top_k=5,
        candidate_limit=50,
    )

    assert result.candidates == ()


def test_fully_contained_chunk_remains_eligible() -> None:
    install_strict_provenance_containment()
    store, item, chunk = _single_prose_chunk()

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="inside target provenance text",
        filters=ProvenanceScopedRetrievalFilters(
            source_ids=(chunk.source_id,),
            source_approval_statuses=("approved",),
            line_ranges=((chunk.line_start, chunk.line_end),),
            scope_binding="strict-containment-full-range",
        ),
        top_k=5,
        candidate_limit=50,
    )

    assert result.candidates
    assert chunk.chunk_id in {candidate.chunk_id for candidate in result.candidates}
    assert all(
        candidate.line_start >= chunk.line_start
        and candidate.line_end <= chunk.line_end
        for candidate in result.candidates
    )
