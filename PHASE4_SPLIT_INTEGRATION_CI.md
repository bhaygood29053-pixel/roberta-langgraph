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

## Source-removal gate

Protected ROBERTA implementation must remain in public Git HEAD until Phase 4 is
complete. Public source removal is a later phase and may begin only after the
split integration gate is green and stable.

The authority chain remains:

**User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider**

No execution, signing, broadcasting, custody, autonomous value movement, new
fact authority, or new service promotion is authorized by Phase 4.
