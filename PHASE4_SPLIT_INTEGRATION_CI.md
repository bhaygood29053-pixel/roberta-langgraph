# Phase 4 — ROBERTA Split Integration / CI

Status: **IN PROGRESS**

Phase 4 hardens the Phase 3 private-core cutover before any protected public
implementation is removed.

## Primary gate

The public ROBERTA repository owns the cross-repository split validation harness.
The Phase 4 gate must prove the runtime works after protected public
implementation is physically absent from the staged public shells and the
private distributions are installed.

Required checks:

1. `roberta-private-core==0.2.0` and `cmis-private-core==0.2.0` install into a clean split runtime.
2. Both private facade contracts match their public adapters.
3. Public/private CMIS service and chain surfaces match exactly.
4. CMIS HTTP authentication fails closed when credentials are absent.
5. User -> ROBERTA -> X1 Scout -> CMIS HTTP -> private CMIS runtime succeeds.
6. User -> ROBERTA -> Solana Scout remains explicit/fail-closed while the Solana provider gate is disabled.
7. Solana Scout must not fall through to X1 or manufacture unsupported facts.
8. No public transition fallback is used.
9. Execution authorization remains false.
10. A machine-readable evidence artifact is emitted by CI.

## Checkpoint 1

Initial Phase 4 split integration passed in Actions run `33228563613`.

Verified:
- source-stripped public-shell assembly;
- private package ownership and facade contracts;
- public/private CMIS service + chain parity;
- authenticated CMIS capability handshake;
- unauthenticated CMIS access fails closed;
- ROBERTA -> X1 Scout -> private CMIS HTTP path;
- ROBERTA -> Solana Scout provider-gate path;
- Solana did not fall through to X1;
- `PUBLIC_FALLBACK_USED=FALSE`;
- `EXECUTION_AUTHORIZED=FALSE`;
- machine-readable evidence artifact uploaded.

Artifact: `phase4-split-integration-evidence`.

## Checkpoint 2 — promoted service surface

Expanded source-stripped/private-core validation passed in Actions run
`33249072477`.

The gate exercised every promoted CMIS runtime service through authenticated
HTTP:

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
- `concentration_change_intelligence` — unavailable with no persisted
  intelligence fixture

These bounded statuses are expected for deliberately absent evidence. The gate
rejects any routing/contract `error`, requires exact public/private service
surface parity, and recursively asserts that no response grants
`execution_authorized=true`.

Checkpoint 2 also reconfirmed `PUBLIC_FALLBACK_USED=FALSE` and
`EXECUTION_AUTHORIZED=FALSE`.

The remaining Phase 4 completion gate is a successful run of this same workflow
from merged `main`.

## Source-removal gate

Protected ROBERTA implementation must remain in public Git HEAD until Phase 4 is
complete. Public source removal is a later phase and may begin only after the
split integration gate is green and stable on the merged `main` workflow.

The authority chain remains:

**User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider**

No execution, signing, broadcasting, custody, autonomous value movement, new
fact authority, or new service promotion is authorized by Phase 4.
