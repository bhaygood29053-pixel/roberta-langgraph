# ROBERTA ↔ CMIS Source Sync Baseline

Last reconciled: 2026-09-08 23:15 America/New_York

This is the mirrored cross-project checkpoint for accepted public/protected state. The four-repository authority baseline remains ROBERTA public/protected + CMIS public/protected; `roberta-eval` is tracked separately as an independent evaluation consumer and does not become an authority layer.

## Authority invariant

`User / transport -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider / verified source`

- ROBERTA owns orchestration and final synthesis.
- Chain Scouts consume and interpret accepted CMIS contracts.
- CMIS owns deterministic facts, freshness, evidence, Proof Score, risk, history, bridge evidence, and provider semantic verification.
- The Evaluation Laboratory measures behavior and may propose remediation; it does not manufacture provider truth or silently modify production authority.
- Open PR evidence is not accepted truth.
- Missing evidence remains unknown/unavailable.
- `execution_authorized=false`.

## Observed heads before this documentation reconciliation

```text
ROBERTA public      83aaf290c665f268fb7966e91f3d8177e4c111fd
ROBERTA protected   91617f8091e7f69094f511956df3481d47f8f66c
CMIS public         1c791eca48b3e9687daac4f5a22db8061e4ced88
CMIS protected      d79b684981bd431f1add5a40fc529cc5d6487720
ROBERTA eval        be1e37267081b8daa5b17c41a4d4575661517622
```

These SHAs are the repository heads observed immediately before writing this reconciliation; the documentation commits created by this update advance the affected `main` branches afterward. Accepted protected ROBERTA runtime code remains the pre-#90 implementation boundary; PR #90 remains open/unaccepted and must not be treated as accepted runtime behavior.

## ROBERTA accepted state

Accepted:

- Opinion v1 and Human Intelligence Experience v1;
- Claim Integrity through the current warning/early-warning surface;
- Instant X1 Scan v6;
- trade price-impact, Large-Trade Discovery, cross-chain provenance / Bridge-to-XDEX, and Regulatory Intelligence consumption;
- public #401 + protected #86 stateless/threaded bridge compatibility;
- Evaluation Telemetry v2 through public #405, with material-first service claim priority through #406;
- website progressive evidence disclosure and read-only ROBERTA-only routing.

## Live evaluation checkpoint

The independent Evaluation Laboratory now has a real live baseline:

```text
live-smoke-004
runtime OK:         20 / 20
PASS:               8
EVIDENCE_REQUIRED:  12
FAIL:               0
```

Fully gradeable on XNT and AGI:

- `asset_lookup`;
- `discovery_intelligence`;
- `instant_x1_scan`;
- `market_report`.

The 12 blocked cases are now classified by accepted LAB #21/#22 logic as:

```text
current_x1_evidence_unavailable
-> current_x1_evidence_delegation_gap
-> bhaygood29053-pixel/roberta-core
-> roberta_oracle_evidence_delegation
```

They remain `EVIDENCE_REQUIRED`, not factual FAIL, while being qualification-blocking product-defect candidates.

## Evaluation / protected ROBERTA state

The Evaluation Laboratory is **PAUSED BY OWNER**.

Protected Issue #89 / PR #90 remains **OPEN / UNACCEPTED** and is preserved as historical remediation work. It is not an active product blocker and must not be merged, validated further, or used to trigger `live-smoke-005` solely from the paused eval program.

The preserved live baseline remains 20/20 runtime OK, 8 PASS, 12 EVIDENCE_REQUIRED, 0 FAIL.

## CMIS

Accepted:

- capability contract `1.27.0`;
- Instant X1 Scan v6 and universal `cmis_response_freshness/v1`;
- cross-chain / Warp promotion through Bridge-to-XDEX and cross-chain asset provenance;
- trade price-impact and Large-Trade Discovery;
- freshness-aware Regulatory Evidence;
- internal CMIS Web Discovery stack through X1 Agents Radio structured discovery, direct RPC corroboration, and program/upgrade semantic verification.

Roadmap boundary changes remain:

- XONE/XNT Conversion Intelligence is **RETIRED / HISTORICAL** by Issue #628 / merge #629. Existing evidence remains auditable; there is no active lead-recovery or public-service/X1-Scout promotion path.
- X1Scroll historical fallback #458 / draft PR #549 is **ON HOLD**. The X1Scroll API key is unavailable; do not merge or promote until the key is available and the exact live gate passes.
- Provider-gap research #30, FortiBlox fact-time qualification #567, delayed-departure research, Theo transport work, and related historical-provider investigations remain parallel and fail closed until separately accepted.

## Evaluation Laboratory

- LAB #21 Live Evidence-Backed Evaluation v1: accepted.
- LAB #22 Live Qualification Diagnostics v1: accepted.
- Telemetry v2 factual grading: accepted.
- material claim relevance checks: accepted.
- current-X1 evidence delegation diagnosis: accepted through PR #51.
- roadmap baseline checkpoint: accepted through PR #52.

The Laboratory remains an evaluator, not a source of provider truth or production authority.

## Next synchronized sequence

1. keep Evaluation Laboratory work paused and preserve PR #90 unaccepted;
2. resume ROBERTA X1 productization under #246;
3. reconcile stale/superseded public issues before treating them as unfinished capability;
4. review #280 only for residual Instant Scan product-view gaps after Human Intelligence Experience v1;
5. continue CMIS provider-gap / FortiBlox freshness work separately from ROBERTA product work;
6. keep Learning Plane scheduling as a bounded supporting track and Telegram as lower priority;
7. keep `execution_authorized=false`.

## Protected cores

Public roadmap/evidence changes do not silently mutate protected runtime behavior. Protected implementation changes remain separately reviewed and merged.

`execution_authorized=false`
