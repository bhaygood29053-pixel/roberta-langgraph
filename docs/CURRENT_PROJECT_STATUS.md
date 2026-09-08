# Current ROBERTA Project Status

Current reconciliation: **2026-09-08 10:55 America/New_York**.

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
- stateless/threaded bridge compatibility through public ROBERTA #401 / merge `4c872b4ac9fb25dda0994632e9e2f7dc4cc8cdfc` and protected `roberta-core` #86 / merge `18c6d82377876c0627edb741e5c36f1f339dbbdc`.

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

Live evaluation requests may explicitly request `roberta_evaluation_telemetry/v1`. Missing structured claims or Claim Integrity remains unqualified rather than guessed. A bounded evidence-contract PASS does not certify upstream provider truth or every natural-language sentence.

`roberta-eval` LAB #22 is also accepted via PR #46 / merge `7eefde5355e99453f43cb4662226200b156cf7a0`. It converts LAB #21 live grades into a deterministic service-by-service remediation map and preserves `EVIDENCE_REQUIRED` as qualification-blocking without mislabeling it as a factual ROBERTA failure.

## Next exact product work

1. synchronize all five operational repositories locally (`cmis`, `cmis-core`, `roberta-langgraph`, `roberta-core`, `roberta-eval`) and refresh the assembled CMIS/ROBERTA runtimes;
2. rerun the 20-case LAB #21 real-subject live smoke plan against the repaired bridge and capture actual PASS / EVIDENCE_REQUIRED / FAIL results;
3. run LAB #22 diagnostics service-by-service, fix confirmed ROBERTA/Scout/CMIS defects narrowly, rerun, and convert confirmed recurring defects into permanent LAB #15 regression memory;
4. keep website and Human/Machine ROBERTA claims synchronized with accepted main-state capability only;
5. continue CMIS provider-gap work, with X1Scroll #458 / draft PR #549 explicitly on hold until an API key exists and the exact live gate can pass;
6. continue remaining specialist/product roadmap work without changing the read-only execution boundary.

`execution_authorized=false`
