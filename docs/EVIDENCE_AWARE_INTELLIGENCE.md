# Roberta Evidence-Aware Intelligence & User Experience

Status: completed implementation milestone; current CMIS capability contract is `1.9.0`.

Phase 11 Controlled Execution remains locked and is not part of this work.

## Authority model

```text
User
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> verified provider / chain evidence
```

Roberta is the conversational and orchestration layer. CMIS remains authoritative for deterministic market/blockchain facts, evidence receipts, proof scores, and risk calculations. Roberta may explain and synthesize those results, but may not rewrite them.

## Answer-first contract

Normal recommendation-style answers should follow this order:

1. recommendation / conclusion / blocker;
2. 2–4 most important evidence-backed reasons;
3. risk;
4. evidence quality;
5. important missing evidence;
6. optional technical evidence only on request.

Pre-trade responses use a deterministic finalizer rather than a second free-form LLM rewrite.

Risk and proof strength remain independent. `PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk levels. If CMIS does not return a dedicated risk level, Roberta keeps the risk level unknown rather than inventing one.

## Evidence receipt / proof contract

Chain Scout reports carry `evidence_context`, projected from CMIS `evidence_receipt` and `proof_score` where the accepted service exposes them.

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

Roberta requires the CMIS capability contract to advertise evidence receipt schema 1, proof score schema 1, `risk_separate_from_proof=true`, and `missing_evidence_is_unknown=true`.

## Recommendation evidence planning

`roberta.recommendation_policy` deterministically identifies evidence needs for:

- buy/sell recommendation questions;
- trade-size questions;
- safer-asset questions;
- what-changed questions;
- liquidity-risk questions;
- LP questions;
- price-move questions.

X1 Scout incorporates the allowed read-only portion of this policy into its deterministic required-operation set. Explicit pre-trade remains separately guarded and cannot be enabled by recommendation wording alone.

## Current CMIS intelligence boundary

CMIS now has accepted deterministic foundations for:

- descriptive classification of the exact concentration direction proven by canonical CMIS evidence;
- direct wallet-relationship evidence for verified observed token-transfer interactions between exact chain identities.

Those foundations are **internal/read-only/non-promoted**. They do not become callable Roberta/Scout operations and preserve equivalent boundaries:

```text
public_service_promoted = false
scout_reliance_promoted = false
cmis_promotable = false
execution_authorized = false
```

The descriptive classification foundation does not infer behavior, ownership, intent, fraud/manipulation, or risk. The wallet-relationship foundation does not infer common ownership, beneficial ownership, coordinated behavior, intent, or complete wallet/relationship-graph history.

Roberta may not call a wallet an insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, scammer, common owner, or equivalent merely because these internal CMIS foundations exist. Such labels remain unavailable unless a separately accepted and promoted deterministic contract explicitly authorizes the exact conclusion.

Facts and interpretations remain separate.

## Promoted CMIS intelligence boundary

The currently promoted read-only Verified Intelligence service remains the X1-only `concentration_change_intelligence/v1` wrapper under CMIS `1.9.0`. Roberta consumes it only through X1 Scout after validating the exact capability/promotion contract.

The promoted concentration service is distinct from the non-promoted descriptive-classification and wallet-relationship foundations. Roberta must not infer that internal CMIS evidence is available through the public service boundary unless the live capability manifest and accepted contract explicitly say so.

## Next evidence-aware milestone

Evidence-backed alerts are the next shared read-only intelligence candidate. A future alert contract must explicitly bind:

- exact evidence scope;
- freshness and observation time;
- explicit threshold/policy identity;
- persistence/repetition semantics;
- the exact triggering observations/evidence;
- deterministic alert identity;
- limitations and unavailable fields;
- fail-closed behavior.

An alert may report only the verified condition that crossed the explicit rule. It may not imply ownership, whale/insider/bot activity, manipulation, fraud/scam, coordinated behavior, intent, or execution authority unless another separately accepted deterministic contract proves that exact conclusion.

Any public-service/Scout-reliance promotion and Roberta adoption/readiness evaluation remain separate later steps.

## Cross-chain boundary

X1 and Solana Scout reports each carry their own chain-specific evidence context. Cross-chain synthesis may compare the evidence returned by each chain, but may not:

- merge source lists;
- treat one chain's scope/freshness as another chain's proof;
- recompute proof strength;
- recompute market risk;
- create a synthetic cross-chain safety grade;
- substitute X1 facts for missing Solana facts or vice versa.

## Execution boundary

This milestone grants no authority for:

- transaction construction;
- signing;
- broadcasting;
- custody;
- swap execution;
- autonomous trading;
- autonomous value movement;
- broad delegated authority.

Roberta's recommendations are analysis only. Deterministic policy remains structurally authoritative over LLM prose.
