# CMIS Roadmap Sync — refreshed 2026-09-12

This document is ROBERTA's current CMIS integration snapshot. The authoritative CMIS living roadmap remains `bhaygood29053-pixel/cmis/docs/CMIS_PRODUCT_ROADMAP.md`; the current dated override is `bhaygood29053-pixel/cmis/docs/CMIS_ROADMAP_CHECKPOINT_2026-09-12.md`.

## Accepted CMIS surface relevant to ROBERTA

Current CMIS capability contract is `1.30.0`.

Accepted ROBERTA-relevant CMIS surface includes:

- Instant X1 Scan v6;
- universal `cmis_response_freshness/v1`;
- X1 history and exact-mint identity;
- Burn and Discovery Intelligence;
- concentration warning / Early Warning facts;
- Bridge-to-XDEX and cross-chain asset provenance;
- `trade_price_impact_intelligence/v1`;
- provider-scoped `large_trade_discovery/v1`;
- freshness-aware `regulatory_evidence/v1`;
- wallet-relationship intelligence with observed-transfer/non-ownership boundaries;
- X1 Daily Intelligence Brief inputs/runtime surface;
- Tokenized Equity / RWA intelligence under CMIS 1.30;
- Smart Route Phase 1 `xdex_multi_hop_route_intelligence/v1`;
- Smart Route Phase 2 `xdex_multi_hop_route_snapshot/v1`.

Older 1.18/1.27-era capability references are compatibility/history, not the current integration target.

## Smart Route state

The former CMIS #681 -> X1 Scout -> ROBERTA #444 handoff is complete.

Accepted chain:

`CMIS multi-hop intelligence/snapshot -> X1 Scout projection -> protected ROBERTA Pre-Trade -> Ask ROBERTA / website`

Future cross-DEX evidence or `x1_route_comparison/v1` is not a current beta blocker. Preserve these boundaries:

- candidate route != global route optimality;
- configured venue support != observed cross-DEX execution;
- quote freshness != reserve freshness;
- quoted output != executed output;
- verified fee arithmetic != verified fee business meaning;
- price impact, minimum-received/slippage, and network fee remain evidence-scoped and may be EVIDENCE_REQUIRED;
- `execution_authorized=false`.

## Tokenized Equity / RWA state

CMIS 1.30 Tokenized Equity intelligence is accepted through public/protected CMIS and consumed through the accepted X1 Scout / ROBERTA Machine/Human chain. Human ROBERTA may answer “What exactly am I buying?” only within verified provenance/rights/backing/custody/jurisdiction/transferability evidence boundaries. Missing legal/economic rights evidence remains unknown rather than inferred.

## Cross-chain state

Bridge Supply + Flow, Bridge-to-XDEX Utilization, and cross-chain asset provenance are accepted through their public/protected promotion paths and may be consumed by X1 Scout only within their verified route/program-family scope.

The earlier #482 / ROBERTA #314 release dependency is complete and is no longer an active blocker.

## X1.Ninja liquidity / freshness state

The earlier #461/#470 semantic proof and #459 rolling-freshness blockers are historical. Their accepted results are incorporated into the later CMIS scan/freshness stack and protected runtime hardening.

Protected `cmis-core` has also accepted the latest staged/decoupled liquidity refresh chain through PR #75, including the production MRO activation fix. These fixes do not widen freshness tolerances, provider fact-time claims, source independence, risk semantics, or execution authority.

## CMIS Web Discovery

CMIS Web Discovery is accepted internally through the source-specific stack, including X1 Agents Radio:

- #564 / PR #566 — X1 Agents Radio source discovery;
- #568 / PR #569 — `x1_agents_radio_structured_discovery/v1`;
- #571 / PR #572 — `x1_agents_radio_rpc_corroboration/v1`;
- #574 / PR #576 — `x1_program_upgrade_semantic_verification/v1`.

Discovery remains subordinate to deterministic verification. Radio application names/categories/frameworks and application IDL/business semantics remain unverified unless separately proven.

## Provider-gap state

CMIS #458 / PR #549 remains qualification-only until a credential-backed live X1Scroll archival proof passes. Deterministic CI alone does not authorize production fallback.

FortiBlox price fact-time remains EVIDENCE_INCOMPLETE where field-level semantics could not be proven by the accepted bounded probe. Theo transport remains externally blocked. Longitudinal delayed-departure research remains evidence-waiting rather than a release blocker.

## Product priority

ROBERTA Cohort 001 is now the flagship. New CMIS work should be evidence-driven by a demonstrated user/evidence gap or reliability defect, not by service-count expansion.

## Safety

Controlled Execution remains locked.

`execution_authorized=false`
