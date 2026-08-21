"""Evidence-grounded Roberta Learning System boundaries."""

from .chunking import (
    CHUNKER_CONTRACT,
    ChunkedDocument,
    ChunkingError,
    ChunkManifest,
    EvidenceChunk,
    chunk_parsed_document,
)
from .source_ingestion import (
    InMemorySourceStore,
    IngestionResult,
    SourceIngestionError,
    SourceRecord,
    SourceStore,
    ingest_utf8_source,
)
from .structure import (
    PARSER_CONTRACT,
    DocumentRecord,
    ParsedDocument,
    SectionRecord,
    StructuralBlock,
    StructureParseError,
    parse_markdown_structure,
)

__all__ = [
    "CHUNKER_CONTRACT",
    "ChunkManifest",
    "ChunkedDocument",
    "ChunkingError",
    "DocumentRecord",
    "EvidenceChunk",
    "InMemorySourceStore",
    "IngestionResult",
    "PARSER_CONTRACT",
    "ParsedDocument",
    "SectionRecord",
    "SourceIngestionError",
    "SourceRecord",
    "SourceStore",
    "StructuralBlock",
    "StructureParseError",
    "chunk_parsed_document",
    "ingest_utf8_source",
    "parse_markdown_structure",
]
