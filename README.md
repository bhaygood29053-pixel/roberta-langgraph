# Roberta LangGraph

Roberta is the top-level Oracle, policy-aware coordinator, learning-workflow coordinator, and normal user-facing voice for the multi-agent system.

## Canonical architecture

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Current chain specialists include X1 Scout and Solana Scout. Roberta owns orchestration, user policy, specialist selection, cross-chain coordination, approval boundaries, learning workflow, and final synthesis. Chain Scouts own chain-specific planning and interpretation. CMIS owns deterministic freshness-sensitive blockchain/market facts, evidence, Evidence Receipts, Proof Scores, risk, capability state, historical intelligence, and bounded analysis-only pre-trade calculations.

Roberta does not call market providers as a trust shortcut and does not reproduce CMIS calculations to manufacture a second market fact.

## Current accepted status — reconciled 2026-08-25

Core Roberta platform work is accepted through Phase 10 plus the post-Phase-10 evidence-aware user experience. X1 decision-production readiness, Solana read-only readiness for the accepted Scout surface, and adoption of CMIS `concentration_change_intelligence/v1` through X1 Scout are accepted.

**Roberta Phase 11 Controlled Execution remains locked / not started.**

### Learning System

Learning System Phases 1-9 are accepted:

1. exact source ingestion;
2. structure detection;
3. structure-aware evidence chunking;
4. lexical/optional embedding indexing;
5. retrieval + deterministic benchmark foundation;
6. grounded evidence packets and citations;
7. independent answer evaluation;
8. provisional reflection + candidate lessons;
9. independent candidate-lesson verification.

Phase 10 verified-lesson retention has an accepted specification under #133/#134, but runtime implementation PR #136 remains **draft / not merge-ready** with five unresolved P1 blockers. `verified_for_learning` therefore remains verification evidence rather than general trusted durable memory.

### Blockchain Reasoning Pyramid

The Pyramid is now a source-specific mastery system rather than a requirement that every source traverse all 20 global capability levels.

Accepted architecture:

```text
approved source
  -> deterministic source mastery plan
  -> source-specific stages mapped to the 20-capability taxonomy
  -> large source-grounded exercise banks
  -> 300-question canonical stage exam
  -> remediation / source-grounded practice / closed-book retention where needed
  -> next required source stage
  -> final source capstone
```

The new canonical stage exam contract is **300 questions**: 249 ordinary + 50 integrity + 1 Boss, with the Boss last. Historical 1,000-question Level 1/2 runs remain immutable audit history and are reconstructed only through explicit legacy paths.

For *Mastering Blockchain, Fourth Edition*, the frozen source plan requires **14 source stages** mapped to global capabilities `1,2,3,4,5,6,7,8,9,10,11,13,14,17`; capabilities `12,15,16,18,19,20` are explicitly excluded from this source. A final source capstone is still required before the source can be declared mastered.

Accepted MB4E curriculum construction now reaches:

- Stage 1 / Fundamentals — historical Level 1 foundation and provenance-migrated curriculum;
- Stage 2 / Blockchain Mechanics — 1,206-question bank;
- Stage 3 / Transactions — source-grounded bank for Chapters 6, 9, 13, and 14;
- Stage 4 / Cryptography — 415-question bank for Chapters 3, 4, and 18;
- Stage 5 / Smart Contracts — 493-question bank for Chapters 8, 11, and 12;
- Stage 6 / Tokenomics — 493-question bank for Chapter 15.

Exercise-bank availability is not the same as mastery. Mastery state comes from the immutable source-plan-bound training ledger and required stage/capstone gates.

### Remediation and learned-concept boundaries

Accepted Pyramid hardening includes source-provenance migration, strict PDF-page provenance containment before retrieval, source-grounded targeted practice, cumulative freshness, supplemental practice when canonical practice is exhausted, critical-origin lineage, bounded adjudicator/answer recovery, closed-book critical retention, and curriculum-scoped learned concepts after the required verification gates.

Pyramid learned concepts are **curriculum-scoped training knowledge**, not general HXMP memory, source truth, current live blockchain truth, governance authority, or execution authority.

## Accepted static Learning System sources

See [`docs/learning_sources/README.md`](./docs/learning_sources/README.md).

Accepted source onboarding includes:

- X1 Blockchain Whitepaper v1.0;
- XDEX documentation snapshot;
- XEN Litepaper v1.7;
- XEN Torrent / XENFT Litepaper v0.3;
- XONE ERC20 Token v4;
- *Mastering Blockchain, Fourth Edition* under an exact external transcript integrity contract;
- Solana whitepaper v0.8.13.

XenBlocks PoW documentation PR #141 remains unaccepted because its exact-byte Phase 1 provenance blocker is unresolved.

Static sources never override fresh Scout -> CMIS -> Provider evidence for prices, liquidity, supply, wallet state, provider health, validator state, risk, fees, software versions, or other changing facts.

## Source-of-truth documents

- [`docs/LANGGRAPH_ROADMAP.md`](./docs/LANGGRAPH_ROADMAP.md) — authoritative Roberta roadmap/status.
- [`docs/LEARNING_SYSTEM.md`](./docs/LEARNING_SYSTEM.md) — Learning System phase/authority map.
- [`docs/PYRAMID_CURRICULUM.md`](./docs/PYRAMID_CURRICULUM.md) — Pyramid capability/stage/exam contract.
- [`docs/ROBERTA_SOURCE_MASTERY_PLAN.md`](./docs/ROBERTA_SOURCE_MASTERY_PLAN.md) — source-specific mastery contract and MB4E mapping.
- [`docs/PYRAMID_TARGETED_PRACTICE.md`](./docs/PYRAMID_TARGETED_PRACTICE.md) — remediation/practice/retention gates.
- [`docs/PYRAMID_PROVENANCE_MIGRATION.md`](./docs/PYRAMID_PROVENANCE_MIGRATION.md) — accepted MB4E legacy provenance migration.
- [`docs/PYRAMID_DASHBOARD.md`](./docs/PYRAMID_DASHBOARD.md) — Learning Command Center read-only telemetry.
- [`docs/learning_sources/README.md`](./docs/learning_sources/README.md) — static source registry.
- [`docs/ENGINEERING_WORKFLOW.md`](./docs/ENGINEERING_WORKFLOW.md) — repository-authoritative engineering workflow.

## Authority rules

1. Fresh accepted CMIS/provider evidence overrides books, RAG, checkpoints, Pyramid training, and remembered live values for freshness-sensitive state.
2. Missing evidence remains unknown/unavailable; it is never converted into zero or a model guess.
3. Proof Score remains separate from market risk.
4. Source text, expected answers, grader notes, practice questions, and generated lessons are not self-authorizing truth.
5. Cross-chain evidence keeps chain-specific provenance.
6. Human approval is exact and non-reusable.
7. Training success does not imply wallet or execution permission.

## Installation and tests

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,deepseek]'
python -m pytest -v -m 'not live and not cmis_live'
```

## Pyramid commands

Current accepted commands include:

```text
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
```

## Controlled execution boundary

No accepted Roberta or Pyramid capability authorizes transaction signing, broadcasting, custody, live trading/swaps, bridge value transfer, autonomous value movement, or broad delegated wallet authority.

**Roberta coordinates and learns under evidence boundaries. CMIS verifies changing blockchain facts. Controlled Execution remains locked.**
