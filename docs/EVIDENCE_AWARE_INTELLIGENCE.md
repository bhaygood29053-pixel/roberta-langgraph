# Roberta Evidence-Aware Intelligence & User Experience

Status: implemented evidence-aware UX baseline. Current CMIS public capability contract is `1.9.0`; existing accepted services may retain older compatible minimums where their own contracts permit it.

Roberta Phase 11 Controlled Execution remains locked and is not part of this work.

## Authority model

```text
User
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> verified provider / chain evidence
```

Roberta is the conversational and orchestration layer. Chain Scouts investigate and interpret chain-specific results without manufacturing facts. CMIS remains authoritative for deterministic market/blockchain facts, Evidence Receipts, Proof Scores, risk calculations, capability eligibility, and accepted intelligence services. Providers remain beneath CMIS.

Fresh accepted CMIS/provider facts override remembered live values. Missing evidence remains unknown/unavailable and is never converted into zero, false, or an LLM estimate.

## Answer-first contract

Normal recommendation-style answers should follow this order:

1. recommendation / conclusion / blocker;
2. 2–4 most important evidence-backed reasons;
3. risk when CMIS actually supplies a dedicated risk result;
4. evidence quality;
5. important missing evidence;
6. optional technical evidence only on request.

Pre-trade responses use a deterministic finalizer rather than a second free-form LLM rewrite.

Risk and proof strength remain independent. `PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk levels. If CMIS does not return a dedicated risk level, Roberta keeps the risk level unknown rather than inventing one.

## Evidence Receipt / Proof Score contract

Chain Scout reports carry `evidence_context`, projected from CMIS `evidence_receipt` and `proof_score`.

Roberta preserves:

- verification status;
- proof strength and category reasons;
- evidence scope;
- freshness;
- disagreements;
- limitations;
- unresolved fields;
- source provenance;
- risk separately from proof.

Provider-reported information remains provider-reported until CMIS explicitly records independent verification. Missing evidence remains unknown/unproven.

Roberta requires accepted CMIS evidence-quality declarations, including Evidence Receipt schema 1, Proof Score schema 1, `risk_separate_from_proof=true`, and `missing_evidence_is_unknown=true`.

## Recommendation evidence planning

`roberta.recommendation_policy` deterministically identifies evidence needs for buy/sell recommendations, trade-size questions, safer-asset questions, what-changed questions, liquidity-risk questions, LP questions, and price-move questions.

X1 Scout incorporates the allowed read-only portion of this policy into its deterministic required-operation set. Explicit pre-trade remains separately guarded and cannot be enabled by recommendation wording alone.

## Verified Intelligence promotion boundary

The core CMIS Phase 11 `intelligence_foundation` remains read-only and non-promoted as a group.

CMIS Phase 12 separately promotes one bounded X1-only wrapper:

```text
service = concentration_change_intelligence
service_contract = concentration_change_intelligence/v1
accepted_conclusion_type = top_account_concentration_change
promotion_scope = cmis_owned_top_account_concentration_change_evidence_by_id
scout_reliance_promoted = true
execution_authorized = false
```

Roberta consumes that service only through X1 Scout after the service-specific CMIS `>=1.9.0` promotion checks pass. Solana remains unavailable/non-promoted for that service.

## Wallet / behavioral boundary

CMIS has accepted internal deterministic descriptive-classification and wallet-relationship evidence foundations. They remain read-only and non-promoted:

```text
public_service_promoted = false
scout_reliance_promoted = false
cmis_promotable = false
execution_authorized = false
```

The classification foundation may describe only the exact concentration direction proven by canonical CMIS evidence. The wallet-relationship foundation may describe only verified observed direct token-transfer interactions within its bounded evidence scope.

Roberta may not convert those internal foundations into public/Scout operations or label a wallet/entity as an insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, scammer, common owner, beneficial owner, coordinated actor, or equivalent unless a later separately accepted deterministic contract and promotion/adoption gate explicitly permit the claim.

Facts and interpretations remain separate.

## Active alert-evidence boundary

CMIS Issue #263 is the active next read-only intelligence milestone: deterministic concentration-threshold alert evidence. The current slice is internal/read-only/non-promoted and does not change Roberta behavior.

Any future alert promotion must define and prove exact evidence identity/scope, freshness, threshold/comparator policy, triggering observations, persistence/repetition semantics where used, provenance, limitations, deterministic alert identity, and Proof Score/risk separation.

An internal alert record does not imply ownership, intent, manipulation, fraud/scam, risk severity, imminent price movement, or execution authority. Roberta adoption requires a separate CMIS promotion contract plus a separate Roberta roadmap/adoption/readiness gate.

## Cross-chain boundary

X1 and Solana Scout reports each carry their own chain-specific evidence context. Cross-chain synthesis may compare the evidence returned by each chain, but may not merge source lists, transfer one chain's scope/freshness to another, recompute Proof Score or market risk, create a synthetic cross-chain safety grade, or substitute X1 facts for missing Solana facts or vice versa.

## Execution boundary

`pre_trade_check` remains analysis only and preserves:

```text
analysis_only = true
execution_authorized = false
```

This milestone and all current read-only intelligence foundations grant no authority for transaction construction, signing, broadcasting, custody, swap execution, autonomous trading, bridge/value transfer, autonomous value movement, or broad delegated authority.

Roberta's recommendations are analysis only. Deterministic policy remains structurally authoritative over LLM prose.
