# ROBERTA Roadmap Reconciliation — 2026-09-03

This reconciliation records the current ROBERTA state against accepted CMIS capability and the active cross-chain evidence gates. It does not create a new fact authority, promote unverified bridge claims, or change execution authority.

## Current accepted platform

- ROBERTA uses the canonical path `User / transport -> ROBERTA -> Chain Scout -> CMIS -> provider/source`.
- Instant X1 Scan v3 is accepted through X1 Scout.
- Burn Intelligence is accepted through X1 Scout.
- Discovery Intelligence is accepted through X1 Scout.
- WHAT CHANGED? v1 is accepted.
- CMIS 1.17 field-scoped freshness is accepted and presented without ROBERTA recomputation.
- CMIS 1.18 Concentration Warning Intelligence is accepted end-to-end through X1 Scout and the Canonical ROBERTA Decision Object.
- Human and Machine ROBERTA preserve the same warning evidence.
- Push warning delivery remains unauthorized.
- Controlled Execution remains unauthorized.

## Cross-chain / Warp state

ROBERTA Issue #314 remains OPEN and BLOCKED. It must not promote live Warp bridge claims yet.

CMIS has accepted the structural foundations for cross-chain provenance and bridge-route qualification, and has now observed official Warp same-origin GET endpoints from the official X1 bridge application. However, deterministic response-body semantics are still missing. CMIS #407 is therefore OPEN and remains the flagship evidence gate.

Observed official endpoints include:
- `https://app.bridge.x1.xyz/api/bridge/config`
- `https://app.bridge.x1.xyz/api/bridge/guardians`
- `https://app.bridge.x1.xyz/api/bridge/tvl?chain=sol&token=<token>`

PR #427 proves endpoint provenance and HTTP 200/JSON metadata, not route/backing/custody semantic truth. PR #426 is a separate bounded structural account-capture slice and also does not qualify Warp by itself.

ROBERTA must continue to preserve:

```text
live_warp_fact_authority=false
bridge_execution_authorized=false
execution_authorized=false
```

## Corrected repository state

- ROBERTA PR #310 was closed as stale/superseded because the accepted freshness adoption already merged through PR #301 and later reconciliation.
- The mirrored `ROBERTA_CMIS_SOURCE_SYNC_BASELINE.md` was refreshed in both public repos with the same content blob.
- CMIS #407 was reopened because its explicit semantic acceptance gate had not actually passed.

## Next sequence

1. Do not implement live Warp promotion in ROBERTA yet.
2. Let CMIS finish #407 semantic acceptance first.
3. CMIS then advances #409 Bridge Supply + 24h/7d/30d Inflow/Outflow Intelligence.
4. CMIS then advances #410 Bridge -> XDEX Utilization Intelligence.
5. Once CMIS exposes an accepted public bridge service with Scout reliance, implement ROBERTA #314 through X1 Scout without recomputing bridge facts.

The immediate ROBERTA job is therefore **hold the boundary and stay synchronized with CMIS**, not invent a parallel bridge intelligence path.

`execution_authorized=false`
