# Learning System Evidence Chunk Contract

Status: Phase 3 first slice for Issue #112.

## Purpose

Phase 3 converts canonical Phase 2 structural blocks into deterministic, source-located `EvidenceChunk` records. Chunks are evidence units for later indexing/retrieval work; they are not embeddings, concepts, summaries, learned truths, or live observations.

The first accepted chunker profile is:

```text
chunker_contract = structure-aware-chunk/v1
chunker_version = 1.0.0
max_chars = explicit positive integer; implementation default 1600
overlap_lines = 0
```

The default `max_chars` is an initial implementation baseline, not a universal quality threshold. Later retrieval evaluation may justify a different versioned value.

## Authority boundary

```text
Phase 1 SourceRecord / immutable artifact
  -> Phase 2 canonical ParsedDocument
    -> Phase 3 deterministic EvidenceChunk records
```

Learning System chunks are static source-derived evidence. They never authorize current market/blockchain state. Current freshness-sensitive facts remain on the existing authority path:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

## Canonical-input rule

The chunker does not trust a supplied `ParsedDocument` as a truth root.

Before chunking it MUST:

1. resolve the exact Phase 1 `SourceRecord` from the supplied document source id;
2. retrieve and SHA-256 verify the exact retained artifact;
3. recompute Phase 2 structure using the supplied document parser contract/version;
4. require the recomputed `ParsedDocument` to equal the supplied structure exactly;
5. fail closed on any mismatch.

This prevents caller-authored/tampered structure from silently becoming durable chunk provenance.

## EvidenceChunk

Each chunk records:

```text
chunk_id
source_id
document_id
section_id
block_ids
structural_path
kind
order
line_start
line_end
text
content_hash
source_authority_class
source_approval_status
parser_contract
parser_version
chunker_contract
chunker_version
max_chars
overlap_lines
status
warnings
fragment_index
fragment_count
previous_chunk_id
next_chunk_id
live_state_authorized = false
```

Accepted `kind` values in v1:

```text
prose
code_fence
list
table
```

Accepted `status` values in v1:

```text
normal
oversize_line
oversize_atomic
```

`prose` is a structural grouping label only. It does not claim subject/topic/meaning.

## Exact source text

Chunk text is reconstructed from the retained Phase 1 source artifact using inclusive 1-based source line ranges.

For grouped prose, the exact source span from the first contributing block line through the last contributing block line is retained, including blank separators and original line endings.

For atomic blocks and fragments, exact original source text is preserved. `content_hash` is SHA-256 over the UTF-8 bytes of the exact chunk text.

## Natural-boundary rules

### Atomic structures

These Phase 2 block kinds remain atomic:

- `code_fence`
- `list`
- `table`

They are never merged with prose or each other in v1.

If an atomic block exceeds `max_chars`, preserve it intact:

```text
status = oversize_atomic
warning = oversize_atomic:block=<block_id>:max_chars=<n>:observed_chars=<n>
```

No truncation is permitted.

### Prose grouping

`preamble` and `paragraph` blocks map to chunk kind `prose`.

Consecutive prose blocks may be grouped only when:

- they are adjacent in Phase 2 block order;
- they have the same `section_id`;
- the exact source span including intervening blank lines is `<= max_chars`.

A prose group never crosses a section boundary. Preamble (`section_id = null`) remains separate from headed sections.

### Oversize prose

If one prose block exceeds `max_chars`, it is split only at source-line boundaries.

The splitter greedily preserves whole source lines while keeping a fragment at or under `max_chars` whenever possible.

A single source line longer than `max_chars` is preserved intact:

```text
status = oversize_line
warning = oversize_line:line=<line>:max_chars=<n>:observed_chars=<n>
```

The line is never truncated or split merely to meet the limit.

Every fragment preserves the contributing `block_id` and records deterministic `fragment_index` and `fragment_count`.

## No overlap in v1

`overlap_lines` MUST equal zero. Any nonzero value fails closed.

Overlap may be added only in a future version after retrieval evaluation demonstrates a measurable benefit. Phase 3 does not duplicate evidence preemptively.

## Source-block coverage invariant

Every source line belonging to every Phase 2 structural block MUST be covered exactly once by chunks that cite that block id.

The chunker validates this invariant after candidate construction. Missing or duplicate coverage fails closed.

Blank source lines between grouped prose blocks may appear inside the exact grouped chunk span even though those blank lines were not separate Phase 2 blocks.

## Context linkage

Chunk ids are computed first from each chunk's own deterministic provenance/content material. Final records then expose:

```text
previous_chunk_id
next_chunk_id
```

The first previous id and final next id are `null`.

Neighbor linkage is contextual metadata; it is not part of the chunk's own content-addressed identity.

## Deterministic identity

Canonical JSON uses sorted keys, compact separators, UTF-8, and no NaN.

`chunk_id` uses:

```text
chk_<64 lowercase hex>
```

It binds:

- source/document/section identity;
- contributing block ids;
- structural path;
- kind and deterministic order;
- source line range;
- exact content hash;
- parser contract/version;
- chunker contract/version;
- `max_chars` and `overlap_lines`;
- fragment index/count.

The chunk manifest exposes:

```text
chunk_set_id = cset_<64 hex>
chunking_hash = <64 hex>
```

The manifest hash covers the full ordered final chunk records, parameters, source/document identity, and warnings. Same accepted inputs and parameters reproduce exactly the same output.

## Explicit non-goals

Phase 3 does not add:

- embeddings or embedding-model selection;
- pgvector/vector search;
- lexical indexing/search;
- retrieval or reranking;
- concepts or knowledge graphs;
- summaries or generated claims;
- questions/answers/evaluation/curriculum;
- reflection, candidate lessons, or verified lessons;
- fine-tuning;
- additional learning agents;
- any CMIS/provider truth or execution authority.

## Release gate

Issue #112 is complete only after deterministic tests prove exact grouped source text, section isolation, atomic blocks, oversize behavior, zero overlap, canonical-input verification, complete/nonduplicated block coverage, deterministic rebuild identity, previous/next linkage, parameter/version identity behavior, and live-state authority denial while the existing full deterministic Roberta suite remains green.
