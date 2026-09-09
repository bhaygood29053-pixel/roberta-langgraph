# ROBERTA Live Roadmap Checkpoint — 2026-09-08

This checkpoint records the current accepted state and immediate execution order after the first meaningful LAB #21 Telemetry v2 live qualification.

## Current position

ROBERTA is operational and the 20-case XNT/AGI live suite now has a trustworthy pre-fix baseline:

```text
runtime OK:         20 / 20
PASS:               8
EVIDENCE_REQUIRED:  12
FAIL:               0
```

The four fully gradeable service families on both XNT and AGI are:

- `asset_lookup`;
- `discovery_intelligence`;
- `instant_x1_scan`;
- `market_report`.

The six blocked service families are:

- `burn_intelligence`;
- `historical_compare`;
- `pre_trade_check`;
- `risk_check`;
- `tokenomics`;
- `verification_evidence`.

Accepted LAB #21/#22 logic localizes all 12 blocked cases to:

```text
current_x1_evidence_unavailable
-> current_x1_evidence_delegation_gap
-> roberta-core
-> roberta_oracle_evidence_delegation
```

This is a protected orchestration defect candidate, not a Telemetry v2 projection gap and not a factual FAIL.

## Active gate

Protected `roberta-core` Issue #89 / PR #90 is the active production remediation.

PR #90 must enforce this invariant:

> An explicit current/verified X1 evidence request may not finish without a valid current-turn X1 Scout evidence result.

If first-pass orchestration omits X1 Scout, ROBERTA retries once while preserving the exact user objective. If evidence delegation is still absent, ROBERTA fails closed rather than substituting model knowledge or another chain specialist.

Current head: `ba9a26a75367b352cc6603f0be6d062fe92dcc99`.

Current validation evidence:

- private/public package overlay imports: PASS;
- first targeted #89 suite: 5 PASS / 1 FAIL;
- single historical-compare classifier miss identified and patched;
- corrected head still requires a fresh executable targeted/full-suite run;
- pinned-public-shell compatibility remains required;
- GitHub Actions runs that execute zero steps are non-diagnostic and are not acceptance evidence.

## Exact next sequence

1. rerun the targeted #89 regression suite on `ba9a26a75367b352cc6603f0be6d062fe92dcc99`;
2. run the full protected package suite and doctor/build gate;
3. run pinned-public-shell overlay compatibility on that exact head;
4. merge protected PR #90 only if deterministic validation passes;
5. keep Issue #89 open after code merge;
6. synchronize `cmis`, `cmis-core`, `roberta-langgraph`, `roberta-core`, and `roberta-eval` locally and refresh assembled runtimes;
7. run the same exact 20 cases as `live-smoke-005`;
8. grade with LAB #21 and diagnose with LAB #22;
9. compare to the preserved `8 PASS / 12 EVIDENCE_REQUIRED / 0 FAIL` baseline;
10. close protected #89 and public ROBERTA #404 only if live evidence proves the delegation gap resolved;
11. convert only confirmed recurring/replayable defects into LAB #15 Regression Memory.

## Parallel roadmap state

CMIS remains accepted at capability contract `1.27.0` with no new production capability change in this checkpoint.

- XONE/XNT Conversion Intelligence remains retired/historical.
- X1Scroll #458 / draft PR #549 remains ON HOLD until an API key exists and the exact archival live gate passes.
- Telegram PR #264 remains open/unaccepted.
- X1Labs Intelligence Scout PR #190 remains planning-only.
- XenBlocks source PR #141 remains blocked on exact-byte source fidelity.
- protected autonomous-training PR #11 remains separate from the current live-qualification gate.

## Authority boundary

`User / transport -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider / verified source`

The Evaluation Laboratory measures behavior but does not become a production authority layer.

`execution_authorized=false`
