# CMIS Roadmap Sync — refreshed 2026-09-05

This document is ROBERTA's current CMIS integration snapshot. The authoritative CMIS roadmap remains `bhaygood29053-pixel/cmis/docs/CMIS_PRODUCT_ROADMAP.md`.

## Canonical hierarchy

`User / transport -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider / verified source`

CMIS remains the deterministic authority for freshness-sensitive facts, evidence, Proof Score, risk, historical intelligence, bridge evidence, and provider semantics. ROBERTA does not recreate those facts.

## Accepted CMIS surface relevant to ROBERTA

CMIS capability contract remains `1.18.0`, including:

- accepted X1 all-available history and exact-mint identity;
- bounded verified-provider price backfill limitations;
- Instant X1 Scan v3;
- Burn Intelligence;
- Discovery Intelligence;
- field-scoped current-market freshness;
- pull-only Concentration Warning Intelligence;
- accepted #409 Warp bridge supply/flow evidence foundation.

## Current X1.Ninja liquidity state

Accepted:

- PR #465: five same-fact revaluation events across five pools;
- PR #466: current Warp USDC reserve backing for USDC.X;
- PR #468: current USDC.X/USD equivalence live gate.

Open:

- PR #470: final five-pool X1.Ninja USD-liquidity semantics;
- Issue #459: later liquidity and rolling-24h freshness promotion.

ROBERTA must not infer X1.Ninja USD-liquidity semantics or liquidity freshness from the accepted prerequisite evidence alone.

## Current cross-chain state

Accepted:

- #407 exact Warp config semantics;
- #441 bounded 60-day lifecycle retention;
- #409 Bridge Supply + 24h/7d/30d Flow Intelligence;
- PR #467 Bridge-to-XDEX utilization foundation and verified wSOL.X XDEX program-family pool universe.

Open:

- PR #469: final #410 24h XDEX activity-window + comparable wSOL.X value basis;
- current exact-head dedicated final workflow is green;
- public-service / Scout-reliance promotion remains separate.

ROBERTA #314 remains queued until those CMIS acceptance/promotion gates are complete.

## CMIS Web Discovery

Accepted internally through v4:

- PR #472 — six-source bounded Web Discovery;
- PR #474 — X1 Explorer structured discovery;
- PR #476 — sanitized X1 Explorer network observation;
- PR #478 — operator-controlled passive one-page browser capture.

Web Discovery remains `DISCOVERED` candidate evidence. It is not a provider-truth shortcut and is not public-service / Scout-reliance promoted.

## Safety

Controlled Execution remains locked.

`execution_authorized=false`
