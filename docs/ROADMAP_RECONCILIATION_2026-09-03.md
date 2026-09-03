# ROBERTA Roadmap Reconciliation — 2026-09-03

This reconciliation records the current ROBERTA state against accepted CMIS
capability and the active Warp / cross-chain evidence gates.

It does not create a new fact authority, promote unverified bridge claims, or
change execution authority.

## Current accepted platform

- ROBERTA uses the canonical path
  `User / transport -> ROBERTA -> Chain Scout -> CMIS -> provider/source`.
- Instant X1 Scan v3 is accepted through X1 Scout.
- Burn Intelligence is accepted through X1 Scout.
- Discovery Intelligence is accepted through X1 Scout.
- WHAT CHANGED? v1 is accepted.
- CMIS 1.17 field-scoped freshness is accepted without ROBERTA recomputation.
- CMIS 1.18 Concentration Warning Intelligence is accepted end-to-end through
  X1 Scout and the Canonical ROBERTA Decision Object.
- Human and Machine ROBERTA preserve the same underlying CMIS facts/evidence.
- Push warning delivery remains unauthorized.
- Controlled Execution remains unauthorized.

## Cross-chain / Warp checkpoint

ROBERTA Issue #314 remains OPEN and intentionally blocked from live bridge-flow
or utilization adoption.

The old blocker state that treated CMIS #407 as unresolved is superseded.

Accepted CMIS progress now includes:

- #407 / PR #429 — exact official Warp config semantics accepted;
- PR #432 — deterministic `bridge_flow_intelligence/v1` foundation;
- PR #436 — canonical settled Warp events through exact on-chain
  OutgoingMsg/IncomingMsg pairing;
- PR #439 — connected wallet-history response body pinned as corroboration only;
- #437 / PR #440 — current Warp message-universe counter/account closure
  accepted against official config, exact on-chain Config, and the full
  PDA-verified message-account universe.

Current remaining coverage boundary:

```text
retention_deletion_semantics_verified = false
historical_retention_complete_verified = false
requested_60d_window_coverage_verified = false
coverage_complete_verified = false
missing_history_zero_authorized = false

verified_bridged_supply = false
public_service_promoted = false
scout_reliance_promoted = false
execution_authorized = false
```

The active CMIS gate is now **Issue #441**: prove the required 60-day Warp
message-account lifecycle retention for #409.

## ROBERTA boundary during #441

ROBERTA must not:

- calculate its own bridge 24h/7d/30d totals;
- infer missing historical bridge activity as zero;
- reinterpret wallet-history provider status as canonical settlement truth;
- infer bridged supply from token labels or representation names;
- call Warp providers directly as a trust shortcut;
- expose Bridge-to-XDEX utilization before CMIS #410 is accepted;
- authorize bridge execution.

ROBERTA may continue preserving already accepted cross-chain provenance facts,
but live flow/utilization adoption remains gated.

## Corrected sequence

1. **CMIS #441** — prove the required 60-day message-account lifecycle
   retention / requested-window completeness.
2. **Finish CMIS #409** — verified Bridge Supply + 24h/7d/30d current/prior
   Flow Intelligence, with supply and coverage passing separate gates.
3. **CMIS #410** — Bridge-to-XDEX Utilization Intelligence.
4. **ROBERTA #314** — X1 Scout adoption only after CMIS exposes accepted
   public-service / Scout-reliance bridge contracts.

The immediate ROBERTA job is therefore **hold the boundary and stay synchronized
with CMIS while #441/#409 advance**, not create a parallel bridge fact layer.

`execution_authorized=false`
