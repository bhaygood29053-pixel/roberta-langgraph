from __future__ import annotations

from dataclasses import replace
import math

import pytest

from roberta.learning import (
    ChunkedDocument,
    DeterministicHashEmbeddingProvider,
    EmbeddingProviderInfo,
    EmbeddingRequest,
    EmbeddingResult,
    IndexingError,
    InMemorySourceStore,
    build_evidence_index,
    chunk_parsed_document,
    ingest_utf8_source,
    parse_markdown_structure,
)


def _chunked(
    content: str,
    *,
    authority_class: str = "internal",
    approval_status: str = "approved",
    max_chars: int = 1600,
):
    store = InMemorySourceStore()
    source = ingest_utf8_source(
        store=store,
        content=content,
        origin="test://learning-indexing",
        title="Index Fixture",
        version="1",
        authority_class=authority_class,
        approval_status=approval_status,
        parser_version="utf8-source/v1",
    ).record
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)
    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=max_chars)
    return store, source, chunked


def test_tampered_chunked_document_fails_canonical_phase3_check() -> None:
    store, _, chunked = _chunked("# H\ntext\n")
    tampered_first = replace(chunked.chunks[0], text="caller-authored\n")
    tampered = ChunkedDocument(
        manifest=chunked.manifest,
        chunks=(tampered_first, *chunked.chunks[1:]),
    )

    with pytest.raises(IndexingError, match="canonical Phase 3"):
        build_evidence_index(store=store, chunked=tampered)


def test_lexical_analyzer_is_unicode_nfkc_casefold_and_ordered() -> None:
    store, _, chunked = _chunked(
        "# H\nStraße CAFÉ café ΚαληΜΈΡΑ 123_456 ＡＢＣ\n"
    )

    indexed = build_evidence_index(store=store, chunked=chunked)

    assert len(indexed.lexical_entries) == 1
    entry = indexed.lexical_entries[0]
    assert entry.tokens == (
        "strasse",
        "café",
        "café",
        "καλημέρα",
        "123",
        "456",
        "abc",
    )
    assert entry.token_count == 7
    assert entry.unique_term_count == 6


def test_lexical_entries_preserve_chunk_provenance_and_filter_metadata() -> None:
    store, source, chunked = _chunked(
        "# A\none\n\n## B\ntwo\n",
        authority_class="primary",
        approval_status="approved",
    )

    indexed = build_evidence_index(store=store, chunked=chunked)

    assert indexed.manifest.source_id == source.source_id
    assert indexed.manifest.chunk_set_id == chunked.manifest.chunk_set_id
    assert len(indexed.lexical_entries) == len(chunked.chunks)
    for entry, chunk in zip(indexed.lexical_entries, chunked.chunks, strict=True):
        assert entry.chunk_id == chunk.chunk_id
        assert entry.source_id == chunk.source_id
        assert entry.document_id == chunk.document_id
        assert entry.section_id == chunk.section_id
        assert entry.structural_path == chunk.structural_path
        assert entry.chunk_kind == chunk.kind
        assert entry.line_start == chunk.line_start
        assert entry.line_end == chunk.line_end
        assert entry.source_authority_class == "primary"
        assert entry.source_approval_status == "approved"
        assert entry.chunk_content_hash == chunk.content_hash


def test_lexical_only_rebuild_is_deterministic_and_explicit() -> None:
    store, _, chunked = _chunked("# H\none\n\ntwo\n")

    first = build_evidence_index(store=store, chunked=chunked)
    second = build_evidence_index(store=store, chunked=chunked)

    assert second == first
    assert first.manifest.index_id == f"idx_{first.manifest.index_hash}"
    assert first.manifest.status == "lexical_only"
    assert first.manifest.embedding_provider_id is None
    assert first.manifest.embedding_entry_ids == ()
    assert first.embedding_entries == ()


def test_index_or_analyzer_version_changes_only_derived_index_identity() -> None:
    store, source, chunked = _chunked("# H\none\n\ntwo\n")

    baseline = build_evidence_index(store=store, chunked=chunked)
    index_changed = build_evidence_index(
        store=store, chunked=chunked, index_version="1.0.1"
    )
    analyzer_changed = build_evidence_index(
        store=store, chunked=chunked, lexical_analyzer_version="1.0.1"
    )

    assert baseline.manifest.source_id == source.source_id
    assert index_changed.manifest.source_id == source.source_id
    assert analyzer_changed.manifest.source_id == source.source_id
    assert baseline.manifest.chunk_set_id == chunked.manifest.chunk_set_id
    assert index_changed.manifest.chunk_set_id == chunked.manifest.chunk_set_id
    assert analyzer_changed.manifest.chunk_set_id == chunked.manifest.chunk_set_id
    assert baseline.manifest.index_id != index_changed.manifest.index_id
    assert baseline.manifest.index_id != analyzer_changed.manifest.index_id
    assert baseline.manifest.lexical_entry_ids != index_changed.manifest.lexical_entry_ids
    assert baseline.manifest.lexical_entry_ids != analyzer_changed.manifest.lexical_entry_ids


def test_deterministic_test_embedding_provider_is_reproducible_and_typed() -> None:
    store, _, chunked = _chunked("# H\none\n\n- two\n")
    provider = DeterministicHashEmbeddingProvider(dimension=6)

    first = build_evidence_index(
        store=store, chunked=chunked, embedding_provider=provider
    )
    second = build_evidence_index(
        store=store, chunked=chunked, embedding_provider=provider
    )

    assert second == first
    assert first.manifest.status == "complete"
    assert first.manifest.embedding_provider_id == "deterministic-hash-test"
    assert first.manifest.embedding_model_id == "sha256-contract-vector"
    assert first.manifest.embedding_model_version == "1.0.0"
    assert first.manifest.embedding_dimension == 6
    assert first.manifest.embedding_ok_count == len(chunked.chunks)
    assert first.manifest.embedding_error_count == 0
    assert first.manifest.embedding_unavailable_count == 0
    for entry, chunk in zip(first.embedding_entries, chunked.chunks, strict=True):
        assert entry.chunk_id == chunk.chunk_id
        assert entry.status == "ok"
        assert entry.dimension == 6
        assert entry.vector is not None and len(entry.vector) == 6
        assert all(math.isfinite(value) for value in entry.vector)
        assert entry.vector_fingerprint is not None
        assert entry.error is None


def test_provider_model_version_change_preserves_lexical_identity_but_changes_embedding_identity() -> None:
    store, _, chunked = _chunked("# H\none\n\ntwo\n")

    first = build_evidence_index(
        store=store,
        chunked=chunked,
        embedding_provider=DeterministicHashEmbeddingProvider(model_version="1.0.0"),
    )
    second = build_evidence_index(
        store=store,
        chunked=chunked,
        embedding_provider=DeterministicHashEmbeddingProvider(model_version="2.0.0"),
    )

    assert first.manifest.chunk_set_id == second.manifest.chunk_set_id
    assert first.manifest.lexical_entry_ids == second.manifest.lexical_entry_ids
    assert first.manifest.embedding_entry_ids != second.manifest.embedding_entry_ids
    assert first.manifest.index_id != second.manifest.index_id


class _BadDimensionProvider:
    def describe(self) -> EmbeddingProviderInfo:
        return EmbeddingProviderInfo(
            provider_id="bad",
            model_id="bad-dimension",
            model_version="1",
            dimension=3,
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        return EmbeddingResult(
            chunk_id=request.chunk_id,
            content_hash=request.content_hash,
            status="ok",
            vector=(0.1, 0.2),
        )


class _NonFiniteProvider:
    def describe(self) -> EmbeddingProviderInfo:
        return EmbeddingProviderInfo(
            provider_id="bad",
            model_id="non-finite",
            model_version="1",
            dimension=2,
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        return EmbeddingResult(
            chunk_id=request.chunk_id,
            content_hash=request.content_hash,
            status="ok",
            vector=(0.1, float("nan")),
        )


@pytest.mark.parametrize(
    "provider, message",
    [
        (_BadDimensionProvider(), "dimension"),
        (_NonFiniteProvider(), "finite"),
    ],
)
def test_malformed_embedding_vectors_fail_closed(provider, message: str) -> None:
    store, _, chunked = _chunked("# H\ntext\n")

    with pytest.raises(IndexingError, match=message):
        build_evidence_index(
            store=store, chunked=chunked, embedding_provider=provider
        )


class _IdentityMismatchProvider:
    def describe(self) -> EmbeddingProviderInfo:
        return EmbeddingProviderInfo(
            provider_id="bad",
            model_id="identity",
            model_version="1",
            dimension=1,
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        return EmbeddingResult(
            chunk_id="chk_wrong",
            content_hash=request.content_hash,
            status="ok",
            vector=(0.0,),
        )


def test_embedding_result_identity_mismatch_fails_closed() -> None:
    store, _, chunked = _chunked("# H\ntext\n")

    with pytest.raises(IndexingError, match="identity"):
        build_evidence_index(
            store=store,
            chunked=chunked,
            embedding_provider=_IdentityMismatchProvider(),
        )


class _RuntimeFailureProvider:
    def describe(self) -> EmbeddingProviderInfo:
        return EmbeddingProviderInfo(
            provider_id="runtime-test",
            model_id="offline",
            model_version="1",
            dimension=4,
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        raise RuntimeError("offline")


def test_embedding_runtime_failure_is_partial_without_fabricated_vector() -> None:
    store, _, chunked = _chunked("# H\none\n\n- two\n")

    indexed = build_evidence_index(
        store=store,
        chunked=chunked,
        embedding_provider=_RuntimeFailureProvider(),
    )

    assert indexed.manifest.status == "partial"
    assert indexed.manifest.embedding_ok_count == 0
    assert indexed.manifest.embedding_error_count == len(chunked.chunks)
    assert indexed.manifest.embedding_unavailable_count == 0
    assert len(indexed.manifest.errors) == len(chunked.chunks)
    for entry in indexed.embedding_entries:
        assert entry.status == "error"
        assert entry.vector is None
        assert entry.vector_fingerprint is None
        assert entry.error is not None and "RuntimeError:offline" in entry.error


class _UnavailableProvider:
    def describe(self) -> EmbeddingProviderInfo:
        return EmbeddingProviderInfo(
            provider_id="availability-test",
            model_id="temporarily-unavailable",
            model_version="1",
            dimension=2,
        )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        return EmbeddingResult(
            chunk_id=request.chunk_id,
            content_hash=request.content_hash,
            status="unavailable",
            vector=None,
            warnings=("retry_later",),
            error="provider unavailable",
        )


def test_provider_declared_unavailable_is_partial_and_diagnostic() -> None:
    store, _, chunked = _chunked("# H\ntext\n")

    indexed = build_evidence_index(
        store=store, chunked=chunked, embedding_provider=_UnavailableProvider()
    )

    assert indexed.manifest.status == "partial"
    assert indexed.manifest.embedding_unavailable_count == 1
    assert indexed.manifest.embedding_error_count == 0
    assert indexed.embedding_entries[0].status == "unavailable"
    assert indexed.embedding_entries[0].vector is None
    assert any("retry_later" in warning for warning in indexed.manifest.warnings)
    assert any("provider unavailable" in warning for warning in indexed.manifest.warnings)


def test_unsupported_index_and_analyzer_contracts_fail_closed() -> None:
    store, _, chunked = _chunked("# H\ntext\n")

    with pytest.raises(IndexingError, match="index_contract"):
        build_evidence_index(
            store=store, chunked=chunked, index_contract="other/v1"
        )
    with pytest.raises(IndexingError, match="lexical_analyzer_contract"):
        build_evidence_index(
            store=store,
            chunked=chunked,
            lexical_analyzer_contract="other/v1",
        )


def test_all_index_records_deny_live_state_authority() -> None:
    store, _, chunked = _chunked("# H\ntext\n")
    provider = DeterministicHashEmbeddingProvider(dimension=3)

    indexed = build_evidence_index(
        store=store, chunked=chunked, embedding_provider=provider
    )
    info = provider.describe()
    request = EmbeddingRequest(
        chunk_id=chunked.chunks[0].chunk_id,
        content_hash=chunked.chunks[0].content_hash,
        text=chunked.chunks[0].text,
    )
    result = provider.embed(request)

    assert indexed.live_state_authorized is False
    assert indexed.manifest.live_state_authorized is False
    assert info.live_state_authorized is False
    assert request.live_state_authorized is False
    assert result.live_state_authorized is False
    assert all(entry.live_state_authorized is False for entry in indexed.lexical_entries)
    assert all(entry.live_state_authorized is False for entry in indexed.embedding_entries)
