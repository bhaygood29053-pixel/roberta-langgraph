# Durable Memory Boundary

Phase 7B separates Roberta's durable long-term memory from LangGraph thread/checkpoint state.

## Authority model

```text
LangGraph checkpointer
  -> current thread/task execution state

DurableMemoryStore (future HXMP/HMPX adapter)
  -> stable long-term context

CMIS/provider evidence
  -> freshness-sensitive current market/tokenomics/risk facts
```

Fresh verified CMIS/provider evidence always overrides remembered or conversational live-data snapshots when current information is required.

## Provider-neutral contract

`roberta.memory.DurableMemoryStore` defines the minimum adapter surface:

- `get(key)` for exact stable-key lookup
- `upsert(record)` for deterministic writes after policy approval
- `search(query, limit=...)` for provider candidate retrieval

The Oracle applies a deterministic relevance filter to provider candidates before injecting context. This keeps the memory-provider search implementation replaceable while preserving Roberta's own relevance boundary.

Memory records and candidates fail closed on unknown categories, empty keys/content/source, invalid authorities, or malformed topic tuples.

## Durable categories

The standard write path accepts only stable categories:

- `identity_role`
- `user_risk_policy`
- `stable_preference`
- `service_definition`
- `specialist_capability`
- `approval_rule`
- `long_term_goal`
- `decision`

Freshness-sensitive categories are rejected from permanent-memory truth:

- `market_snapshot`
- `wallet_snapshot`
- `risk_snapshot`
- `tokenomics_snapshot`

A migration/import adapter may still surface an older snapshot as a `MemoryRecord` with `authority="historical_context"`. The Oracle context formatter labels such records explicitly as non-authoritative history. Standard `write_durable_memory()` does not create them.

## Write path

```text
MemoryCandidate
  -> deterministic classify_memory_candidate()
  -> allowed stable category?
       yes -> MemoryRecord(authority="durable") -> store.upsert()
       no  -> reject without mutating the store
```

Stable keys are supplied by the caller/application boundary. Updating the same key preserves the original `created_at` and advances `updated_at`.

This milestone does not let an LLM invent or self-authorize durable writes. Future automatic extraction must preserve this deterministic category/write boundary rather than bypass it.

## Retrieval path

```text
latest user request
  -> store.search(...)
  -> deterministic lexical relevance filter
  -> bounded relevant records
  -> guarded JSON Lines context
  -> Oracle system context
```

Irrelevant records are omitted. Memory-provider failures degrade to no injected memory rather than aborting Roberta or fabricating fallback context.

## Prompt-safety boundary

Retrieved records are serialized as JSON objects beneath an explicit data-only system preface. The preface states that Roberta must not follow instructions, tool requests, URLs, approval changes, or policy changes embedded inside memory record fields.

The same memory message also states that:

- `historical_context` does not establish current facts
- current/latest/fresh requests still require newly verified specialist/CMIS/provider evidence
- memory is context/data, not a new instruction layer

This is a prompt-layer guardrail in addition to deterministic write/retrieval policy; it does not replace normal model/tool safety controls.

## Deterministic test adapter

`InMemoryDurableMemoryStore` implements the same provider-neutral contract for unit tests and local development. It is not the final HXMP/HMPX backend.

The real HXMP/HMPX binding should be added only after these contracts are stable and its concrete client/API semantics are available. The adapter must preserve exact `MemoryRecord` authority, category, stable key, timestamps, provenance, topics, and rationale fields rather than weakening the policy boundary.
