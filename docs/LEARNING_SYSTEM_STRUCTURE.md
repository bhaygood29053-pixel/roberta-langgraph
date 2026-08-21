# Learning System Structure Contract

Status: Phase 2 first slice for Issue #109.

## Purpose

Phase 2 performs a deterministic structure-first transformation over an immutable Phase 1 source artifact. It creates source-located document, section, and structural-block records without changing the source artifact or promoting generated interpretation into trusted knowledge.

The first accepted parser profile is deliberately narrow:

```text
format = markdown
parser_contract = markdown-structure/v1
encoding = UTF-8
```

PDF, DOCX, OCR, embeddings, semantic chunks, concepts, retrieval, question generation, reflection, lesson promotion, and fine-tuning are out of scope.

## Authority boundary

Structure output is static derived source metadata. It never authorizes current market/blockchain state.

```text
Phase 1 SourceStore -> exact source bytes -> Phase 2 deterministic structure

Current market/blockchain truth:
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

Fresh accepted CMIS/provider evidence remains authoritative for freshness-sensitive state.

## Public seam

```text
parse_markdown_structure(
    store=SourceStore,
    source_id=...,
    parser_version=...,
    parser_contract="markdown-structure/v1",
) -> ParsedDocument
```

The parser resolves the exact Phase 1 `SourceRecord` and artifact. Missing source/artifact state, content-hash mismatch, invalid UTF-8, or unsupported parser contract fails closed with `StructureParseError`.

## Records

### DocumentRecord

```text
document_id
source_id
source_content_hash
parser_contract
parser_version
title
status = complete | partial
section_ids
block_ids
warnings
structure_hash
live_state_authorized = false
```

The title is copied from the Phase 1 source record. Phase 2 does not infer a replacement title from headings.

### SectionRecord

```text
section_id
document_id
parent_section_id
heading
level
order
line_start
line_end
heading_line
structural_path
```

Line numbers are 1-based and inclusive. `heading_line` preserves the exact source line text including its original line ending when present. `structural_path` is the tuple of ancestor heading text plus the current heading.

A section extends from its heading line through the line immediately before the next heading whose level is less than or equal to the section level, or through end-of-source.

### StructuralBlock

```text
block_id
document_id
section_id
kind
order
line_start
line_end
text
text_hash
```

`text` preserves the exact source bytes for the block after UTF-8 decoding, including original line endings. `text_hash` is SHA-256 over that exact block text.

Accepted first-slice kinds:

- `preamble`
- `paragraph`
- `list`
- `code_fence`
- `table`

A block before the first heading may have `section_id = null`. Ordinary prose before the first heading is `preamble`. A code/list/table before the first heading keeps its structural kind and `section_id = null`.

## Heading rules

Only ATX headings using one through six leading `#` characters followed by whitespace are structural headings.

The parent of a section is the nearest still-open prior section with a lower heading level. The parser never invents missing intermediate headings.

A heading-level jump greater than one emits a deterministic warning such as:

```text
heading_level_jump:line=8:from=1:to=3
```

Repeated heading text is never merged. Section identity also binds deterministic order and source location.

Heading-looking text inside a fenced code block is data, not a document heading.

## Code fences

A fence begins with at least three backticks or tildes after optional leading whitespace. The opening marker character and minimum marker length bind the closing rule.

A closing fence must use the same marker character with at least the opening marker length and no non-whitespace text after the marker.

The full opening/body/closing source slice is one `code_fence` block.

If no valid closing fence exists, the parser preserves the remainder of the source in one `code_fence` block, sets the document status to `partial`, and emits:

```text
unclosed_code_fence:line=<opening line>
```

It does not synthesize a closing fence.

## Lists

The first slice intentionally supports only simple line-bounded Markdown lists. A list line must independently begin with a supported unordered marker (`-`, `+`, `*`) or ordered marker (`1.`, `1)`, etc.) followed by whitespace.

Consecutive non-blank lines that each independently satisfy the list-line rule form one `list` block. Indented continuation paragraphs are not absorbed into the list in v1; they are parsed separately.

## Tables

A narrow pipe-table is recognized only when:

1. the candidate header line contains a pipe;
2. the immediately following line is a separator row;
3. the separator contains at least two cells; and
4. every separator cell is at least three hyphens with optional leading/trailing colon alignment markers.

After the header + separator, consecutive non-blank pipe-containing rows are included until another structural boundary. Ambiguous pipe prose without a valid separator remains paragraph content.

## Paragraphs and preamble

Blank lines delimit prose blocks. A paragraph stops before a recognized heading, fence, list line, or valid narrow table start.

Ordinary prose before the first heading is emitted as `preamble`; after a heading it is `paragraph`.

## Source accounting

Every non-blank source line is accounted for exactly once as either:

- one section heading line; or
- content of exactly one structural block.

Blank lines remain source locations but are not emitted as blocks. The parser validates this accounting invariant before returning output. A duplicate or missing non-blank line fails closed.

## Deterministic identity

All ids are content-addressed SHA-256 values over canonical JSON with sorted keys, compact separators, UTF-8, and no NaN.

```text
document_id = doc_<64 hex>
section_id  = sec_<64 hex>
block_id    = blk_<64 hex>
```

The document identity binds source identity/content plus parser contract/version. Section identity binds document identity, hierarchy, heading, deterministic order, and location. Block identity binds document identity, section identity, kind, deterministic order, location, and exact text hash.

`structure_hash` is SHA-256 over the canonical completed structure manifest (document identity fields, section records, block records, status, and warnings). Same accepted source + parser contract/version produces the same ids and hash.

## Failure and uncertainty

Fail closed for:

- unknown `source_id`;
- missing source artifact;
- source artifact SHA-256 mismatch;
- invalid UTF-8 artifact;
- unsupported parser contract;
- invalid parser version;
- violated line-accounting invariant.

Represent bounded structural uncertainty rather than inventing structure:

- unclosed code fence -> `partial` + warning;
- heading-level jump -> warning with no synthetic headings.

## Phase 2 release gate

Issue #109 is complete only when deterministic tests prove hierarchy, line locations, repeated headings, code-fence isolation, simple lists, narrow tables, preamble/prose, source accounting, partial/warning behavior, source mismatch failure, deterministic rebuild equality, and live-state authority denial while the existing Roberta deterministic suite remains green.
