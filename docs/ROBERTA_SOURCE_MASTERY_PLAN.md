# Roberta Source Mastery Plan

Last reconciled: 2026-08-25 (America/New_York)

## Purpose

Roberta does not assume that every source must traverse all 20 global Pyramid capability levels. A source-specific mastery plan analyzes the complete source, maps only the materially supported capabilities into a sequential source-learning program, explicitly excludes unrelated capabilities, and freezes that plan before source-mastery progress continues.

The 20-level Pyramid remains the reusable **global capability taxonomy**. A source mastery plan is the source-specific route through that taxonomy.

## Canonical plan contract

For a source-aware curriculum, the frozen plan lives inside the validated curriculum package:

```text
curricula/<curriculum_id>/source_mastery_plan.json
```

Current contract:

```text
contract = roberta-source-mastery-plan/v1
version = 1.0.0
```

A valid plan binds at minimum:

```text
curriculum_id
source_key
source_title
planner
planner_basis
exam_questions_per_stage = 300
coverage_complete = true
source_capstone_required
stages[]
excluded_capability_levels[]
plan_hash
```

Every source stage contains:

```text
stage                 # contiguous source ordinal 1..N
capability_level      # one unique global Pyramid capability
capability_name
domain
source_chapters[]
rationale
```

Required and excluded capabilities together must account for all 20 global capability levels, without overlap. A plan with incomplete coverage, duplicate capability mappings, invalid stage order, or a mismatched content hash fails closed.

## Runner and ledger behavior

The source-aware Pyramid runner consumes the frozen plan directly.

When a run is first bound to a plan:

- the plan contract/content is validated;
- the plan hash is stored with the source-mastery run;
- later plan drift is rejected rather than silently changing the course of an active run;
- source-stage progress is recorded separately from legacy global-level progress;
- sequential source stages may legally map to non-contiguous global capabilities;
- historical pre-plan results are mapped into source-stage history without rewriting their original result bytes or timestamps.

The ledger therefore distinguishes:

```text
source-stage progress        -> progress through one exact source plan
global capability progress   -> reusable capability achievement across sources
```

A source stage being passed does not imply that every lower-numbered global capability is globally mastered when the source plan skips unrelated capabilities.

## Canonical stage exam contract

Every new required source-stage attempt uses:

```text
300 total questions
249 ordinary
50 integrity
1 Boss, last
```

Historical 1,000-question Level 1/2 results remain immutable audit history. They are reconstructed only through explicit legacy workflows and are not reinterpreted as 300-question attempts.

## Mastering Blockchain, Fourth Edition plan

Current deterministic planner:

```text
roberta-mb4e-source-mastery-planner/v2
```

Curriculum:

```text
mastering_blockchain_4e_2023_book01
```

Source key:

```text
mastering_blockchain_4e_2023
```

Required source stages: **14**.

| Stage | Capability | Source chapters |
| ---: | --- | --- |
| 1 | 1 — Fundamentals | 1, 2 |
| 2 | 2 — Blockchain Mechanics | 1, 5, 6, 9, 13, 14 |
| 3 | 3 — Transactions | 6, 9, 13, 14 |
| 4 | 4 — Cryptography | 3, 4, 18 |
| 5 | 5 — Smart Contracts | 8, 11, 12 |
| 6 | 6 — Tokenomics | 15 |
| 7 | 7 — Liquidity | 21 |
| 8 | 8 — Market Structure | 21 |
| 9 | 9 — DeFi | 21 |
| 10 | 10 — Advanced DeFi | 19, 21 |
| 11 | 11 — On-chain Analysis | 7, 10, 12 |
| 12 | 13 — Risk Reasoning | 18, 19, 21 |
| 13 | 14 — Adversarial Analysis | 19 |
| 14 | 17 — Cross-chain Reasoning | 17, 19, 21 |

Explicitly excluded from this source:

```text
12 Wallet Relationships
15 Evidence Forensics
16 Intelligence Synthesis
18 Complex Investigations
19 Red-Team Mastery
20 Grandmaster
```

These exclusions do not say those capabilities are unimportant. They mean *Mastering Blockchain, Fourth Edition* is not forced to prove material it does not teach deeply enough merely to reach a fixed Level 20 endpoint.

## Current MB4E curriculum-build state

Accepted source-grounded exercise-bank construction is present through **Stage 6 / Tokenomics**:

- Stage 1 — historical Fundamentals curriculum/provenance foundation;
- Stage 2 — Blockchain Mechanics, 1,206-question bank;
- Stage 3 — Transactions;
- Stage 4 — Cryptography, 415-question bank;
- Stage 5 — Smart Contracts, 493-question bank;
- Stage 6 — Tokenomics, 493-question bank.

Stages 7-14 and the final source capstone require separate accepted implementation/build milestones.

**Bank availability is not mastery.** A source stage is mastered only through the source-plan-bound training ledger and its accepted stage pass rules. The source itself is mastered only after every required stage and the required final source capstone pass.

## Dashboard behavior

The Learning Command Center reads the same source-plan/source-stage model. It does not invent a fixed 20-stage source denominator.

The read-only UI may show:

- source title;
- required source-stage count;
- mastered-through/current source stage;
- mapped global capability;
- source chapters and page ranges;
- what is being learned from each chapter;
- run/history/accuracy/failure telemetry;
- source-capstone outstanding state.

The dashboard cannot mutate the plan, ledger, source approval, Learning System retention, CMIS/provider state, or execution authority.

## Authority boundary

Source-mastery planning and Pyramid performance remain static learning/training state. They cannot override fresh Scout -> CMIS -> Provider evidence for current blockchain or market facts.

A source plan does not authorize HXMP writes, general verified-lesson retention, governance mutation, wallet actions, signing, broadcasting, trading, custody, bridge transfer, or Controlled Execution.
