"""Deterministic structure-first parsing for the Roberta Learning System.

Phase 2 transforms an exact Phase 1 UTF-8 source artifact into source-located
Markdown document, section, and structural-block records. It does not perform
semantic chunking, retrieval, summarization, concept extraction, or learning.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from .source_ingestion import SourceStore


PARSER_CONTRACT = "markdown-structure/v1"
_DEFAULT_PARSER_VERSION = "1.0.0"

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)(?:[ \t]+#+[ \t]*)?$")
_FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
_LIST_RE = re.compile(r"^[ \t]*(?:[-+*]|\d+[.)])[ \t]+\S")
_TABLE_SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")


class StructureParseError(ValueError):
    """Raised when structure parsing cannot safely produce accepted output."""


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    document_id: str
    source_id: str
    source_content_hash: str
    parser_contract: str
    parser_version: str
    title: str
    status: str
    section_ids: tuple[str, ...]
    block_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    structure_hash: str

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SectionRecord:
    section_id: str
    document_id: str
    parent_section_id: str | None
    heading: str
    level: int
    order: int
    line_start: int
    line_end: int
    heading_line: str
    structural_path: tuple[str, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class StructuralBlock:
    block_id: str
    document_id: str
    section_id: str | None
    kind: str
    order: int
    line_start: int
    line_end: int
    text: str
    text_hash: str

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    document: DocumentRecord
    sections: tuple[SectionRecord, ...]
    blocks: tuple[StructuralBlock, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(slots=True)
class _SectionBuilder:
    section_id: str
    document_id: str
    parent_section_id: str | None
    heading: str
    level: int
    order: int
    line_start: int
    line_end: int | None
    heading_line: str
    structural_path: tuple[str, ...]


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
        raise StructureParseError("structure material must be canonical JSON-compatible data") from exc


def _content_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}{digest}"


def _normalized_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise StructureParseError(f"{name} must be a normalized non-empty string")
    return value


def _line_body(raw_line: str) -> str:
    if raw_line.endswith("\r\n"):
        return raw_line[:-2]
    if raw_line.endswith("\n") or raw_line.endswith("\r"):
        return raw_line[:-1]
    return raw_line


def _heading(body: str) -> tuple[int, str] | None:
    match = _HEADING_RE.match(body)
    if match is None:
        return None
    heading = match.group(2).strip()
    if not heading:
        return None
    return len(match.group(1)), heading


def _fence_open(body: str) -> tuple[str, int] | None:
    match = _FENCE_RE.match(body)
    if match is None:
        return None
    marker = match.group(1)
    return marker[0], len(marker)


def _is_fence_close(body: str, marker_char: str, minimum_length: int) -> bool:
    stripped = body.lstrip(" \t")
    count = 0
    while count < len(stripped) and stripped[count] == marker_char:
        count += 1
    if count < minimum_length:
        return False
    return stripped[count:].strip() == ""


def _is_list_line(body: str) -> bool:
    return _LIST_RE.match(body) is not None


def _table_cells(body: str) -> list[str]:
    text = body.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip() for cell in text.split("|")]


def _is_table_separator(body: str) -> bool:
    if "|" not in body:
        return False
    cells = _table_cells(body)
    return len(cells) >= 2 and all(
        bool(cell) and _TABLE_SEPARATOR_CELL_RE.fullmatch(cell) is not None
        for cell in cells
    )


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    body = _line_body(lines[index])
    next_body = _line_body(lines[index + 1])
    if not body.strip() or "|" not in body:
        return False
    if _heading(body) is not None or _fence_open(body) is not None or _is_list_line(body):
        return False
    return _is_table_separator(next_body)


def _section_dict(section: SectionRecord) -> dict[str, Any]:
    return {
        "section_id": section.section_id,
        "document_id": section.document_id,
        "parent_section_id": section.parent_section_id,
        "heading": section.heading,
        "level": section.level,
        "order": section.order,
        "line_start": section.line_start,
        "line_end": section.line_end,
        "heading_line": section.heading_line,
        "structural_path": list(section.structural_path),
    }


def _block_dict(block: StructuralBlock) -> dict[str, Any]:
    return {
        "block_id": block.block_id,
        "document_id": block.document_id,
        "section_id": block.section_id,
        "kind": block.kind,
        "order": block.order,
        "line_start": block.line_start,
        "line_end": block.line_end,
        "text": block.text,
        "text_hash": block.text_hash,
    }


def parse_markdown_structure(
    *,
    store: SourceStore,
    source_id: str,
    parser_version: str = _DEFAULT_PARSER_VERSION,
    parser_contract: str = PARSER_CONTRACT,
) -> ParsedDocument:
    """Parse one immutable Phase 1 source into deterministic Markdown structure."""

    normalized_source_id = _normalized_text("source_id", source_id)
    normalized_parser_version = _normalized_text("parser_version", parser_version)
    normalized_contract = _normalized_text("parser_contract", parser_contract)
    if normalized_contract != PARSER_CONTRACT:
        raise StructureParseError(
            f"unsupported parser_contract {normalized_contract!r}; expected {PARSER_CONTRACT!r}"
        )

    source = store.get_source(normalized_source_id)
    if source is None:
        raise StructureParseError(f"unknown source_id {normalized_source_id}")
    if source.source_id != normalized_source_id:
        raise StructureParseError("source store returned a record with mismatched source identity")

    artifact = store.get_artifact(source.artifact_ref)
    if artifact is None:
        raise StructureParseError("source artifact is unavailable")
    observed_hash = hashlib.sha256(artifact).hexdigest()
    if observed_hash != source.content_hash:
        raise StructureParseError("source artifact content hash does not match SourceRecord")
    try:
        text = artifact.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StructureParseError("source artifact is not valid UTF-8") from exc

    document_id = _content_id(
        "doc_",
        {
            "source_id": source.source_id,
            "source_content_hash": source.content_hash,
            "parser_contract": normalized_contract,
            "parser_version": normalized_parser_version,
        },
    )

    lines = text.splitlines(keepends=True)
    section_builders: list[_SectionBuilder] = []
    open_sections: list[int] = []
    blocks: list[StructuralBlock] = []
    warnings: list[str] = []
    account_counts: dict[int, int] = {}
    status = "complete"
    previous_heading_level = 0

    def account(line_start: int, line_end: int) -> None:
        for line_number in range(line_start, line_end + 1):
            account_counts[line_number] = account_counts.get(line_number, 0) + 1

    def current_section_id() -> str | None:
        if not open_sections:
            return None
        return section_builders[open_sections[-1]].section_id

    def append_block(kind: str, start_index: int, end_index: int) -> None:
        line_start = start_index + 1
        line_end = end_index + 1
        block_text = "".join(lines[start_index : end_index + 1])
        text_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
        order = len(blocks)
        section_id = current_section_id()
        block_id = _content_id(
            "blk_",
            {
                "document_id": document_id,
                "section_id": section_id,
                "kind": kind,
                "order": order,
                "line_start": line_start,
                "line_end": line_end,
                "text_hash": text_hash,
            },
        )
        blocks.append(
            StructuralBlock(
                block_id=block_id,
                document_id=document_id,
                section_id=section_id,
                kind=kind,
                order=order,
                line_start=line_start,
                line_end=line_end,
                text=block_text,
                text_hash=text_hash,
            )
        )
        account(line_start, line_end)

    index = 0
    while index < len(lines):
        body = _line_body(lines[index])
        if not body.strip():
            index += 1
            continue

        fence = _fence_open(body)
        if fence is not None:
            marker_char, marker_length = fence
            end_index = index + 1
            closed = False
            while end_index < len(lines):
                if _is_fence_close(
                    _line_body(lines[end_index]), marker_char, marker_length
                ):
                    closed = True
                    break
                end_index += 1
            if not closed:
                end_index = len(lines) - 1
                status = "partial"
                warnings.append(f"unclosed_code_fence:line={index + 1}")
            append_block("code_fence", index, end_index)
            index = end_index + 1
            continue

        heading_result = _heading(body)
        if heading_result is not None:
            level, heading_text = heading_result
            line_number = index + 1

            while open_sections and section_builders[open_sections[-1]].level >= level:
                closing = section_builders[open_sections.pop()]
                closing.line_end = line_number - 1

            parent_id = (
                section_builders[open_sections[-1]].section_id
                if open_sections
                else None
            )
            parent_path = (
                section_builders[open_sections[-1]].structural_path
                if open_sections
                else ()
            )
            structural_path = (*parent_path, heading_text)
            order = len(section_builders)
            section_id = _content_id(
                "sec_",
                {
                    "document_id": document_id,
                    "parent_section_id": parent_id,
                    "heading": heading_text,
                    "level": level,
                    "order": order,
                    "line_start": line_number,
                    "structural_path": list(structural_path),
                },
            )
            section_builders.append(
                _SectionBuilder(
                    section_id=section_id,
                    document_id=document_id,
                    parent_section_id=parent_id,
                    heading=heading_text,
                    level=level,
                    order=order,
                    line_start=line_number,
                    line_end=None,
                    heading_line=lines[index],
                    structural_path=structural_path,
                )
            )
            open_sections.append(len(section_builders) - 1)
            account(line_number, line_number)

            if level > previous_heading_level + 1:
                warnings.append(
                    f"heading_level_jump:line={line_number}:from={previous_heading_level}:to={level}"
                )
            previous_heading_level = level
            index += 1
            continue

        if _is_table_start(lines, index):
            end_index = index + 1
            probe = end_index + 1
            while probe < len(lines):
                probe_body = _line_body(lines[probe])
                if not probe_body.strip() or "|" not in probe_body:
                    break
                if (
                    _heading(probe_body) is not None
                    or _fence_open(probe_body) is not None
                    or _is_list_line(probe_body)
                ):
                    break
                end_index = probe
                probe += 1
            append_block("table", index, end_index)
            index = end_index + 1
            continue

        if _is_list_line(body):
            end_index = index
            probe = index + 1
            while probe < len(lines):
                probe_body = _line_body(lines[probe])
                if not probe_body.strip() or not _is_list_line(probe_body):
                    break
                end_index = probe
                probe += 1
            append_block("list", index, end_index)
            index = end_index + 1
            continue

        end_index = index
        probe = index + 1
        while probe < len(lines):
            probe_body = _line_body(lines[probe])
            if not probe_body.strip():
                break
            if (
                _fence_open(probe_body) is not None
                or _heading(probe_body) is not None
                or _is_list_line(probe_body)
                or _is_table_start(lines, probe)
            ):
                break
            end_index = probe
            probe += 1
        append_block("preamble" if not section_builders else "paragraph", index, end_index)
        index = end_index + 1

    final_line = len(lines)
    while open_sections:
        closing = section_builders[open_sections.pop()]
        closing.line_end = final_line

    sections = tuple(
        SectionRecord(
            section_id=builder.section_id,
            document_id=builder.document_id,
            parent_section_id=builder.parent_section_id,
            heading=builder.heading,
            level=builder.level,
            order=builder.order,
            line_start=builder.line_start,
            line_end=builder.line_end if builder.line_end is not None else final_line,
            heading_line=builder.heading_line,
            structural_path=builder.structural_path,
        )
        for builder in section_builders
    )

    nonblank_lines = {
        line_number
        for line_number, raw_line in enumerate(lines, start=1)
        if _line_body(raw_line).strip()
    }
    invalid_accounting = {
        line_number: account_counts.get(line_number, 0)
        for line_number in sorted(nonblank_lines)
        if account_counts.get(line_number, 0) != 1
    }
    if invalid_accounting:
        raise StructureParseError(
            f"source line accounting invariant failed: {invalid_accounting}"
        )

    manifest = {
        "document_id": document_id,
        "source_id": source.source_id,
        "source_content_hash": source.content_hash,
        "parser_contract": normalized_contract,
        "parser_version": normalized_parser_version,
        "title": source.title,
        "status": status,
        "warnings": warnings,
        "sections": [_section_dict(section) for section in sections],
        "blocks": [_block_dict(block) for block in blocks],
    }
    structure_hash = hashlib.sha256(_canonical_json(manifest).encode("utf-8")).hexdigest()
    document = DocumentRecord(
        document_id=document_id,
        source_id=source.source_id,
        source_content_hash=source.content_hash,
        parser_contract=normalized_contract,
        parser_version=normalized_parser_version,
        title=source.title,
        status=status,
        section_ids=tuple(section.section_id for section in sections),
        block_ids=tuple(block.block_id for block in blocks),
        warnings=tuple(warnings),
        structure_hash=structure_hash,
    )
    return ParsedDocument(document=document, sections=sections, blocks=tuple(blocks))
