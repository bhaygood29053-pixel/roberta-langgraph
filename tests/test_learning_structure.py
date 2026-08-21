from __future__ import annotations

import hashlib

import pytest

from roberta.learning import (
    InMemorySourceStore,
    StructureParseError,
    ingest_utf8_source,
    parse_markdown_structure,
)


def _source(store: InMemorySourceStore, content: str, *, title: str = "Fixture"):
    return ingest_utf8_source(
        store=store,
        content=content,
        origin="test://learning-structure",
        title=title,
        version="1",
        authority_class="internal",
        approval_status="approved",
        parser_version="utf8-source/v1",
    ).record


def test_structure_parser_preserves_hierarchy_locations_and_exact_blocks() -> None:
    store = InMemorySourceStore()
    content = (
        "Intro line\r\n"
        "\r\n"
        "# Root\r\n"
        "Paragraph one\r\n"
        "continued\r\n"
        "\r\n"
        "- a\r\n"
        "- b\r\n"
        "\r\n"
        "| A | B |\r\n"
        "| --- | :---: |\r\n"
        "| 1 | 2 |\r\n"
        "\r\n"
        "## Child\r\n"
        "```python\r\n"
        "# not a heading\r\n"
        "```\r\n"
        "\r\n"
        "### Grandchild\r\n"
        "text\r\n"
        "## Child\r\n"
        "again\r\n"
    )
    source = _source(store, content, title="Structure Fixture")

    parsed = parse_markdown_structure(store=store, source_id=source.source_id)

    assert parsed.document.title == "Structure Fixture"
    assert parsed.document.status == "complete"
    assert parsed.document.warnings == ()
    assert parsed.document.document_id.startswith("doc_")
    assert len(parsed.document.structure_hash) == 64
    assert parsed.document.source_content_hash == hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    assert [(section.heading, section.level) for section in parsed.sections] == [
        ("Root", 1),
        ("Child", 2),
        ("Grandchild", 3),
        ("Child", 2),
    ]
    root, first_child, grandchild, second_child = parsed.sections
    assert root.parent_section_id is None
    assert first_child.parent_section_id == root.section_id
    assert grandchild.parent_section_id == first_child.section_id
    assert second_child.parent_section_id == root.section_id
    assert first_child.section_id != second_child.section_id
    assert first_child.structural_path == ("Root", "Child")
    assert grandchild.structural_path == ("Root", "Child", "Grandchild")
    assert root.line_start == 3 and root.line_end == 22
    assert first_child.line_start == 14 and first_child.line_end == 20
    assert grandchild.line_start == 19 and grandchild.line_end == 20
    assert second_child.line_start == 21 and second_child.line_end == 22
    assert root.heading_line == "# Root\r\n"

    assert [(block.kind, block.line_start, block.line_end) for block in parsed.blocks] == [
        ("preamble", 1, 1),
        ("paragraph", 4, 5),
        ("list", 7, 8),
        ("table", 10, 12),
        ("code_fence", 15, 17),
        ("paragraph", 20, 20),
        ("paragraph", 22, 22),
    ]
    assert parsed.blocks[0].text == "Intro line\r\n"
    assert parsed.blocks[1].text == "Paragraph one\r\ncontinued\r\n"
    assert parsed.blocks[2].text == "- a\r\n- b\r\n"
    assert parsed.blocks[4].text == "```python\r\n# not a heading\r\n```\r\n"
    assert "not a heading" not in [section.heading for section in parsed.sections]


def test_every_nonblank_line_is_accounted_for_once_by_heading_or_block() -> None:
    store = InMemorySourceStore()
    content = "preamble\n\n# A\ntext\n\n- x\n- y\n\n## B\nbody\n"
    source = _source(store, content)
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)

    counts: dict[int, int] = {}
    for section in parsed.sections:
        counts[section.line_start] = counts.get(section.line_start, 0) + 1
    for block in parsed.blocks:
        for line_number in range(block.line_start, block.line_end + 1):
            if content.splitlines()[line_number - 1].strip():
                counts[line_number] = counts.get(line_number, 0) + 1

    nonblank = {
        index
        for index, line in enumerate(content.splitlines(), start=1)
        if line.strip()
    }
    assert set(counts) == nonblank
    assert all(count == 1 for count in counts.values())


def test_heading_level_jump_warns_without_inventing_missing_section() -> None:
    store = InMemorySourceStore()
    source = _source(store, "# One\n### Three\nbody\n")

    parsed = parse_markdown_structure(store=store, source_id=source.source_id)

    assert [section.level for section in parsed.sections] == [1, 3]
    assert parsed.sections[1].parent_section_id == parsed.sections[0].section_id
    assert parsed.document.warnings == ("heading_level_jump:line=2:from=1:to=3",)
    assert parsed.document.status == "complete"


def test_unclosed_code_fence_is_preserved_and_marks_partial() -> None:
    store = InMemorySourceStore()
    source = _source(store, "# H\n```python\n# data\nprint('x')\n")

    parsed = parse_markdown_structure(store=store, source_id=source.source_id)

    assert len(parsed.sections) == 1
    assert [section.heading for section in parsed.sections] == ["H"]
    assert len(parsed.blocks) == 1
    assert parsed.blocks[0].kind == "code_fence"
    assert parsed.blocks[0].line_start == 2
    assert parsed.blocks[0].line_end == 4
    assert parsed.blocks[0].text == "```python\n# data\nprint('x')\n"
    assert parsed.document.status == "partial"
    assert parsed.document.warnings == ("unclosed_code_fence:line=2",)


def test_ambiguous_pipe_prose_is_not_promoted_to_table() -> None:
    store = InMemorySourceStore()
    source = _source(store, "# H\nthis | is prose\nnext line\n")

    parsed = parse_markdown_structure(store=store, source_id=source.source_id)

    assert len(parsed.blocks) == 1
    assert parsed.blocks[0].kind == "paragraph"
    assert parsed.blocks[0].text == "this | is prose\nnext line\n"


def test_simple_list_contract_does_not_absorb_unmarked_continuation() -> None:
    store = InMemorySourceStore()
    source = _source(store, "# H\n- one\n- two\ncontinuation prose\n")

    parsed = parse_markdown_structure(store=store, source_id=source.source_id)

    assert [(block.kind, block.text) for block in parsed.blocks] == [
        ("list", "- one\n- two\n"),
        ("paragraph", "continuation prose\n"),
    ]


def test_deterministic_rebuild_has_identical_ids_hash_and_records() -> None:
    store = InMemorySourceStore()
    source = _source(store, "# H\ntext\n## C\nmore\n")

    first = parse_markdown_structure(store=store, source_id=source.source_id)
    second = parse_markdown_structure(store=store, source_id=source.source_id)

    assert second == first
    assert second.document.structure_hash == first.document.structure_hash
    assert second.document.section_ids == first.document.section_ids
    assert second.document.block_ids == first.document.block_ids


def test_parser_version_changes_document_identity_without_changing_source() -> None:
    store = InMemorySourceStore()
    source = _source(store, "# H\ntext\n")

    first = parse_markdown_structure(
        store=store, source_id=source.source_id, parser_version="1.0.0"
    )
    second = parse_markdown_structure(
        store=store, source_id=source.source_id, parser_version="1.0.1"
    )

    assert first.document.source_id == second.document.source_id == source.source_id
    assert first.document.document_id != second.document.document_id
    assert first.document.structure_hash != second.document.structure_hash


def test_unknown_source_unsupported_contract_and_artifact_tampering_fail_closed() -> None:
    store = InMemorySourceStore()

    with pytest.raises(StructureParseError, match="unknown source_id"):
        parse_markdown_structure(store=store, source_id="src_missing")

    source = _source(store, "# H\ntext\n")
    with pytest.raises(StructureParseError, match="unsupported parser_contract"):
        parse_markdown_structure(
            store=store,
            source_id=source.source_id,
            parser_contract="markdown-structure/v2",
        )

    store._artifacts[source.artifact_ref] = b"tampered\n"
    with pytest.raises(StructureParseError, match="content hash"):
        parse_markdown_structure(store=store, source_id=source.source_id)


def test_structure_records_never_authorize_live_state() -> None:
    store = InMemorySourceStore()
    source = _source(store, "# H\ntext\n")
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)

    assert parsed.live_state_authorized is False
    assert parsed.document.live_state_authorized is False
    assert all(section.live_state_authorized is False for section in parsed.sections)
    assert all(block.live_state_authorized is False for block in parsed.blocks)
