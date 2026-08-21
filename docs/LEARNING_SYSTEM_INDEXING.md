# Learning System Indexing Contract

Status: Phase 4 first slice for Issue #115.

## Purpose

Phase 4 converts canonical Phase 3 `EvidenceChunk` records into replaceable lexical and embedding index representations. Indexes are derived relevance structures for later retrieval. They are not the source corpus, the concept model, a truth score, a risk score, or a current-state authority.

The first accepted index profile is deliberately backend-neutral:

```text
index_contract = evidence-index/v1
index_version = 1.0.0
lexical_analyzer_contract = unicode-word-casefold/v1
lexical_analyzer_version = 1.0.0
embedding = optional EmbeddingProvider
```

The broader Learning System specification recommends Python + PostgreSQL + PostgreSQL full-text search + pgvector as the early production baseline. This phase establishes the contracts and deterministic test path before adding that deployment coupling.

## Authority boundary

```text
Phase 1 SourceRecord / exact artifact
  -> Phase 2 canonical ParsedDocument
    -> Phase 3 canonical ChunkedDocument
      -> Phase 4 derived lexical / embedding index
```

Current freshness-sensitive market/blockchain truth remains:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

A lexical token, vector, vector fingerprint, index id, future similarity score, or future ranking score is relevance metadata only. It MUST NOT become source authority, CMIS verification, Proof Score, risk, current state, or execution authorization.

## Canonical-input rule

The index builder does not trust a caller-supplied `ChunkedDocument` as a provenance root.

Before indexing it MUST:

1. resolve the exact Phase 1 `SourceRecord` named by the chunk manifest;
2. recompute canonical Phase 2 structure from the retained source artifact using the declared parser contract/version;
3. recompute canonical Phase 3 chunks using the declared chunker contract/version/parameters;
4. require exact equality with the supplied `ChunkedDocument`;
5. fail closed on mismatch.

This keeps a caller-generated or tampered chunk set from becoming durable index provenance.

## Lexical analyzer

The v1 lexical analyzer is deterministic and intentionally simple:

1. normalize chunk text with Unicode NFKC;
2. apply Unicode `casefold()`;
3. extract contiguous Unicode word characters while excluding underscore as a token character;
4. preserve token order.

The analyzer does not stem, infer synonyms, infer concepts, or judge meaning. Its behavior is versioned so a future PostgreSQL analyzer, language-aware stemmer, or other lexical implementation can be benchmarked and introduced without silently changing prior identities.

## LexicalIndexEntry

Each lexical entry preserves at least:

```text
lexical_entry_id
chunk_id
source_id
document_id
section_id
structural_path
chunk_kind
line_start
line_end
source_authority_class
source_approval_status
chunk_content_hash
index_contract
index_version
lexical_analyzer_contract
lexical_analyzer_version
tokens
token_count
unique_term_count
live_state_authorized = false
```

The entry id is content-addressed from canonical chunk identity/content plus index/analyzer contract metadata and the exact normalized token sequence.

## EmbeddingProvider

Embedding generation is optional. Phase 4 defines a typed provider seam rather than selecting a production model.

A provider exposes deterministic metadata through `EmbeddingProviderInfo`:

```text
provider_id
model_id
model_version
dimension
```

Each request binds:

```text
chunk_id
content_hash
text
```

Each result must echo the exact chunk/content identity and declare one of:

```text
ok
error
unavailable
```

An `ok` result MUST contain exactly the provider-declared vector dimension and every element MUST be a finite numeric value. `error` or `unavailable` results MUST NOT carry a vector. Malformed provider contract output fails closed.

Provider runtime exceptions are represented as explicit failed embedding entries so a lexical index can still be produced without fabricating a vector.

## DeterministicHashEmbeddingProvider

The first slice includes a deterministic hash-based embedding provider solely as a test/index-contract adapter. It is deliberately named as a test provider and is NOT a semantic embedding model.

Its purpose is to prove:

- exact request binding;
- provider/model/version metadata preservation;
- vector-dimension validation;
- vector fingerprinting;
- stable derived identities;
- partial-state behavior.

It MUST NOT be used as evidence that semantic retrieval quality is acceptable.

## EmbeddingIndexEntry

One embedding entry is emitted for every chunk when an embedding provider is configured.

Successful entries preserve:

```text
embedding_entry_id
chunk_id
source/document/section metadata
structural_path
chunk_kind
chunk_content_hash
provider_id
model_id
model_version
dimension
status = ok
vector
vector_fingerprint
warnings
error = null
live_state_authorized = false
```

Failed/unavailable entries preserve the same provenance/provider metadata but contain:

```text
status = error | unavailable
vector = null
vector_fingerprint = null
warnings
error
```

No fallback vector is synthesized.

`vector_fingerprint` is SHA-256 over canonical JSON for the validated Python-float vector. It is a reproducibility fingerprint for the derived representation, not a source-content hash and not truth evidence.

## IndexManifest

The manifest preserves:

```text
index_id
index_hash
source_id
document_id
chunk_set_id
index_contract
index_version
lexical_analyzer_contract
lexical_analyzer_version
lexical_entry_ids
embedding_provider_id
embedding_model_id
embedding_model_version
embedding_dimension
embedding_entry_ids
embedding_ok_count
embedding_error_count
embedding_unavailable_count
status
warnings
errors
live_state_authorized = false
```

Accepted overall statuses:

```text
lexical_only  # no embedding provider requested
complete      # provider configured and every embedding result is ok
partial       # provider configured and at least one result is error/unavailable
```

The manifest hash binds canonical source/chunk-set identity, index/analyzer configuration, provider metadata when present, and ordered entry ids/status diagnostics.

## Failure policy

Fail closed for structural contract violations, including:

- non-canonical/tampered `ChunkedDocument`;
- unsupported index or lexical-analyzer contract;
- invalid index/analyzer/provider version metadata;
- invalid provider dimension;
- non-`EmbeddingResult` provider output;
- provider result identity mismatch;
- `ok` result without a vector;
- wrong vector dimension;
- boolean, non-numeric, NaN, or infinite vector element;
- failed/unavailable result that nevertheless contains a vector.

Represent operational embedding failure without invention:

- provider exception -> per-chunk `error` entry + manifest `partial`;
- provider-declared `error` -> per-chunk `error` entry + manifest `partial`;
- provider-declared `unavailable` -> per-chunk `unavailable` entry + manifest `partial`.

## Explicit non-goals

Phase 4 does not add:

- PostgreSQL schema/migrations;
- pgvector deployment;
- production embedding credentials or model selection;
- lexical search APIs;
- vector-nearest-neighbor search APIs;
- hybrid retrieval/candidate fusion;
- ranking or reranking;
- concept extraction/knowledge graph;
- grounded answer generation;
- question generation/evaluation/curriculum;
- reflection, candidate lessons, or verified lessons;
- fine-tuning;
- CMIS/provider truth changes;
- wallet or transaction execution authority.

## Release gate

Issue #115 is complete only after deterministic tests prove canonical Phase 3 revalidation, explicit Unicode lexical behavior, exact provenance/filter metadata, stable lexical/index identities, lexical-only mode, deterministic embedding test-provider behavior, provider/model/version/dimension preservation, malformed-provider failure, explicit provider-runtime partial state, derived-identity changes when index/provider configuration changes, exact chunk mapping, and live-state authority denial while the existing deterministic Roberta suite remains green.