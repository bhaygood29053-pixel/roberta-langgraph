# ROBERTA System-Wide Evidence Completion v1

Upstream CMIS contract: `cmis_evidence_complete_response/v1`

## Product invariant

For every live request routed through:

```text
User -> ROBERTA -> Chain Scout -> CMIS
```

ROBERTA must receive the evidence-completion metadata attached by CMIS together with the normal service result. The user or ROBERTA must not have to separately remember to ask for Evidence Receipt, Proof Score, proof/risk separation, or service-scope missing-evidence state.

X1 Scout preserves the CMIS envelope and the protected ROBERTA evidence interpreter projects the completion state into the Scout report's `evidence_context`.

## Meaning

- `COMPLETE`: no material unresolved evidence remains inside the exact returned service scope.
- `PARTIAL`: useful evidence exists, but one or more material evidence elements remain unavailable, stale, conflicting, unknown, or incomplete.
- `BLOCKED`: the requested judgment cannot proceed from the returned service result.

`COMPLETE` is not the same thing as safe, low-risk, good investment, compliant, or authorized to trade.

## Required safety boundaries

ROBERTA and Chain Scouts must preserve:

```text
risk_separate_from_proof = true
facts_recomputed = false
risk_recomputed = false
status_rewritten = false
execution_authorized = false
```

Missing evidence remains missing. An unavailable slippage estimate, route-quality result, fee estimate, simulation, historical interval, holder fact, provenance hop, or other service-specific fact is never converted to zero, false, or an LLM estimate.

## Service-wide behavior

The rule applies uniformly to market, history, tokenomics, burns, risk, pre-trade, trade verification, asset activity, price-impact intelligence, large-trade discovery, Instant X1 Scan, verification evidence, concentration intelligence, bridge/XDEX utilization, cross-chain provenance, regulatory evidence, Daily Intelligence Brief inputs, Tokenized Equity Intelligence, Wallet Relationship Intelligence, and future services that use the same CMIS runtime post-processing path.

This does **not** mean every service is called for every question. Each CMIS service remains responsible for its own accepted deterministic dependencies and internal composition. Evidence Completion tells the Scout whether the returned bounded service scope is complete, partial, or blocked and names missing/unavailable evidence explicitly.
