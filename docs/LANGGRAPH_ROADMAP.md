# Roberta LangGraph Roadmap

Last reconciled: 2026-08-25 (America/New_York)

This is the authoritative living roadmap for Roberta. Open branches are not accepted behavior until their contract, deterministic verification, review, and merge gates pass.

## Canonical architecture

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Roberta owns orchestration, user policy, specialist selection, learning-workflow coordination, approval boundaries, cross-chain coordination, and final synthesis. Chain Scouts own chain-specific planning/interpretation. CMIS owns deterministic freshness-sensitive facts, evidence, Proof Scores, risk, capability state, historical intelligence, and bounded analysis-only pre-trade calculations.

Fresh accepted CMIS/provider evidence overrides remembered, checkpointed, book/RAG, Pyramid, or Learning System material for freshness-sensitive state. Missing evidence remains unknown/unavailable. Proof Score remains separate from risk.

## Core platform status

Accepted/completed:

- Phase 1 — Core Agent Loop;
- Phase 2 — Provider-Neutral Model Loop;
- Phase 3 — X1 Scout Boundary;
- Phase 4 — CMIS / X1 Provider Integration;
- Phase 5 — X1 evidence completeness as bounded/fail-closed capability state;
- Phase 6 — Agentic X1 Scout Planning;
- Phase 7A — Thread / Checkpoint Persistence;
- Phase 7B — HXMP Durable Memory foundation;
- Phase 8 — Oracle Policy;
- Phase 9 — Human in the Loop;
- Phase 10 — More Specialists / Providers;
- post-Phase-10 evidence-aware intelligence/user experience;
- X1 decision-production readiness;
- Solana read-only readiness for the accepted Scout surface;
- X1 Scout adoption/readiness of CMIS `concentration_change_intelligence/v1`.

Roberta Phase 11 — Controlled Execution remains **LOCKED / NOT STARTED**.

## Learning System roadmap

Accepted pipeline:

```text
approved source bytes
  -> structure
  -> evidence chunks
  -> index
  -> retrieval
  -> grounded evidence packet / citations
  -> answer evaluation
  -> provisional reflection / candidate lesson
  -> independent candidate verification
  -> separately gated retention
```

- Phase 1 Source ingestion — ✅ complete.
- Phase 2 Structure detection — ✅ complete.
- Phase 3 Structure-aware chunking — ✅ complete.
- Phase 4 Indexing foundation — ✅ complete.
- Phase 5 Retrieval/benchmark foundation — ✅ complete.
- Phase 6 Grounded answer/citation foundation — ✅ complete.
- Phase 7 Independent answer evaluation — ✅ complete.
- Phase 8 Provisional reflection/candidate lesson — ✅ complete.
- Phase 9 Independent candidate verification — ✅ complete.
- Phase 10 Verified lesson retention — ⚠️ specification accepted; implementation blocked.

Phase 10 Issue #133 / PR #134 defines the accepted retention contract. Draft PR #136 remains not merge-ready with five P1 blockers:

1. procedural lesson-body eligibility is not deterministically proven;
2. approved-source contradiction state lacks an accepted deterministic comparison;
3. trusted source-scope completeness is not proven through a canonical enumeration boundary;
4. lifecycle supersession/revocation is not bound to exact evidence/decision identities;
5. duplicate outcomes do not persist recoverable Phase 8/9/proposal provenance.

Until #136 is fixed and independently re-reviewed, `verified_for_learning` remains verification evidence and not general trusted retained knowledge.

## Blockchain Reasoning Pyramid roadmap

The Pyramid is an accepted training/evaluation/remediation subsystem. It is not a shortcut around Learning System retention and is not a live-fact authority.

### Foundation accepted

The original 20-level Pyramid remains the reusable **global capability taxonomy**. The system no longer requires every source to traverse all 20 capabilities.

Accepted infrastructure includes:

- deterministic curriculum/exercise validation;
- automated answer, grading, checkpoint, resume, and SQLite ledger paths;
- PASS/PARTIAL/FAIL grading with question-first adjudication;
- bounded malformed JSON/schema/answer-ID recovery;
- historical regrade without re-answering;
- critical-failure validation/revalidation;
- remediation analysis and cumulative fresh-practice selection;
- content-addressed Pyramid -> Learning System handoffs;
- source-grounded reconstruction through the accepted Learning System evidence path;
- strict PDF-page provenance containment before retrieval/ranking;
- source-grounded targeted practice;
- supplemental source-grounded practice when canonical fresh practice is exhausted;
- critical-origin lineage preservation;
- closed-book critical retention before canonical retry when critical-origin learning is involved;
- curriculum-scoped learned concepts after exact source-grounded + closed-book verification;
- read-only Learning Command Center telemetry.

### Canonical exam contract

For **new** canonical stage attempts:

```text
300 total questions
249 ordinary
50 integrity
1 Boss, last
```

Historical 1,000-question Level 1/2 runs remain immutable audit history. Their explicit legacy reconstruction contract is 949 ordinary + 50 integrity + 1 Boss.

### Source-specific mastery architecture

PR #219 accepted the source-mastery plan contract. PR #220 integrated it into the runner and ledger.

A frozen `source_mastery_plan.json`:

- is bound to one curriculum/source identity;
- maps sequential source stages to unique global capability levels;
- accounts explicitly for excluded capabilities;
- requires 300 canonical questions per stage;
- asserts complete source-scope analysis;
- is content/hash-bound;
- cannot silently change after a run is bound;
- may require a separate source capstone.

Source mastery is distinct from global blockchain capability mastery.

## Mastering Blockchain 4e source mastery plan

Current deterministic planner: `roberta-mb4e-source-mastery-planner/v2`.

Required source stages: **14**.

| Source stage | Global capability | Chapters |
| ---: | ---: | --- |
| 1 | 1 Fundamentals | 1, 2 |
| 2 | 2 Blockchain Mechanics | 1, 5, 6, 9, 13, 14 |
| 3 | 3 Transactions | 6, 9, 13, 14 |
| 4 | 4 Cryptography | 3, 4, 18 |
| 5 | 5 Smart Contracts | 8, 11, 12 |
| 6 | 6 Tokenomics | 15 |
| 7 | 7 Liquidity | 21 |
| 8 | 8 Market Structure | 21 |
| 9 | 9 DeFi | 21 |
| 10 | 10 Advanced DeFi | 19, 21 |
| 11 | 11 On-chain Analysis | 7, 10, 12 |
| 12 | 13 Risk Reasoning | 18, 19, 21 |
| 13 | 14 Adversarial Analysis | 19 |
| 14 | 17 Cross-chain Reasoning | 17, 19, 21 |

Explicitly excluded from this source: capabilities **12, 15, 16, 18, 19, 20**.

A final MB4E source capstone is required. Passing all currently built banks is not enough to declare source mastery unless every required source stage and the capstone pass.

### Accepted MB4E bank/build state

Accepted on `main` through PR #227:

- Stage 1 / Fundamentals — historical Level 1 curriculum; accepted provenance migration #179 preserves the 1,206-exercise historical package identity and historical checkpoints.
- Stage 2 / Blockchain Mechanics — 1,206-question production-shaped bank (#212/#214).
- Stage 3 / Transactions — source-grounded bank for Chapters 6/9/13/14 (#217).
- Stage 4 / Cryptography — 415-question bank for Chapters 3/4/18 (#221).
- Stage 5 / Smart Contracts — 493-question bank for Chapters 8/11/12 (#222).
- Stage 6 / Tokenomics — 493-question bank for Chapter 15, PDF pages 502-529 (#223).
- Stage 7 / Liquidity — 415-question bank grounded in Chapter 21 liquidity material (#225).
- Stage 8 / Market Structure — 428-question bank grounded in Chapter 21 market-structure material (#227).

Stages 9-14 and the final source capstone are not yet accepted curriculum-build milestones on `main`.

Bank existence is not mastery. Source mastery progress comes from the immutable source-plan-bound ledger.

### Autonomous training proposal — pending

PR #228 proposes an end-to-end `roberta-train --source <file>` controller that would preserve already-installed Levels 1-8 and generically generate missing source-stage banks under exact source/provenance gates, run canonical exams/remediation, and require a final source capstone. It remains **open/unaccepted** and does not alter accepted `main` behavior until its review, CI, and merge gates pass.

## Source/provenance status

Accepted static Learning System source registry is in [`learning_sources/README.md`](./learning_sources/README.md).

Accepted MB4E provenance work includes:

- #179 legacy Level 1 provenance migration;
- explicit `pdf_pages` vs `book_pages` locator basis;
- PDF -> transcript alignment bound to exact source/transcript hashes;
- verified alignment windows for Level 1 remediation, including pages 37-41 and 44-60;
- provenance-constrained retrieval before ranking;
- full-containment requirement so evidence anchors cannot straddle outside declared page scope.

PR #141 XenBlocks PoW onboarding remains unaccepted because the original CRLF upload must be the canonical Phase 1 artifact rather than an LF-normalized derivative.

## Future specialist proposal — not accepted

PR #190 proposes a post-Learning-System **X1Labs Intelligence Scout** roadmap. It remains unaccepted and has an unresolved P1 requiring freshness-sensitive remote-agent claims to route through the correct chain-specific Scout rather than always through X1 Scout. It introduces no runtime capability on `main`.

## CMIS dependency status

Roberta consumes accepted CMIS capability contracts only through the relevant Chain Scout. Current accepted CMIS contract remains `1.9.0`; X1 `concentration_change_intelligence/v1` is the first separately promoted Verified Intelligence service adopted by Roberta. Internal CMIS classification, direct wallet-relationship, and concentration-alert foundations remain non-promoted.

## Near-term allowed sequence

1. Continue MB4E source-specific curriculum construction under the frozen 14-stage plan and exact provenance contracts; accepted banks currently stop at Stage 8.
2. Build/accept Stages 9-14 and the final source capstone before declaring the source mastered; PR #228 may automate that path only if separately accepted.
3. Run source stages through the source-plan-bound 300-question canonical runner; preserve historical Level 1/2 audit state rather than rewriting it.
4. Use source-grounded remediation, cumulative freshness, critical retention, and learned-concept gates when failures occur.
5. Separately fix Phase 10 PR #136 before any general verified-lesson retention is accepted.
6. Fix PR #141 exact-byte provenance before accepting XenBlocks PoW as a source.
7. Keep X1Labs Intelligence Scout, Technology Radar runtime, HXMP lesson persistence, and Controlled Execution behind separate future gates.

## Non-negotiable authority rules

1. Facts before interpretation.
2. Static source material is not current live state.
3. Unknown remains unknown.
4. Generated answers, grader notes, practice questions, reflections, and lessons cannot self-authorize source truth.
5. Pyramid learned concepts remain curriculum-scoped and do not become CMIS truth or general HXMP memory by implication.
6. Proof Score remains separate from risk.
7. Cross-chain facts preserve chain provenance.
8. Human approval remains exact and non-reusable.
9. Training/remediation success does not authorize wallet actions.
10. Controlled Execution remains locked.
