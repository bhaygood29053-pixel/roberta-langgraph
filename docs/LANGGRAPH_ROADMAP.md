# Roberta LangGraph Roadmap

Last reconciled: 2026-08-23 (America/New_York)

This file is the authoritative living roadmap for Roberta. Detailed phase contracts remain in their dedicated documents; this roadmap records accepted state, active gates, blocked work, and the next allowed sequence without turning open PRs into accepted behavior.

## Canonical architecture

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Roberta owns orchestration, user policy, specialist selection, cross-chain coordination, human-review boundaries, learning-workflow coordination, and final synthesis.

Chain Scouts own chain-specific planning and interpretation while preserving CMIS facts, evidence, limitations, and capability states.

CMIS owns deterministic freshness-sensitive facts, Evidence Receipts, Proof Scores, risk, capability eligibility, historical intelligence, and bounded analysis-only pre-trade calculations.

Providers remain beneath CMIS.

Fresh accepted CMIS/provider evidence overrides remembered, checkpointed, book/RAG, Pyramid, or Learning System material for freshness-sensitive state. Missing evidence remains unknown/unavailable and is never converted into zero or a model estimate. Risk remains separate from Proof Score.

## Current position

### Core Roberta platform

Accepted/completed:

- Phase 1 — Core Agent Loop;
- Phase 2 — Provider-Neutral Model Loop;
- Phase 3 — X1 Scout Boundary;
- Phase 4 — CMIS / X1 Provider Integration;
- Phase 5 — X1 Evidence Completeness as a deliberately bounded/fail-closed capability boundary;
- Phase 6 — Agentic X1 Scout Planning;
- Phase 7A — Thread / Checkpoint Persistence;
- Phase 7B — HXMP Durable Memory;
- Phase 8 — Oracle Policy;
- Phase 9 — Human in the Loop;
- Phase 10 — More Specialists / Providers;
- Post-Phase-10 Evidence-Aware Intelligence & User Experience;
- X1 decision-production readiness;
- Solana read-only production readiness for the currently promoted Scout surface;
- adoption/readiness of CMIS `concentration_change_intelligence/v1` through X1 Scout.

Roberta Phase 11 — Controlled Execution remains **LOCKED / NOT STARTED**.

CMIS and Roberta phase numbering are independent. CMIS Phase 11/12 read-only intelligence work does not imply Roberta Controlled Execution.

## Learning System roadmap

The Learning System is built as a deterministic evidence pipeline, not as a shortcut around source provenance or CMIS live truth.

```text
approved source bytes
  -> structure
  -> evidence chunks
  -> index
  -> retrieval
  -> evidence packet / citations
  -> answer evaluation
  -> provisional reflection / candidate lesson
  -> independent candidate verification
  -> separately gated retention
```

### Phase 1 — Source ingestion ✅ Complete

Accepted contract: exact UTF-8 artifact preservation, deterministic SHA-256/content identity, immutable `SourceRecord`, idempotent re-ingestion, provider-neutral `SourceStore`, fail-closed malformed/conflicting input, and no live-state authority.

See [`LEARNING_SYSTEM.md`](./LEARNING_SYSTEM.md).

### Phase 2 — Structure detection ✅ Complete

Accepted deterministic structure-first Markdown parsing preserves source hierarchy, exact source locations/text, block types, structural warnings, and content-addressed identities without inventing headings or source meaning.

See [`LEARNING_SYSTEM_STRUCTURE.md`](./LEARNING_SYSTEM_STRUCTURE.md).

### Phase 3 — Structure-aware evidence chunking ✅ Complete

Accepted chunking revalidates Phase 1/2 state, preserves source/document/section/block provenance, prevents silent truncation, uses explicit zero-overlap v1 semantics, and content-addresses chunks/manifests.

See [`LEARNING_SYSTEM_CHUNKING.md`](./LEARNING_SYSTEM_CHUNKING.md).

### Phase 4 — Indexing foundation ✅ Complete

Accepted lexical indexing uses deterministic Unicode normalization/tokenization. Optional embeddings remain behind a typed provider seam with exact model/version/dimension/request validation and no semantic-quality assumption from the test adapter.

See [`LEARNING_SYSTEM_INDEXING.md`](./LEARNING_SYSTEM_INDEXING.md).

### Phase 5 — Retrieval + benchmark foundation ✅ Complete

Accepted retrieval revalidates canonical corpus/index state, preserves exact filters/provenance, keeps lexical/vector channels observable, uses deterministic Reciprocal Rank Fusion, exposes explicit partial/no-match states, and provides deterministic benchmark helpers.

See [`LEARNING_SYSTEM_RETRIEVAL.md`](./LEARNING_SYSTEM_RETRIEVAL.md).

### Phase 6 — Grounded answer + citation foundation ✅ Complete

Accepted grounding reconstructs exact retrieval state, builds deterministic evidence anchors/packets, treats retrieved source text as untrusted evidence data, fails closed on fabricated citations, and keeps structural citation validity separate from semantic entailment.

See [`LEARNING_SYSTEM_GROUNDING.md`](./LEARNING_SYSTEM_GROUNDING.md).

### Phase 7 — Independent answer evaluation ✅ Complete

Accepted evaluation reconstructs Phase 6 state, uses content-addressed approved golden cases, keeps retrieval failures separate from answer failures, preserves per-dimension evaluation, and refuses to fabricate semantic-groundedness/calibration signals that lack an accepted evaluator.

See [`LEARNING_SYSTEM_EVALUATION.md`](./LEARNING_SYSTEM_EVALUATION.md).

### Phase 8 — Provisional reflection + candidate lesson ✅ Complete

Accepted reflection/candidate state is generated/provisional only, deterministically diagnosed from canonical failed Phase 7 results, content-addressed, lifecycle-bound, and incapable of self-authorizing truth, memory promotion, governance, or execution.

See [`LEARNING_SYSTEM_REFLECTION.md`](./LEARNING_SYSTEM_REFLECTION.md).

### Phase 9 — Independent candidate-lesson verification ✅ Complete

Accepted verification reconstructs exact Phase 8 state, executes only the canonical verification plan, performs fresh deterministic retest evaluation, preserves original/retest provenance, and aggregates to `verified_for_learning`, `rejected`, or `inconclusive`.

`verified_for_learning` is verification evidence only; it is not durable-memory promotion.

See [`LEARNING_SYSTEM_VERIFICATION.md`](./LEARNING_SYSTEM_VERIFICATION.md).

### Phase 10 — Verified lesson retention ⚠️ Specification accepted; implementation blocked

Issue #133 / PR #134 accepted the retention contract. Phase 10 v1 is intentionally provider-neutral/in-memory and requires all of the following before a `VerifiedLessonRecord` can exist:

- exact Phase 8/9 revalidation;
- deterministically proven procedural lesson eligibility;
- complete trusted contradiction/source scope;
- exact duplicate handling with recoverable provenance;
- bounded evidence-derived confidence basis without fabricated probability;
- exact human retention approval through the existing LangGraph approval boundary;
- authenticated human principal binding;
- one-time approval-binding consumption;
- deterministic/content-addressed decision/lesson identities;
- immutable lifecycle transitions bound to exact accepted evidence/decision identities;
- no HXMP write path in this slice.

Draft PR #136 is **not merge-ready**. Five unresolved P1 findings remain:

1. procedural lesson eligibility is inferred rather than deterministically proven from the lesson body;
2. source contradiction state can become clear without an accepted deterministic source-contradiction comparison;
3. source-scope completeness is not proven through a trusted canonical enumeration boundary;
4. supersession/revocation is not bound to exact evidence/decision identities;
5. duplicate outcomes do not persist recoverable Phase 8/9/proposal provenance.

Until those findings are fixed, re-tested, and independently re-reviewed, Phase 10 runtime retention remains unaccepted.

See [`LEARNING_SYSTEM_RETENTION.md`](./LEARNING_SYSTEM_RETENTION.md).

## Blockchain Reasoning Pyramid track

The Pyramid is the accepted training/evaluation/remediation system for sharpening Roberta's blockchain reasoning. It is **not** trusted-memory promotion and does not bypass Learning System Phase 10.

### Accepted foundation and runner

- #149 — 20-level Blockchain Reasoning Pyramid, 1,000-question level structure, integrity questions, Boss gate, accuracy thresholds, SQLite performance ledger, and Learning Command Center dashboard;
- #150 — automated answer/grading/checkpoint/resume loop;
- #151 — semantic-equivalence grader calibration;
- #152 — weighted PASS/PARTIAL/FAIL scoring;
- #153 — bounded fenced-JSON parser support;
- #154 — question-first grading and checkpoint schema v3;
- #155 — remediation analyzer and fresh-practice generation;
- #160 — first 50-question MB4E Level 1 smoke curriculum;
- #162 — question-first grader hardening against reference anchoring;
- #167 — one bounded missing-answer recovery for model answer batches.

### Accepted Learning System bridge

- #169 — weak Pyramid items become deterministic, content-addressed remediation handoffs that preserve curriculum/exercise/checkpoint/source provenance and explicitly stop before Phase 8 candidate creation;
- #171 — MB4E question-first grading semantics v2 and historical-semantics invalidation;
- #173 — historical checkpoint regrade reuses stored Roberta answers exactly and invokes only the current grader/adjudicator path;
- #175 — one bounded corrective adjudication when a single-part question improperly retains `incomplete_reasoning`;
- #177 — source-grounded Pyramid reconstruction rebinds a remediation handoff to the exact curriculum/checkpoint and accepted Learning System source/retrieval/evidence-packet path.

The accepted Pyramid-to-learning sequence is therefore:

```text
Pyramid result
  -> weak-item/remediation analysis
  -> deterministic learning handoff
  -> source-grounded reconstruction
  -> later separately accepted Phase 7/8/9/10 learning path
```

No Pyramid grade, weakness, grader note, expected answer, practice question, or reconstruction is automatically a verified lesson or source truth.

## Active source/provenance work

### PR #179 — MB4E legacy Level 1 provenance migration ⚠️ Open / blocked

Goal: migrate the existing local canonical Mastering Blockchain Level 1 package to stronger canonical source binding without rewriting historical checkpoints or rerunning the 1,000-question model exam.

Current state:

- PR is open and GitHub-mergeable;
- exact-head CI is passing;
- two unresolved P2 review findings remain.

Required fixes before acceptance:

1. PDF-page-basis locator support must live in the core source-grounded reconstruction API, not only in the CLI, so programmatic callers can consume migrated packages;
2. output directories nested beneath the input package must fail closed or stage outside the input tree to prevent recursive copy/staging behavior.

The migration is not accepted `main` behavior until those findings are resolved and the PR merges.

### PR #141 — XenBlocks PoW source onboarding ❌ P1 blocked

The source is not accepted on `main` yet. The unresolved P1 requires the canonical Phase 1 source artifact to preserve/hash the exact uploaded CRLF bytes. LF normalization may exist only as a derived parsing representation, not as a replacement canonical source artifact.

## Accepted static source registry

Accepted source onboarding is tracked in [`learning_sources/README.md`](./learning_sources/README.md).

Accepted on `main`:

- X1 Blockchain Whitepaper v1.0 (#138);
- XDEX documentation snapshot (#147);
- XEN Litepaper v1.7 (#147);
- XEN Torrent / XENFT Litepaper v0.3 (#147);
- XONE ERC20 Token v4 (#147);
- *Mastering Blockchain, Fourth Edition* as an external exact-transcript integrity contract (#147);
- Solana whitepaper v0.8.13 (#147).

Static source inclusion never creates live-state authority.

## CMIS dependency status

Roberta currently consumes CMIS contract `1.9.0` where required by the promoted X1 Verified Intelligence service.

Accepted CMIS state relevant to Roberta:

- Phase 11 read-only Verified Intelligence foundation complete but non-promoted as a group;
- X1 `concentration_change_intelligence/v1` is the first separately promoted public-service/Scout-reliance wrapper and is adopted through X1 Scout;
- deterministic descriptive classification is internal/non-promoted;
- deterministic direct wallet-relationship evidence is internal/non-promoted and explicitly non-ownership;
- deterministic concentration-threshold alert evidence is internal/non-promoted;
- no public alert service or Roberta alert-planner adoption is accepted yet;
- Controlled Execution/value movement remains unauthorized.

## Technology Radar

[`TECHNOLOGY_RADAR.md`](./TECHNOLOGY_RADAR.md) is an accepted read-only design/specification only. There is no accepted Radar runtime, scheduler, dependency-adoption automation, provider-trust mutation, or execution authority.

Technology Radar implementation requires a separate accepted implementation gate.

## Human approval boundary

A Roberta approval binds one exact request/proposal/scope and explicit human decision. It is not a reusable signing credential, broad wallet permission, or blanket future authorization.

Phase 10 retention may reuse this review mechanism only under its accepted exact retention proposal/binding/principal rules. It does not inherit wallet/HXMP authorization from a retention approval.

## Durable memory boundary

```text
LangGraph checkpoints -> current task/thread state
HXMP                  -> durable context under its own wallet-bound write contract
Learning System       -> static source knowledge + separately gated verified learning
Pyramid               -> training/evaluation/remediation state
CMIS                  -> current verified market/blockchain facts/evidence
```

Phase 10 v1 must not write HXMP. A future verified-lesson-to-HXMP path requires a separate accepted gate.

## Controlled Execution gate

Roberta Phase 11 remains locked. No accepted roadmap item currently grants:

- transaction preparation as an execution path;
- wallet signing;
- transaction broadcasting;
- custody;
- live swap/trade execution;
- bridge value transfer;
- autonomous trading/value movement;
- broad delegated wallet authority.

Research, recommendations, Learning System output, Pyramid performance, human review, and CMIS pre-trade analysis cannot be interpreted as execution authorization.

## Near-term implementation sequence

The allowed sequence is:

1. fix/re-review/merge #179 before treating the MB4E provenance migration as accepted;
2. rerun/regenerate provenance-bound remediation artifacts only after the accepted migration, without mutating historical checkpoint bytes;
3. continue source-grounded remediation/mastery work through explicit deterministic gates;
4. fix the five P1 blockers on Phase 10 PR #136 before any verified-lesson retention can be accepted;
5. fix #141 exact-byte provenance before XenBlocks PoW source onboarding;
6. only then consider separately gated Phase 10 follow-ons such as production retention persistence/HXMP integration;
7. keep Technology Radar implementation and Controlled Execution separate future initiatives.

Any new branch that changes this ordering requires an explicit roadmap/spec gate.

## Engineering governance

Meaningful Roberta changes follow [`ENGINEERING_WORKFLOW.md`](./ENGINEERING_WORKFLOW.md):

1. roadmap/issue ownership;
2. contract/spec before implementation when semantics/authority change;
3. narrow tracer-bullet implementation;
4. behavior-first deterministic tests;
5. exact-head/full applicable CI;
6. independent review on **Spec Fidelity**, **Code/Architecture Quality**, and **Authority/Safety Boundary**;
7. no merge while a required review axis is blocked;
8. post-merge README/roadmap/source-of-truth reconciliation.

Green CI alone is not acceptance.

## Non-negotiable authority rules

1. Facts before interpretation.
2. Provider output is not verified merely because it is available.
3. Unknown remains unknown.
4. Static learning material cannot silently become current live state.
5. Generated lesson/reflection/grader text cannot self-authorize source truth.
6. Proof Score remains separate from risk.
7. Cross-chain evidence preserves chain provenance and scope.
8. Human approval remains exact and non-reusable.
9. Pyramid/training success does not bypass retention gates.
10. No execution authority by implication.
