# Learning System Retrieval Contract

Status: Phase 5 first slice for Issue #118.

## Purpose

Phase 5 retrieves exact evidence chunks from validated Phase 4 indexes. Retrieval is a relevance mechanism only. It does not determine truth, source authority, market risk, freshness, policy, or execution authorization.

The first accepted profile is backend-neutral and deterministic:

```text
retrieval_contract = evidence-retrieval/v1
retrieval_version = 1.0.0
fusion_contract = reciprocal-rank-fusion/v1
rrf_k = 60
```

The intended early production storage baseline remains PostgreSQL full-text search + pgvector after this retrieval contract and its benchmark obligations are proven.

## Authority boundary

```text
Phase 1 SourceRecord / exact artifact
  -> Phase 2 canonical ParsedDocument
    -> Phase 3 canonical ChunkedDocument
      -> Phase 4 validated IndexedDocument
        -> Phase 5 RetrievalResult
```

Changing market/blockchain state remains outside the Learning System authority path:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

A token match, vector similarity, fused rank, benchmark score, or retrieval result is relevance evidence only.

## Canonical index integrity

Before retrieval, every `RetrievalCorpusItem` must bind one canonical Phase 3 `ChunkedDocument` to one Phase 4 `IndexedDocument`.

The retrieval layer:

1. invokes Phase 4 index rebuilding over the supplied chunk set, which in turn revalidates the Phase 1 artifact and canonical Phase 2/3 structure;
2. requires exact equality with the canonical lexical entries for the declared index/analyzer versions;
3. validates embedding-entry provenance against canonical chunks;
4. validates embedding provider/model/version/dimension metadata;
5. validates finite vectors, vector fingerprints, entry ids, counts, status, warnings/errors, and manifest hash/id;
6. rejects inconsistent or tampered input.

Phase 5 does not re-contact a production embedding provider. It validates the accepted stored derived representation; provider authenticity remains an indexing/storage-system responsibility rather than something retrieval invents.

## Corpus semantics

V1 accepts one or more `RetrievalCorpusItem` values.

- corpus order is normalized by `index_id` and does not affect retrieval identity;
- duplicate index ids fail closed;
- duplicate canonical chunk ids across corpus items fail closed to prevent score inflation;
- all corpus indexes must use one lexical-analyzer contract/version in v1;
- contradictory or disagreeing sources remain separate evidence candidates and are never reconciled by retrieval.

## Query contract

A retrieval query preserves:

```text
query_id
exact query text
normalized lexical tokens
filters
top_k
candidate_limit
retrieval contract/version
fusion contract / rrf_k
lexical analyzer contract/version
optional QueryVector metadata/fingerprint
live_state_authorized = false
```

Query text must contain non-whitespace text. The exact text is preserved; lexical normalization derives a separate token sequence.

If lexical normalization produces no tokens, retrieval requires an explicit valid query vector. It does not invent query terms.

## Lexical normalization

V1 matches the Phase 4 `unicode-word-casefold/v1` analyzer:

1. Unicode NFKC normalization;
2. Unicode `casefold()`;
3. contiguous Unicode word characters, excluding underscore;
4. token order preserved.

No stemming, synonym inference, concept expansion, or model-generated query rewriting is performed.

## Filters

`RetrievalFilters` supports exact-match constraints for:

```text
source_ids
document_ids
section_ids         # may explicitly contain null for preamble scope
source_authority_classes
source_approval_statuses
chunk_kinds
```

Filter dimensions are set-like: supplied values are normalized, deduplicated, and ordered deterministically. An empty dimension means unrestricted. A supplied dimension is never silently widened.

## Lexical candidate channel

A lexical candidate must match at least one distinct normalized query term.

For each eligible chunk, Phase 5 records:

- matched distinct terms;
- matched-term count;
- total matched occurrences;
- whether the full normalized query token sequence appears contiguously;
- lexical rank.

V1 ranks deterministically by:

1. phrase match;
2. matched distinct-term count;
3. matched occurrences;
4. shorter indexed token count;
5. stable `chunk_id` tie-break.

These values are relevance metadata, not evidence quality or truth.

## Optional vector channel

`QueryVector` binds an exact embedding space:

```text
provider_id
model_id
model_version
dimension
vector
vector_fingerprint
```

The vector must contain exactly the declared number of finite numeric values and have non-zero magnitude.

An index is vector-eligible only when its Phase 4 provider/model/version/dimension metadata exactly matches the query vector. Vector spaces are never mixed or compared by assumption.

For eligible `ok` embedding entries, Phase 5 computes cosine similarity and preserves the raw similarity + channel rank. Zero-magnitude stored vectors cannot produce a cosine candidate and are surfaced as diagnostics.

A mismatched or unavailable vector channel does not fabricate vectors. Lexical retrieval may still proceed with explicit `partial` status.

The Phase 4 deterministic hash embedding adapter may be used only to test vector-channel mechanics. It is not a semantic embedding model and does not establish paraphrase quality.

## Deterministic fusion

V1 uses Reciprocal Rank Fusion over channel ranks:

```text
score = sum(1 / (rrf_k + channel_rank))
```

Fusion is computed using exact rational arithmetic. Candidate output preserves numerator/denominator rather than hiding fusion behind an opaque floating score.

Fusion never incorporates source authority, approval state, risk, truth, or freshness.

## Diversity pass

After fusion, Phase 5 performs a deterministic local-context diversity pass.

Two chunks are local neighbors only when they share exact source, document, and section identities and their canonical chunk orders differ by at most one.

Selection behavior:

1. first pass chooses fused candidates while deferring a local neighbor of already-selected evidence;
2. independent/cross-source candidates can therefore enter the result before adjacent fragments dominate it;
3. second pass backfills deferred candidates if needed to reach `top_k`;
4. all first-pass deferred chunk ids remain visible in `diversity_deferred_chunk_ids`.

This is diversity handling, not contradiction resolution. Cross-source disagreement is preserved.

## Retrieval result

Every selected candidate preserves exact canonical evidence and provenance:

```text
chunk/source/document/section/block identities
structural path + chunk kind/order
line range
exact chunk text + content hash
source authority / approval metadata
lexical diagnostics
optional vector diagnostics
fusion rank + exact rational score
live_state_authorized = false
```

The result also preserves:

```text
retrieval_id / retrieval_hash
query
corpus index ids
vector eligible/ineligible index ids
diversity deferred ids
status
warnings/errors
```

Statuses:

```text
ok        # candidates returned with every requested usable channel in accepted state
partial   # candidates returned but a requested vector channel is mismatched/partial/degraded
no_match  # no candidate matched the explicit query/filter/channel constraints
```

A `no_match` result contains no fabricated evidence.

The retrieval hash binds query/configuration, corpus index identities, ordered selected chunk identities/ranks, diversity metadata, channel eligibility, and diagnostics. Raw floating vector similarity is not promoted into source identity or truth.

## Golden benchmark surface

`evaluate_retrieval()` computes first-slice deterministic metrics for a caller-declared set of relevant canonical chunk ids:

- Recall@K;
- Precision@K;
- reciprocal rank (the per-case building block for MRR);
- binary nDCG@K;
- evidence coverage (currently equal to Recall@K for binary chunk relevance);
- local-context redundancy rate;
- source diversity ratio;
- filter correctness;
- retrieved/relevant/hit counts.

For a negative case with zero declared relevant chunks, relevance-denominator metrics are `None` rather than manufactured zeros. The retrieval result itself is expected to express `no_match` when appropriate.

The deterministic regression corpus covers exact-term retrieval, Unicode normalization, exact filters, no-match behavior, cross-source disagreement visibility, corpus-order stability, diversity deferral, index tampering, vector-space matching/mismatch, malformed query vectors, duplicate-corpus defense, benchmark metrics, and live-state authority denial.

Paraphrase/semantic benchmark claims are deferred until an actual accepted semantic embedding provider exists.

## Explicit non-goals

Phase 5 does not add:

- PostgreSQL schema/migrations;
- pgvector deployment;
- production embedding credentials or model selection;
- model reranking;
- model-generated query expansion;
- grounded answer generation;
- concepts/knowledge graph;
- question generation or adaptive curriculum;
- reflection, candidate lessons, or verified lessons;
- fine-tuning;
- CMIS/provider truth changes;
- wallet or transaction execution authority.

## Release gate

Issue #118 is complete only when deterministic tests prove canonical index validation, exact filter semantics, lexical transparency, optional vector-space safety, deterministic fusion, local-context diversity, explicit no-match/partial behavior, exact evidence provenance, benchmark metrics, and live-state authority denial while the existing deterministic Roberta suite remains green.
