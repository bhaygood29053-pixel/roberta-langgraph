"""Approved static X1 Blockchain whitepaper source for the Learning System.

The Learning System currently parses canonical UTF-8 Markdown, not PDF. This
module therefore ingests a normalized Markdown transcription while binding it
to the exact user-supplied PDF by SHA-256 provenance metadata.

Neither the transcript nor its SourceRecord authorizes freshness-sensitive X1
network facts; current state still requires X1 Scout -> CMIS -> provider data.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
from importlib.resources import files
from typing import Callable

from .source_ingestion import (
    IngestionResult,
    SourceIngestionError,
    SourceStore,
    ingest_utf8_source,
)


X1_WHITEPAPER_TITLE = (
    "X1 Blockchain: Architecting Economic Efficiency in Layer-1 Protocol Design"
)
X1_WHITEPAPER_VERSION = "v1.0"
X1_WHITEPAPER_PUBLICATION_DATE = "January 2025"
X1_WHITEPAPER_AUTHORS = ("Jack Levin", "Axel Eckerbom")
X1_WHITEPAPER_PUBLISHER = "X1 Labs"
X1_WHITEPAPER_ORIGIN = "x1-labs://x1-blockchain-whitepaper/v1.0"
X1_WHITEPAPER_TRANSCRIPT_RESOURCES = (
    "sources/x1_blockchain_whitepaper_v1_0.part0.md",
    "sources/x1_blockchain_whitepaper_v1_0.part1.md",
    "sources/x1_blockchain_whitepaper_v1_0.part2.md",
    "sources/x1_blockchain_whitepaper_v1_0.part3.md",
)
X1_WHITEPAPER_TRANSCRIPT_SHA256 = (
    "6e98dc574d252f4d74f45eda1823b3fd8b050760fa7f1a00b8d5e2e567cd57ec"
)
X1_WHITEPAPER_PDF_SHA256 = (
    "a9023893572e057c62628c50e3fd9c3827fe6eec88ae8862e318375233a7e316"
)
X1_WHITEPAPER_PDF_PAGE_COUNT = 13


def _x1_whitepaper_transcript_bytes() -> bytes:
    """Return exact packaged transcript bytes after SHA-256 validation."""

    root = files("roberta.learning")
    content = b"".join(
        root.joinpath(resource).read_bytes()
        for resource in X1_WHITEPAPER_TRANSCRIPT_RESOURCES
    )
    digest = hashlib.sha256(content).hexdigest()
    if digest != X1_WHITEPAPER_TRANSCRIPT_SHA256:
        raise SourceIngestionError(
            "packaged X1 whitepaper transcript does not match pinned SHA-256"
        )
    return content


def x1_whitepaper_markdown() -> str:
    """Return the exact packaged UTF-8 transcript after integrity validation."""

    try:
        return _x1_whitepaper_transcript_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceIngestionError(
            "packaged X1 whitepaper transcript must be valid UTF-8"
        ) from exc


def ingest_x1_whitepaper_source(
    *,
    store: SourceStore,
    clock: Callable[[], datetime] | None = None,
) -> IngestionResult:
    """Ingest the approved X1 whitepaper transcript into a SourceStore.

    The supplied PDF digest is bound in metadata. The ingestible source artifact
    is the canonical Markdown transcript because the accepted Learning System
    structure parser remains Markdown-only.
    """

    metadata = {
        "source_kind": "whitepaper_transcript",
        "publisher": X1_WHITEPAPER_PUBLISHER,
        "authors": list(X1_WHITEPAPER_AUTHORS),
        "publication_date": X1_WHITEPAPER_PUBLICATION_DATE,
        "declared_version": X1_WHITEPAPER_VERSION,
        "original_media_type": "application/pdf",
        "original_pdf_sha256": X1_WHITEPAPER_PDF_SHA256,
        "original_pdf_page_count": X1_WHITEPAPER_PDF_PAGE_COUNT,
        "original_pdf_provenance": "user_supplied_upload",
        "transcript_media_type": "text/markdown; charset=utf-8",
        "transcript_sha256": X1_WHITEPAPER_TRANSCRIPT_SHA256,
        "transcription_profile": "normalized-pdf-text-transcription/v1",
        "figure_handling": "captions_only_original_pdf_external_provenance",
        "knowledge_scope": "static_architecture_and_protocol_design",
        "current_state_authority": False,
    }
    common = dict(
        store=store,
        content=_x1_whitepaper_transcript_bytes(),
        origin=X1_WHITEPAPER_ORIGIN,
        title=X1_WHITEPAPER_TITLE,
        version=X1_WHITEPAPER_VERSION,
        authority_class="primary",
        approval_status="approved",
        parser_version="utf8-source/v1",
        metadata=metadata,
    )
    if clock is None:
        return ingest_utf8_source(**common)
    return ingest_utf8_source(**common, clock=clock)
