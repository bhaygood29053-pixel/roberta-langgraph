# ROBERTA ↔ CMIS Source Sync Baseline

Last reconciled: 2026-09-08 (America/New_York)

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
ROBERTA public      3274a9b9be0a7954ddf9d90b6f0890a5135c95c7
ROBERTA protected   d864daf1e70dde7cb1734649efa7a36ccda1aa7f
CMIS public         4778da694a3a735c946908fef08bec3664c36107
CMIS protected      9cf490f55eeee12e109343b50b1642a1f15854ff
ROBERTA eval        9f97bd640c4b85d9a85ce6a15af153f46f428744
```

Documentation reconciliation commits may advance these heads after this checkpoint.

## ROBERTA

Accepted:

- Opinion v1 and Claim Integrity through the current warning/early-warning surface;
- Instant X1 Scan v6;
- Human Intelligence Experience v1;
- trade price-impact, Large-Trade Discovery, cross-chain provenance / Bridge-to-XDEX, and Regulatory Intelligence consumption;
- Evaluation Telemetry v1 plus accepted Evaluation Telemetry v2 factual projection and material-first claim prioritization through public PRs #405/#406;
- public ROBERTA #401 + protected `roberta-core` #86 stateless/threaded bridge compatibility.

Current operational gate:

- `live-smoke-004` is complete: 20/20 runtime OK, 8 PASS, 12 EVIDENCE_REQUIRED, 0 FAIL;
- the 8 PASS cases cover asset lookup, Discovery Intelligence, Instant X1 Scan, and Market Report for both XNT and AGI;
- LAB #22 now localizes the 12 blocked burn/history/pre-trade/risk/tokenomics/verification-evidence cases to protected `roberta_oracle_evidence_delegation`;
- protected Issue #89 / PR #90 is the active remediation gate and remains unaccepted;
- after deterministic package + pinned-shell validation and accepted protected merge, synchronize all five repos/runtimes and run `live-smoke-005`;
- close protected #89/public #404 only on live proof; promote only confirmed recurring/replayable defects into LAB #15 regression memory.

Open/unaccepted work remains non-current truth, including native Telegram PR #264, planning-only X1Labs Intelligence Scout PR #190, and blocked XenBlocks source PR #141.

## CMIS

Accepted:

- capability contract `1.27.0`;
- Instant X1 Scan v6 and universal `cmis_response_freshness/v1`;
- cross-chain / Warp promotion through Bridge-to-XDEX and cross-chain asset provenance;
- trade price-impact and Large-Trade Discovery;
- freshness-aware Regulatory Evidence;
- internal CMIS Web Discovery stack through X1 Agents Radio structured discovery, direct RPC corroboration, and program/upgrade semantic verification.

Roadmap boundary changes:

- XONE/XNT Conversion Intelligence is **RETIRED / HISTORICAL** by Issue #628 / merge #629. Existing evidence remains auditable; there is no active lead-recovery or public-service/X1-Scout promotion path.
- X1Scroll historical fallback #458 / draft PR #549 is **ON HOLD**. The X1Scroll API key is unavailable; do not merge or promote until the key is available and the exact live gate passes.
- Provider-gap research #30, FortiBlox fact-time qualification #567, delayed-departure research, Theo transport work, and related historical-provider investigations remain parallel and fail closed until separately accepted.

## Evaluation Laboratory

- LAB #21 Live Evidence-Backed Evaluation v1: accepted.
- LAB #22 Live Qualification Diagnostics v1: accepted.
- Evaluation Telemetry v2 grading is accepted through `roberta-eval` PR #49; material-claim relevance through PR #50; missing current-X1 evidence delegation classification through PR #51.
- `live-smoke-004`: 20/20 runtime OK, 8 PASS, 12 EVIDENCE_REQUIRED, 0 FAIL.
- Current qualification blocker is protected ROBERTA evidence delegation, not Telemetry v2 projection.
- Next operational proof is `live-smoke-005` after protected #90 is deterministically accepted and synchronized.

## Protected cores

Public roadmap/evidence changes do not silently mutate protected runtime behavior. Protected implementation changes remain separately reviewed and merged.

`execution_authorized=false`
