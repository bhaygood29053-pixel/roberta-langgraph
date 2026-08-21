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

## Provenance reconciliation

Issue #99 adds a provider-neutral deterministic seam for comparing remembered/historical context with a candidate observation without turning memory into a second market-data authority.

`reconcile_memory_observations()` produces only one bounded provenance label:

- `superseded` — accepted evidence confirms the same semantic value at the same or a later observation time, so the remembered context is no longer the usable evidence source;
- `evolution` — newer accepted evidence differs at a later observation time, so both observations may be historically valid because state changed;
- `conflict` — materially comparable observations disagree at the same observation time;
- `unknown` — evidence is insufficient to reconcile safely, including missing/ambiguous timestamps, missing chain/evidence scope, incompatible semantic/category/chain/scope, unaccepted candidate evidence, or reversed ordering.

`unknown` is the explicit insufficient-evidence state; missing fields are never converted into zero, false, or a guessed reconciliation label.

The reconciliation result can set `requires_fresh_verification=True`. This lets historical memory inform verification strategy, especially for conflicts or insufficient evidence, without promoting HXMP/checkpoint/conversation state into current truth.

The seam is deliberately authority-free:

- it does not mutate HXMP or durable memory;
- it does not manufacture or recompute CMIS facts, risk, Evidence Receipts, or Proof Scores;
- it never grants `current_truth_authorized` or `execution_authorized`;
- both observations must carry explicit chain and evidence scope before a deterministic reconciliation label other than `unknown` is possible;
- X1 and Solana observations with different chain scope remain isolated;
- only explicitly accepted candidate evidence can resolve a historical comparison;
- current/latest answers still require the normal `User -> Roberta -> Chain Scout -> CMIS -> provider` authority path.

HXMP approval, preview-hash, wallet, lane, signer, readback, secret-safety, and capacity controls are unchanged.

## Decision-record discipline

Hard-to-reverse, trade-off-driven architectural decisions belong in an authoritative GitHub ADR/design record. Durable memory may retain only compact decision context or a reference when useful and when the normal durable-memory policy allows the write.

A compact durable-memory decision reference may include a stable key, short decision summary, repository issue/PR/ADR reference, and bounded rationale. It must not duplicate a long ADR/design document into HXMP, and it does not replace or supersede the repository design record.

Remembered decision context is still context rather than live evidence. It cannot override fresh accepted CMIS/provider evidence or create new execution, approval, market-fact, risk, or Proof Score authority.

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
