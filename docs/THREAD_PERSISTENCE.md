# Roberta Thread / Checkpoint Persistence

Phase 7A adds LangGraph thread-level execution persistence without introducing durable HXMP/HMPX memory.

## Authority boundary

- LangGraph checkpointers own current task/thread execution state.
- HXMP/HMPX durable long-term memory is a separate future layer.
- Checkpointed market snapshots are historical conversation context, not authoritative current market data.
- Current/fresh X1 market or risk requests must still go through X1 Scout -> CMIS -> X1 Provider.

## Graph construction

`build_graph(..., checkpointer=<backend>)` enables LangGraph checkpointing. Omitting the checkpointer preserves the existing stateless behavior.

For deterministic tests and local debugging, use LangGraph's `InMemorySaver`. It is not a production persistence backend and does not survive process restarts.

A production backend can be injected later without changing Roberta's graph authority boundaries.

## Invocation boundary

Use `roberta.runtime.invoke_thread(...)` rather than constructing LangGraph configurable metadata throughout application code.

Each persistence-enabled invocation requires an explicit non-empty `thread_id`. The same thread ID resumes saved state from the configured checkpoint backend; different thread IDs remain isolated.

## Restart / resume semantics

Restart/resume means a newly compiled Roberta graph can continue a thread when it is given the same checkpoint backend and the same thread ID. The deterministic Phase 7A tests prove this using one shared `InMemorySaver` object across two graph instances.

Durability across process or machine restarts requires a durable injected checkpointer and is intentionally not implemented in Phase 7A.

## Not durable memory

Thread checkpoints must not be used as a replacement for HXMP/HMPX. Phase 7B will define durable-memory contracts, relevance filtering, write policy, and fresh-data override behavior separately.
