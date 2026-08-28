# Roberta LangGraph Roadmap

Last reconciled: 2026-08-28 (America/New_York)

Status source: accepted code and contracts on `main`. Open PRs are not current truth unless explicitly identified as pending.

## Canonical authority model

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Roberta owns orchestration, policy coordination, specialist selection, cross-chain synthesis, learning coordination, approval boundaries, and the final user-facing answer. Chain Scouts own chain-specific planning and interpretation. CMIS owns deterministic freshness-sensitive blockchain/market facts, evidence, Evidence Receipts, Proof Scores, risk, capability state, historical intelligence, and bounded analysis-only pre-trade calculations.

Fresh accepted CMIS/provider evidence overrides books, RAG, source-mastery state, Pyramid checkpoints, learned concepts, retained lessons, and remembered live values for freshness-sensitive facts. Missing evidence remains unknown/unavailable; it is never converted into zero or a model guess. Proof Score remains separate from risk.

Controlled Execution remains locked/not started. No Learning System result, CMIS result, Scout result, pre-trade PASS, policy decision, or human approval grants transaction construction, signing, broadcasting, custody, trading, bridge transfer, or autonomous value movement.

## Current accepted platform state

Accepted on `main`:

- core LangGraph platform work through Roberta Phase 10 plus the post-Phase-10 evidence-aware user experience;
- X1 Scout decision-production readiness under the accepted CMIS boundary;
- Solana Scout read-only readiness for its accepted surface;
- X1 Scout adoption of CMIS `concentration_change_intelligence/v1`;
- X1 Scout adoption of the current CMIS `1.12.0` contract boundary, including CMIS `1.10.0` all-available history, CMIS `1.11.0` exact-mint X1 identity, and the bounded CMIS `1.12.0` verified-provider historical price-backfill semantics;
- Learning System Phases 1-10;
- fail-closed `verified_learned_knowledge` classification with no general operational-trust promotion wrapper;
- source-specific Blockchain Reasoning Pyramid architecture and source-mastery ledger;
- Mastering Blockchain 4e frozen 14-stage source plan;
- accepted prebuilt MB4E banks through Stage 8 / Market Structure;
- autonomous source-grounded Learning Plane controller from PR #228;
- read-only Learning Command Center telemetry for source mastery and autonomous-training jobs.
- autonomous remediation hardening through PRs #241-#243: complete Boss synthesis routing, candidate-only retention memory, and bounded candidate-memory retention;
- autonomous target-generation hardening through PRs #244-#245: bounded zero-valid-target retries and fail-closed normalization of malformed optional defensive metadata.

`main` includes the hardened Phase 10 verified-retention implementation and the separate knowledge-classification boundary. The old draft PR #136 remains open historical work and is no longer the implementation source of truth.

## Learning System — accepted Phases 1-10

The accepted Learning System pipeline is:

1. **Source ingestion** — exact approved bytes/source identity are preserved and hashed.
2. **Structure detection** — deterministic document structure is extracted without inventing source semantics.
3. **Structure-aware chunking** — evidence chunks retain source location and lineage.
4. **Indexing** — lexical indexing is accepted; optional embeddings remain an implementation choice behind the same evidence boundaries.
5. **Retrieval** — deterministic source filtering/ranking and benchmark foundations.
6. **Grounding** — evidence packets and citations are bound to retrieved source material.
7. **Evaluation** — answers are independently evaluated against evidence-aware criteria.
8. **Reflection** — provisional lessons/candidates are generated without self-authorizing trust.
9. **Verification** — candidate lessons are independently rechecked and may become `verified_for_learning`.
10. **Verified retention** — only exact eligible Phase 9 results can enter the narrow, provenance-bound retention contract after complete contradiction checks and exact human approval.

Phase 10 is accepted as a deterministic provider-neutral/in-memory retention layer. It does **not** authorize HXMP writes, source truth, live-state truth, CMIS/provider trust, governance mutation, wallet authority, or execution.

The accepted Learning Plane classification boundary can classify an exact active retained lesson as:

```text
verified_learned_knowledge
```

That classification preserves the retention/verification/source/approval lineage and explicitly sets `operational_trust_authorized=false`. General operational promotion remains unavailable until a separately reviewed wrapper is accepted.

## Autonomous Learning Plane — accepted

PR #228 merged on 2026-08-26 and is now accepted `main` behavior.

One selected PDF, Markdown, or UTF-8 text source can be handled by:

```bash
roberta-train --source "/path/to/source.pdf"
```

The controller can:

- hash and durably register the selected source, transcript, extracted pages, and chapter map;
- reject OCR-only PDFs and provenance mismatches;
- inspect every source page, including front matter, before declaring plan coverage complete;
- auto-match an existing curriculum by immutable artifact hash or create a source-specific curriculum;
- freeze and durably cache the exact source-mastery plan before authoritative ledger binding;
- generate missing stage banks from every assigned source chunk under exact quote/page/chapter validation and independent support verification;
- publish validated curriculum changes atomically while guarding against unexpected ledger mutation;
- run 300-question canonical stage exams automatically;
- derive source-bound weaknesses after failure;
- require source-grounded practice, closed-source bounded candidate-memory retention, provenance-bound `LearnedConcept` conversion, and transfer verification before learned-concept persistence/promotion and retry;
- preserve failed attempts as immutable evidence without erasing the completed source-stage prefix;
- run a separate 60-question final source capstone;
- resume from durable state after interruption with advisory locking and source-registry transaction safety;
- expose read-only job/status telemetry to the Learning Command Center.

The accepted controller is autonomous source mastery, **not** unrestricted self-modification. It cannot change Roberta prompts, tools, policies, Scouts, CMIS contracts, provider authority, human-approval semantics, wallet permissions, or execution permissions as a consequence of learning.

A broader background scheduler with explicit concurrency/model/token/question/source/retention budgets and load-aware throttling remains a separate operational hardening milestone. The current accepted controller is durable and unattended after source selection, but that does not imply an unrestricted always-on self-modification daemon.

## Blockchain Reasoning Pyramid

The reusable 20-level Pyramid is a global capability taxonomy. Each source receives a frozen source-specific plan containing only the capabilities materially supported by that source.

New canonical source-stage attempts use:

```text
300 questions
249 ordinary
50 integrity
1 Boss, last
```

Historical 1,000-question Level 1/2 runs remain immutable audit history and are reconstructed only through explicit legacy paths.

For *Mastering Blockchain, Fourth Edition*, the frozen plan requires 14 source stages mapped to global capabilities:

```text
1,2,3,4,5,6,7,8,9,10,11,13,14,17
```

Explicitly excluded for this source:

```text
12,15,16,18,19,20
```

Accepted prebuilt curriculum-bank construction reaches:

- Stage 1 — Fundamentals;
- Stage 2 — Blockchain Mechanics;
- Stage 3 — Transactions;
- Stage 4 — Cryptography;
- Stage 5 — Smart Contracts;
- Stage 6 — Tokenomics;
- Stage 7 — Liquidity (PR #225);
- Stage 8 — Market Structure (PR #227).

Stages 9-14 do not yet exist as separately accepted prebuilt repository banks. The accepted autonomous controller may generate missing later-stage banks at runtime from the exact selected source under its validation contract. Generated bank availability still does not equal mastery.

MB4E is mastered only after the source-plan-bound ledger records every required stage as passed and the required final source capstone passes.

## Static source registry

Accepted curated static sources currently include:

- X1 Blockchain Whitepaper v1.0;
- XDEX documentation snapshot;
- XEN Litepaper v1.7;
- XEN Torrent / XENFT Litepaper v0.3;
- XONE ERC20 Token v4;
- *Mastering Blockchain, Fourth Edition* under its exact external transcript integrity contract;
- Solana whitepaper v0.8.13.

The autonomous source registry additionally provides an accepted mechanism for explicitly selected local PDF/Markdown/text sources to receive an independent hash-bound `local_<digest>` trusted binding. That mechanism does not silently add a local source to the curated named catalog and never creates live-state authority.

XenBlocks PoW documentation PR #141 remains open/unaccepted. Its current review blocker is the exact-byte Phase 1 rule: the canonical ingested artifact still represents the LF-normalized derivative instead of the exact uploaded CRLF bytes. Until fixed and merged, XenBlocks must not be listed as accepted.

## CMIS synchronization

Current accepted CMIS capability contract is `1.12.0`.

The existing X1 `historical_compare` service is accepted for `window`, `all_available`, and `all_available_pair` use through X1 Scout. All-available modes require the service-specific CMIS `>=1.10.0` guard and exact limitation semantics. Pair requests preserve the second user/trusted-context asset explicitly and issue one CMIS pair-history call; Roberta does not recompute two independent histories. For CMIS `>=1.12.0`, Scout reliance additionally requires the accepted price-only provider-backfill limitations: provider source independence, archive completeness, continuous coverage, historical USD-stable peg behavior, and complete asset lifetime remain unverified. Returned lifetime/continuous-coverage limits remain authoritative.

The core Phase 11 `intelligence_foundation` remains internal/non-promoted. The separately accepted X1 wrapper is exactly `concentration_change_intelligence/v1`, read-only, with `execution_authorized=false`.

Classification, direct wallet-relationship evidence, and concentration-threshold alert evidence remain internal/read-only/non-promoted. There is no accepted next public intelligence/alert promotion by implication.

## Near-term roadmap

### 1. Operate and harden the accepted Learning Plane

- exercise `roberta-train` against approved real source workflows;
- preserve deterministic provenance/integrity hard stops;
- expand autonomous-training telemetry and operator diagnostics where evidence shows a need;
- add bounded background scheduling/load-throttling only under a separate accepted contract;
- define delayed/recurrent retention scheduling without weakening the Phase 10 authority boundary.

### 2. Continue MB4E source mastery

- repository-accepted prebuilt MB4E banks remain through Stage 8 / Market Structure;
- operator-local autonomous validation has now passed runtime-generated Stage 9 / DeFi, Stage 10 / Advanced DeFi, and Stage 11 / On-chain Analysis; Stage 11 canonical Attempt 3 reached 99.33% accuracy, 100% integrity, Boss PASS, and zero critical failures;
- Stage 12 / Risk Reasoning is the next active stage; PRs #244-#245 harden missing-bank generation with bounded source-chunk retries and fail-closed handling of malformed optional `forbidden_inferences` metadata without weakening exact-evidence or independent-support gates;
- continue Stages 12-14 under the frozen plan using canonical exams and verified remediation as required;
- complete the required final source capstone before declaring MB4E mastered.

### 3. Clean stale historical branches without treating them as current truth

- PR #136 remains an obsolete draft relative to the hardened Phase 10 implementation now on `main`; close/supersede it when repository housekeeping is performed;
- PR #141 remains blocked until its exact-byte ingestion issue is fixed and re-reviewed.

### 4. Future X1Labs Intelligence Scout

PR #190 remains open documentation/planning only. Its specialist/remote-agent design must be reconciled against the now-accepted Learning Plane before acceptance. Remote-agent output cannot become independent factual verification, cannot bypass X1 Scout -> CMIS for freshness-sensitive claims, and cannot obtain Learning System/HXMP, wallet, or execution authority by implication.

### 5. Controlled Execution

Still locked/not started. Any future execution work requires a new explicit architecture, contract, safety, approval, and readiness gate. It is not unlocked by completion of the Learning System.

## Definition of done for the current learning milestone

The core autonomous-learning implementation milestone is complete on `main` when evaluated as:

```text
approved/static source selection
  -> immutable source/provenance registration
  -> complete frozen source plan
  -> source-grounded curriculum generation
  -> canonical exams
  -> verified remediation/retention/transfer
  -> curriculum-scoped learned concepts
  -> final source capstone
  -> durable restart-safe job state
```

The next work is operational hardening and continued source mastery, not rebuilding the autonomous controller from scratch.

## Core rule

**Roberta may learn autonomously from accepted static evidence, but learning never self-authorizes truth or operational power. Fresh chain facts remain behind Chain Scout -> CMIS -> Provider, and operational/execution authority remains separately gated.**
