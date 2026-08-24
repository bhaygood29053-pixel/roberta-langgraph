from __future__ import annotations

import json
from importlib.resources import files

import pytest

from roberta.learning import (
    InMemorySourceStore,
    RetrievalCorpusItem,
    build_evidence_index,
    chunk_parsed_document,
    ingest_utf8_source,
    parse_markdown_structure,
    retrieve_evidence,
)
from roberta.learning.pyramid_source_provenance_compat import (
    BasisAwareSourceProvenanceLocator,
)
from roberta.learning.pyramid_source_reconstruction import (
    PyramidSourceReconstructionError,
    SourceProvenanceLocator,
)
from roberta.learning.pyramid_provenance_scoped_reconstruction import (
    ProvenanceScopedRetrievalFilters,
    load_pdf_transcript_alignment,
    resolve_provenance_scope,
    validate_pdf_transcript_alignment,
)
from roberta.learning.user_source_batch import get_user_source_spec


MASTERING_SOURCE_KEY = "mastering_blockchain_4e_2023"


def _retrieval_fixture(
    *,
    in_scope_text: str,
    out_of_scope_text: str,
) -> tuple[InMemorySourceStore, RetrievalCorpusItem, object, object]:
    store = InMemorySourceStore()
    content = (
        "# Chapter 1\n"
        f"{in_scope_text}\n\n"
        "# Later chapter\n"
        f"{out_of_scope_text}\n"
    )
    source = ingest_utf8_source(
        store=store,
        content=content,
        origin="test://pyramid/provenance-scope",
        title="Provenance scope fixture",
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
    in_scope = next(
        chunk for chunk in chunked.chunks if in_scope_text in chunk.text
    )
    out_of_scope = next(
        chunk for chunk in chunked.chunks if out_of_scope_text in chunk.text
    )
    return (
        store,
        RetrievalCorpusItem(chunked=chunked, indexed=indexed),
        in_scope,
        out_of_scope,
    )


@pytest.mark.parametrize(
    ("concept", "query", "in_scope_text", "out_of_scope_text"),
    [
        (
            "architecture/network_layer",
            "network layer communication",
            "The network layer is the base communication layer.",
            "network layer network layer communication network layer later chapter",
        ),
        (
            "types/tokenized",
            "tokenized blockchain token",
            "A tokenized blockchain has a native consensus-related token.",
            "tokenized tokenization tokenized asset security token later chapter",
        ),
        (
            "benefits/immutability",
            "immutability absolute change",
            "Immutability is practical: changing history is extremely hard, not absolute.",
            "immutability absolute immutable change immutability later chapter",
        ),
        (
            "types/monolithic_polylithic",
            "monolithic polylithic blockchain",
            "Monolithic and polylithic distinguish single-chain and multi-chain architecture.",
            "monolithic blockchain scalability monolithic blockchain later chapter",
        ),
    ],
)
def test_provenance_scope_excludes_later_chapter_before_ranking(
    concept: str,
    query: str,
    in_scope_text: str,
    out_of_scope_text: str,
) -> None:
    store, item, in_scope, out_of_scope = _retrieval_fixture(
        in_scope_text=in_scope_text,
        out_of_scope_text=out_of_scope_text,
    )
    filters = ProvenanceScopedRetrievalFilters(
        source_ids=(in_scope.source_id,),
        source_approval_statuses=("approved",),
        line_ranges=((in_scope.line_start, in_scope.line_end),),
        scope_binding=f"scope-{concept}",
    )

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text=query,
        filters=filters,
        top_k=5,
        candidate_limit=50,
    )

    assert result.candidates
    assert in_scope.chunk_id in {candidate.chunk_id for candidate in result.candidates}
    assert out_of_scope.chunk_id not in {
        candidate.chunk_id for candidate in result.candidates
    }
    assert all(
        candidate.line_end >= in_scope.line_start
        and candidate.line_start <= in_scope.line_end
        for candidate in result.candidates
    )


def test_scope_binding_changes_retrieval_identity_even_when_lines_are_same() -> None:
    store, item, in_scope, _ = _retrieval_fixture(
        in_scope_text="The network layer is the base communication layer.",
        out_of_scope_text="network layer network layer later chapter",
    )
    common = dict(
        source_ids=(in_scope.source_id,),
        source_approval_statuses=("approved",),
        line_ranges=((in_scope.line_start, in_scope.line_end),),
    )

    first = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="network layer",
        filters=ProvenanceScopedRetrievalFilters(
            **common,
            scope_binding="alignment-a",
        ),
        top_k=1,
    )
    second = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="network layer",
        filters=ProvenanceScopedRetrievalFilters(
            **common,
            scope_binding="alignment-b",
        ),
        top_k=1,
    )

    assert first.query.query_id != second.query.query_id
    assert first.retrieval_id != second.retrieval_id


def test_mastering_blockchain_alignment_is_bound_and_covers_verified_chapter1_lines() -> None:
    spec = get_user_source_spec(MASTERING_SOURCE_KEY)
    alignment = load_pdf_transcript_alignment(
        source_key=MASTERING_SOURCE_KEY,
        source_artifact_sha256=spec.original_sha256,
        source_transcript_sha256=spec.transcript_sha256,
        original_page_count=spec.original_page_count,
        transcript_line_count=33988,
    )
    by_page = {entry.pdf_page: entry for entry in alignment.entries}

    assert by_page[46].line_start <= 1710 <= by_page[46].line_end
    assert by_page[46].line_start <= 1713 <= by_page[46].line_end
    assert by_page[54].line_start <= 2004 <= by_page[54].line_end
    assert by_page[58].line_start <= 2196 <= by_page[58].line_end
    assert by_page[58].line_start <= 2199 <= by_page[58].line_end
    assert by_page[59].line_start <= 2223 <= by_page[59].line_end
    assert by_page[59].line_start <= 2237 <= by_page[59].line_end


def test_mastering_blockchain_unmapped_pdf_page_fails_closed() -> None:
    spec = get_user_source_spec(MASTERING_SOURCE_KEY)
    locator = BasisAwareSourceProvenanceLocator(
        chapter="Chapter 1",
        section="unmapped fixture",
        page_basis="pdf",
        pages=(61,),
        legacy_source_ref="TEST-P61",
    )

    with pytest.raises(
        PyramidSourceReconstructionError,
        match="no verified transcript mapping",
    ):
        resolve_provenance_scope(
            source_key=MASTERING_SOURCE_KEY,
            source_artifact_sha256=spec.original_sha256,
            source_transcript_sha256=spec.transcript_sha256,
            original_page_count=spec.original_page_count,
            transcript_line_count=33988,
            locations=(locator,),
        )


def test_tampered_alignment_hash_fails_closed() -> None:
    spec = get_user_source_spec(MASTERING_SOURCE_KEY)
    resource = files("roberta.learning").joinpath(
        "source_alignments",
        "mastering_blockchain_4e_2023.pdf-lines.v1.json",
    )
    raw = json.loads(resource.read_text(encoding="utf-8"))
    raw["entries"][0]["line_end"] += 1

    with pytest.raises(
        PyramidSourceReconstructionError,
        match="alignment hash",
    ):
        validate_pdf_transcript_alignment(
            raw,
            expected_source_key=MASTERING_SOURCE_KEY,
            expected_source_artifact_sha256=spec.original_sha256,
            expected_source_transcript_sha256=spec.transcript_sha256,
            expected_original_page_count=spec.original_page_count,
            expected_transcript_line_count=33988,
        )


def test_book_page_locator_keeps_legacy_unscoped_behavior() -> None:
    locator = SourceProvenanceLocator(
        chapter="Chapter 1",
        section="legacy printed pages",
        book_pages=(1, 2),
    )

    scope = resolve_provenance_scope(
        source_key="legacy-book-fixture",
        source_artifact_sha256="a" * 64,
        source_transcript_sha256="b" * 64,
        original_page_count=None,
        transcript_line_count=10,
        locations=(locator,),
    )

    assert scope is None
