# Current ROBERTA Project Status

Current reconciliation: **2026-09-08 20:14 America/New_York**.

## Accepted ROBERTA state

Accepted on public/protected main:

- ROBERTA Opinion v1;
- Claim Integrity for Asset Intelligence, Compare, History, Burn, Discovery, WHAT CHANGED?, and Concentration Warning / Early Warning;
- Instant X1 Scan v6;
- Burn, Discovery, WHAT CHANGED?, concentration warning, cross-chain provenance, and Bridge-to-XDEX consumption;
- verified wallet trade + pool price-impact intelligence through public PR #359 + protected `roberta-core` #61;
- Large-Trade Discovery through public PR #361 + protected `roberta-core` #63;
- GENIUS Act Regulatory Intelligence Learning Layer v1 through public PR #364 + protected `roberta-core` #65;
- live CMIS 1.26 Regulatory Evidence adoption through public PR #368 + protected `roberta-core` #69 + reconciliation PR #369;
- CMIS 1.27 universal `cmis_response_freshness/v1` adoption so every public token/service response carries an explicit freshness result, including UNKNOWN/NOT_VERIFIED when proof is incomplete;
- conversation-first public website with saved investigations/evidence panel through PR #374;
- read-only Evaluation Telemetry v1 through public PR #399 / merge `109f91f289c3fd6a2542b1eebca93091d5c0a225`, with protected public-shell compatibility through `roberta-core` PR #85 / merge `13a870195f038865d023280fd3d1277bc9736397`. The telemetry is opt-in, uses the same final graph invocation, exposes only accepted final-message structures, and remains bounded by Claim Integrity;
- stateless/threaded bridge compatibility through public ROBERTA #401 / merge `4c872b4ac9fb25dda0994632e9e2f7dc4cc8cdfc` and protected `roberta-core` #86 / merge `18c6d82377876c0627edb741e5c36f1f339dbbdc`;
- Evaluation Telemetry v2 factual projection through public ROBERTA PR #405 / merge `55608b5f53bb309daa319436dde564b2ca7e1550`, with material-first claim prioritization through PR #406 / merge `3274a9b9be0a7954ddf9d90b6f0890a5135c95c7`. v2 preserves v1, uses only same-turn structured X1 Scout/CMIS evidence, makes no second CMIS/provider query, does not infer claims from prose, and keeps `execution_authorized=false`.

## Regulatory Intelligence

The end-to-end regulatory path is accepted for the initial bounded U.S. GENIUS Act / X1 USDC.X proof case.

ROBERTA preserves exact X1 mint, jurisdiction/framework, current rulemaking state, evidence freshness, primary-law/regulator provenance, applicability state, and bridged-representation dependencies.

`legal_compliance=null`
`legal_advice=false`
`automatic_risk_conclusion_authorized=false`
`execution_authorized=false`

ROBERTA may explain what the verified framework/evidence says and what remains unknown; she may not issue a legal compliance determination.

## Large trades / price impact

Trade price-impact and provider-scoped Large-Trade Discovery are accepted through ROBERTA.

The upstream `cmis-core` PR #41 live Large-Trade → #498 handoff proof is now **ACCEPTED**. Exact live run #7 passed at protected head `9ff63bcac15d9bd7f46868489f444508ed126c06`; PR #41 merged as `f659f53f3d565bd5886dfae3e1a12370100cddc9` and Issue #40 closed completed.

ROBERTA may describe the bounded handoff as proven while preserving its provider-scoped, pool-local, public-wallet-only, non-causal, read-only evidence boundaries.

## Website

The website on `main` is the accepted Human Intelligence Experience v1 conversation surface. PR #394 adds human decision labels, field-specific risk/evidence/freshness presentation, and keyboard-safe progressive evidence disclosure while preserving saved investigations, universal question entry, and ROBERTA-only routing.

This reconciliation adds **Understand Regulations** as the seventh human-friendly service plus a GENIUS Act / USDC.X example. The service routes through ROBERTA and the accepted regulatory intelligence boundary; it does not calculate compliance in the browser and does not bypass X1 Scout → CMIS.

## Human Intelligence Experience v1 — COMPLETE

**ROBERTA #376 — Human Intelligence Experience v1 is COMPLETE.** The full human-response, continuity, evaluation, and website disclosure sequence is accepted without weakening evidence boundaries.

Implementation sequence:

1. #377 Human Response Contract v1 — **ACCEPTED** via PR #384 / merge `8ec6fbf1274543e54c2c04508fe968044c72d989`;
2. protected `roberta-core#72` canonical Human Response Decision Object — **ACCEPTED** via PR #74 / merge `cff1be5bf95c29ac163dc9228bfdf4c1056762dd`;
3. #378 human renderer and Quick / Normal / Deep Dive modes — **ACCEPTED** via public PR #388 / merge `ee52d60079571d349a45299fc524d0ea972412f3` + protected PR #76 / merge `971c49b675b5dee43d5b6d002a86b61a1a951811`;
4. #379 evidence-safe conversational continuity — **ACCEPTED** via public PR #390 / merge `e2045d3243afd2e2b810cb560530bc44f0b6396b` + protected PR #78 / merge `5842e359cb671358638373199a442d800046cc80`;
5. #380 100-scenario learning corpus and response-quality evaluator — **ACCEPTED** via public PR #392 / merge `25641db5a67428b4f32f2158e7402b3208a36865` + protected compatibility PR #80 / merge `002fa78b012699ff661f817b16f8ebf7d5cd563c`;
6. #381 website progressive evidence disclosure + human decision labels — **ACCEPTED** via public PR #394 / merge `c71fe592caf26c900816e1068b672894bd5b9095` + protected compatibility PR #82 / merge `3f503ff508739adceeb0407fd85642cff0f3296e`.

This program builds on the already-accepted answer-first/evidence-aware milestones #33, #45, and #51.

## Evaluation Laboratory integration

`roberta-eval` LAB #21 is accepted via PR #43 / merge `bd42df06d7fa80034a38e875fed96328774460f0`.

New live runs now consume Evaluation Telemetry v2 through `roberta-eval` PR #49 / merge `72b1aa1884966ff4b0cf5204380eb0c91939bc4b`. Material service-claim coverage is enforced through PR #50 / merge `d2decf06386e7eaf41ff0067e46f944755dc4b78`. Missing structured evidence remains unqualified rather than guessed, and bounded PASS still does not certify upstream provider truth or every natural-language sentence.

`roberta-eval` LAB #22 is accepted via PR #46 / merge `7eefde5355e99453f43cb4662226200b156cf7a0`. PR #51 / merge `9f97bd640c4b85d9a85ce6a15af153f46f428744` now distinguishes a missing current-turn X1 Scout result from a claim-projection gap and assigns that defect to protected ROBERTA orchestration.

### Live qualification checkpoint — `live-smoke-004`

The exact 20-case XNT/AGI live run completed with **20/20 runtime OK** and:

- **PASS: 8**
- **EVIDENCE_REQUIRED: 12**
- **FAIL: 0**

Fully gradeable on both XNT and AGI:

- `asset_lookup`
- `discovery_intelligence`
- `instant_x1_scan`
- `market_report`

The remaining 12 cases are:

- `burn_intelligence`
- `historical_compare`
- `pre_trade_check`
- `risk_check`
- `tokenomics`
- `verification_evidence`

LAB #22 now localizes all 12 to `current_x1_evidence_delegation_gap` / `roberta_oracle_evidence_delegation`, owned by `bhaygood29053-pixel/roberta-core`. They are product-defect candidates but remain `EVIDENCE_REQUIRED`, not factual FAILs.

Protected Issue #89 / PR #90 is the active remediation gate. PR #90 is **OPEN / UNACCEPTED**. The first executable local targeted validation reached the new regression suite and produced 5 PASS / 1 FAIL; the one missed historical-compare wording has been patched at head `ba9a26a75367b352cc6603f0be6d062fe92dcc99`. GitHub private-core Actions attempts are currently non-diagnostic because jobs fail/cancel before executing steps. Do not merge #90 until executable package + pinned-public-shell validation passes.

Public ROBERTA Issue #404 also remains open until protected acceptance and a post-fix live rerun prove the end-to-end result.

## Next exact product work

1. finish executable local validation of protected `roberta-core` PR #90 at head `ba9a26a75367b352cc6603f0be6d062fe92dcc99`;
2. prove pinned public-shell overlay compatibility for that same protected head;
3. only after those deterministic gates pass, merge PR #90 while keeping Issue #89 open for live acceptance;
4. synchronize the five operational repositories and assembled runtimes;
5. run `live-smoke-005` over the same 20 XNT/AGI cases, then grade and diagnose with LAB #21/#22;
6. close protected #89 and public #404 only if live evidence shows the current-X1 evidence delegation gap is resolved; convert only confirmed recurring/replayable defects into LAB #15 Regression Memory;
7. keep X1Scroll #458 / draft PR #549 explicitly on hold until an API key exists and the exact live gate can pass;
8. keep website and Human/Machine ROBERTA claims synchronized with accepted main-state capability only.

`execution_authorized=false`
