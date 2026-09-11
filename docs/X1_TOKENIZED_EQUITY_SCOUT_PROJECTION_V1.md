# X1 Tokenized Equity Scout Projection v1

Issue: ROBERTA #421, parent #418.

## Purpose

Project the accepted CMIS `tokenized_equity_intelligence/v1` service into a typed X1 Scout product without widening CMIS authority.

The Scout projection preserves:

- exact X1 mint identity and optional exact underlying-security selector;
- subject resolution state;
- requested component set and each component state;
- only components CMIS marks `AVAILABLE`;
- deterministic Tokenized Equity evidence-quality material;
- top-level response freshness, confidence, sources, warnings, and errors;
- protected Evidence Receipt and Proof Score when the protected runtime supplies them.

## Evidence boundary

The projection does not manufacture values for missing components. `EVIDENCE_REQUIRED`, `UNAVAILABLE`, and `ERROR` remain visible downstream.

The projection must not infer:

- beneficial ownership or shareholder status;
- legal/economic equivalence from ticker, name, wrapper, or route similarity;
- live X1 deployment from service availability;
- a Robinhood Chain → X1 route without direct accepted route evidence;
- adoption from bridge configuration or bridge flow;
- volume from liquidity, or trades from transfers;
- executed price from a quoted/reference/oracle/derived price;
- risk from Proof Score;
- causality, manipulation, insider status, bot status, or intent;
- investment recommendation or legal advice.

`execution_authorized=false` is invariant.

## Contract

Scout output uses `x1_tokenized_equity_intelligence/v1` and carries the accepted CMIS component payloads as evidence-bounded structured data. Human explanation and ROBERTA Machine synthesis are intentionally deferred to later #418 tasks.
