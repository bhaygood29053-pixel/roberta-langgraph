from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from importlib.resources import files as resource_files
import json

import roberta.learning.x1_whitepaper as whitepaper
from roberta.learning import (
    InMemorySourceStore,
    RetrievalCorpusItem,
    X1_WHITEPAPER_AUTHORS,
    X1_WHITEPAPER_PDF_PAGE_COUNT,
    X1_WHITEPAPER_PDF_SHA256,
    X1_WHITEPAPER_TITLE,
    X1_WHITEPAPER_TRANSCRIPT_SHA256,
    X1_WHITEPAPER_VERSION,
    build_evidence_index,
    build_evidence_packet,
    chunk_parsed_document,
    ingest_x1_whitepaper_source,
    parse_markdown_structure,
    retrieve_evidence,
    serialize_evidence_packet_for_model,
    x1_whitepaper_markdown,
)


def _clock() -> datetime:
    return datetime(2026, 8, 21, 15, 0, tzinfo=timezone.utc)


def _pipeline():
    store = InMemorySourceStore()
    source = ingest_x1_whitepaper_source(store=store, clock=_clock).record
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)
    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=1600)
    indexed = build_evidence_index(store=store, chunked=chunked)
    item = RetrievalCorpusItem(chunked=chunked, indexed=indexed)
    return store, source, parsed, chunked, indexed, item


def test_supplied_x1_whitepaper_pdf_provenance_is_pinned() -> None:
    assert X1_WHITEPAPER_PDF_SHA256 == (
        "a9023893572e057c62628c50e3fd9c3827fe6eec88ae8862e318375233a7e316"
    )
    assert X1_WHITEPAPER_PDF_PAGE_COUNT == 13


def test_x1_whitepaper_transcript_is_packaged_integrity_checked_and_ingested_approved() -> None:
    store = InMemorySourceStore()
    content = x1_whitepaper_markdown()
    result = ingest_x1_whitepaper_source(store=store, clock=_clock)
    source = result.record

    assert result.status == "ingested"
    assert hashlib.sha256(content.encode("utf-8")).hexdigest() == X1_WHITEPAPER_TRANSCRIPT_SHA256
    assert store.get_artifact(source.artifact_ref) == content.encode("utf-8")
    assert source.title == X1_WHITEPAPER_TITLE
    assert source.version == X1_WHITEPAPER_VERSION
    assert source.authority_class == "primary"
    assert source.approval_status == "approved"
    assert source.status == "approved"
    assert tuple(source.metadata["authors"]) == X1_WHITEPAPER_AUTHORS
    assert source.metadata["original_pdf_sha256"] == X1_WHITEPAPER_PDF_SHA256
    assert source.metadata["original_pdf_page_count"] == 13
    assert source.metadata["transcript_sha256"] == X1_WHITEPAPER_TRANSCRIPT_SHA256
    assert source.metadata["current_state_authority"] is False
    assert source.live_state_authorized is False

    repeat = ingest_x1_whitepaper_source(store=store, clock=_clock)
    assert repeat.status == "existing"
    assert repeat.record == source


def test_whitepaper_loader_hashes_exact_resource_bytes_before_utf8_decode(monkeypatch) -> None:
    root = resource_files("roberta.learning")
    exact_parts = tuple(
        root.joinpath(resource).read_bytes()
        for resource in whitepaper.X1_WHITEPAPER_TRANSCRIPT_RESOURCES
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
            index = whitepaper.X1_WHITEPAPER_TRANSCRIPT_RESOURCES.index(resource)
            return _BytesOnlyResource(self._parts[index])

    monkeypatch.setattr(whitepaper, "files", lambda _: _BytesOnlyRoot(crlf_parts))
    monkeypatch.setattr(
        whitepaper,
        "X1_WHITEPAPER_TRANSCRIPT_SHA256",
        hashlib.sha256(expected_bytes).hexdigest(),
    )

    assert whitepaper.x1_whitepaper_markdown() == expected_bytes.decode("utf-8")


def test_x1_whitepaper_runs_through_existing_markdown_structure_chunk_and_index_contracts() -> None:
    _, source, parsed, chunked, indexed, _ = _pipeline()

    headings = tuple(section.heading for section in parsed.sections)
    assert headings[:3] == (
        X1_WHITEPAPER_TITLE,
        "Abstract",
        "1. Introduction",
    )
    assert "2. Optimized Validator Economics" in headings
    assert (
        "3.1 VRF-Based Leader Selection, Anti-Collusion Measures, and Leader Schedule Optimization"
        in headings
    )
    assert "5. Dynamic Base Fee Mechanism" in headings
    assert "6. Decentralized MEV Handling and Fair Extraction" in headings
    assert "7. Technology and Performance Enhancements" in headings
    assert "8. Conclusion" in headings
    assert "References" in headings

    assert parsed.document.status == "complete"
    assert chunked.chunks
    assert indexed.manifest.status == "lexical_only"
    assert all(chunk.source_id == source.source_id for chunk in chunked.chunks)
    assert parsed.live_state_authorized is False
    assert chunked.live_state_authorized is False
    assert indexed.live_state_authorized is False


def test_x1_whitepaper_static_evidence_is_retrievable_without_becoming_live_truth() -> None:
    store, source, _, _, _, item = _pipeline()

    result = retrieve_evidence(
        store=store,
        corpus=(item,),
        text="dynamic base fee compute units transaction pricing",
        top_k=3,
    )

    assert result.status == "ok"
    assert result.candidates
    assert all(candidate.source_id == source.source_id for candidate in result.candidates)
    assert any("dynamic base fee" in candidate.text.casefold() for candidate in result.candidates)
    assert result.live_state_authorized is False
    assert all(candidate.live_state_authorized is False for candidate in result.candidates)

    packet = build_evidence_packet(store=store, corpus=(item,), result=result)
    model_context = json.loads(serialize_evidence_packet_for_model(packet))
    boundary = model_context["instruction_boundary"]
    assert boundary["source_authority_labels_can_authorize_live_state"] is False
    for evidence in model_context["evidence_packet"]["evidence"]:
        assert evidence["source_authority_class"] == "primary"
        assert evidence["source_approval_status"] == "approved"
        assert evidence["source_live_state_authorized"] is False
