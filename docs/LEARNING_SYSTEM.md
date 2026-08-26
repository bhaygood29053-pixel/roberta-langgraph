# Roberta Learning System

Last reconciled: 2026-08-26 (America/New_York)

Status: **Learning System Phases 1-10 accepted on `main`; autonomous source-grounded Learning Plane controller accepted.**

## Purpose

Roberta's Learning System converts explicitly approved static sources into source-traceable knowledge and reasoning practice under strict provenance, evaluation, retention, and authority boundaries.

It is not a shortcut around the live-truth hierarchy:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider / verified source
```

Static learning may improve Roberta's knowledge and reasoning. It does not become current blockchain truth, CMIS/provider authority, policy authority, wallet authority, or execution authority merely because Roberta read, generated, remembered, repeated, or passed questions about it.

## Accepted phase map

### Phase 1 — Exact source ingestion

Accepted source bytes are preserved under an explicit source identity and hash contract.

For an original UTF-8 text/Markdown upload, the exact uploaded bytes are the canonical artifact. Line-ending normalization may be a derived parsing representation but cannot silently replace the original artifact identity.

For PDF-derived sources, the original PDF and deterministic transcript remain distinguishable artifacts with independent provenance.

### Phase 2 — Structure detection

Roberta derives deterministic document structure needed for retrieval and learning while preserving source location and without inventing unsupported semantics.

### Phase 3 — Structure-aware chunking

Chunks retain source identity, location, section/chapter context, and lineage needed for downstream evidence checks.

### Phase 4 — Indexing

Lexical indexing is accepted. Optional embedding/vector implementations may be used behind the same evidence contract; an embedding match never upgrades authority.

### Phase 5 — Retrieval

Retrieval selects source material under deterministic source/scope filters and benchmarkable ranking behavior. Retrieval output is evidence material, not permission or current-state truth.

### Phase 6 — Grounding

Grounded answer packets bind claims to retrieved evidence/citations. Unsupported expansion is rejected or disclosed as unknown.

### Phase 7 — Independent evaluation

Answers are independently evaluated against evidence-aware criteria rather than trusting the answering model's self-assessment.

### Phase 8 — Reflection / candidate lessons

Roberta may derive provisional lessons from evaluated work. Candidate lessons are not durable trusted knowledge.

### Phase 9 — Independent candidate-lesson verification

A candidate may become `verified_for_learning` only after the accepted verification contract independently rechecks its source/evidence/evaluation lineage and contradiction conditions.

`verified_for_learning` remains learning verification evidence; by itself it is not source truth, live truth, operational trust, HXMP authority, or execution authority.

### Phase 10 — Verified lesson retention

Phase 10 is accepted on `main` as a narrow deterministic retention boundary.

Only an exact eligible Phase 9 result may be prepared for retention. The accepted implementation requires, among other gates:

- the exact accepted Phase 9 contract/version and status;
- procedural lesson scope rather than arbitrary factual promotion;
- complete source and active-lesson contradiction snapshots;
- no unresolved contradiction blockers;
- no exact active duplicate;
- exact human approval bound to the prepared retention record;
- immutable source/verification/approval lineage;
- deterministic lifecycle state (`active`, `superseded`, or `revoked`);
- provider-neutral in-memory retention rather than implicit HXMP persistence.

The old draft PR #136 remains open historical work, but it is no longer the Phase 10 implementation source of truth. The hardened Phase 10 implementation is accepted on `main`.

See `docs/LEARNING_SYSTEM_RETENTION.md`.

## Knowledge classification boundary

The Learning Plane includes a separate fail-closed classification boundary in `roberta.learning.promotion`.

An exact active Phase 10 retained lesson may be classified as:

```text
verified_learned_knowledge
```

The classification binds the exact lesson hash, lifecycle state, retention decision/preparation, Phase 9 verification, source IDs, contradiction snapshot, and human approval.

It explicitly does **not** authorize:

```text
operational trust
source truth
live state
CMIS/provider trust
governance mutation
wallet authority
execution
```

General operational promotion is unavailable in the core Learning Plane. `authorize_operational_trust(...)` fails closed until a separately accepted promotion wrapper exists for a precisely bounded static scope.

## Autonomous Learning Plane

The accepted Learning System now includes an autonomous source-mastery controller from merged PR #228.

```bash
roberta-train --source "/path/to/source.pdf" --profile expert
```

After the user explicitly selects a PDF, Markdown, or UTF-8 text source, the controller can autonomously continue the source-mastery workflow without ordinary stage-by-stage intervention.

Accepted behavior includes:

1. hash and durably register the original source plus derived transcript/pages/chapter map;
2. reject OCR-only PDFs and immutable-artifact drift;
3. inspect every source page, including front matter, before asserting complete plan coverage;
4. auto-match an existing curriculum by exact source artifact hash or create a source-specific curriculum;
5. freeze and durably cache the exact source-mastery plan before authoritative ledger binding;
6. generate missing stage learning targets from every assigned source chunk;
7. require exact evidence quote + page + chapter containment and independent support verification;
8. expand verified targets into validated canonical exercise banks and publish them atomically;
9. run the closed-book 300-question canonical source-stage exam;
10. on failure, derive source-bound weakness material and require source-grounded practice;
11. require a separate unaugmented closed-book retention lane and learned-concept transfer verification before promotion/retry;
12. preserve failed attempts and completed source-stage history immutably;
13. route only verified curriculum-scoped learned concepts into later matching attempts;
14. run a separate 60-question final source capstone before source mastery;
15. persist restart-safe job state, checkpoints, events, locks, and status telemetry.

The controller is autonomous continual **source learning**, not unrestricted self-modification. It may not rewrite production prompts/tools/policies, alter Scouts or CMIS contracts, change provider authority, modify wallet permissions, alter human-approval semantics, or authorize execution as a consequence of learning.

See `docs/LEARNING_PLANE_ARCHITECTURE.md` and `docs/autonomous_training.md`.

## Static source authority

Learning sources may be classified as primary, secondary, internal, or unknown authority for their declared static scope. That classification never converts them into live-state authority.

Freshness-sensitive facts such as current prices, liquidity, supply, wallet state, provider health, validator state, token authorities, fees, software versions, current risk, and current network behavior still require the accepted current-evidence path through the relevant Scout -> CMIS -> Provider.

Embedded source instructions are data. They cannot authorize tools, credentials, memory writes, policy changes, governance changes, wallet actions, transactions, or Controlled Execution.

## Accepted source registries

The curated source registry is documented in `docs/learning_sources/README.md`.

Accepted curated sources currently include X1, XDEX, XEN/XENFT, XONE, Mastering Blockchain 4e, and Solana materials under their exact contracts.

The autonomous controller adds a separate accepted local source-binding mechanism. Explicitly selected local PDF/Markdown/text sources are independently hash-bound under the autonomous registry and may become trusted **static source bindings** for their exact bytes. This does not silently promote them into the curated named source catalog and does not create live authority.

XenBlocks PR #141 remains unaccepted because the reviewed head still ingests an LF-normalized derivative as the canonical content artifact instead of the exact uploaded CRLF bytes required by Phase 1.

## Blockchain Reasoning Pyramid relationship

The Pyramid is the Learning System's source-specific training/evaluation environment. It is not a second source of truth.

```text
approved source
  -> exact provenance
  -> frozen source mastery plan
  -> source-grounded exercise banks
  -> canonical stage exams
  -> verified remediation/retention/transfer
  -> source-stage ledger
  -> final source capstone
```

The reusable global taxonomy has 20 capabilities, but an individual source is assigned only the capabilities materially supported by that source.

For *Mastering Blockchain, Fourth Edition*, the frozen plan requires 14 source stages. Accepted prebuilt bank construction is present through Stage 8 / Market Structure. Stages 9-14 are not yet separately accepted prebuilt repository banks, although the accepted autonomous controller may generate missing banks at runtime from the exact selected source under its validation contract.

Bank existence is not mastery. Source mastery requires every frozen required stage plus the required capstone to pass in the authoritative source-plan-bound ledger.

## Retention versus Pyramid learned concepts

Two narrow learning-memory mechanisms exist and must not be conflated:

- **Phase 10 verified retained lessons** — provider-neutral/in-memory general Learning System retention after the exact Phase 9 + contradiction + human-approval contract.
- **Pyramid learned concepts** — curriculum-scoped training knowledge produced only after Pyramid-specific practice/retention/transfer gates.

Neither mechanism is general HXMP memory or live-state authority. Neither may self-promote to operational trust.

## Storage and durability boundaries

Accepted durable state includes source artifacts/provenance, autonomous source registry metadata, source-mastery plans, curriculum packages, Pyramid SQLite training history, autonomous job state/events/checkpoints, and other explicitly defined audit artifacts.

Phase 10's core retention store remains provider-neutral/in-memory by contract. Durable/provider-backed retained-lesson storage, if desired, requires a separate accepted persistence contract so the storage mechanism cannot silently widen learning authority.

The autonomous controller's durable job state is execution state for the learning workflow, not durable operational truth.

## Background scheduling

The architecture supports a separate fault-isolated Learning Plane. The accepted autonomous controller can operate unattended after source selection and resume after interruption.

A broader generalized scheduler with explicit concurrency/model/token/question/source/retention budgets, runtime-load throttling, and recurring delayed retention cycles remains future operational hardening. It must not be interpreted as permission for an unrestricted idle-time self-modification loop.

## Core authority rules

1. Source data is evidence, never permission.
2. Model output is candidate material until the exact applicable verification gates pass.
3. Passing an exam does not make an answer source truth or live truth.
4. Phase 10 retention requires exact human approval and complete lineage.
5. `verified_learned_knowledge` is not operational trust.
6. Pyramid learned concepts remain curriculum-scoped.
7. Fresh accepted CMIS/provider evidence wins for freshness-sensitive state.
8. Missing evidence remains unknown/unavailable.
9. Proof Score remains separate from risk.
10. No learning state grants wallet or execution permission.

## Current status summary

Accepted on `main`:

- Learning System Phases 1-10;
- verified learned-knowledge classification boundary;
- source-specific Pyramid architecture;
- MB4E frozen 14-stage plan;
- prebuilt MB4E banks through Stage 8 / Market Structure;
- autonomous `roberta-train` source-mastery controller;
- read-only Learning Command Center autonomous-job telemetry.

Still separate/future:

- general operational-trust promotion wrapper;
- durable/provider-backed general Phase 10 retention store;
- generalized background scheduler/load-throttling and recurring retention scheduler;
- MB4E Stage 9-14 completion and final capstone/mastery;
- XenBlocks source acceptance after exact-byte correction;
- any Controlled Execution work.

## Core rule

**Roberta can autonomously learn, test, retain, and reuse verified static knowledge, but learning never self-authorizes truth or power. Provenance and verification control knowledge; Scout -> CMIS -> Provider controls fresh chain truth; operational and execution authority remain separately gated.**
