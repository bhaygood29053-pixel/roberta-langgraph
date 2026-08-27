# Roberta Project Status — 2026-08-26

## Executive status

Roberta's core autonomous Learning Plane milestone is now accepted on `main`.

The project has moved from "design/review the autonomous learning controller" to "operate and harden the accepted controller while continuing source mastery."

Controlled Execution remains locked/not started.

## Accepted on `main`

### Core platform / authority

- Core LangGraph platform work through Roberta Phase 10 and post-Phase-10 evidence-aware UX is complete.
- X1 Scout and Solana Scout operate under the accepted `Chain Scout -> CMIS -> Provider` authority boundary.
- X1 Scout adoption/readiness for CMIS `concentration_change_intelligence/v1` is complete.
- X1 Scout adopts CMIS `1.10.0` all-available historical modes with explicit second-asset preservation and a single CMIS pair-history request.
- CMIS remains the trust root for deterministic freshness-sensitive facts/evidence/risk/capability state within its accepted scope.
- Fresh accepted CMIS/provider facts override static learning material, retained lessons, Pyramid state, checkpoints, and remembered live values.
- Controlled Execution remains locked/not started.

### Learning System

- Learning System Phases 1-10 are accepted.
- Hardened Phase 10 verified retention is implemented on `main` as a narrow deterministic, provider-neutral/in-memory retention layer.
- Phase 10 requires exact eligible Phase 9 verification, complete contradiction checks, exact human approval, immutable lineage, and explicit lifecycle state.
- Historical draft PR #136 remains open but is obsolete as the implementation-status source of truth.
- An exact active retained lesson may be classified as `verified_learned_knowledge` with complete lineage.
- General operational-trust promotion is not accepted; the core promotion boundary fails closed and preserves `operational_trust_authorized=false`.

### Autonomous Learning Plane

PR #228 merged on 2026-08-26.

Accepted `roberta-train` behavior includes:

- explicit PDF/Markdown/UTF-8 source selection;
- immutable original/transcript/pages/chapter-map hashing and durable local source registration;
- complete-source planning including front matter;
- existing-curriculum match by trusted artifact hash or source-specific curriculum creation;
- durable frozen-plan cache before ledger binding / first package publication;
- all-assigned-chunk target generation with exact quote/page/chapter verification;
- independent target support verification;
- deterministic canonical bank expansion and atomic package publication;
- automatic 300-question source-stage exams;
- verified source-grounded remediation before retry;
- separate closed-book retention and transfer verification before curriculum-scoped learned-concept promotion;
- immutable failure evidence and preservation of the completed source-stage prefix;
- final 60-question source capstone;
- restart-safe state/events/checkpoints/advisory locks;
- source-registry transaction safety;
- read-only Learning Command Center telemetry.

This is autonomous continual source learning, not unrestricted self-modification. Learning cannot modify production prompts/tools/policies, Scouts, CMIS contracts, provider authority, human-approval semantics, wallet permissions, or execution authority.

### Blockchain Reasoning Pyramid / MB4E

- Source-specific Pyramid/source-mastery architecture is accepted.
- The reusable taxonomy remains 20 global capabilities.
- Mastering Blockchain 4e uses a frozen 14-stage source plan mapped to global capabilities `1,2,3,4,5,6,7,8,9,10,11,13,14,17`.
- Capabilities `12,15,16,18,19,20` are explicitly excluded from this source.
- New canonical source-stage exams remain 300 questions: 249 ordinary + 50 integrity + 1 Boss.
- Accepted **prebuilt** MB4E banks are present through Stage 8 / Market Structure:
  - Stage 1 — Fundamentals;
  - Stage 2 — Blockchain Mechanics;
  - Stage 3 — Transactions;
  - Stage 4 — Cryptography;
  - Stage 5 — Smart Contracts;
  - Stage 6 — Tokenomics;
  - Stage 7 — Liquidity (PR #225);
  - Stage 8 — Market Structure (PR #227).
- Stages 9-14 are not yet separately accepted prebuilt repository banks.
- The accepted autonomous controller may generate missing later-stage banks at runtime from the exact selected source under its validation contract.
- Bank availability is not mastery. MB4E is not mastered until every frozen required stage and the required final capstone pass in the authoritative source-mastery ledger.

### Learning sources

Accepted curated static sources include:

- X1 Blockchain Whitepaper v1.0;
- XDEX documentation snapshot;
- XEN Litepaper v1.7;
- XEN Torrent / XENFT Litepaper v0.3;
- XONE ERC20 Token v4;
- Mastering Blockchain 4e under its exact source integrity contract;
- Solana Whitepaper v0.8.13.

The autonomous local-source registry is also accepted as a generic hash-bound static source mechanism after explicit source selection. It does not silently add a source to the curated named catalog or create live authority.

XenBlocks PoW source PR #141 remains open/unaccepted because its reviewed head still ingests the LF-normalized derivative as the canonical Learning System artifact rather than preserving/ingesting the exact uploaded CRLF bytes required by Phase 1.

## Current CMIS dependency

Accepted CMIS capability contract is `1.10.0`.

X1 `historical_compare` now supports accepted Scout use of `window`, `all_available`, and `all_available_pair`. The two all-available modes require CMIS `>=1.10.0` plus exact capability limitations preserving stored-verified-observation scope, non-lifetime completeness, non-continuous coverage, and non-promotion of external OHLCV/archive history. Pair mode additionally requires explicit overlapping-history semantics. A failed service-specific guard returns unavailable before any service POST.

The core Phase 11 `intelligence_foundation` remains non-promoted.

The separately accepted promoted X1 wrapper remains:

```text
concentration_change_intelligence/v1
```

with the exact accepted read-only X1 concentration-change scope and `execution_authorized=false`.

Classification, direct wallet relationships, and concentration-threshold alert evidence remain internal/read-only/non-promoted. There is no accepted next public intelligence/alert promotion by implication.

## Current active/pending work

### 1. Operate and harden the Learning Plane

The autonomous controller itself is no longer pending. Remaining Learning Plane work is operational hardening:

- run approved real-source workflows and collect failure/telemetry evidence;
- improve diagnostics where actual operational evidence shows a need;
- add a separately accepted generalized background scheduler with explicit resource budgets/load-aware throttling if desired;
- define recurring/delayed retention cycles separately without weakening Phase 10 approval and authority rules;
- define provider-backed durable general retention only under a new explicit persistence contract.

### 2. Continue MB4E source mastery

- Stage 9 / DeFi is the next missing MB4E stage.
- Continue Stages 10-14 under the frozen source plan.
- Use canonical exams and verified remediation as required.
- Complete the required final source capstone.
- Do not declare MB4E mastered until the ledger proves every required gate.

### 3. Repository cleanup

- Historical Phase 10 draft PR #136 should eventually be closed/superseded so its open state cannot be mistaken for current implementation status.
- XenBlocks PR #141 must fix its exact-byte Phase 1 blocker and be re-reviewed before source acceptance.

### 4. X1Labs Intelligence Scout planning

PR #190 remains open documentation/planning only.

Its original sequencing language says it is blocked until the Learning System is complete. The core autonomous Learning Plane milestone is now complete, but PR #190 still requires explicit reconciliation against the accepted Learning Plane, remote-agent provenance/authority boundaries, X1 Scout -> CMIS freshness routing, and separate acceptance before any runtime implementation.

Remote-agent consensus is not independent factual verification and cannot obtain Learning System/HXMP, wallet, or execution authority by implication.

### 5. Controlled Execution

Still locked/not started.

Learning System completion does not unlock transaction construction, signing, broadcasting, custody, trading, bridge transfers, autonomous value movement, or broad delegated wallet authority. Any future execution work needs a new explicit architecture/contract/safety/readiness gate.

## Current assessment

The Learning System's primary development bottleneck is no longer the existence of an autonomous source-mastery loop. That loop is accepted.

The next maturity challenge is operating it safely at scale while preserving three separations:

1. **static knowledge vs fresh chain truth**;
2. **verified learned knowledge vs operational trust**;
3. **reasoning capability vs execution permission**.

If those separations remain intact, Roberta can expand source mastery and continual learning without turning the Learning Plane into an uncontrolled authority channel.

## Current source-of-truth chain

Use these current documents together:

1. `ROBERTA_CMIS_SOURCE_SYNC_BASELINE.md`;
2. `docs/CMIS_CONTRACT.md`;
3. `docs/LANGGRAPH_ROADMAP.md`;
4. `docs/LEARNING_SYSTEM.md`;
5. `docs/LEARNING_SYSTEM_RETENTION.md`;
6. `docs/LEARNING_PLANE_ARCHITECTURE.md`;
7. `docs/autonomous_training.md`;
8. `docs/PYRAMID_CURRICULUM.md`;
9. `docs/ROBERTA_SOURCE_MASTERY_PLAN.md`;
10. `docs/learning_sources/README.md`.

The 2026-08-25 project/sync status files remain historical snapshots and should not override these living documents or this 2026-08-26 status snapshot.

## Core rule

**Roberta's autonomous learning milestone is accepted; the roadmap now shifts to safe operation, source mastery, and separately gated future capabilities rather than treating the Learning Plane as an unmerged proposal.**
