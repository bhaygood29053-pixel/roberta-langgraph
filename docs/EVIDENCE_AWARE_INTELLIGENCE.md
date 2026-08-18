# Roberta Evidence-Aware Intelligence & User Experience

Status: implementation milestone for CMIS evidence contract `>=1.7.0`.

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

Chain Scout reports now carry `evidence_context`, projected from CMIS `evidence_receipt` and `proof_score`.

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

## Wallet / whale boundary

`roberta.wallet_interpretation` defines accepted future CMIS wallet primitives, but behavioral/identity labels remain unavailable in this milestone.

Roberta may not call a wallet an insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, or equivalent until CMIS supplies accepted deterministic primitives and a later classification contract explicitly permits the label.

Facts and interpretations remain separate.

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
