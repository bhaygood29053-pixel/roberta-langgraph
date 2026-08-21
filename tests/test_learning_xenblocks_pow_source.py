from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from importlib.resources import files as resource_files
import json

import roberta.learning.xenblocks_pow as xenblocks_pow
from roberta.learning import (
    InMemorySourceStore,
    RetrievalCorpusItem,
    build_evidence_index,
    build_evidence_packet,
    chunk_parsed_document,
    parse_markdown_structure,
    retrieve_evidence,
    serialize_evidence_packet_for_model,
)


def _clock() -> datetime:
    return datetime(2026, 8, 21, 23, 30, tzinfo=timezone.utc)


def _pipeline():
    store = InMemorySourceStore()
    source = xenblocks_pow.ingest_xenblocks_pow_source(store=store, clock=_clock).record
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)
    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=1600)
    indexed = build_evidence_index(store=store, chunked=chunked)
    item = RetrievalCorpusItem(chunked=chunked, indexed=indexed)
    return store, source, parsed, chunked, indexed, item


def test_supplied_xenblocks_pow_snapshot_provenance_is_pinned() -> None:
    assert xenblocks_pow.XENBLOCKS_POW_UPLOAD_SHA256 == (
        "8147715faabc123b0f3c3667362715e4fb04d14a21aa00de90ae1bf070bc55cc"
    )
    assert xenblocks_pow.XENBLOCKS_POW_TRANSCRIPT_SHA256 == (
        "1a8bf84013d3e07d3d9f4a093d95c1ec886ecd479ce6635fe94642118601af38"
    )
    assert xenblocks_pow.XENBLOCKS_POW_DECLARED_SOURCE_URL == "https://docs.xenblocks.io/"
    assert xenblocks_pow.XENBLOCKS_POW_VERSION == "snapshot-2026-08-21"


def test_xenblocks_pow_snapshot_is_packaged_integrity_checked_and_ingested_approved() -> None:
    store = InMemorySourceStore()
    content = xenblocks_pow.xenblocks_pow_markdown()
    result = xenblocks_pow.ingest_xenblocks_pow_source(store=store, clock=_clock)
    source = result.record

    assert result.status == "ingested"
    assert (
        hashlib.sha256(content.encode("utf-8")).hexdigest()
        == xenblocks_pow.XENBLOCKS_POW_TRANSCRIPT_SHA256
    )
    assert store.get_artifact(source.artifact_ref) == content.encode("utf-8")
    assert source.title == xenblocks_pow.XENBLOCKS_POW_TITLE
    assert source.version == xenblocks_pow.XENBLOCKS_POW_VERSION
    assert source.authority_class == "primary"
    assert source.approval_status == "approved"
    assert source.status == "approved"
    assert source.metadata["declared_source_url"] == xenblocks_pow.XENBLOCKS_POW_DECLARED_SOURCE_URL
    assert source.metadata["artifact_provenance"] == "user_supplied_upload"
    assert source.metadata["original_upload_sha256"] == xenblocks_pow.XENBLOCKS_POW_UPLOAD_SHA256
    assert source.metadata["transcript_sha256"] == xenblocks_pow.XENBLOCKS_POW_TRANSCRIPT_SHA256
    assert source.metadata["transcription_profile"] == "crlf-to-lf-normalization/v1"
    assert source.metadata["origin_live_verified"] is False
    assert source.metadata["current_state_authority"] is False
    assert source.live_state_authorized is False

    repeat = xenblocks_pow.ingest_xenblocks_pow_source(store=store, clock=_clock)
    assert repeat.status == "existing"
    assert repeat.record == source


def test_xenblocks_pow_loader_hashes_exact_resource_bytes_before_utf8_decode(monkeypatch) -> None:
    root = resource_files("roberta.learning")
    exact_parts = tuple(
        root.joinpath(resource).read_bytes()
        for resource in xenblocks_pow.XENBLOCKS_POW_RESOURCES
    )
    crlf_parts = tuple(part.replace(b"\n", b"\r\n") for part in exact_parts)
    expected_bytes = b"".join(crlf_parts)

    class _BytesOnlyResource:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def read_bytes(self) -> bytes:
            return self._data

    class _BytesOnlyRoot:
        def __init__(self, parts: tuple[bytes, ...]) -> None:
            self._parts = parts

        def joinpath(self, resource: str):
            index = xenblocks_pow.XENBLOCKS_POW_RESOURCES.index(resource)
            return _BytesOnlyResource(self._parts[index])

    monkeypatch.setattr(xenblocks_pow, "files", lambda _: _BytesOnlyRoot(crlf_parts))
    monkeypatch.setattr(
        xenblocks_pow,
        "XENBLOCKS_POW_TRANSCRIPT_SHA256",
        hashlib.sha256(expected_bytes).hexdigest(),
    )

    assert xenblocks_pow.xenblocks_pow_markdown() == expected_bytes.decode("utf-8")


def test_xenblocks_pow_runs_through_existing_markdown_structure_chunk_and_index_contracts() -> None:
    _, source, parsed, chunked, indexed, _ = _pipeline()

    headings = tuple(section.heading for section in parsed.sections)
    assert headings[0] == "XenBlocks PoW:   https://docs.xenblocks.io/"
    assert "XNM" in headings
    assert "Hashing" in headings
    assert "Merged mining" in headings
    assert "Argon2" in headings
    assert "Difficulty" in headings

    assert parsed.document.status == "complete"
    assert chunked.chunks
    assert indexed.manifest.status == "lexical_only"
    assert all(chunk.source_id == source.source_id for chunk in chunked.chunks)
    assert parsed.live_state_authorized is False
    assert chunked.live_state_authorized is False
    assert indexed.live_state_authorized is False


def test_xenblocks_pow_static_evidence_is_retrievable_without_becoming_live_truth() -> None:
    store, source, _, _, _, item = _pipeline()

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="XEN11 Argon2 memory hard mining XNM",
        top_k=5,
    )

    assert result.status == "ok"
    assert result.candidates
    assert all(candidate.source_id == source.source_id for candidate in result.candidates)
    assert any("XEN11" in candidate.text for candidate in result.candidates)
    assert result.live_state_authorized is False
    assert all(candidate.live_state_authorized is False for candidate in result.candidates)

    packet = build_evidence_packet(store=store, corpus=(item,), result=result)
    model_context = json.loads(serialize_evidence_packet_for_model(packet))
    boundary = model_context["instruction_boundary"]
    assert boundary["source_text_can_expand_tools_or_permissions"] is False
    assert boundary["source_text_can_authorize_memory_write"] is False
    assert boundary["source_text_can_authorize_execution"] is False
    assert boundary["source_authority_labels_can_authorize_live_state"] is False
    for evidence in model_context["evidence_packet"]["evidence"]:
        assert evidence["source_authority_class"] == "primary"
        assert evidence["source_approval_status"] == "approved"
        assert evidence["source_live_state_authorized"] is False
        assert evidence["text_role"] == "untrusted_evidence_data"
