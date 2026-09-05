# Current ROBERTA Project Status

Current reconciliation: **2026-09-05 19:35 America/New_York**.

Read in this order:

1. `../ROBERTA_CMIS_SOURCE_SYNC_BASELINE.md` — synchronized ROBERTA ↔ CMIS authority/status checkpoint.
2. `LANGGRAPH_ROADMAP.md` — authoritative living ROBERTA roadmap.
3. `CHECKPOINT_2026-09-05_FOUR_REPOS.md` — earlier September 5 checkpoint.
4. Earlier dated reconciliation/status files — historical snapshots only.

## Accepted ROBERTA state

Accepted on public/protected main:

- ROBERTA Opinion v1;
- Scout-first X1 Asset Intelligence;
- ROBERTA Claim Integrity v1 for X1 asset intelligence;
- X1 Compare Claim Integrity;
- standalone X1 History Claim Integrity;
- X1 Burn Claim Integrity;
- X1 Discovery Claim Integrity;
- X1 WHAT CHANGED? Claim Integrity;
- Human ROBERTA canonical evidence/recommendation presentation;
- accepted X1 Scan, Burn, Discovery, WHAT CHANGED?, field-scoped freshness v1, pull-only Concentration Warning, Bridge-to-XDEX utilization, and canonical cross-chain provenance consumption through X1 Scout;
- the public/protected cross-chain path through ROBERTA #314 is complete.

## Current Truth Gate

**Next ROBERTA Truth Gate: Concentration Warning / Early Warning Claim Integrity.**

The previous specialist Truth Gates through WHAT CHANGED? are accepted and must remain single-authority adapters over existing Scout/CMIS evidence, not new fact engines.

## Cross-chain state

ROBERTA #314 is **COMPLETE**.

Accepted lineage now includes:

- CMIS #410 / PR #469 — Bridge-to-XDEX utilization acceptance;
- CMIS #482 / PR #487 + protected `cmis-core` PR #23 — public service and X1 Scout reliance for `bridge_to_xdex_utilization/v1`;
- CMIS #491 / PR #493 + protected `cmis-core` PR #24 — public service and X1 Scout reliance for `cross_chain_asset_provenance/v1`;
- ROBERTA PR #344 — Bridge-to-XDEX adoption;
- ROBERTA PR #345 + protected `roberta-core` PR #50 — canonical provenance preserved for Human and Machine ROBERTA.

The accepted scope is still bounded. ROBERTA must not infer global X1 DEX absence, bridge adoption, backing/solvency, causality, or risk from those facts alone.

## X1.Ninja liquidity / freshness

CMIS #461 is **COMPLETE** through merged PR #470.

That closes the USD-liquidity semantic proof. It does **not** close current freshness.

CMIS #459 remains active through PR #500. At the current PR #500 head `af1478fd1ab9e8e8f02671debae235dff0d27078`, both the dedicated liquidity-freshness workflow and the standard public-shell suite are failing deterministic aggregate-liquidity-freshness coverage.

Therefore ROBERTA must continue to preserve `liquidity_freshness_verified=false` unless and until CMIS accepts a new freshness composition. Rolling 24h volume and rolling transaction freshness also remain unverified.

## Web Discovery

CMIS Web Discovery v1-v11 is complete internally through PR #497.

X1 Explorer, XDEX, and X1.Ninja discovery/reconciliation results remain below CMIS verification. ROBERTA does not call those sources directly and does not convert `DISCOVERED` material into verified market truth.

## Next product-facing intelligence

### ROBERTA #354 — wallet trade + pool price-impact intelligence

Issue #354 is open and depends on CMIS #498.

When upstream `trade_price_impact_intelligence/v1` is accepted, X1 Scout/ROBERTA may preserve exact wallet/transaction/time, trade size, measured-window volume contribution, pre-trade spot price, average execution price, post-trade pool spot price, and next verified trade price.

ROBERTA may explain the deterministic price movement of the **exact AMM pool** when CMIS proves the reserve transition. It must not widen that into whole-market causality, real-world wallet identity, whale/insider/manipulator labels, intent, coordination, automatic risk, or a recommendation without separate accepted evidence.

## Learning / maintenance

Learning System and Learning Plane work remain supporting tracks and do not displace the current X1 intelligence roadmap. Historical/open maintenance issues remain separate from accepted product capability.

`execution_authorized=false`
