from __future__ import annotations

from dataclasses import replace

import pytest

from roberta.learning import (
    ChunkingError,
    InMemorySourceStore,
    ParsedDocument,
    chunk_parsed_document,
    ingest_utf8_source,
    parse_markdown_structure,
)


def _parsed(content: str, *, authority_class: str = "internal"):
    store = InMemorySourceStore()
    source = ingest_utf8_source(
        store=store,
        content=content,
        origin="test://learning-chunking",
        title="Chunk Fixture",
        version="1",
        authority_class=authority_class,
        approval_status="approved",
        parser_version="utf8-source/v1",
    ).record
    parsed = parse_markdown_structure(store=store, source_id=source.source_id)
    return store, source, parsed


def test_adjacent_same_section_prose_groups_with_exact_blank_lines() -> None:
    store, source, parsed = _parsed("# H\r\nfirst\r\n\r\nsecond\r\n")

    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=100)

    assert len(parsed.blocks) == 2
    assert len(chunked.chunks) == 1
    chunk = chunked.chunks[0]
    assert chunk.kind == "prose"
    assert chunk.block_ids == (parsed.blocks[0].block_id, parsed.blocks[1].block_id)
    assert chunk.line_start == 2 and chunk.line_end == 4
    assert chunk.text == "first\r\n\r\nsecond\r\n"
    assert chunk.section_id == parsed.sections[0].section_id
    assert chunk.structural_path == ("H",)
    assert chunk.source_id == source.source_id
    assert chunk.source_authority_class == "internal"
    assert chunk.source_approval_status == "approved"


def test_prose_never_crosses_section_boundary() -> None:
    store, _, parsed = _parsed("# A\none\n\n# B\ntwo\n")

    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=100)

    assert len(chunked.chunks) == 2
    assert chunked.chunks[0].section_id == parsed.sections[0].section_id
    assert chunked.chunks[1].section_id == parsed.sections[1].section_id
    assert chunked.chunks[0].text == "one\n"
    assert chunked.chunks[1].text == "two\n"


def test_code_list_and_table_blocks_remain_separate_atomic_chunks() -> None:
    content = (
        "# H\n"
        "- one\n"
        "- two\n"
        "\n"
        "| A | B |\n"
        "| --- | --- |\n"
        "| 1 | 2 |\n"
        "\n"
        "```python\n"
        "# data\n"
        "```\n"
    )
    store, _, parsed = _parsed(content)

    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=1000)

    assert [chunk.kind for chunk in chunked.chunks] == ["list", "table", "code_fence"]
    assert all(len(chunk.block_ids) == 1 for chunk in chunked.chunks)
    assert [chunk.status for chunk in chunked.chunks] == ["normal", "normal", "normal"]


def test_prose_group_stops_before_exact_source_span_exceeds_max_chars() -> None:
    store, _, parsed = _parsed("# H\naaaa\n\nbbbb\n\ncccc\n")

    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=12)

    assert len(chunked.chunks) == 2
    assert chunked.chunks[0].text == "aaaa\n\nbbbb\n"
    assert len(chunked.chunks[0].text) == 11
    assert len(chunked.chunks[0].block_ids) == 2
    assert chunked.chunks[1].text == "cccc\n"


def test_oversize_prose_splits_only_at_source_line_boundaries() -> None:
    store, _, parsed = _parsed("# H\n1111\n2222\n3333\n")

    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=10)

    assert len(parsed.blocks) == 1
    assert len(chunked.chunks) == 2
    first, second = chunked.chunks
    assert first.text == "1111\n2222\n"
    assert second.text == "3333\n"
    assert first.line_start == 2 and first.line_end == 3
    assert second.line_start == 4 and second.line_end == 4
    assert first.block_ids == second.block_ids == (parsed.blocks[0].block_id,)
    assert first.fragment_index == 0 and second.fragment_index == 1
    assert first.fragment_count == second.fragment_count == 2
    assert first.status == second.status == "normal"


def test_oversize_single_line_is_preserved_and_flagged_not_split() -> None:
    store, _, parsed = _parsed("# H\n1234567890\n")

    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=5)

    assert len(chunked.chunks) == 1
    chunk = chunked.chunks[0]
    assert chunk.text == "1234567890\n"
    assert chunk.status == "oversize_line"
    assert chunk.warnings == (
        "oversize_line:line=2:max_chars=5:observed_chars=11",
    )
    assert chunked.manifest.warnings == chunk.warnings


def test_oversize_atomic_blocks_are_preserved_and_flagged() -> None:
    content = (
        "# H\n"
        "- aaa\n"
        "- bbb\n"
        "\n"
        "| A | B |\n"
        "| --- | --- |\n"
        "| 1 | 2 |\n"
        "\n"
        "```\n"
        "abc\n"
        "```\n"
    )
    store, _, parsed = _parsed(content)

    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=5)

    assert [chunk.kind for chunk in chunked.chunks] == ["list", "table", "code_fence"]
    assert all(chunk.status == "oversize_atomic" for chunk in chunked.chunks)
    assert [chunk.text for chunk in chunked.chunks] == [block.text for block in parsed.blocks]
    assert len(chunked.manifest.warnings) == 3


def test_nonzero_overlap_and_invalid_max_chars_fail_closed() -> None:
    store, _, parsed = _parsed("# H\ntext\n")

    with pytest.raises(ChunkingError, match="overlap_lines"):
        chunk_parsed_document(store=store, parsed=parsed, overlap_lines=1)

    with pytest.raises(ChunkingError, match="positive integer"):
        chunk_parsed_document(store=store, parsed=parsed, max_chars=0)


def test_tampered_parsed_document_fails_canonical_structure_check() -> None:
    store, _, parsed = _parsed("# H\ntext\n")
    tampered_document = replace(parsed.document, title="Caller-authored title")
    tampered = ParsedDocument(
        document=tampered_document,
        sections=parsed.sections,
        blocks=parsed.blocks,
    )

    with pytest.raises(ChunkingError, match="canonical Phase 2 structure"):
        chunk_parsed_document(store=store, parsed=tampered)


def test_source_artifact_mismatch_fails_before_chunking() -> None:
    store, source, parsed = _parsed("# H\ntext\n")
    store._artifacts[source.artifact_ref] = b"tampered\n"

    with pytest.raises(ChunkingError, match="content hash"):
        chunk_parsed_document(store=store, parsed=parsed)


def test_every_structural_block_line_is_covered_exactly_once() -> None:
    content = (
        "preamble one\n"
        "\n"
        "preamble two\n"
        "\n"
        "# H\n"
        "a\n"
        "b\n"
        "c\n"
        "\n"
        "- x\n"
        "- y\n"
    )
    store, _, parsed = _parsed(content)
    chunked = chunk_parsed_document(store=store, parsed=parsed, max_chars=4)

    for block in parsed.blocks:
        counts = {line: 0 for line in range(block.line_start, block.line_end + 1)}
        for chunk in chunked.chunks:
            if block.block_id not in chunk.block_ids:
                continue
            start = max(block.line_start, chunk.line_start)
            end = min(block.line_end, chunk.line_end)
            for line in range(start, end + 1):
                counts[line] += 1
        assert counts and all(count == 1 for count in counts.values())


def test_deterministic_rebuild_and_previous_next_linkage() -> None:
    store, _, parsed = _parsed("# H\none\n\n- x\n\nlast\n")

    first = chunk_parsed_document(store=store, parsed=parsed, max_chars=20)
    second = chunk_parsed_document(store=store, parsed=parsed, max_chars=20)

    assert second == first
    assert first.manifest.chunk_set_id == f"cset_{first.manifest.chunking_hash}"
    assert first.manifest.chunk_ids == tuple(chunk.chunk_id for chunk in first.chunks)
    assert first.chunks[0].previous_chunk_id is None
    assert first.chunks[-1].next_chunk_id is None
    for index, chunk in enumerate(first.chunks):
        if index > 0:
            assert chunk.previous_chunk_id == first.chunks[index - 1].chunk_id
        if index + 1 < len(first.chunks):
            assert chunk.next_chunk_id == first.chunks[index + 1].chunk_id


def test_chunker_version_and_parameter_changes_change_derived_identity_only() -> None:
    store, source, parsed = _parsed("# H\none\n\ntwo\n")

    baseline = chunk_parsed_document(
        store=store, parsed=parsed, chunker_version="1.0.0", max_chars=100
    )
    version_changed = chunk_parsed_document(
        store=store, parsed=parsed, chunker_version="1.0.1", max_chars=100
    )
    parameter_changed = chunk_parsed_document(
        store=store, parsed=parsed, chunker_version="1.0.0", max_chars=5
    )

    assert baseline.manifest.source_id == source.source_id
    assert version_changed.manifest.source_id == source.source_id
    assert parameter_changed.manifest.source_id == source.source_id
    assert baseline.manifest.chunk_set_id != version_changed.manifest.chunk_set_id
    assert baseline.manifest.chunk_set_id != parameter_changed.manifest.chunk_set_id
    assert baseline.manifest.chunk_ids != version_changed.manifest.chunk_ids


def test_all_chunk_records_and_manifest_deny_live_state_authority() -> None:
    store, _, parsed = _parsed("# H\ntext\n")

    chunked = chunk_parsed_document(store=store, parsed=parsed)

    assert chunked.live_state_authorized is False
    assert chunked.manifest.live_state_authorized is False
    assert all(chunk.live_state_authorized is False for chunk in chunked.chunks)
