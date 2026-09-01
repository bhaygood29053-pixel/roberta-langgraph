# ROBERTA Project Status — 2026-09-01

## Executive status

ROBERTA — Verified On-Chain Intelligence is in active X1 productization. Public `main` is at `9b3de1de8ba5033df046657fc936bee8d496c6a3` at this reconciliation. Instant X1 Scan and first-class X1 Compare are accepted through the canonical Roberta -> X1 Scout -> CMIS authority path. The previous dated status statement that CMIS dependency remained at `1.12.0` is superseded; the accepted CMIS capability boundary is `1.13.0`.

The public-shell/private-core migration is complete. Protected orchestration remains in `roberta-core`. Controlled Execution remains locked/not started.

## Accepted X1 product state

Accepted on public `main`:

- X1 Scout adoption of CMIS `instant_x1_scan/v1` with exact capability validation and no direct provider shortcut;
- deterministic Instant X1 Scan product projection with unknown/unverified values preserved and Proof Score kept separate from risk;
- deterministic `x1_compare/v1` product contract;
- first-class Compare workflow using two validated Instant X1 Scan product views;
- optional full-history comparison uses one capability-gated CMIS `historical_compare(mode="all_available_pair")` request only for explicit full/entire/lifetime-history intent;
- Human ROBERTA + Machine ROBERTA two-face product roadmap under one canonical decision/evidence layer;
- planned BURN workflow consumption of CMIS burn amounts and 24h/7d/30d period-over-period changes without local recomputation;
- Learning System Phases 1-10, autonomous source-grounded Learning Plane, mastered-run replay protection, and authoritative read-only training telemetry.

## Learning Plane operational status

Protected `roberta-core` PR #10 is accepted and adds bounded scheduler admission plus durable restart-safe queue state.

Protected `roberta-core` PR #11 remains open/mergeable for deterministic one-cycle worker orchestration. Its current scope is deliberately bounded: it is not an always-on daemon and does not yet wire the production autonomous-training controller as the default worker. Cooperative budget checkpoints, production controller integration, and broader background scheduling/load-throttling remain later gates.

## Active product dependencies

### CMIS burn intelligence

CMIS has accepted deterministic burn metrics, verified scanner coverage wiring, and deterministic circulating-supply evidence on `main`. Historical burn-time valuation remains pending in CMIS PR #377. ROBERTA must not expose burn valuation as accepted truth until the CMIS layer and a valid X1 Scout consumption contract are accepted.

### Discovery / first observation

CMIS public PR #365 plus protected `cmis-core` PR #6 remain pending for `x1_discovery_ledger/v1`. Until accepted, ROBERTA must not claim complete Discovery Ledger support or promote first-observation semantics beyond currently accepted historical evidence.

### CMIS PR #363 / issue #374

The delayed X1.Ninja departure investigation remains unaccepted. Routed target-leg diagnostics are present on the #363 branch, but no general routed/automated-order classifier is promoted to CMIS `main`. ROBERTA must treat those findings as diagnostic, not product facts.

## Transport status

Native Telegram adapter PR #264 remains pending. Its required boundary remains: Telegram is transport only, owner/private-chat scoped, and routes through ROBERTA/private-core orchestration. It must not select CMIS tools directly or create a direct provider path. No OpenClaw dependency is accepted.

## Current roadmap

1. Build the shared Canonical ROBERTA Decision Object and Human/Machine renderers over accepted Scout/CMIS evidence.
2. Harden the Human X1 experience around SCAN and COMPARE, then add BURN only after CMIS burn valuation/Scout gates are accepted.
3. Add WHAT CHANGED?, Discovery, and Early Warning only on accepted CMIS Discovery/history evidence; do not invent local historical facts.
4. Complete bounded Learning Plane one-cycle orchestration and cooperative resource checkpoints before any always-on background scheduler.
5. Continue Telegram as a Roberta-owned transport if its security/authority gates pass.
6. Build X1 ecosystem/network brief workflows from accepted CMIS/Scout facts.
7. Keep Solana as a secondary read-only maintenance/portability track; no X1 capability inheritance.
8. Keep Controlled Execution locked/not started.

## Cross-project authority rule

Human ROBERTA and Machine ROBERTA may render the same accepted decision evidence differently, but neither becomes a second fact engine. Fresh chain/market facts remain behind X1 Scout -> CMIS -> verified source. Missing evidence stays unknown.

## Safety boundary

`execution_authorized=false`. No Learning Plane result, Human/Machine renderer, Scout result, CMIS result, risk result, Proof Score, alert, pre-trade PASS, transport message, or human approval authorizes transaction construction, signing, broadcasting, custody, trading, bridge movement, or autonomous value movement.

## Live status — 2026-09-01 11:20 America/New_York

- Repository: `bhaygood29053-pixel/roberta-langgraph`
- Current main head observed before this status commit: `5a8964a59f053c400eafeceb128f5548cf5f1057`
- PR #295 X1 Burn Intelligence hardening: **OPEN / CLEAN / CI GREEN**
- CMIS #363 delayed departure evidence: **UPSTREAM LIVE EVIDENCE IN PROGRESS**
- CMIS Discovery #365 + `cmis-core` #6: **BLOCKED BY PRIVATE CI**
- `roberta-core` #11 one-cycle orchestration: **OPEN / PRIVATE CI FAILING**
- Telegram #264: **OPEN / DIRTY / NON-MERGEABLE**
- OpenClaw: **NOT ACCEPTED**
- Execution authorization: **FALSE**
