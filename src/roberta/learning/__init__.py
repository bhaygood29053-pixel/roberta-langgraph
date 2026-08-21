"""Evidence-grounded Roberta Learning System boundaries."""

from .source_ingestion import (
    InMemorySourceStore,
    IngestionResult,
    SourceIngestionError,
    SourceRecord,
    SourceStore,
    ingest_utf8_source,
)

__all__ = [
    "InMemorySourceStore",
    "IngestionResult",
    "SourceIngestionError",
    "SourceRecord",
    "SourceStore",
    "ingest_utf8_source",
]
