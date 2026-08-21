"""Deterministic structure-aware evidence chunking for the Learning System.

Phase 3 turns canonical Phase 2 structural blocks into source-located evidence
chunks. It deliberately performs no embedding, retrieval, concept extraction,
summarization, question generation, or learning/promotion behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .source_ingestion import SourceStore
from .structure import ParsedDocument, StructuralBlock, parse_markdown_structure


CHUNKER_CONTRACT = "structure-aware-chunk/v1"
_DEFAULT_CHUNKER_VERSION = "1.0.0"
_DEFAULT_MAX_CHARS = 1600


class ChunkingError(ValueError):
    """Raised when canonical evidence chunks cannot be produced safely."""


@dataclass(frozen=True, slots=True)
class EvidenceChunk:
    chunk_id: str
    source_id: str
    document_id: str
    section_id: str | None
    block_ids: tuple[str, ...]
    structural_path: tuple[str, ...]
    kind: str
    order: int
    line_start: int
    line_end: int
    text: str
    content_hash: str
    source_authority_class: str
    source_approval_status: str
    parser_contract: str
    parser_version: str
    chunker_contract: str
    chunker_version: str
    max_chars: int
    overlap_lines: int
    status: str
    warnings: tuple[str, ...]
    fragment_index: int
    fragment_count: int
    previous_chunk_id: str | None
    next_chunk_id: str | None

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class ChunkManifest:
    chunk_set_id: str
    source_id: str
    document_id: str
    parser_contract: str
    parser_version: str
    chunker_contract: str
    chunker_version: str
    max_chars: int
    overlap_lines: int
    chunk_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    chunking_hash: str

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class ChunkedDocument:
    manifest: ChunkManifest
    chunks: tuple[EvidenceChunk, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class _ChunkCandidate:
    source_id: str
    document_id: str
    section_id: str | None
    block_ids: tuple[str, ...]
    structural_path: tuple[str, ...]
    kind: str
    line_start: int
    line_end: int
    text: str
    status: str
    warnings: tuple[str, ...]
    fragment_index: int
    fragment_count: int


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ChunkingError("chunk material must be canonical JSON-compatible data") from exc


def _content_id(prefix: str, value: Any) -> str:
    return prefix + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _normalized_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ChunkingError(f"{name} must be a normalized non-empty string")
    return value


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ChunkingError(f"{name} must be a positive integer")
    return value


def _zero_overlap(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise ChunkingError("overlap_lines must equal 0 for structure-aware-chunk/v1")
    return value


def _source_slice(lines: list[str], line_start: int, line_end: int) -> str:
    if line_start < 1 or line_end < line_start or line_end > len(lines):
        raise ChunkingError(
            f"invalid source line range {line_start}-{line_end} for {len(lines)} lines"
        )
    return "".join(lines[line_start - 1 : line_end])


def _chunk_dict(chunk: EvidenceChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "source_id": chunk.source_id,
        "document_id": chunk.document_id,
        "section_id": chunk.section_id,
        "block_ids": list(chunk.block_ids),
        "structural_path": list(chunk.structural_path),
        "kind": chunk.kind,
        "order": chunk.order,
        "line_start": chunk.line_start,
        "line_end": chunk.line_end,
        "text": chunk.text,
        "content_hash": chunk.content_hash,
        "source_authority_class": chunk.source_authority_class,
        "source_approval_status": chunk.source_approval_status,
        "parser_contract": chunk.parser_contract,
        "parser_version": chunk.parser_version,
        "chunker_contract": chunk.chunker_contract,
        "chunker_version": chunk.chunker_version,
        "max_chars": chunk.max_chars,
        "overlap_lines": chunk.overlap_lines,
        "status": chunk.status,
        "warnings": list(chunk.warnings),
        "fragment_index": chunk.fragment_index,
        "fragment_count": chunk.fragment_count,
        "previous_chunk_id": chunk.previous_chunk_id,
        "next_chunk_id": chunk.next_chunk_id,
    }


def _prose_fragments(
    *,
    block: StructuralBlock,
    lines: list[str],
    source_id: str,
    document_id: str,
    structural_path: tuple[str, ...],
    max_chars: int,
) -> list[_ChunkCandidate]:
    fragments: list[tuple[int, int, str, str, tuple[str, ...]]] = []
    current_start: int | None = None
    current_end: int | None = None
    current_text = ""

    def flush_current() -> None:
        nonlocal current_start, current_end, current_text
        if current_start is None or current_end is None:
            return
        fragments.append((current_start, current_end, current_text, "normal", ()))
        current_start = None
        current_end = None
        current_text = ""

    for line_number in range(block.line_start, block.line_end + 1):
        raw_line = lines[line_number - 1]
        if len(raw_line) > max_chars:
            flush_current()
            warning = (
                f"oversize_line:line={line_number}:max_chars={max_chars}:"
                f"observed_chars={len(raw_line)}"
            )
            fragments.append(
                (line_number, line_number, raw_line, "oversize_line", (warning,))
            )
            continue

        if current_start is None:
            current_start = line_number
            current_end = line_number
            current_text = raw_line
            continue

        if len(current_text) + len(raw_line) <= max_chars:
            current_end = line_number
            current_text += raw_line
        else:
            flush_current()
            current_start = line_number
            current_end = line_number
            current_text = raw_line

    flush_current()
    fragment_count = len(fragments)
    return [
        _ChunkCandidate(
            source_id=source_id,
            document_id=document_id,
            section_id=block.section_id,
            block_ids=(block.block_id,),
            structural_path=structural_path,
            kind="prose",
            line_start=line_start,
            line_end=line_end,
            text=text,
            status=status,
            warnings=warnings,
            fragment_index=index,
            fragment_count=fragment_count,
        )
        for index, (line_start, line_end, text, status, warnings) in enumerate(fragments)
    ]


def chunk_parsed_document(
    *,
    store: SourceStore,
    parsed: ParsedDocument,
    chunker_version: str = _DEFAULT_CHUNKER_VERSION,
    chunker_contract: str = CHUNKER_CONTRACT,
    max_chars: int = _DEFAULT_MAX_CHARS,
    overlap_lines: int = 0,
) -> ChunkedDocument:
    """Create deterministic evidence chunks from canonical Phase 2 structure."""

    if not isinstance(parsed, ParsedDocument):
        raise ChunkingError("parsed must be a canonical ParsedDocument")
    normalized_contract = _normalized_text("chunker_contract", chunker_contract)
    if normalized_contract != CHUNKER_CONTRACT:
        raise ChunkingError(
            f"unsupported chunker_contract {normalized_contract!r}; expected {CHUNKER_CONTRACT!r}"
        )
    normalized_version = _normalized_text("chunker_version", chunker_version)
    normalized_max_chars = _positive_int("max_chars", max_chars)
    normalized_overlap = _zero_overlap(overlap_lines)

    source = store.get_source(parsed.document.source_id)
    if source is None:
        raise ChunkingError(f"unknown source_id {parsed.document.source_id}")
    if source.source_id != parsed.document.source_id:
        raise ChunkingError("source store returned mismatched source identity")
    artifact = store.get_artifact(source.artifact_ref)
    if artifact is None:
        raise ChunkingError("source artifact is unavailable")
    observed_hash = hashlib.sha256(artifact).hexdigest()
    if observed_hash != source.content_hash:
        raise ChunkingError("source artifact content hash does not match SourceRecord")
    if parsed.document.source_content_hash != source.content_hash:
        raise ChunkingError("ParsedDocument source content hash does not match SourceRecord")
    try:
        text = artifact.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ChunkingError("source artifact is not valid UTF-8") from exc

    canonical_parsed = parse_markdown_structure(
        store=store,
        source_id=source.source_id,
        parser_contract=parsed.document.parser_contract,
        parser_version=parsed.document.parser_version,
    )
    if canonical_parsed != parsed:
        raise ChunkingError("supplied ParsedDocument does not match canonical Phase 2 structure")

    lines = text.splitlines(keepends=True)
    section_paths = {
        section.section_id: section.structural_path for section in parsed.sections
    }
    blocks = list(parsed.blocks)
    candidates: list[_ChunkCandidate] = []
    index = 0

    while index < len(blocks):
        block = blocks[index]
        structural_path = (
            section_paths.get(block.section_id, ()) if block.section_id is not None else ()
        )
        if block.section_id is not None and block.section_id not in section_paths:
            raise ChunkingError(f"block {block.block_id} references an unknown section")

        if block.kind in {"code_fence", "list", "table"}:
            exact_text = _source_slice(lines, block.line_start, block.line_end)
            if exact_text != block.text:
                raise ChunkingError(f"block {block.block_id} text does not match source artifact")
            status = "normal"
            warnings: tuple[str, ...] = ()
            if len(exact_text) > normalized_max_chars:
                status = "oversize_atomic"
                warnings = (
                    f"oversize_atomic:block={block.block_id}:max_chars={normalized_max_chars}:"
                    f"observed_chars={len(exact_text)}",
                )
            candidates.append(
                _ChunkCandidate(
                    source_id=source.source_id,
                    document_id=parsed.document.document_id,
                    section_id=block.section_id,
                    block_ids=(block.block_id,),
                    structural_path=structural_path,
                    kind=block.kind,
                    line_start=block.line_start,
                    line_end=block.line_end,
                    text=exact_text,
                    status=status,
                    warnings=warnings,
                    fragment_index=0,
                    fragment_count=1,
                )
            )
            index += 1
            continue

        if block.kind not in {"preamble", "paragraph"}:
            raise ChunkingError(f"unsupported Phase 2 block kind {block.kind!r}")

        exact_block_text = _source_slice(lines, block.line_start, block.line_end)
        if exact_block_text != block.text:
            raise ChunkingError(f"block {block.block_id} text does not match source artifact")

        if len(exact_block_text) > normalized_max_chars:
            candidates.extend(
                _prose_fragments(
                    block=block,
                    lines=lines,
                    source_id=source.source_id,
                    document_id=parsed.document.document_id,
                    structural_path=structural_path,
                    max_chars=normalized_max_chars,
                )
            )
            index += 1
            continue

        grouped = [block]
        end_index = index
        probe = index + 1
        while probe < len(blocks):
            next_block = blocks[probe]
            if next_block.kind not in {"preamble", "paragraph"}:
                break
            if next_block.section_id != block.section_id:
                break
            candidate_text = _source_slice(
                lines, grouped[0].line_start, next_block.line_end
            )
            if len(candidate_text) > normalized_max_chars:
                break
            grouped.append(next_block)
            end_index = probe
            probe += 1

        grouped_text = _source_slice(lines, grouped[0].line_start, grouped[-1].line_end)
        candidates.append(
            _ChunkCandidate(
                source_id=source.source_id,
                document_id=parsed.document.document_id,
                section_id=block.section_id,
                block_ids=tuple(item.block_id for item in grouped),
                structural_path=structural_path,
                kind="prose",
                line_start=grouped[0].line_start,
                line_end=grouped[-1].line_end,
                text=grouped_text,
                status="normal",
                warnings=(),
                fragment_index=0,
                fragment_count=1,
            )
        )
        index = end_index + 1

    block_map = {block.block_id: block for block in parsed.blocks}
    for block in parsed.blocks:
        coverage: dict[int, int] = {
            line_number: 0
            for line_number in range(block.line_start, block.line_end + 1)
        }
        for candidate in candidates:
            if block.block_id not in candidate.block_ids:
                continue
            start = max(block.line_start, candidate.line_start)
            end = min(block.line_end, candidate.line_end)
            if end < start:
                raise ChunkingError(
                    f"chunk candidate cites block {block.block_id} without overlapping its source lines"
                )
            for line_number in range(start, end + 1):
                coverage[line_number] += 1
        invalid = {
            line_number: count
            for line_number, count in coverage.items()
            if count != 1
        }
        if invalid:
            raise ChunkingError(
                f"source-block coverage invariant failed for {block.block_id}: {invalid}"
            )

    for candidate in candidates:
        for block_id in candidate.block_ids:
            if block_id not in block_map:
                raise ChunkingError(f"chunk candidate references unknown block {block_id}")

    chunk_ids: list[str] = []
    for order, candidate in enumerate(candidates):
        content_hash = hashlib.sha256(candidate.text.encode("utf-8")).hexdigest()
        chunk_ids.append(
            _content_id(
                "chk_",
                {
                    "source_id": candidate.source_id,
                    "document_id": candidate.document_id,
                    "section_id": candidate.section_id,
                    "block_ids": list(candidate.block_ids),
                    "structural_path": list(candidate.structural_path),
                    "kind": candidate.kind,
                    "order": order,
                    "line_start": candidate.line_start,
                    "line_end": candidate.line_end,
                    "content_hash": content_hash,
                    "parser_contract": parsed.document.parser_contract,
                    "parser_version": parsed.document.parser_version,
                    "chunker_contract": normalized_contract,
                    "chunker_version": normalized_version,
                    "max_chars": normalized_max_chars,
                    "overlap_lines": normalized_overlap,
                    "fragment_index": candidate.fragment_index,
                    "fragment_count": candidate.fragment_count,
                },
            )
        )

    chunks = tuple(
        EvidenceChunk(
            chunk_id=chunk_ids[order],
            source_id=candidate.source_id,
            document_id=candidate.document_id,
            section_id=candidate.section_id,
            block_ids=candidate.block_ids,
            structural_path=candidate.structural_path,
            kind=candidate.kind,
            order=order,
            line_start=candidate.line_start,
            line_end=candidate.line_end,
            text=candidate.text,
            content_hash=hashlib.sha256(candidate.text.encode("utf-8")).hexdigest(),
            source_authority_class=source.authority_class,
            source_approval_status=source.approval_status,
            parser_contract=parsed.document.parser_contract,
            parser_version=parsed.document.parser_version,
            chunker_contract=normalized_contract,
            chunker_version=normalized_version,
            max_chars=normalized_max_chars,
            overlap_lines=normalized_overlap,
            status=candidate.status,
            warnings=candidate.warnings,
            fragment_index=candidate.fragment_index,
            fragment_count=candidate.fragment_count,
            previous_chunk_id=chunk_ids[order - 1] if order > 0 else None,
            next_chunk_id=chunk_ids[order + 1] if order + 1 < len(chunk_ids) else None,
        )
        for order, candidate in enumerate(candidates)
    )

    manifest_warnings: list[str] = []
    for chunk in chunks:
        for warning in chunk.warnings:
            if warning not in manifest_warnings:
                manifest_warnings.append(warning)

    manifest_material = {
        "source_id": source.source_id,
        "document_id": parsed.document.document_id,
        "parser_contract": parsed.document.parser_contract,
        "parser_version": parsed.document.parser_version,
        "chunker_contract": normalized_contract,
        "chunker_version": normalized_version,
        "max_chars": normalized_max_chars,
        "overlap_lines": normalized_overlap,
        "warnings": manifest_warnings,
        "chunks": [_chunk_dict(chunk) for chunk in chunks],
    }
    chunking_hash = hashlib.sha256(
        _canonical_json(manifest_material).encode("utf-8")
    ).hexdigest()
    manifest = ChunkManifest(
        chunk_set_id=f"cset_{chunking_hash}",
        source_id=source.source_id,
        document_id=parsed.document.document_id,
        parser_contract=parsed.document.parser_contract,
        parser_version=parsed.document.parser_version,
        chunker_contract=normalized_contract,
        chunker_version=normalized_version,
        max_chars=normalized_max_chars,
        overlap_lines=normalized_overlap,
        chunk_ids=tuple(chunk_ids),
        warnings=tuple(manifest_warnings),
        chunking_hash=chunking_hash,
    )
    return ChunkedDocument(manifest=manifest, chunks=chunks)
