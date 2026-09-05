# CMIS Roadmap Sync — refreshed 2026-09-05

This document is ROBERTA's current CMIS integration snapshot. The authoritative CMIS roadmap remains `bhaygood29053-pixel/cmis/docs/CMIS_PRODUCT_ROADMAP.md`.

## Accepted CMIS surface relevant to ROBERTA

CMIS capability contract remains `1.18.0`, with accepted X1 history, exact-mint identity, Instant X1 Scan v3, Burn Intelligence, Discovery Intelligence, field-scoped freshness, and pull-only Concentration Warning Intelligence.

Cross-chain evidence has now advanced through **completed #410**:

- #409 bridge supply + current/prior 24h/7d/30d flow intelligence;
- verified XDEX program-family wSOL.X pool state;
- bounded 24h XDEX activity-window proof;
- comparable wSOL.X USD value basis;
- final `bridge_to_xdex_utilization/v1` acceptance.

## Current cross-chain release gate

CMIS Issue **#482** is now the only cross-chain release gate before ROBERTA #314.

#482 must expose the already-accepted #410 contract through the public CMIS capability/service boundary and authorize X1 Scout reliance without widening scope or recomputing facts.

ROBERTA #314 may proceed only after #482 is accepted.

## Current X1.Ninja liquidity state

Accepted prerequisites: PRs #465, #466, and #468.

Active:

- PR #470 final five-pool USD-liquidity semantic proof;
- its current repeated-revaluation evidence workflow is still running;
- #459 remains the later liquidity/rolling-24h freshness promotion gate.

## CMIS Web Discovery

v1-v4 is accepted internally. Issue #479 / PR #481 is active for XDEX structured endpoint discovery.

Discovery remains `DISCOVERED` candidate evidence and is not a provider-truth shortcut.

## Safety

Controlled Execution remains locked.

`execution_authorized=false`
