# ROBERTA ↔ CMIS Source Sync Baseline

Last reconciled: 2026-09-08 22:33 America/New_York

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

## Repository heads at this reconciliation

```text
ROBERTA public      b023bce04b0426ff71d66a8c1023cf428a86e60b
ROBERTA protected   f6fdab139b3573939b66ef4a934bb4b59bd362ee
CMIS public         4778da694a3a735c946908fef08bec3664c36107
CMIS protected      9cf490f55eeee12e109343b50b1642a1f15854ff
ROBERTA eval        9fb6cc488b169e00a9654f8a70bdf1b2a520e3dd
```

Repository heads above include documentation-only reconciliation commits. Accepted protected ROBERTA runtime code remains the pre-#90 implementation boundary; PR #90 remains open/unaccepted and must not be treated as accepted runtime behavior.

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

## Active protected ROBERTA gate

Protected Issue #89 / PR #90 is the current production remediation.

PR #90 adds deterministic current-X1 evidence delegation enforcement. It remains **OPEN / UNACCEPTED** at head `ba9a26a75367b352cc6603f0be6d062fe92dcc99` after a first executable targeted run produced 5 PASS / 1 FAIL and exposed one historical-compare classifier miss. That exact miss has been patched, but the corrected head still requires targeted/full package validation plus pinned-public-shell compatibility before merge.

GitHub Actions failures that execute zero steps are not accepted as a substitute for executable validation and are not treated as product test failures.

After #90 acceptance, the exact next live proof is `live-smoke-005` using the same preserved 20-case plan.

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

1. validate and, only if accepted, merge protected PR #90;
2. synchronize all five operational repositories/runtimes;
3. run `live-smoke-005` using the exact 20-case plan;
4. compare against the preserved 8/12/0 baseline;
5. close protected #89/public #404 only on live proof;
6. promote only confirmed recurring/replayable defects to LAB #15 Regression Memory.

## Protected cores

Public roadmap/evidence changes do not silently mutate protected runtime behavior. Protected implementation changes remain separately reviewed and merged.

`execution_authorized=false`
