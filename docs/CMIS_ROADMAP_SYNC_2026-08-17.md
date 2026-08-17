# CMIS Roadmap Sync — 2026-08-17

This document is Roberta's current integration snapshot of the Cross-Chain Market Intelligence Service (CMIS) roadmap. It is a consumption guide for Roberta and Chain Scouts, not a second CMIS roadmap and not an authority to promote draft CMIS work.

## Source-of-truth rule

CMIS remains authoritative for freshness-sensitive market, liquidity, tokenomics, verification, provenance, and risk facts. Roberta may interpret accepted CMIS results but must not manufacture stronger facts, override fresher CMIS data, or infer that an open CMIS pull request is production capability.

Authority continues to flow:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

Verified information flows upward in the reverse direction.

## Current CMIS roadmap position

CMIS Phase 1, the X1 deterministic foundation, is advanced and mostly established.

CMIS Phase 2, trust/provenance/independent verification, is the current active CMIS phase. The trust architecture is now materially ahead of the original roadmap baseline:

- the fail-closed `verification_evidence` wrapper is accepted on CMIS `main`;
- the sanitized content-addressed SQLite evidence ledger is accepted on CMIS `main`;
- exact read-only evidence lookup by stable `evidence_id` or exact `fact_type + subject_id` is accepted on CMIS `main`;
- deterministic data-quality state preserves identity, semantics, freshness, source-agreement, and promotion requirements;
- CMIS does not expose a promoted fact value when evidence is non-promotable.

The accepted internal flow is:

```text
fact-specific verifier
        ↓
verification_evidence wrapper
        ↓
sanitized content-addressed ledger
        ↓
exact read-only lookup
```

## Runtime eligibility boundary

Internal CMIS acceptance is not the same as Roberta runtime eligibility.

CMIS pull request #87 (`Expose exact verification evidence through CMIS gateway`) is the current draft gateway-eligibility slice. It is not accepted merely because the wrapper/ledger/lookup are accepted.

Until that gateway slice is tested, merged, deployed, and reflected in the Roberta integration contract:

- Roberta must not call internal CMIS Python evidence helpers directly;
- Roberta must not submit raw verifier/provider observations;
- Roberta must not infer evidence from a free-form asset name;
- Roberta must not choose verification status, confidence, or `cmis_promotable` state;
- `verification_evidence` should be treated as unavailable for production Roberta invocation.

The intended future selector boundary is exactly one of:

1. stable `evidence_id`; or
2. exact `fact_type + subject_id` for the latest stored evidence for that fact.

## Remaining X1 trust gaps

The X1 trust layer is not complete. Important open or not-yet-accepted areas include:

- common provider/RPC observation-scope and freshness rules for reserve promotion;
- X1.Ninja holder semantics and coverage;
- empirical SSE trade-stream behavior and access;
- history/RPC redundancy and retention behavior;
- unresolved XDEX history/quote semantics;
- source-agreement and provider freshness/failure rules across fact types.

Roberta must not interpret X1 Scout availability as proof that every X1 fact has complete CMIS evidence coverage.

## Historical and derived intelligence sequencing

After the trust layer is sufficiently proven, CMIS Phase 3 is the next major infrastructure investment: provenance-aware, versioned historical market memory.

Later CMIS phases build deterministic intelligence from trusted history, including liquidity concentration, holder/entity intelligence, anomalies, risk changes over time, market-health profiles, and replayable risk decisions.

Roberta should consume those capabilities only after CMIS publishes accepted service contracts for them.

## Solana / Roberta Phase 10 boundary

CMIS Solana Provider development has started early in draft form, including read-only RPC/source adapters and transport-free cross-checks. Those drafts do not make Solana a production CMIS chain.

Roberta Phase 10 may safely build provider-neutral specialist contracts and a Solana Scout skeleton against deterministic fake/unavailable CMIS states, provided it preserves these rules:

- no direct Roberta -> Solana RPC/DEX/indexer calls;
- no invented Solana price, liquidity, supply, holders, authority, risk, route, or confidence facts;
- no fallback from Solana to X1;
- live Solana facts remain unavailable until the Solana Provider path is independently accepted and deployed beneath CMIS;
- Solana Scout should reuse the same shared CMIS service/evidence contracts rather than create a parallel intelligence stack.

This aligns with Roberta Phase 10 tracker issue #31.

## Roberta milestone status

Roberta `main` has completed Phase 8 deterministic Oracle Policy and Phase 9 human approval boundary. Phase 10 — multi-specialist/provider architecture — is the next active development direction.

Phase 9 approval remains non-executing. CMIS `pre_trade_check` remains analysis and must never be reinterpreted as authorization to sign or broadcast value-moving transactions.

## Near-term coordination rule

The two projects may advance in parallel only where boundaries remain explicit:

```text
CMIS
  finish X1 trust gaps
  -> provenance-aware history
  -> provider maturity
  -> accepted Solana provider capabilities

Roberta
  Phase 10 provider-neutral specialist registry
  -> Solana Scout skeleton with fake/unavailable CMIS
  -> live Solana eligibility only after CMIS acceptance
```

Roberta should not wait to build provider-neutral orchestration contracts, but it must wait for accepted CMIS/provider capability before claiming live chain facts.

## Core integration principle

**CMIS determines what is happening in supported markets now and preserves the evidence for that determination.**

**Chain Scouts determine what accepted CMIS facts mean within their respective chains.**

**Roberta determines what those specialist findings mean for the user and across chains, subject to user policy and approval boundaries.**
