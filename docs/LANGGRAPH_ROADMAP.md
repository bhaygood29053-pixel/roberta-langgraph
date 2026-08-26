# Roberta LangGraph Roadmap

Last reconciled: 2026-08-25 (America/New_York)

This is the authoritative living roadmap for Roberta. Open branches are not accepted behavior until their contract, deterministic verification, review, and merge gates pass.

## Canonical architecture

```text
User / transport
  -> Roberta Runtime
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source

Approved static sources
  -> Roberta Learning Plane
    -> candidate knowledge
      -> verified learned knowledge
        -> separately gated operational knowledge
```

Roberta Runtime owns orchestration, user policy, specialist selection, approval boundaries, cross-chain coordination, and final synthesis. Chain Scouts own chain-specific planning/interpretation and do not manufacture facts. CMIS owns deterministic freshness-sensitive facts, evidence, Proof Scores, risk, capability state, historical intelligence, and bounded analysis-only pre-trade calculations. Providers remain beneath CMIS.

The Learning Plane is a separate automated background subsystem for source ingestion, provenance, curriculum construction, training, examination, remediation, retention, and knowledge promotion. It improves knowledge and reasoning but cannot self-authorize runtime, Scout, CMIS, provider, wallet, or execution changes.

Fresh accepted CMIS/provider evidence overrides remembered, checkpointed, book/RAG, Pyramid, or Learning System material for freshness-sensitive state. Missing evidence remains unknown/unavailable. Proof Score remains separate from risk.

See [`LEARNING_PLANE_ARCHITECTURE.md`](./LEARNING_PLANE_ARCHITECTURE.md).

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

## Learning Plane roadmap

### Accepted learning foundation

Learning System Phases 1-9 remain accepted:

1. Source ingestion — complete.
2. Structure detection — complete.
3. Structure-aware chunking — complete.
4. Indexing foundation — complete.
5. Retrieval/benchmark foundation — complete.
6. Grounded answer/citation foundation — complete.
7. Independent answer evaluation — complete.
8. Provisional reflection/candidate lesson — complete.
9. Independent candidate verification — complete.
10. Verified lesson retention — specification accepted; implementation blocked.

Phase 10 Issue #133 / PR #134 defines the accepted retention contract. Draft PR #136 remains not merge-ready with five P1 blockers: procedural lesson eligibility, deterministic contradiction handling, canonical trusted-source scope completeness, exact lifecycle supersession/revocation identity binding, and recoverable Phase 8/9/proposal provenance for duplicate outcomes.

Until #136 is fixed and independently re-reviewed, `verified_for_learning` is verification evidence and not general trusted retained knowledge.

### Target Learning Plane architecture

The Learning System is now planned as a fault-isolated automated background **Learning Plane**, not as an unrestricted self-modifying loop inside the user-facing agent.

Layered workers:

```text
Source Intake
  -> Provenance Verification
    -> Curriculum Planning / Generation
      -> Training
        -> Examination
          -> Remediation
            -> Retention
              -> Knowledge Promotion
```

Each layer emits auditable artifacts for the next layer. Raw model output cannot write directly into trusted runtime memory.

Knowledge states are explicit:

- **Candidate knowledge** — encountered/proposed, not independently proven.
- **Verified learned knowledge** — source/provenance-bound and independently verified.
- **Operationally trusted knowledge** — separately promoted for runtime use within a defined static-knowledge scope.

For freshness-sensitive state the authority order remains:

```text
fresh accepted CMIS/provider evidence
  > remembered/checkpointed live values
  > operationally trusted static learned knowledge
  > verified learned knowledge
  > candidate knowledge
```

### Background automation

“Downtime training” means scheduled background work with resource budgets and runtime priority, not a binary idle switch. The implementation should support maximum concurrent jobs, model/token budgets, question/exam budgets, source-ingestion budgets, retention-test budgets, load-aware throttling, durable checkpoints, and restart-safe job state.

User-facing Runtime and accepted Scout/CMIS work outrank background learning. A learning-job failure must not impair Runtime availability.

### Retention lifecycle

Verified concepts are revisited on delayed retention horizons. Retention failures route back through source-grounded remediation and may weaken/revoke learned-knowledge status under the accepted lifecycle contract. The system must not silently preserve confidence after failed retention.

### Autonomous training proposal — pending

PR #228 proposes the first end-to-end Learning Plane controller through `roberta-train --source <file>`: immutable source hashing, curriculum matching/bootstrap, generic missing-bank generation, exact source evidence validation, canonical exams, remediation/retries, durable jobs, and final source capstone.

PR #228 remains **open/unaccepted**. Its architecture is directionally consistent with the Learning Plane, but it requires separate implementation, provenance, authority, CI, and review acceptance. Existing accepted Levels 1-8 remain valid and must not be rewritten merely to adopt automation.

### Learning Plane hard boundaries

The Learning Plane may autonomously learn, construct bounded curricula, train, examine, remediate, and run retention under accepted contracts. It may not autonomously:

- alter `User -> Roberta -> Chain Scout -> CMIS -> Provider`;
- manufacture freshness-sensitive facts;
- bypass CMIS as live-truth authority;
- modify production prompts/tools/policies as a consequence of learning;
- add/promote Scout or CMIS capabilities;
- change human-approval or wallet permissions;
- authorize trades/transactions;
- unlock Controlled Execution.

## Blockchain Reasoning Pyramid roadmap

The Pyramid is an accepted training/evaluation/remediation subsystem inside the Learning Plane. It is not a shortcut around Learning System retention and is not a live-fact authority.

The original 20-level Pyramid remains the reusable **global capability taxonomy**. A source-specific mastery plan maps only the capabilities actually supported by that source.

Accepted infrastructure includes deterministic curriculum validation, automated grading/checkpoint/resume/ledger paths, historical regrade, critical-failure revalidation, remediation, content-addressed Learning System handoffs, provenance-constrained retrieval, source-grounded targeted/supplemental practice, critical retention, curriculum-scoped learned concepts, and read-only Learning Command Center telemetry.

### Canonical exam contract

For new canonical stage attempts:

```text
300 total questions
249 ordinary
50 integrity
1 Boss, last
```

Historical 1,000-question Level 1/2 runs remain immutable audit history. Their explicit legacy reconstruction contract is 949 ordinary + 50 integrity + 1 Boss.

## Mastering Blockchain 4e source mastery plan

Current deterministic planner: `roberta-mb4e-source-mastery-planner/v2`.

Required source stages: **14**, followed by a final source capstone.

| Stage | Capability | Chapters |
| ---: | --- | --- |
| 1 | Fundamentals | 1, 2 |
| 2 | Blockchain Mechanics | 1, 5, 6, 9, 13, 14 |
| 3 | Transactions | 6, 9, 13, 14 |
| 4 | Cryptography | 3, 4, 18 |
| 5 | Smart Contracts | 8, 11, 12 |
| 6 | Tokenomics | 15 |
| 7 | Liquidity | 21 |
| 8 | Market Structure | 21 |
| 9 | DeFi | 21 |
| 10 | Advanced DeFi | 19, 21 |
| 11 | On-chain Analysis | 7, 10, 12 |
| 12 | Risk Reasoning | 18, 19, 21 |
| 13 | Adversarial Analysis | 19 |
| 14 | Cross-chain Reasoning | 17, 19, 21 |

Explicitly excluded from this source: global capabilities **12, 15, 16, 18, 19, 20**.

### Accepted MB4E bank/build state

Accepted on `main` through PR #227:

- Stage 1 / Fundamentals — accepted historical Level 1 package/provenance migration.
- Stage 2 / Blockchain Mechanics — accepted production-shaped bank/provenance integration.
- Stage 3 / Transactions — accepted source-grounded bank.
- Stage 4 / Cryptography — accepted source-grounded bank.
- Stage 5 / Smart Contracts — accepted source-grounded bank.
- Stage 6 / Tokenomics — accepted source-grounded bank.
- Stage 7 / Liquidity — accepted source-grounded bank (#225).
- Stage 8 / Market Structure — accepted source-grounded bank (#227).

Stages **9-14 plus the final source capstone remain unaccepted build milestones**. Bank existence is not mastery; mastery comes from the immutable source-plan-bound ledger.

## Source/provenance status

Accepted static Learning System source registry is in [`learning_sources/README.md`](./learning_sources/README.md). Accepted provenance rules include exact source hashes, explicit locator basis, source/transcript alignment, provenance-constrained retrieval before ranking, and full evidence containment within declared source scope.

PR #141 XenBlocks PoW onboarding remains unaccepted until exact-byte provenance is corrected.

## Future specialist proposal — not accepted

PR #190 proposes a future X1Labs Intelligence Scout. It remains unaccepted and introduces no runtime capability on `main`.

## CMIS dependency status

Roberta consumes accepted CMIS capability contracts only through the relevant Chain Scout. Current accepted CMIS contract remains `1.9.0`. Core Phase 11 `intelligence_foundation` remains non-promoted. X1 `concentration_change_intelligence/v1` is the separately accepted Phase 12 promoted wrapper adopted by Roberta. Internal CMIS classification, direct wallet-relationship, and concentration-alert foundations remain read-only/non-promoted.

`pre_trade_check` remains analysis-only. Working `liquidity_scout` identifiers may remain as compatibility identifiers during incremental migration. Any promoted service must match both projects on contract version, chain, scope, accepted conclusion, Scout reliance, read-only state, and `execution_authorized=false`.

## Near-term allowed sequence

1. Merge the paired architecture/source-sync reconciliation only after exact-head CI/review passes.
2. Treat the Learning Plane architecture as the target for automated source mastery while keeping current accepted runtime behavior unchanged.
3. Independently review/fix/accept PR #228 as the first Learning Plane automation implementation; do not infer acceptance from green tests alone.
4. Complete MB4E Stages 9-14 and the final source capstone, manually or through separately accepted automation, before declaring MB4E mastered.
5. Fix Phase 10 retention PR #136 before general retained lessons or broad operational knowledge promotion is accepted.
6. Add retention scheduling, budgets, throttling, durable worker telemetry, and explicit candidate -> verified -> operational promotion gates.
7. Fix PR #141 exact-byte provenance before XenBlocks PoW source acceptance.
8. Keep X1Labs Intelligence Scout, Technology Radar runtime, HXMP general lesson persistence, and Controlled Execution behind separate future gates.

## Non-negotiable authority rules

1. Facts before interpretation.
2. Static source material is not current live state.
3. Unknown remains unknown; missing evidence is not zero.
4. Generated answers, grader notes, curricula, practice questions, reflections, and lessons cannot self-authorize source truth or runtime authority.
5. Pyramid learned concepts remain curriculum-scoped until separately promoted and never become CMIS truth.
6. Fresh verified CMIS/provider facts override remembered or learned live values.
7. Proof Score remains separate from risk.
8. Cross-chain facts preserve chain provenance.
9. Human approval remains exact and non-reusable.
10. Training/remediation/retention success does not authorize wallet actions.
11. The Learning Plane cannot self-modify runtime authority, Scouts, CMIS contracts, or execution permissions.
12. Controlled Execution remains locked.