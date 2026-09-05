# Current ROBERTA Project Status

Current reconciliation: **2026-09-05**.

Read in this order:

1. `../ROBERTA_CMIS_SOURCE_SYNC_BASELINE.md` — synchronized ROBERTA ↔ CMIS authority/status checkpoint.
2. `LANGGRAPH_ROADMAP.md` — authoritative living ROBERTA roadmap.
3. `CHECKPOINT_2026-09-05_FOUR_REPOS.md` — four-repository checkpoint for this reconciliation.
4. Earlier dated reconciliation/status files — historical snapshots only.

## Current ROBERTA state

Accepted on public/protected main:

- ROBERTA Opinion v1;
- Scout-first X1 Asset Intelligence;
- ROBERTA Claim Integrity v1 for X1 asset-intelligence synthesis;
- X1 Compare Claim Integrity with per-side freshness/risk boundaries and pair-history limitations;
- Human ROBERTA evidence-first presentation and the canonical decision layer;
- accepted X1 Scan, Burn, Discovery, WHAT CHANGED?, field-scoped freshness, and pull-only Concentration Warning consumption through X1 Scout.

**Next ROBERTA Truth Gate:** standalone History, followed by Burn, Discovery, and the remaining specialist products.

## CMIS dependency checkpoint

### X1.Ninja liquidity semantics

Accepted upstream:

- PR #465 — five verified same-fact liquidity revaluations across five pools; `liquidity_fact_time_verified=true`;
- PR #466 — current exact Warp USDC reserve backing for USDC.X;
- PR #468 — current `x1_current_usdcx_usd_equivalence/v1` live gate; dedicated equivalence workflow passed.

Still open:

- PR #470 — final five-pool X1.Ninja USD-liquidity semantic proof;
- Issue #459 — later liquidity/rolling-24h freshness promotion.

ROBERTA must preserve `x1_ninja_liquidity_usd_semantics_verified=false` and `liquidity_freshness_verified=false` until those exact CMIS gates pass.

### Cross-chain / Warp

Accepted upstream:

- #409 Bridge Supply + Flow Intelligence;
- PR #467 `bridge_to_xdex_utilization/v1` foundation and verified wSOL.X XDEX program-family pool universe.

Current final #410 gate:

- PR #469 remains open;
- its exact-head 24h XDEX activity-window proof passed;
- its comparable wSOL.X USD value-basis proof passed;
- its dedicated Bridge-to-XDEX Final workflow passed.

ROBERTA #314 remains blocked until PR #469 is merged/reconciled **and** CMIS separately promotes a public-service / Scout-reliance contract that ROBERTA may consume.

### Web discovery

CMIS PRs #472, #474, and #476 are accepted internal discovery foundations. Issue #477 is active for bounded operator-controlled passive X1 Explorer browser capture. Discovery output remains `DISCOVERED`, not verified ROBERTA market/blockchain truth.

Canonical authority remains `User / transport -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider / verified source`.

`execution_authorized=false`
