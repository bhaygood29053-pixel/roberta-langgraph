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
ROBERTA public      4c872b4ac9fb25dda0994632e9e2f7dc4cc8cdfc
ROBERTA protected   18c6d82377876c0627edb741e5c36f1f339dbbdc
CMIS public         e2a53c94f481ecec4a4f9e1e7051684203e32299
CMIS protected      9cf490f55eeee12e109343b50b1642a1f15854ff
ROBERTA eval        ee624173a1af899a3290b456fb4056ef2e5e35bb
```

Documentation reconciliation commits may advance these heads after this checkpoint.

## ROBERTA

Accepted:

- Opinion v1 and Claim Integrity through the current warning/early-warning surface;
- Instant X1 Scan v6;
- Human Intelligence Experience v1;
- trade price-impact, Large-Trade Discovery, cross-chain provenance / Bridge-to-XDEX, and Regulatory Intelligence consumption;
- Evaluation Telemetry v1;
- public ROBERTA #401 + protected `roberta-core` #86 stateless/threaded bridge compatibility.

Current operational gate:

- synchronize the five operational repositories and assembled runtimes;
- rerun the 20-case LAB #21 live smoke plan;
- classify results with LAB #22;
- fix confirmed defects service-by-service, rerun, and promote confirmed recurring defects into LAB #15 regression memory.

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
- Next operational proof is the repaired-runtime 20-case live rerun; no live-quality PASS should be claimed before those results exist.

## Protected cores

Public roadmap/evidence changes do not silently mutate protected runtime behavior. Protected implementation changes remain separately reviewed and merged.

`execution_authorized=false`
