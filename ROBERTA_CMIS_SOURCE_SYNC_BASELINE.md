# ROBERTA ↔ CMIS Source Sync Baseline

Last reconciled: 2026-09-05 (America/New_York)

This is the mirrored cross-project checkpoint for accepted public/protected state. Open PRs remain evidence candidates until merged and reconciled.

## Authority invariant

`User / transport -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider / verified source`

- ROBERTA owns orchestration and final synthesis.
- Chain Scouts interpret accepted CMIS contracts; they do not manufacture chain facts.
- CMIS owns deterministic facts, freshness, evidence, Proof Score, risk, history, burn arithmetic, warning evidence, bridge evidence, and provider semantic verification.
- Missing evidence remains unknown/unavailable.
- Proof Score, warning state, bridge qualification, liquidity fact-time, value equivalence, semantic verification, freshness, and risk remain separate claims.
- `execution_authorized=false`.

## Repository heads at reconciliation start

```text
ROBERTA public      e1ab51fc5a004652274597de297cc96e85132f08
ROBERTA protected   267aa3b1adb1c49ec11ab88ab53c8d2a83515251
CMIS public         9eea8a13f4d19b3c18021c44b62367a3c1bf425b
CMIS protected      e34353c4a4ce90d1f9da7ffb8f62bee4d03d1456
```

Roadmap/documentation reconciliation commits intentionally advance repository heads beyond these checkpoint SHAs.

## ROBERTA accepted state

- Opinion v1: accepted.
- Claim Integrity v1: accepted for X1 asset intelligence and Compare.
- Next ROBERTA Truth Gate: standalone History, then Burn, Discovery, and remaining specialist products.
- Controlled Execution remains locked.

## CMIS #461 / X1.Ninja liquidity state

Accepted on CMIS main:

- PR #465: five same-fact X1.Ninja revaluations across five distinct pools; `liquidity_fact_time_verified=true`.
- PR #466: current exact Warp Solana USDC reserve backing for X1 USDC.X; retained historical message accounts are not treated as current liabilities.
- PR #468: current `x1_current_usdcx_usd_equivalence/v1` live composition; dedicated USDC.X/USD equivalence workflow passed.

Active:

- Issue #461 is reopened until PR #470 completes the five-pool USD-liquidity semantic proof.
- PR #470 may promote `x1_ninja_liquidity_usd_semantics_verified=true` only when fresh current USDC.X/USD equivalence and all five same-fact pool samples pass together.
- `liquidity_freshness_verified=false` remains separate under Issue #459.

## Cross-chain / Warp state

Accepted:

- #407 exact Warp config semantics;
- #441 bounded 60-day message lifecycle retention;
- #409 Bridge Supply + current/prior 24h/7d/30d Flow Intelligence;
- PR #467 `bridge_to_xdex_utilization/v1` foundation and verified wSOL.X XDEX program-family pool-universe state.

Active:

- Issue #410 is reopened because PR #467 explicitly left `issue_410_acceptance_verified=false`.
- PR #469 is the final #410 evidence slice.
- On PR #469's current exact head, the 24h XDEX-program activity-window proof, comparable wSOL.X USD value-basis proof, and dedicated Bridge-to-XDEX Final workflow are green.
- Open PR evidence remains unaccepted until merge/reconciliation.
- ROBERTA #314 remains blocked until PR #469 is merged/reconciled and CMIS separately accepts public-service / Scout-reliance promotion.

## CMIS Web Discovery

Accepted internal foundations:

- #471 / PR #472 — bounded six-source CMIS Web Discovery v1;
- #473 / PR #474 — X1 Explorer structured discovery;
- #475 / PR #476 — sanitized X1 Explorer network observation.

Active:

- Issue #477 — operator-controlled passive X1 Explorer browser capture.

All Web Discovery state remains discovery-only: no automatic CMIS truth, Proof Score, risk, public-service, Scout-reliance, or execution promotion.

## Parallel evidence work

- Issue #444 — complete remaining Instant X1 Scan evidence gaps.
- Issue #459 — promote eligible X1.Ninja + X1 RPC field-scoped freshness.
- Issue #363 — delayed-vault/X1.Ninja research remains parallel and is not the flagship blocker.

`execution_authorized=false`
