# CMIS Roadmap Sync — refreshed 2026-08-21

This document is Roberta's current integration snapshot of CMIS. It is a consumption guide, not a second CMIS roadmap.

## Canonical hierarchy

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Roberta owns orchestration/final synthesis. Chain Scouts plan and interpret without manufacturing facts. CMIS owns deterministic verified facts, evidence, Proof Scores, risk, historical intelligence, capability eligibility, and bounded analysis-only pre-trade calculations. Providers remain beneath CMIS.

Fresh accepted CMIS/provider facts override remembered live-market values. Missing evidence remains unknown/unavailable rather than zero-filled. Risk remains separate from Proof Score.

## Current synchronized state

- Roberta Phase 10 — complete.
- Roberta Evidence-Aware Intelligence & UX milestone — complete.
- CMIS Phase 10 Solana read-only provider foundation — complete.
- CMIS Phase 11 read-only Verified Intelligence foundation — complete.
- CMIS Phase 12 first narrow promoted intelligence service — complete.
- CMIS deterministic descriptive intelligence classification foundation — complete, internal/read-only/non-promoted.
- CMIS deterministic wallet relationship evidence foundation — complete with explicit non-ownership semantics, internal/read-only/non-promoted.
- CMIS current capability contract — `1.9.0`.
- Roberta adoption/readiness of the promoted X1 concentration service — complete.
- CMIS Issue #263 concentration-threshold alert-evidence milestone — active, internal/read-only/non-promoted.
- CMIS Issue #30 X1 provider-gap workstream — active in parallel, read-only/fail-closed.
- Roberta Controlled Execution — locked / not started.

## Phase 11 foundation versus Phase 12 wrapper

The core Phase 11 `intelligence_foundation` remains read-only and non-promoted as a group:

```text
public_service_promoted = false
scout_reliance_promoted = false
```

CMIS Phase 12 separately promotes exactly one narrow X1 service:

```text
service = concentration_change_intelligence
service_contract = concentration_change_intelligence/v1
minimum_cmis_contract = 1.9.0
chain = x1
state = bounded
callable = true
read_only = true
public_service_promoted = true
scout_reliance_promoted = true
accepted_conclusion_type = top_account_concentration_change
promotion_scope = cmis_owned_top_account_concentration_change_evidence_by_id
execution_authorized = false
```

Solana is unavailable/non-callable/non-promoted for this service.

## Internal deterministic foundations after the first promotion

CMIS has accepted two additional evidence-bound internal contracts without public-service or Scout-reliance promotion:

- descriptive classification of the exact concentration direction proven by canonical CMIS evidence;
- verified direct wallet-relationship evidence for observed token-transfer interactions between exact chain identities.

Both preserve:

```text
public_service_promoted = false
scout_reliance_promoted = false
cmis_promotable = false
execution_authorized = false
```

The classification foundation does not infer behavior, ownership, intent, manipulation/fraud, or risk. The wallet-relationship foundation does not infer common ownership, beneficial ownership, coordinated control, behavioral intent, or complete relationship-graph/history coverage.

Roberta and Chain Scouts do not gain a new operation merely because these internal CMIS contracts exist.

## Roberta adoption boundary

Roberta consumes the promoted concentration service only through X1 Scout. The operation is explicit-only and is not automatically added to autonomous X1 Scout planning.

The accepted CMIS request contract binds X1, asset context, and a canonical CMIS-owned intelligence evidence id. CMIS performs trusted internal evidence resolution/revalidation. Caller-supplied intelligence bundles, Evidence Receipts, Proof Scores, provider assertions, behavioral labels, or replacement verification state are not trust inputs.

Roberta validates the live service-promotion capability record before dispatch. Current Roberta code does **not** claim to independently prove more canonical asset-identity semantics than its typed client actually enforces; exact asset/evidence binding remains an accepted request/CMIS contract requirement unless a stronger local validator is separately implemented.

The service does not establish unique-holder totals or beneficial-owner identity. Token-account concentration remains token-account concentration. Optional threshold output is deterministic policy evaluation, not risk.

## X1 status

X1 remains the mature CMIS surface, but evidence completeness is fact- and scope-specific. Recent bounded provider-gap observations remain non-promotional: tested X1.Ninja SSE access is currently denied for the repository credential, holder-looking provider/RPC/account-authority counts disagree, and Warp Bridge operational evidence remains unavailable pending an exact provenance-approved machine-readable contract.

Roberta preserves verified/bounded/partial/unavailable/conflict/insufficient states rather than guessing.

## Solana status

Solana Phase 10 remains a bounded read-only provider path beneath the same CMIS architecture. Exact-mint identity, SPL Token / Token-2022 handling, bounded market/tokenomics/risk/history, and source cross-checks remain capability-specific. Solana does not inherit X1 capabilities and may not silently fall back to X1.

## Verification evidence and proof quality

`verification_evidence` remains selector-bound. Evidence Receipts / Proof Scores and limitations are preserved. Proof Score is not risk.

## Pre-trade analysis

The deterministic trade-size milestone is complete as a bounded analysis-only foundation. Missing advanced route/slippage/fee/simulation evidence remains unavailable rather than zero or an LLM estimate.

```text
analysis_only = true
execution_authorized = false
```

A `PASS` is not permission to trade.

## Active next shared read-only boundary — CMIS #263

The active CMIS intelligence milestone is **deterministic concentration-threshold alert evidence**. This first alert slice is internal, read-only, and non-promoted.

It must bind accepted canonical concentration evidence to explicit threshold/comparator policy, freshness, exact chain/asset/evidence identity, scope, triggering observations, persistence/repetition semantics where used, provenance, limitations, deterministic content-addressed alert identity, and Proof Score/risk separation.

The milestone does not create a public alert service, grant Scout reliance, change Roberta behavior, infer ownership/intent/manipulation/fraud/risk severity/imminent price movement, or authorize execution.

Roberta adoption of any future alert service requires a separate CMIS promotion contract and a separate Roberta promotion/adoption/readiness gate. X1 provider-gap verification and Solana maturity continue read-only in parallel.

## Memory, policy, approval, and execution

```text
HXMP / memory -> stable context and policy
CMIS          -> fresh verified facts and evidence
Policy code   -> deterministic rule result
LLM           -> explanation / synthesis only
```

Human approval is exact-proposal review, not a reusable signing credential.

No current CMIS/Scout/Roberta result authorizes transaction preparation for execution, signing, broadcasting, custody, live trading, bridge transfer, autonomous execution, or value movement.

**CMIS verifies. Chain Scouts investigate and interpret. Roberta coordinates and explains.**
