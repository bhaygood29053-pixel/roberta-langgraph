# Phase 4 — ROBERTA Split Integration / CI

Status: **COMPLETE**

Phase 4 hardened the Phase 3 private-core cutover before any protected public
implementation is removed.

## Completion gates

The final source-stripped/private-core runtime proved:

1. `roberta-private-core==0.2.0` and `cmis-private-core==0.2.0` install into a clean split runtime.
2. Both private facade contracts match their public adapters.
3. Public/private CMIS service and chain surfaces match exactly.
4. CMIS HTTP authentication fails closed when credentials are absent.
5. User -> ROBERTA -> X1 Scout -> CMIS HTTP -> private CMIS runtime succeeds.
6. User -> ROBERTA -> Solana Scout remains explicit/fail-closed while its provider gate is disabled.
7. Solana does not fall through to X1 or manufacture unsupported facts.
8. No public transition fallback is used.
9. Execution authorization remains false.
10. Machine-readable validation evidence is emitted by CI.
11. Every promoted CMIS runtime service is exercised through the source-stripped/private-core HTTP runtime.
12. The dedicated Phase 4 gate passes from merged `main`.

## Final validation evidence

Merged-main Phase 4 Split Integration Gate:
- run `33249158272` — **SUCCESS**
- ROBERTA main commit: `2e9fb73f0ae6ddd26efa74ecd875b2f6ea2d965d`
- CMIS public runtime baseline: `45551d112e0779343c0d0e50d0d2631efc88f76c`
- artifact: `phase4-split-integration-evidence`
- `PHASE4_PROMOTED_CMIS_SERVICE_SURFACE=PASS`
- `PHASE4_SPLIT_INTEGRATION=PASS`
- `PUBLIC_FALLBACK_USED=FALSE`
- `EXECUTION_AUTHORIZED=FALSE`

Promoted service results:
- `asset_lookup` — ok
- `market_report` — partial
- `rank` — ok
- `historical_compare` — unavailable with no historical fixture
- `tokenomics` — partial
- `risk_check` — partial
- `pre_trade_check` — partial
- `trade_verification` — partial
- `verified_asset_activity` — ok
- `instant_x1_scan` — partial
- `verification_evidence` — unavailable with no persisted evidence fixture
- `concentration_change_intelligence` — unavailable with no persisted intelligence fixture

The partial/unavailable states are expected for deliberately absent evidence.
The gate rejects routing/contract errors and recursively rejects any
`execution_authorized=true`.

Merged-main ROBERTA deterministic regression:
- run `33249158273` — **SUCCESS**

## Safety state

The authority chain remains:

**User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider**

No execution, signing, broadcasting, custody, autonomous value movement, new
fact authority, or new service promotion was authorized by Phase 4.

## Source-removal readiness

The Phase 4 source-removal readiness gate is now **SATISFIED**.

Protected ROBERTA implementation is still present in public Git HEAD by design.
Its removal belongs to the next migration phase. Historical Git cleanup remains
separate and cannot revoke copies already cloned, forked, cached, or downloaded.
