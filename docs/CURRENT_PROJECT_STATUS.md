# Current ROBERTA Project Status

Current reconciliation: **2026-09-08 America/New_York**.

## Executive status

ROBERTA is operational and the Evaluation Laboratory has now produced its first meaningful live qualification baseline against real XNT/AGI requests:

- runtime: **20 / 20 OK**;
- LAB #21 verdicts: **8 PASS / 12 EVIDENCE_REQUIRED / 0 FAIL**;
- actual live factual failures present: **false**;
- provider truth certified: **false**;
- all-natural-language claims certified: **false**;
- execution authority remains disabled.

The current blocker is no longer bridge transport or Evaluation Telemetry. The 12 unqualified cases are now deterministically localized to a protected ROBERTA orchestration defect: `current_x1_evidence_delegation_gap` / `roberta_oracle_evidence_delegation`.

## Accepted ROBERTA state

Accepted on public/protected main:

- ROBERTA Opinion v1;
- Human Intelligence Experience v1;
- Claim Integrity for Asset Intelligence, Compare, History, Burn, Discovery, WHAT CHANGED?, and Concentration Warning / Early Warning;
- Instant X1 Scan v6;
- Burn, Discovery, WHAT CHANGED?, concentration warning, cross-chain provenance, and Bridge-to-XDEX consumption;
- verified wallet trade + pool price-impact intelligence;
- Large-Trade Discovery;
- GENIUS Act learning layer and bounded live Regulatory Intelligence;
- CMIS 1.27 universal `cmis_response_freshness/v1` adoption;
- conversation-first website with progressive evidence disclosure;
- stateless/threaded bridge compatibility;
- Evaluation Telemetry v2 through public ROBERTA #405 and material-first claim priority through #406;
- Evaluation Laboratory LAB #21/#22, including v2 factual grading and current-X1 evidence-delegation diagnostics through `roberta-eval` PRs #49, #50, and #51.

Controlled Execution remains locked: `execution_authorized=false`.

## Live qualification baseline — live-smoke-004

The preserved pre-fix baseline is `live-smoke-004`.

### Fully gradeable on both XNT and AGI

- `asset_lookup` — 2 PASS;
- `discovery_intelligence` — 2 PASS;
- `instant_x1_scan` — 2 PASS;
- `market_report` — 2 PASS.

### Qualification-blocked, not factual FAIL

Each of the following has 2 `EVIDENCE_REQUIRED`, one for XNT and one for AGI:

- `burn_intelligence`;
- `historical_compare`;
- `pre_trade_check`;
- `risk_check`;
- `tokenomics`;
- `verification_evidence`.

The re-grade through accepted `roberta-eval` PR #51 classifies all 12 as:

```text
reason: current_x1_evidence_unavailable
diagnostic_class: current_x1_evidence_delegation_gap
owner_repository: bhaygood29053-pixel/roberta-core
component: roberta_oracle_evidence_delegation
priority: P1
product_defect_candidate: true
```

This means the final ROBERTA turn lacked a valid current-turn X1 Scout evidence result. It is an orchestration/evidence-delegation defect, not a Telemetry v2 projection defect and not yet a factual answer FAIL.

## Paused remediation — protected #89 / PR #90

Protected `roberta-core` Issue #89 / PR #90 remains **OPEN / UNACCEPTED**, but it is no longer an active product blocker while the Evaluation Laboratory workstream is paused.

The branch contains a candidate deterministic current-X1 evidence-delegation gate, but no further validation, merge, live-smoke rerun, or eval-driven remediation is authorized solely from the paused Laboratory program. Preserve the branch and historical evidence; resume only on an explicit owner instruction or a separately justified production requirement outside the paused evaluation track.

## Evaluation Laboratory

`roberta-eval` is an independent evaluation consumer, not a production authority layer.

Accepted live-evaluation progression:

1. LAB #21 Live Evidence-Backed Evaluation v1;
2. LAB #22 Live Qualification Diagnostics v1;
3. Evaluation Telemetry v2 grading support;
4. material service-claim relevance checks;
5. current-X1 evidence delegation diagnostics;
6. roadmap checkpoint PR #52 recording the 8/12/0 baseline and #89/#90 remediation gate.

No confirmed factual/product FAIL has yet been observed in `live-smoke-004`. The 12 current product-defect candidates are evidence-delegation failures and remain `EVIDENCE_REQUIRED` until a new live run proves the repaired behavior.

## CMIS

CMIS remains accepted at capability contract **1.27.0**.

Current boundaries remain unchanged:

- universal `cmis_response_freshness/v1` accepted;
- Instant X1 Scan v6 accepted;
- cross-chain provenance / Bridge-to-XDEX accepted;
- trade price-impact and Large-Trade Discovery accepted;
- Regulatory Evidence accepted;
- CMIS Web Discovery internal stack accepted through X1 Agents Radio structured discovery, X1 RPC corroboration, and program/upgrade semantic verification;
- XONE/XNT Conversion Intelligence remains retired/historical;
- X1Scroll #458 / draft PR #549 remains **ON HOLD** until an API key exists and the exact live archival gate passes.

## Website

The website on public `main` remains the accepted Human Intelligence Experience v1 conversation surface. No website capability should claim the six currently blocked live-evaluation service families are qualified until the post-#90 live gate proves them.

## Next exact roadmap sequence — Evaluation Laboratory paused

1. keep the Evaluation Laboratory paused; do not advance PR #90, LAB #21/#22, or `live-smoke-005` from the eval program;
2. resume the flagship X1 productization umbrella under public Issue #246;
3. reconcile stale/superseded open tickets such as #234 (normalized identity) and #249 (Instant X1 Scan v1) against the already-accepted current identity and Instant X1 Scan v6 stack before doing new implementation;
4. review #280 against the completed Human Intelligence Experience v1 and current website; retain only product-facing Instant Scan UX gaps that are still real;
5. continue CMIS-backed holder/wallet/provider/network intelligence only through explicit accepted Scout -> CMIS contracts; never add a direct ROBERTA -> provider truth path;
6. keep Learning Plane scheduling/hardening (#275 and protected `roberta-core` PR #11) as a supporting, separately gated track rather than a flagship blocker;
7. keep Telegram PR #264 lower priority until it is explicitly re-prioritized and brought forward to the current runtime/website architecture;
8. keep Controlled Execution locked: `execution_authorized=false`.

## Evaluation workstream — PAUSED BY OWNER

The owner has stopped all active Evaluation Laboratory work.

Effective immediately:

- no new LAB #21 / LAB #22 runs;
- no `live-smoke-005` or later live-smoke runs;
- no eval grading/diagnostics/trend work;
- no LAB #15 regression promotion driven by the paused evaluation track;
- no further PR #90 validation or remediation work solely because of the eval program.

`live-smoke-004` remains preserved as historical evidence at 8 PASS / 12 EVIDENCE_REQUIRED / 0 FAIL.

Protected Issue #89 / PR #90 remains OPEN / UNACCEPTED, but it is paused rather than an active product blocker. It must not be merged or closed unless separately justified outside the paused evaluation workstream or the owner explicitly resumes it.

`execution_authorized=false`
