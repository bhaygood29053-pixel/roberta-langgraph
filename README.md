# ROBERTA — Verified On-Chain Intelligence

Roberta is the top-level Oracle, policy-aware coordinator, learning-workflow coordinator, and normal user-facing voice for the multi-agent system.

## Product identity

**ROBERTA — Verified On-Chain Intelligence** is the canonical public-facing product name. The former working name **X1 Intelligence Service** is retired and must not be used as the current product name. X1 Scout, Solana Scout, and CMIS remain component names beneath Roberta; this naming decision does not change authority, verification, or execution boundaries.

See [`docs/PRODUCT_IDENTITY.md`](./docs/PRODUCT_IDENTITY.md) for the repository-authoritative naming rules.

## Canonical architecture

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Current chain specialists include X1 Scout and Solana Scout. Roberta owns orchestration, user policy, specialist selection, cross-chain coordination, approval boundaries, learning coordination, and final synthesis. Chain Scouts own chain-specific planning and interpretation. CMIS owns deterministic freshness-sensitive blockchain/market facts, evidence, Evidence Receipts, Proof Scores, risk, capability state, historical intelligence, and bounded analysis-only pre-trade calculations.

Roberta does not call market providers as a trust shortcut and does not reproduce CMIS calculations to manufacture a second market fact.

## Current accepted status — reconciled 2026-09-01

Core Roberta platform work is accepted through Phase 10 plus the post-Phase-10 evidence-aware user experience. X1 decision-production readiness, Solana read-only readiness for the accepted Scout surface, CMIS `concentration_change_intelligence/v1`, Instant X1 Scan, first-class X1 Compare, and the Canonical ROBERTA Decision Object v1 foundation are accepted. The merged X1 Burn Intelligence v1 tracer is under follow-up contract hardening in PR #295 before BURN is added to the shared Decision Object.

**Roberta Phase 11 Controlled Execution remains locked / not started.**

### Learning System

Learning System Phases 1-10 are accepted on `main`:

1. exact source ingestion;
2. structure detection;
3. structure-aware evidence chunking;
4. lexical/optional embedding indexing;
5. retrieval + deterministic benchmark foundation;
6. grounded evidence packets and citations;
7. independent answer evaluation;
8. provisional reflection + candidate lessons;
9. independent candidate-lesson verification;
10. narrow verified-lesson retention with contradiction checks, exact human approval, lifecycle state, and fail-closed authority boundaries.

The old Phase 10 draft PR #136 remains open historical work, but it is no longer the implementation source of truth. Hardened Phase 10 retention is accepted on `main`.

An exact active retained lesson may be classified as `verified_learned_knowledge` with complete retention/source/verification/approval lineage. That classification does **not** grant source truth, live-state truth, CMIS/provider trust, governance mutation, wallet authority, execution authority, or general operational trust. General operational promotion remains unavailable without a separately accepted wrapper.

### Autonomous Learning Plane

PR #228 merged on 2026-08-26. Roberta now has an accepted autonomous source-grounded Learning Plane controller:

```bash
roberta-train --source "/path/to/source.pdf" --profile expert
```

After a source is explicitly selected, Roberta can hash-bind and durably register it, inspect the full source, freeze a source-specific mastery plan, generate missing validated stage banks, run canonical exams, perform verified remediation with source-grounded practice, closed-source bounded candidate-memory retention, and transfer checks, reuse verified curriculum-scoped learned concepts, resume interrupted jobs, run the final source capstone, and expose authoritative read-only operational telemetry reconciled against the source-mastery ledger.

Private `roberta-core` PR #9 adds accepted `roberta-autonomous-training-telemetry/v1`: a deterministic read-only operator surface for run/source/plan identity, ledger-backed mastery/completion state, stage/remediation/checkpoint progress, controller/event diagnostics, and fail-closed state/ledger consistency findings. It preserves `execution_authorized=false` and does not grant learning, market, wallet, or execution authority.

This is autonomous continual source learning, not unrestricted self-modification. Static source material cannot modify Roberta prompts/tools/policies, Scouts, CMIS contracts, provider authority, wallet permissions, human-approval semantics, or execution authority.

See [`docs/LEARNING_PLANE_ARCHITECTURE.md`](./docs/LEARNING_PLANE_ARCHITECTURE.md) and [`docs/autonomous_training.md`](./docs/autonomous_training.md).

### Instant X1 Scan

CMIS `1.14.0` promotes bounded X1 `instant_x1_scan/v2`. The service remains read-only and composition-only, but it may deepen price history through the accepted bounded XDEX/X1.Ninja corroborated backfill before producing its history section. Roberta preserves the returned observation bounds, provider-backfill evidence, and gap diagnostics while keeping provider archive completeness, full asset lifetime, and continuity explicitly unverified. Missing/unverified holder or current-concentration facts remain explicit unknown/partial values, and Roberta does not treat composition as new underlying fact authority.

### X1 Burn Intelligence

CMIS historical burn-time valuation is accepted upstream together with deterministic burn metrics, scanner fact-time coverage, and circulating-supply evidence. Roberta's merged `x1_burn_intelligence/v1` X1 Scout projection preserves exact-mint identity, CMIS-owned burn/comparison/valuation semantics, evidence, limitations, and `execution_authorized=false` without recalculation.

Follow-up hardening PR #295 remains the immediate acceptance gate. After that gate, BURN should enter the Canonical ROBERTA Decision Object and Human/Machine renderers through a separately tested workflow adapter rather than by widening Instant Scan semantics.


### X1 identity and all-available history

Roberta/X1 Scout accepts the CMIS `1.14.0` Instant X1 Scan v2 contract boundary on this branch. CMIS `1.11.0+` exact-mint normalization under `x1_asset_identity/v1` keeps the exact mint as the fungible identity root while preserving Metaplex and XDEX descriptors as separately sourced observations.

Roberta/X1 Scout also adopts the CMIS `1.10.0` `all_available` / `all_available_pair` historical modes. Natural full-history requests remain on the canonical path `Roberta -> X1 Scout -> CMIS`.

A two-asset request such as “Compare XNT and ANL over their entire history” is delegated with the exact second asset as `compare_asset`; X1 Scout issues one CMIS `all_available_pair` request. The Scout-side client requires the accepted live historical limitation contract and fails closed before POST if it is missing or weakened. Under CMIS `>=1.12.0`, provider backfill may extend **price only**; source independence, archive completeness, continuous coverage, historical USD-stable peg behavior, and complete asset lifetime remain unverified. Roberta preserves those bounds rather than relabeling partial verified history as complete lifetime history.

### Blockchain Reasoning Pyramid

The Pyramid is a source-specific mastery system rather than a requirement that every source traverse all 20 global capability levels.

Accepted architecture:

```text
approved source
  -> deterministic source mastery plan
  -> source-specific stages mapped to the 20-capability taxonomy
  -> large source-grounded exercise banks
  -> 300-question canonical stage exam
  -> verified remediation / closed-book retention / transfer where needed
  -> next required source stage
  -> final source capstone
```

The new canonical stage exam contract is **300 questions**: 249 ordinary + 50 integrity + 1 Boss, with the Boss last. Historical 1,000-question Level 1/2 runs remain immutable audit history and are reconstructed only through explicit legacy paths.

For *Mastering Blockchain, Fourth Edition*, the frozen source plan requires **14 source stages** mapped to global capabilities `1,2,3,4,5,6,7,8,9,10,11,13,14,17`; capabilities `12,15,16,18,19,20` are explicitly excluded from this source. A final source capstone is required before the source can be declared mastered.

Accepted **prebuilt** MB4E curriculum construction now reaches:

- Stage 1 / Fundamentals;
- Stage 2 / Blockchain Mechanics — 1,206-question bank;
- Stage 3 / Transactions;
- Stage 4 / Cryptography — 415-question bank;
- Stage 5 / Smart Contracts — 493-question bank;
- Stage 6 / Tokenomics — 493-question bank;
- Stage 7 / Liquidity — merged in PR #225;
- Stage 8 / Market Structure — merged in PR #227.

Stages 9-14 are not yet separately accepted prebuilt repository banks. The accepted autonomous controller may generate missing banks from the exact selected source under its validation contract. Bank availability is not mastery; mastery state comes only from the immutable source-plan-bound training ledger and required stage/capstone gates.

Operator-local MB4E source mastery is now **complete**. The authoritative source-plan-bound ledger records **14/14 required source stages passed plus the required final source capstone**. Stage 14 / Cross-chain Reasoning passed canonical Attempt 3 at **99.33% accuracy**, **100% integrity**, **Boss PASS**, and **zero critical failures**. Runtime-generated Stages 9-14 remain runtime mastery evidence, not separately accepted prebuilt repository banks; repository-accepted prebuilt banks remain through Stage 8 / Market Structure.

A post-mastery replay exposed a controller resume-safety defect: the pre-fix controller could create a fresh run because it looked only for an active run instead of recognizing verified mastery as terminal. Private `roberta-core` PR #8 (`d86aff9617c975fc9420847cd1d7f8e74d9d7da9`) makes verified mastery terminal/idempotent and fail-closed on conflicting run identity. Private PR #7 (`2ba2873878dc88ab58b81efbaff4cecbb91a9f68`) hardened Stage 14 support-verified target retries. Neither fix relaxes mastery, evidence, provenance, support-verification, or execution boundaries. **MB4E should not be rerun for learning purposes unless a new reviewed source/mastery contract intentionally requires it.**

### Remediation and learned-concept boundaries

Accepted Pyramid hardening includes source-provenance migration, strict PDF-page provenance containment before retrieval, source-grounded targeted practice, cumulative freshness, supplemental practice when canonical practice is exhausted, critical-origin lineage, bounded adjudicator/answer recovery, closed-book critical retention, transfer verification, and curriculum-scoped learned concepts after the required gates.

Pyramid learned concepts are **curriculum-scoped training knowledge**, not general HXMP memory, source truth, current live blockchain truth, governance authority, or execution authority.

## Accepted static Learning System sources

See [`docs/learning_sources/README.md`](./docs/learning_sources/README.md).

Accepted curated source onboarding includes:

- X1 Blockchain Whitepaper v1.0;
- XDEX documentation snapshot;
- XEN Litepaper v1.7;
- XEN Torrent / XENFT Litepaper v0.3;
- XONE ERC20 Token v4;
- *Mastering Blockchain, Fourth Edition* under an exact external transcript integrity contract;
- Solana whitepaper v0.8.13.

The autonomous source registry also accepts an explicitly selected local PDF/Markdown/UTF-8 text source into an independent hash-bound `local_<digest>` binding for source mastery. That does not silently add it to the curated named catalog and does not create live-state authority.

XenBlocks PoW documentation PR #141 remains unaccepted because its canonical ingestion still violates the exact-byte Phase 1 rule by ingesting the LF-normalized derivative rather than the exact uploaded CRLF bytes.

Static sources never override fresh Scout -> CMIS -> Provider evidence for prices, liquidity, supply, wallet state, provider health, validator state, risk, fees, software versions, or other changing facts.

## Source-of-truth documents

- [`docs/PRODUCT_IDENTITY.md`](./docs/PRODUCT_IDENTITY.md) — repository-authoritative product naming and branding boundary.
- [`docs/LANGGRAPH_ROADMAP.md`](./docs/LANGGRAPH_ROADMAP.md) — authoritative Roberta roadmap/status.
- [`docs/PROJECT_STATUS_2026-09-01.md`](./docs/PROJECT_STATUS_2026-09-01.md) — current dated status snapshot.
- [`docs/LEARNING_SYSTEM.md`](./docs/LEARNING_SYSTEM.md) — Learning System phase/authority map.
- [`docs/LEARNING_SYSTEM_RETENTION.md`](./docs/LEARNING_SYSTEM_RETENTION.md) — accepted Phase 10 retention contract.
- [`docs/LEARNING_PLANE_ARCHITECTURE.md`](./docs/LEARNING_PLANE_ARCHITECTURE.md) — Learning Plane architecture and promotion boundary.
- [`docs/autonomous_training.md`](./docs/autonomous_training.md) — accepted autonomous source-mastery controller.
- [`docs/PYRAMID_CURRICULUM.md`](./docs/PYRAMID_CURRICULUM.md) — Pyramid capability/stage/exam contract.
- [`docs/ROBERTA_SOURCE_MASTERY_PLAN.md`](./docs/ROBERTA_SOURCE_MASTERY_PLAN.md) — source-specific mastery contract and MB4E mapping.
- [`docs/PYRAMID_TARGETED_PRACTICE.md`](./docs/PYRAMID_TARGETED_PRACTICE.md) — remediation/practice/retention gates.
- [`docs/PYRAMID_PROVENANCE_MIGRATION.md`](./docs/PYRAMID_PROVENANCE_MIGRATION.md) — accepted MB4E legacy provenance migration.
- [`docs/PYRAMID_DASHBOARD.md`](./docs/PYRAMID_DASHBOARD.md) — Learning Command Center read-only telemetry.
- [`docs/learning_sources/README.md`](./docs/learning_sources/README.md) — static source registry.
- [`docs/ENGINEERING_WORKFLOW.md`](./docs/ENGINEERING_WORKFLOW.md) — repository-authoritative engineering workflow.

## Authority rules

1. Fresh accepted CMIS/provider evidence overrides books, RAG, checkpoints, Pyramid training, retained lessons, and remembered live values for freshness-sensitive state.
2. Missing evidence remains unknown/unavailable; it is never converted into zero or a model guess.
3. Proof Score remains separate from market risk.
4. Source text, expected answers, grader notes, practice questions, generated lessons, and model repetition are not self-authorizing truth.
5. Cross-chain evidence keeps chain-specific provenance.
6. Human approval is exact and non-reusable.
7. Training success does not imply wallet or execution permission.
8. `verified_learned_knowledge` does not imply operational trust.

## Installation and tests

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,deepseek]'
python -m pytest -v -m 'not live and not cmis_live'
```

## Pyramid and Learning Plane commands

Current accepted commands include:

```text
roberta-train
roberta-pyramid-run
roberta-pyramid-dashboard
roberta-pyramid-remediate
roberta-pyramid-regrade
roberta-pyramid-critical-revalidate
roberta-pyramid-source-reconstruct
roberta-pyramid-migrate-provenance
roberta-pyramid-practice
roberta-pyramid-supplemental-practice
roberta-pyramid-critical-blocker-practice
roberta-pyramid-critical-retention
roberta-pyramid-critical-autofix
roberta-pyramid-plan-mb4e-source
roberta-pyramid-build-mb4e-level2
roberta-pyramid-build-mb4e-level3
roberta-pyramid-build-mb4e-level4
roberta-pyramid-build-mb4e-level5
roberta-pyramid-build-mb4e-level6
roberta-pyramid-build-mb4e-level7
roberta-pyramid-build-mb4e-level8
```

## Controlled execution boundary

No accepted Roberta, Learning Plane, Pyramid, Scout, or CMIS capability authorizes transaction signing, broadcasting, custody, live trading/swaps, bridge value transfer, autonomous value movement, or broad delegated wallet authority.

**Roberta coordinates and learns under evidence boundaries. CMIS verifies changing blockchain facts. Controlled Execution remains locked.**
