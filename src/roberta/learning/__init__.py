"""Evidence-grounded Roberta Learning System boundaries."""

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
    "DocumentRecord",
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
    "ingest_utf8_source",
    "parse_markdown_structure",
]
