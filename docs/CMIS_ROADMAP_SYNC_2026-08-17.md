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

CMIS Phase 2, trust/provenance/independent verification, remains the active CMIS phase. The trust architecture is materially ahead of the original roadmap baseline:

- the fail-closed `verification_evidence` wrapper is accepted on CMIS `main`;
- the sanitized content-addressed SQLite evidence ledger is accepted on CMIS `main`;
- exact read-only evidence lookup by stable `evidence_id` or exact `fact_type + subject_id` is accepted on CMIS `main`;
- the exact `verification_evidence` gateway is accepted on CMIS `main`;
- the production CMIS HTTP runtime now composes and advertises `verification_evidence` alongside the existing runtime services;
- deterministic data-quality state preserves identity, semantics, freshness, source agreement, and promotion requirements;
- CMIS does not expose a promoted fact value when evidence is non-promotable.

The accepted runtime flow is:

```text
fact-specific verifier
        ↓
verification_evidence wrapper
        ↓
sanitized content-addressed ledger
        ↓
exact read-only lookup
        ↓
verification_evidence gateway
        ↓
CMIS HTTP runtime
```

CMIS PR #87 accepted the gateway boundary. CMIS PR #88 accepted the HTTP runtime composition. The #88 post-merge test run passed on exact CMIS `main` SHA `08ac97810163168048192665d314cce90f5b89fa`.

## Runtime and Roberta eligibility boundary

The CMIS HTTP runtime now supports `verification_evidence`, but Roberta's typed client does not yet expose that operation.

The accepted CMIS selector boundary is exactly one of:

1. stable `evidence_id`; or
2. exact `fact_type + subject_id` for the latest stored evidence for that fact.

CMIS rejects free-form asset selection, raw verifier/provider payloads, and request-controlled database paths. CMIS owns ledger selection/configuration, stored-envelope revalidation, content-address checking, fact/chain identity validation, timestamps, verification state, data quality, and `cmis_promotable`.

A callable route is not proof that an evidence record exists. CMIS does not invent or backfill evidence. Missing records or an empty ledger remain explicit `unavailable`.

Until a separate Roberta client/X1 Scout eligibility slice is accepted:

- Roberta must not bypass its typed client to call `verification_evidence`;
- Roberta must not call internal CMIS Python evidence helpers directly;
- Roberta must not submit raw verifier/provider observations;
- Roberta must not infer evidence from a free-form asset name;
- Roberta must not choose verification status, confidence, or `cmis_promotable` state.

## Remaining X1 trust gaps

The X1 trust layer is not complete. Important open or not-yet-accepted areas include:

- connecting accepted fact-producing verification workflows to the persistent evidence ledger without bypassing their fact-specific gates;
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

The projects may advance in parallel only where boundaries remain explicit:

```text
CMIS
  connect accepted fact producers to persistent evidence
  -> finish X1 trust gaps
  -> provenance-aware history
  -> provider maturity
  -> accepted Solana provider capabilities

Roberta
  Phase 10 provider-neutral specialist registry
  -> exact verification_evidence client/X1 Scout eligibility
  -> Solana Scout skeleton with fake/unavailable CMIS
  -> live Solana eligibility only after CMIS acceptance
```

Roberta should not wait to build provider-neutral orchestration contracts, but it must wait for accepted CMIS/provider capability before claiming live chain facts.

## Core integration principle

**CMIS determines what is happening in supported markets now and preserves the evidence for that determination.**

**Chain Scouts determine what accepted CMIS facts mean within their respective chains.**

**Roberta determines what those specialist findings mean for the user and across chains, subject to user policy and approval boundaries.**
