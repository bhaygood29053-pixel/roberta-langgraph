# CMIS Roadmap Sync — refreshed 2026-09-08

This document is ROBERTA's current CMIS integration snapshot. The authoritative CMIS roadmap remains `bhaygood29053-pixel/cmis/docs/CMIS_PRODUCT_ROADMAP.md`.

## Accepted CMIS surface relevant to ROBERTA

Current CMIS capability contract is `1.27.0`.

Accepted ROBERTA-relevant CMIS surface includes:

- Instant X1 Scan v6;
- universal `cmis_response_freshness/v1`;
- X1 history and exact-mint identity;
- Burn and Discovery Intelligence;
- concentration warning / Early Warning facts;
- Bridge-to-XDEX and cross-chain asset provenance;
- `trade_price_impact_intelligence/v1`;
- provider-scoped `large_trade_discovery/v1`;
- freshness-aware `regulatory_evidence/v1`.

Older 1.18-era capability references are compatibility history, not the current integration target.

## Cross-chain state

Bridge Supply + Flow, Bridge-to-XDEX Utilization, and cross-chain asset provenance are accepted through their public/protected promotion paths and may be consumed by X1 Scout only within their verified route/program-family scope.

The earlier #482 / ROBERTA #314 release dependency is complete and is no longer an active blocker.

## X1.Ninja liquidity / freshness state

The earlier #461/#470 semantic proof and #459 rolling-freshness blockers are historical. Their accepted results are incorporated into the later CMIS scan/freshness stack through 1.27 and Instant X1 Scan v6.

## CMIS Web Discovery

CMIS Web Discovery is accepted internally through the source-specific stack, including X1 Agents Radio:

- #564 / PR #566 — X1 Agents Radio source discovery;
- #568 / PR #569 — `x1_agents_radio_structured_discovery/v1`;
- #571 / PR #572 — `x1_agents_radio_rpc_corroboration/v1`;
- #574 / PR #576 — `x1_program_upgrade_semantic_verification/v1`.

Discovery remains subordinate to deterministic verification. Radio application names/categories/frameworks and application IDL/business semantics remain unverified unless separately proven.

## XONE/XNT boundary

XONE/XNT Conversion Intelligence is **RETIRED / HISTORICAL** by CMIS Issue #628 / merge #629. Existing accepted evidence remains auditable, but there is no active XONE/XNT lead-recovery or public-service/X1-Scout promotion gate. Retirement is not proof for or against the existence of a conversion mechanism.

## Current provider-gap hold

CMIS #458 / draft PR #549 (X1Scroll historical transaction fallback) is **ON HOLD** because the required X1Scroll API key is unavailable. Do not merge or promote it until the key exists and the exact live acceptance gate passes.

Other provider-gap work remains fail-closed until separately accepted.

## Safety

Controlled Execution remains locked.

`execution_authorized=false`
