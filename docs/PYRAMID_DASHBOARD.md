# Roberta Learning Command Center

Last reconciled: 2026-08-25 (America/New_York)

The Learning Command Center is a local **read-only** observability surface over Roberta's Pyramid training ledger, source-mastery plan, curriculum metadata, and Roberta bridge health.

It does not approve lessons, mutate Learning System state, modify the Pyramid ledger, call CMIS/providers for market truth, write HXMP, or trigger execution.

## Start the dashboard

```bash
roberta-pyramid-dashboard --db .roberta/pyramid_training.sqlite3
```

Default address:

```text
http://127.0.0.1:8770
```

Keep it loopback-only unless a separately accepted authenticated deployment contract exists.

## Current behavior

The dashboard uses real repository/local runtime data rather than placeholder progress.

It can display:

- current curriculum/source identity;
- source-specific mastery-stage count from the frozen source plan;
- mastered-through and current source stage;
- mapped global capability for a source stage;
- source chapters and page ranges contributing to the current stage;
- a `WHAT IS BEING LEARNED` description for each contributing chapter;
- current concepts/subconcepts and learning targets without exposing expected answers;
- canonical training history, accuracy, failures, and recent runs from SQLite;
- source-stage progress separately from global capability progress;
- Roberta bridge online/offline state based on the real `/healthz` response;
- explicit pending/unavailable telemetry when a data source is not implemented rather than fabricated metrics.

The JSON backing view is available at:

```text
GET /api/summary
```

The dashboard itself also exposes:

```text
GET /healthz
```

It polls summary state so the UI can reflect newly recorded training results without pretending that the dashboard initiated them.

## Source-adaptive Pyramid display

The dashboard no longer assumes every source requires 20 stages.

For a source-aware curriculum, the frozen `source_mastery_plan.json` is authoritative for the source-stage denominator and stage-to-capability mapping. The plan is validated through the same source-mastery contract used by the runner.

For *Mastering Blockchain, Fourth Edition*, the current frozen plan contains **14 required source stages** plus a required final source capstone.

A source-stage row can map to a non-contiguous global capability because source mastery and global capability mastery are separate measurements.

If source-plan state is unavailable or invalid, the dashboard must show that condition rather than silently inventing a 20-stage source requirement.

## Source Mastery panel

The Source Mastery panel identifies the actual source material being trained rather than only displaying a curriculum id.

Where validated metadata is available it may show:

```text
source title
source key
source stage / total source stages
mapped capability
source chapters
PDF/book page ranges
chapter learning summaries
concepts/subconcepts
learning targets
capstone-required/outstanding state
```

The panel deliberately does **not** expose exercise `expected_answer` fields as teaching content.

Bank construction and actual mastery are displayed as different concepts. The presence of a Stage 6 bank, for example, does not mean Stage 6 has been passed.

## Ledger and plan ownership

The dashboard opens the Pyramid database read-only. Training processes own writes through the accepted runner/ledger APIs.

The source-aware ledger records source-mastery runs/stage results while preserving historical fixed-level results. Historical Level 1/2 records are mapped into source-stage history rather than rewritten.

A bound source-plan hash cannot be changed by the dashboard.

## Roberta health

Roberta is shown online only when the configured Roberta bridge responds successfully to its health endpoint. Transport or dashboard availability must not be inferred from a static configuration value.

If Roberta is unavailable, the dashboard reports that state; it does not expose raw CMIS data as a substitute conversational response.

## Security and authority

The Learning Command Center must never be interpreted as:

- a verified-lesson retention store;
- RAG/source truth;
- current blockchain truth;
- CMIS/provider capability control;
- source approval authority;
- human lesson-retention approval;
- HXMP write authority;
- wallet/execution approval.

Fresh accepted CMIS/provider evidence remains authoritative for freshness-sensitive blockchain facts regardless of any score, learned concept, source chapter, or historical lesson shown in the dashboard.
