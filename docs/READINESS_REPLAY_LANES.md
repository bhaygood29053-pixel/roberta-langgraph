# Controlled Degradation and Freshness Readiness Lanes

Tracking: issue #62

The configured live readiness lane proves that the real deployment path works. It cannot reliably prove every degraded state because providers may be healthy during evaluation. These controlled lanes make those behaviors reproducible while keeping the production model and normal Roberta graph in the loop.

## Lane B — degraded evidence replay

Run:

```bash
roberta-readiness-replay --skip-freshness
```

The production model receives normal Chain Scout results backed by a deterministic evaluation-only CMIS client. Profiles cover:

- stale evidence;
- source conflict;
- ambiguous asset identity;
- insufficient evidence;
- unavailable provider fields;
- provider error;
- null field semantics;
- verified zero semantics.

Each case requires the expected read-only CMIS service path and checks that the final answer surfaces the material degraded state instead of manufacturing a cleaner conclusion.

These fixture values are never live market authority. Generated reports are historical evaluation snapshots only.

## Lane C — checkpoint/HXMP freshness challenge

Run the default replay command:

```bash
roberta-readiness-replay
```

The graph is seeded with both:

- prior conversation containing an explicitly historical AGI snapshot; and
- an in-memory durable-memory record with `authority=historical_context`.

The user then asks for current X1 AGI market risk. The challenge passes only when the current turn produces new Scout/CMIS calls including `market_report` and `risk_check`. The historical snapshot cannot satisfy current truth by itself.

The in-memory adapter is used deliberately for repeatability. It exercises the same `DurableMemoryStore` contract that HXMP implements without requiring an external write or treating the fixture as durable production memory.

## Report

Default output:

```text
artifacts/readiness/replay-latest.json
```

The report separates degraded-case results from the freshness challenge and records any failed invariant as a deployment blocker.

## Combined issue #62 evidence

Issue #62 should be evaluated using both commands:

```bash
roberta-readiness
roberta-readiness-replay
```

The first command provides configured live-path, provider, latency, and production-model evidence. The second provides reproducible degraded-state and stale-memory evidence.

Neither command grants transaction construction, signing, broadcasting, custody, bridge transfer, autonomous execution, or value movement authority.
