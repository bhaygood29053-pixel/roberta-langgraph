# Roberta ↔ CMIS Source Sync Baseline

Last reconciled: 2026-08-26 (America/New_York)

This file is the compact cross-project synchronization baseline for Roberta documentation. It does not replace `docs/CMIS_CONTRACT.md`, `docs/CMIS_ROADMAP_SYNC_2026-08-17.md`, `docs/LANGGRAPH_ROADMAP.md`, or the canonical CMIS repository contracts.

## Canonical authority path

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

- Roberta owns orchestration, policy coordination, specialist selection, learning coordination, and final synthesis.
- Chain Scouts own chain-specific planning and interpretation; they do not manufacture facts.
- CMIS owns deterministic freshness-sensitive verified facts, evidence, Proof Scores, risk, capability state, historical intelligence, and bounded analysis-only pre-trade calculations.
- Providers remain beneath CMIS.
- Fresh accepted CMIS/provider facts override remembered, checkpointed, RAG/source-mastery, Pyramid, retained-lesson, or conversational live values.
- Missing evidence remains unknown/unavailable and is never converted into zero, false, or an LLM estimate.
- Proof Score remains separate from risk.
- `pre_trade_check` remains analysis-only and preserves `execution_authorized=false`.
- The working `liquidity_scout` namespace may remain during incremental migration as a compatibility identifier only.

## Learning Plane boundary

Roberta's autonomous Learning Plane is accepted on `main` through merged PR #228.

It may ingest an explicitly selected static PDF/Markdown/text source, preserve immutable provenance, build or resume a source-specific curriculum, run canonical exams, perform verified remediation/retention/transfer, reuse curriculum-scoped learned concepts, and complete a final source capstone.

Learning state never becomes a second live-fact authority path.

```text
static source / RAG / Pyramid / Phase 10 retained lesson
  != current market or chain truth
```

The Learning Plane cannot, as a consequence of learning, change Scouts, CMIS contracts, provider authority, production prompts/tools/policies, human-approval semantics, wallet permissions, or execution authority.

Phase 10 verified retention is accepted on `main`. An exact active retained lesson may be classified as `verified_learned_knowledge`, but the accepted core classification has `operational_trust_authorized=false`. No general operational-trust promotion wrapper is accepted.

## Current CMIS/Roberta capability baseline

```text
CMIS capability contract = 1.12.0
Phase 11 intelligence_foundation public_service_promoted = false
Phase 11 intelligence_foundation scout_reliance_promoted = false
```

The separately accepted Phase 12 wrapper is exactly:

```text
service = concentration_change_intelligence
service_contract = concentration_change_intelligence/v1
chain = x1
accepted_conclusion_type = top_account_concentration_change
promotion_scope = cmis_owned_top_account_concentration_change_evidence_by_id
read_only = true
public_service_promoted = true
scout_reliance_promoted = true
execution_authorized = false
```

Solana remains unavailable/non-promoted for this service.

## CMIS 1.10 all-available history adoption

X1 Scout accepts the existing `historical_compare` service's new CMIS 1.10 modes without creating a new Roberta-to-CMIS authority path:

```text
window
all_available
all_available_pair
```

For a two-asset entire/full/lifetime-history request, Roberta copies the exact second user-supplied asset into X1 Scout's `compare_asset` field. X1 Scout then issues one CMIS `all_available_pair` request. Roberta does not independently fetch two histories and recompute a pair result.

Scout reliance on `all_available` / `all_available_pair` is fail-closed. The live CMIS manifest must be contract `>=1.10.0` and X1 `historical_compare` must be callable. For CMIS 1.10/1.11 the legacy stored-observation/non-external-history boundary remains required. For CMIS `>=1.12.0`, X1 Scout requires the accepted verified-provider-price backfill boundary: provider backfill may extend price history only; provider source independence, provider archive completeness, continuous coverage, historical USD-stable peg behavior, and complete asset lifetime remain unverified. Pair mode additionally requires the exact overlapping-history limitation.

CMIS output fields such as `full_asset_lifetime_verified=false` and `continuous_coverage_verified=false` remain authoritative and must be preserved through X1 Scout and Roberta. X1 Scout also projects coverage into presentation metadata; verified partial history must not be described as zero historical coverage.

## Internal non-promoted foundations

Accepted on CMIS `main` and safe for documentation/source synchronization, but not Scout-callable by implication:

- deterministic descriptive concentration-direction classification;
- direct wallet-relationship evidence with explicit non-ownership/non-beneficial-owner semantics;
- concentration-threshold alert evidence.

All remain internal/read-only/non-promoted and do not create public-service, Scout-reliance, behavioral/ownership, risk, or execution authority.

## Current promotion state

There is currently **no accepted next public intelligence/alert service, Scout-reliance promotion, or broader Verified Intelligence promotion**. Any future promotion requires a separate CMIS contract/roadmap acceptance gate and a separate Roberta/Scout adoption-readiness gate.

Learning Plane `verified_learned_knowledge` classification is also not a CMIS/public-service promotion and cannot be used to bypass this gate.

## Execution boundary

Roberta Controlled Execution remains locked/not started. No current source material, Learning System/Pyramid state, retained lesson, learned-knowledge classification, CMIS result, Scout report, Proof Score, risk result, alert state, pre-trade `PASS`, policy decision, or human approval authorizes transaction construction as an execution path, signing, broadcasting, custody, trading, bridge transfer, or autonomous value movement.

## Current Roberta learning baseline

As of this reconciliation:

- Learning System Phases 1-10 are accepted on `main`;
- the historical Phase 10 draft PR #136 is obsolete as an implementation-status signal;
- the autonomous source-grounded controller from PR #228 is merged/accepted;
- Mastering Blockchain 4e prebuilt banks are accepted through Stage 8 / Market Structure;
- MB4E Stages 9-14 and the required final capstone remain outstanding mastery/build work, although the accepted controller may generate missing banks at runtime under its validation contract;
- XenBlocks source PR #141 remains unaccepted because of its exact-byte Phase 1 ingestion blocker;
- Controlled Execution remains locked.

## Core sync rule

**Roberta may learn from static evidence and CMIS may verify changing chain facts, but neither learning nor analysis self-promotes into a new authority boundary. Every public-service, operational-trust, wallet, or execution promotion remains separately gated.**
