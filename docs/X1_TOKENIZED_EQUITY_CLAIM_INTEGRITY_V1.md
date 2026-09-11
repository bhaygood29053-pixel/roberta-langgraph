# X1 Tokenized Equity Claim Integrity v1

Parent: ROBERTA #418

Contract: `roberta_tokenized_equity_claim_integrity/v1`

## Purpose

Tokenized Equity Claim Integrity is the deterministic truth boundary between the accepted X1 Scout `x1_tokenized_equity_intelligence/v1` projection and later ROBERTA Machine/Human synthesis.

It does not create new chain facts. It decides which exact claims ROBERTA may safely carry forward from accepted Scout/CMIS evidence and which claims must remain `EVIDENCE_REQUIRED`, `NOT_APPLICABLE`, or explicitly unauthorized.

## Authority path

`User -> ROBERTA -> X1 Scout -> CMIS -> verified provider/source`

- CMIS owns deterministic factual evidence.
- X1 Scout preserves the exact chain-specific evidence boundary.
- Claim Integrity authorizes downstream claim classes without changing the facts.
- ROBERTA owns later judgment/explanation.

`execution_authorized=false` remains invariant.

## Claim classes

### Identity / representation

ROBERTA may preserve exact X1 mint identity and exact underlying-security identity when provenance is AVAILABLE and structurally bound.

Representation type and wrapper structure remain descriptive unless separately verified. They do not prove that the token is legally/economically equivalent to the underlying share.

### Issuer / counterparty

Issuer and material-counterparty claims are authorized only from the evidence-bound `issuer_counterparty` rights dimension. A descriptive issuer field in structural provenance is not sufficient by itself.

### Backing / collateral

Backing/collateral claims are authorized only from the corresponding evidence-bound rights state. A backing description never becomes a claim that backing is sufficient.

### Custody / wrapper

Custody claims require evidence-bound `custody_structure`. A custody description does not establish custody safety. Wrapper structure never establishes direct ownership of the underlying share.

### Holder rights

All nine accepted rights dimensions are evaluated independently:

- underlying ownership / exposure type;
- voting rights;
- dividend/economic-distribution treatment;
- redemption/conversion rights;
- backing/collateral representation;
- issuer/material counterparty;
- jurisdiction/governing-document scope;
- transfer restrictions/eligibility;
- custody structure/dependency.

`VERIFIED`, `DENIED`, `CONDITIONAL`, and `NOT_APPLICABLE` require the accepted evidence binding. `UNKNOWN` remains `EVIDENCE_REQUIRED`; it is never converted to false, zero, or a cleaner conclusion.

An evidence-bound rights state is not legal adjudication or legal advice.

### Cross-chain lineage

When `cross_chain_equity_provenance/v1` is AVAILABLE, ROBERTA may preserve exact origin/current endpoints, lineage, and qualified route evidence.

This authorizes route/configuration lineage only. It does not prove:

- observed asset movement;
- bridge adoption;
- legal/economic equivalence;
- backing sufficiency;
- custody safety;
- shareholder rights.

A Robinhood Chain -> X1 statement remains unavailable unless separate accepted direct route evidence exists.

### Market activity

Only metrics with `state=OBSERVED` may be carried forward. Exact metric semantics, fact time/window, scope, and freshness are preserved.

The boundary explicitly keeps separate:

- liquidity vs trade volume;
- transfers vs trades;
- bridge flow vs adoption;
- holder count vs beneficial ownership;
- reference/quoted/derived price vs executed trade price;
- bounded zero vs global zero.

### Evidence quality / Proof Score

Freshness, conflicts, unresolved fields, component/evidence receipts, and confidence inputs remain evidence-quality material only.

- retrieval time does not prove fact freshness;
- absence of recorded conflict does not prove agreement;
- distinct source labels do not prove source independence;
- Proof Score is evidence strength, not risk;
- Proof Score does not establish legal sufficiency or an investment recommendation.

### Observed wallet relationships

A separately accepted `x1_wallet_relationship_intelligence/v1` product may be attached only when its exact asset mint matches the Tokenized Equity subject.

The resulting claim is limited to the selected finalized direct transfer. It does not prove common/beneficial ownership, real-world identity, whale/insider/bot status, behavior, intent, coordination, manipulation, fraud, causality, risk, complete wallet history, or a complete relationship graph.

## Fail-closed rules

Claim Integrity fails closed when:

- the Scout product/contract/chain is incompatible;
- exact subject identity is missing or conflicting;
- component-state coverage does not match the component payloads;
- a decisive rights state lacks accepted evidence binding;
- route evidence is widened into movement/adoption;
- market metric semantics are missing or malformed;
- evidence-quality UNKNOWN state is promoted into agreement;
- a wallet relationship targets a different asset;
- any upstream negative-authority guardrail becomes true;
- execution authority is widened.

## Downstream contract

The output contains deterministic claim records with:

- `state`;
- `claim_mode`;
- exact `evidence_paths`;
- bounded copied `data`;
- explicit `limitations`.

The output is intended as the required input boundary for the next ROBERTA #418 step: Tokenized Equity Machine synthesis, followed by the Human **“What exactly am I buying?”** explanation flow.

## Non-goals

This contract does not provide legal advice, compliance conclusions, investment recommendations, automatic risk conclusions, trading/execution, bridge execution, custody, signing, broadcasting, or autonomous value movement.
