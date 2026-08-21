# Roberta Learning System

Status: Phase 1 source-ingestion foundation for Issue #106.

## Purpose

The Roberta Learning System extends Roberta with evidence-grounded learning while preserving existing authority boundaries. The first implementation slice is deliberately narrow: reproducible ingestion and preservation of one approved technical source.

This phase does **not** implement embeddings, vector search, retrieval, reranking, concepts, question generation, reflection, lesson promotion, fine-tuning, or additional learning agents.

## Authority boundary

Roberta remains the reasoning and orchestration authority. Learning-system persistence is external/system-of-record state behind typed interfaces. Model context is never the authoritative source store.

The existing live-data hierarchy remains unchanged:

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Learning-system source records are static source knowledge. They are not authoritative for current market, blockchain, wallet, software-service, or other freshness-sensitive state. Current facts still require the normal authorized live-tool path.

## Phase 1 ingestion contract

An accepted ingestion produces a `SourceRecord` containing:

```text
source_id
origin
title
version
content_hash
authority_class
approval_status
ingested_at
parser_version
artifact_ref
status
metadata
```

### Identity

`content_hash` is lowercase SHA-256 over the exact original UTF-8 bytes.

`source_id` is content-addressed from canonical JSON containing the stable source identity material:

```text
origin
title
version
content_hash
```

Canonical JSON uses sorted keys, compact separators, UTF-8, and no NaN values. The identifier format is:

```text
src_<64 lowercase hex>
```

Identical input therefore produces the same source identity. Changed content produces a different content hash and source identity rather than overwriting the prior source record.

### Original artifact preservation

The storage adapter persists the exact original bytes and returns an `artifact_ref`. The source record is stored separately from the artifact bytes.

The ingestion path does not accept generated summaries, chunks, concepts, reflections, lessons, or model-authored transformations as substitutes for the original artifact.

### Allowed states

Accepted authority classes:

```text
primary
secondary
internal
unknown
```

Accepted approval states:

```text
approved
pending_review
rejected
quarantined
```

Accepted source statuses:

```text
approved
pending_review
rejected
quarantined
superseded
```

Inputs outside these enumerations fail closed.

### Metadata

Metadata must be a JSON-compatible mapping with string keys. It is canonicalized on write. Non-JSON values, non-string keys, NaN, and infinite values are rejected.

### Idempotency and immutability

Re-ingesting the same canonical source returns the existing `SourceRecord` and does not duplicate or mutate the stored artifact.

A `SourceStore` implementation must reject conflicting writes for an existing `source_id` or `artifact_ref` rather than silently overwrite accepted state.

## Provider-neutral storage interface

Phase 1 defines a minimal replaceable `SourceStore` contract:

```text
get_source(source_id)
put_source(record)
get_artifact(artifact_ref)
put_artifact(artifact_ref, content)
```

`InMemorySourceStore` is the deterministic unit-test/local-development adapter. It is not the production persistence backend. A future PostgreSQL/object-storage adapter must preserve the same identity, immutability, provenance, and failure semantics.

## Observability

Ingestion returns an explicit `IngestionResult` with:

```text
status = ingested | existing
record
```

Malformed or conflicting input raises an explicit deterministic error. No hidden model reasoning is required to reconstruct an ingestion decision.

## Phase 1 release gate

Issue #106 is complete only when:

- one approved UTF-8 source ingests reproducibly;
- exact original bytes are retained;
- deterministic source/content identity is tested;
- duplicate ingestion is idempotent;
- changed content preserves the prior record and creates a distinct record;
- malformed inputs fail closed;
- existing Roberta deterministic tests remain green;
- no live-state or execution authority is widened.

## Next phase

After this gate passes, Phase 2 may add structure detection and document hierarchy while preserving the Phase 1 source/artifact identities unchanged.
