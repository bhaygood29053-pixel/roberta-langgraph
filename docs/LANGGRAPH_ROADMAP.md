# Roberta LangGraph Roadmap

Last updated: 2026-08-20

## Current position

Roberta has completed:

- Phase 1 — Core Agent Loop;
- Phase 2 — Provider-Neutral Model Loop;
- Phase 3 — X1 Scout Boundary;
- Phase 4 — CMIS / X1 Provider Integration;
- Phase 6 — Agentic X1 Scout Planning;
- Phase 7A — Thread / Checkpoint Persistence;
- Phase 7B — HXMP Durable Memory;
- Phase 8 — Oracle Policy;
- Phase 9 — Human in the Loop;
- Phase 10 — More Specialists / Providers;
- Post-Phase-10 Evidence-Aware Intelligence & User Experience;
- X1 Decision Production Readiness (#62);
- adoption/readiness of the first separately promoted CMIS 1.9 Verified Intelligence service through X1 Scout (#73/#74);
- Solana Read-Only Production Readiness (#78) for the exact currently promoted Roberta Solana Scout surface.

Phase 5 — X1 Evidence Completeness remains deliberately **bounded**, with explicit verified/bounded/partial/unavailable/conflict/insufficient-evidence states.

Roberta Phase 11 — Controlled Execution remains **locked / not started**.

## Canonical hierarchy

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Roberta owns orchestration, user policy, specialist selection, cross-chain coordination, approval boundaries, and final synthesis.

Chain Scouts own chain-specific planning and interpretation. They preserve CMIS facts/evidence/limitations and do not manufacture market facts.

CMIS owns deterministic verified facts, evidence, Evidence Receipts, Proof Scores, deterministic risk, historical intelligence, capability eligibility, and bounded analysis-only pre-trade calculations.

Providers remain beneath CMIS.

Fresh accepted CMIS/provider evidence overrides remembered, checkpointed, or conversational live-market values. Missing evidence remains unknown/unavailable; it is never converted into zero, false, or an LLM estimate. Risk remains separate from Proof Score.

## Migration rule

The repository/project identity is CMIS, while working internal Python identifiers such as `liquidity_scout` may remain during incremental migration to avoid breaking imports, tests, entry points, and deployments. Compatibility identifiers do not create a second authority layer.

## Engineering governance

Meaningful Roberta changes are governed by [`ENGINEERING_WORKFLOW.md`](./ENGINEERING_WORKFLOW.md). That document is the repository authority for roadmap/issue gating, narrow tracer-bullet implementation, behavior-first verification, exact-head deterministic testing, and the independent three-axis PR gate: **Spec Fidelity**, **Code/Architecture Quality**, and **Authority/Safety Boundary**.

A roadmap item being active does not waive those gates. A PR is not merge-ready if any required axis fails, and acceptance must be followed by roadmap/source-of-truth reconciliation. This governance does not start or widen Controlled Execution.

## Phase 10 — More Specialists / Providers ✅ Complete

Roberta supports separate X1 Scout and Solana Scout paths above one shared CMIS layer:

```text
Roberta
  ├── X1 Scout
  │     -> CMIS -> X1 / XDEX providers
  └── Solana Scout
        -> CMIS -> Solana providers
```

The Scout -> CMIS boundary validates the live machine-readable capability manifest before dispatch. Missing, malformed, incompatible, or non-callable capability state fails closed. No unsupported chain silently falls back to another chain.

Solana Phase 10 remains read-only, capability-specific, and not assumed to have X1 parity.

## Completed readiness gates

### X1 Decision Production Readiness (#62) ✅ Complete

The X1 read-only decision-quality production gate is complete. Representative live/configured and degraded-evidence cases proved answer-first presentation, uncertainty preservation, risk/evidence separation, freshness handling, null-versus-zero preservation, provider-error handling, and read-only execution boundaries.

### First promoted CMIS intelligence adoption (#73/#74) ✅ Complete

Roberta adopted the first separately promoted CMIS 1.9 read-only intelligence service, `concentration_change_intelligence/v1`, through X1 Scout. The operation remains explicit-only and evidence-id-bound; it does not authorize broader intelligence promotion or execution.

### Solana Read-Only Production Readiness (#78) ✅ Complete

The configured production-model/provider path is accepted for the exact current Roberta Solana Scout surface:

- `market_report`;
- `tokenomics`;
- `risk_check`;
- exact-mint identity preservation and symbol-only fail-closed handling required by those services;
- X1/Solana evidence isolation.

The final configured operator run on 2026-08-20 executed all five corpus cases with `--require-no-skips` and recorded:

```text
total: 5
completed: 5
passed: 5
failed: 0
skipped: 0
oracle_retry_calls: 1
provider_error_events: 1
```

The nonzero provider-error count is preserved as an operational measurement rather than hidden; readiness blockers are based on failed deterministic scenario checks, and the accepted run had zero failures. The symbol-only case required one presentation retry after PR #94 and then passed with separate Risk/Evidence quality disclosure.

This is **not** an X1/Solana parity claim. Solana `historical_compare`, `rank`, `pre_trade_check`, `concentration_change_intelligence`, broader Verified Intelligence primitives, and all execution capabilities remain outside the accepted Roberta Solana production-ready scope unless separately promoted and evaluated.

The separately accepted live Token-2022 fixture from CMIS #244 proves only the exact-mint read-only RPC contract for that fixture; it does not promote a broader Token-2022 market or holder/ownership claim.

## Evidence-aware intelligence ✅ Complete

Roberta preserves CMIS Evidence Receipts, Proof Scores, source/provenance, scope, freshness, disagreements, limitations, unresolved fields, and risk through Chain Scout reports.

Roberta may explain those results but does not recompute CMIS proof/risk or upgrade provider-reported evidence to independently verified truth.

Cross-chain evidence may be compared but not merged into a synthetic source set, Proof Score, freshness state, deterministic risk result, or safety grade.

Behavioral/ownership labels such as insider, whale, bot, accumulator, distributor, market maker, manipulator, common owner, or intent remain unavailable unless a separately accepted deterministic classification contract explicitly permits them.

## CMIS Phase 11 foundation versus Phase 12 promotion

CMIS Phase 11 established the read-only Verified Intelligence foundation. The core `intelligence_foundation` remains non-promoted as a group:

```text
read_only = true
public_service_promoted = false
scout_reliance_promoted = false
```

Its broader primitives—top-account concentration snapshots, neutral wallet activity, sanitized sparse history, and generic evidence-bound conclusions—do not automatically become public Scout services.

CMIS **Phase 12** separately promoted exactly one narrow X1 wrapper under current CMIS contract `1.9.0`:

```text
service = concentration_change_intelligence
service_contract = concentration_change_intelligence/v1
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

## Roberta adoption of the Phase 12 service ✅ Complete

Roberta has adopted `concentration_change_intelligence/v1` through **X1 Scout** with a service-specific CMIS `>=1.9.0` promotion gate.

The operation is explicit-only; it is not an autonomous X1 Scout planning action merely because CMIS advertises it.

Roberta/X1 Scout validates the live capability record before dispatch and requires the exact service contract, bounded/callable/read-only state, public-service promotion, Scout reliance, accepted conclusion type, promotion scope, and `execution_authorized=false`.

The public request uses exact X1 asset context plus a canonical CMIS-owned intelligence evidence id. CMIS resolves/revalidates trusted stored evidence internally. Caller-supplied intelligence bundles, Evidence Receipts, Proof Scores, provider assertions, behavioral labels, or replacement verification state are not accepted as trust shortcuts.

Exact canonical asset/evidence binding remains a CMIS/request-contract requirement unless and until Roberta adds a stronger local canonical-identity validator; documentation must not claim Roberta itself proves more identity semantics than the current client enforces.

The service does not establish total unique holders or beneficial owners. Token-account concentration remains token-account concentration. Optional threshold output is deterministic policy evaluation, not risk, and Proof Score remains separate from risk.

## X1 evidence boundary 🟡 Bounded

X1 is the mature CMIS surface, but completeness remains field- and scope-specific.

Recent bounded provider-gap observations include:

- X1.Ninja SSE handshake access currently denied for the tested repository credential; no event semantics are promoted from that result;
- holder-looking provider/RPC/account-authority counts disagree and remain insufficient evidence for holder/beneficial-owner semantics;
- Warp Bridge machine-readable operational facts remain unavailable until an exact provenance-approved contract is accepted;
- historical redundancy/source-independence evidence remains a separate proof obligation.

Roberta must preserve these unavailable/partial/insufficient states rather than guessing.

## Pre-trade analysis ✅ Bounded analysis-only foundation complete

The deterministic pre-trade trade-size milestone previously tracked as CMIS Issue #99 is complete and is no longer a current roadmap dependency.

CMIS owns deterministic trade-size analysis. Roberta explains the returned structured result without recomputing replacement ratios, risk, proof, price impact, fees, slippage, route quality, or simulation.

Advanced fields remain available only where exact semantics/evidence are independently proven. Missing advanced evidence is not zero-filled.

Every current pre-trade result preserves:

```text
analysis_only = true
execution_authorized = false
```

A `PASS` is not permission to trade.

## Memory and policy

```text
HXMP / memory -> stable context and policy
CMIS          -> current verified facts and evidence
Policy code   -> deterministic rule result
LLM           -> explanation / synthesis only
```

Fresh accepted CMIS/provider evidence overrides remembered live-market snapshots.

## Human approval

Phase 9 human approval is exact-proposal review. Approval is not a reusable signing credential and does not grant broad future wallet authority.

## Phase 11 — Controlled Execution ⬜ Locked / not started

No current CMIS result, Chain Scout report, Roberta policy decision, readiness result, or human approval authorizes:

- transaction preparation for execution;
- wallet signing;
- transaction broadcasting;
- custody;
- live swap execution;
- autonomous trading;
- bridge/value transfer;
- autonomous value movement;
- broad delegated wallet authority.

If Controlled Execution is ever promoted, it requires a separate accepted transaction-construction/simulation, exact approval-consumption/revalidation, signer/broadcast, replay-protection, precondition, and failure contract.

## Next read-only intelligence boundary

The first narrow CMIS 1.9 promotion/adoption and the current Solana read-only readiness gate are complete. The next shared intelligence work should proceed only through separately accepted deterministic contracts, especially:

1. deterministic inference/classification contracts before behavioral/ownership labels;
2. wallet relationship evidence with explicit non-ownership semantics;
3. evidence-backed alerts with explicit scope/freshness/threshold/persistence rules;
4. deeper X1 provider-gap and historical redundancy verification;
5. field-by-field Solana maturity beyond the currently accepted Scout surface;
6. future Ethereum support only under an explicit capability/verification plan.

None of these items starts Controlled Execution.

## Core rule

**CMIS verifies. Chain Scouts investigate and interpret without inventing facts. Roberta coordinates, applies policy, and explains. The system becomes more capable by proving more—not by guessing more.**
