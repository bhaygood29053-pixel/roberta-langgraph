# CMIS Roadmap Sync — refreshed 2026-08-20

This document is Roberta's current integration snapshot of **CMIS — Cross-Chain Market Intelligence Service**. It is a consumption guide for Roberta and Chain Scouts, not a second CMIS roadmap and not authority to promote unaccepted CMIS work.

## Source-of-truth rule

CMIS remains authoritative for freshness-sensitive market, liquidity, tokenomics, verification, provenance, proof-quality, deterministic risk, historical intelligence, and bounded pre-trade facts. Roberta may interpret accepted CMIS results but must not manufacture stronger facts, override fresher CMIS data, recompute CMIS proof/risk, or infer production capability from draft work.

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Verified information flows upward in the reverse direction.

## Current synchronized project position

Accepted state as of 2026-08-20:

- **Roberta Phase 10 — More Specialists / Providers: complete.**
- **Roberta Post-Phase-10 Evidence-Aware Intelligence & User Experience: complete.**
- **CMIS Phase 10 — Solana read-only provider foundation: complete.**
- **CMIS Evidence Receipts + Proof Score milestone: complete.**
- **CMIS X1 evidence-capability boundary: complete and fail-closed.**
- **CMIS deterministic pre-trade trade-size analysis: complete.**
- **CMIS Phase 11 — read-only Verified Intelligence foundation: complete.**
- **CMIS 1.9.0 first public-service / Scout-reliance promotion: complete for X1 `concentration_change_intelligence/v1`.**
- **Roberta adoption of that exact X1 service: complete.**
- **Roberta readiness replay for that service: complete.**
- **Roberta Phase 11 — Controlled Execution: locked / not started.**

CMIS and Roberta use different phase numbering. CMIS Phase 11 completion and the first promoted read-only intelligence service do **not** mean Roberta Controlled Execution has started.

Roberta roadmap gate #73 and implementation issue #74 are closed completed. Core adoption merged in Roberta PR #76; readiness replay merged in PR #77.

## Shared Scout / CMIS architecture

```text
Roberta
  ├── X1 Scout
  │     -> CMIS -> X1 / XDEX providers
  └── Solana Scout
        -> CMIS -> Solana providers
```

Do not duplicate CMIS per chain. Chain-specific providers remain beneath shared deterministic CMIS contracts; a Chain Scout exists for chain-specific planning and interpretation.

The Scout -> CMIS boundary is guarded by:

```text
GET /v1/cmis/capabilities
```

Missing, malformed, incompatible, or non-callable capability state fails closed.

## CMIS contract state

CMIS currently advertises contract **1.9.0**.

Roberta retains a global minimum of **1.8.0** for already accepted existing services. The promoted concentration-change operation has its own stricter service-specific requirement of **CMIS >=1.9.0**.

This distinction is intentional: a new service may require a newer contract without needlessly invalidating older accepted operations.

## Phase 11 foundation versus promoted service

The core Phase 11 `intelligence_foundation` remains read-only and non-promoted as a group:

```text
public_service_promoted = false
scout_reliance_promoted = false
```

Its internal foundations still include top-account concentration, compatible numeric changes, neutral wallet-activity facts, sanitized sparse intelligence history, and evidence-bound conclusions.

Separately, CMIS 1.9.0 promotes one exact X1 wrapper:

```text
service = concentration_change_intelligence
service_contract = concentration_change_intelligence/v1
chain = x1
accepted_conclusion_type = top_account_concentration_change
promotion_scope = cmis_owned_top_account_concentration_change_evidence_by_id
read_only = true
execution_authorized = false
```

This is a narrow promotion, not a blanket promotion of Phase 11.

## Roberta adoption boundary

Roberta consumes the promoted service only through **X1 Scout**.

The operation is explicit-only and is not added to autonomous X1 Scout planning. Roberta/X1 Scout requires:

- exact X1 asset identity;
- an exact canonical CMIS-owned `ie_<64 lowercase hex>` intelligence evidence id from the user or trusted current context;
- a live CMIS 1.9 capability record proving the exact promotion contract.

The request does not accept caller-supplied intelligence bundles, Evidence Receipts, Proof Scores, provider assertions, behavioral labels, or replacement verification state.

X1 Scout preserves CMIS status, facts, optional policy assessment, Evidence Receipt / Proof Score metadata, freshness, unresolved fields, limitations, warnings/errors, and `risk` without recomputation.

Solana remains unavailable/non-promoted for this service.

## Behavioral and ownership boundary

The promoted concentration service does **not** establish:

- holder-total completeness;
- beneficial-owner identity;
- whale/insider/bot/accumulator/distributor/market-maker labels;
- manipulation or intent;
- common ownership;
- risk from Proof Score alone.

Token-account scope remains token-account scope. Missing ownership evidence stays missing.

Risk and proof quality remain separate dimensions.

## X1 provider-gap status

X1 remains the more mature CMIS surface, but completeness is fact- and scope-specific.

Recent live read-only observations remain deliberately non-promotional:

- the current repository X1.Ninja credential received HTTP `403` / `access_denied` on the bounded `/v1/stream/trades` SSE handshake probe; no event body or stream semantics were consumed/inferred;
- same-run XENCAT holder-looking evidence observed provider candidate `116`, RPC token-account candidate `180`, and unique token-account-authority candidate `174`; CMIS still reports insufficient evidence for holder semantics/coverage/beneficial ownership;
- Warp Bridge operational evidence remains unavailable until an exact provenance-approved machine-readable read URL and deterministic contract are accepted.

Roberta preserves these as provider-gap evidence, not definitive market/identity facts.

## Solana status

The Solana read-only foundation is complete beneath shared CMIS contracts. Accepted architecture includes exact-mint identity, canonical Solana RPC foundations, SPL Token / Token-2022 handling, Jupiter/Helius/DEX Screener adapters where configured, deterministic cross-source checks, provenance-safe history, and bounded/partial service coverage.

Recent CMIS readiness work accepts a PYUSD Token-2022 fixture contract while keeping largest-account evidence subject to its dedicated RPC/readiness proof.

Solana remains fail-closed and capability-specific. It is not assumed to have X1 parity, and no Solana request may silently fall back to X1.

## Verification evidence and proof quality

Roberta has an accepted constrained `verification_evidence` path through the appropriate Scout/typed client boundary. Evidence lookup remains selector-bound and must not become a free-form verifier bypass.

Roberta and Chain Scouts preserve CMIS evidence context including verification state, Evidence Receipt identity/provenance, Proof Score, scope, freshness, disagreements, limitations, unresolved fields, data-quality reasons, and promotion state.

Risk and proof quality remain separate. Roberta may explain both but must not recompute either into a new authoritative score.

## Pre-trade analysis status

CMIS pre-trade sizing is complete as a bounded analysis-only foundation.

CMIS can supply requested notional, verified liquidity context, notional-to-liquidity ratio, explicit versioned policy, freshness handling, and advanced route facts only where exact evidence gates pass.

Missing advanced evidence remains unavailable, never zero or an LLM estimate.

```text
analysis_only = true
execution_authorized = false
```

A CMIS `PASS` is not permission to trade.

## Memory, policy, and approval boundaries

```text
HXMP / durable memory -> stable context and explicit policy
CMIS                  -> current verified facts and evidence
Policy code           -> deterministic rule result
LLM                    -> explanation / synthesis only
```

Fresh accepted CMIS/provider evidence overrides remembered or checkpointed live-market snapshots.

Phase 9 human approval remains a review boundary. Approval of one exact proposal is not a reusable signing credential and does not create execution authority.

## Controlled Execution remains locked

Roberta Phase 11 Controlled Execution has **not started**.

No current CMIS/Scout result, Roberta policy decision, or human-review state authorizes transaction construction as an execution path, signing, broadcasting, custody, live swaps, autonomous trading, bridge/value transfer, or broad delegated wallet authority.

## Current coordination rule

The first read-only intelligence promotion/adoption gate is complete. The next shared intelligence milestone is **not** broader automatic interpretation by default.

Near-term work should proceed in this order unless explicitly reprioritized:

1. define deterministic inference/classification contracts before behavioral or ownership labels;
2. add wallet relationship evidence only with explicit scope, identity, provenance, and non-ownership semantics;
3. add alert rules only after scope/freshness/threshold/persistence/evidence semantics are accepted;
4. continue X1 provider-gap verification and historical redundancy work;
5. mature Solana coverage field-by-field;
6. keep Controlled Execution locked.

## Core integration principle

**CMIS determines what verified evidence supports now.**

**Chain Scouts determine what those accepted CMIS facts mean within their respective chains.**

**Roberta determines what those specialist findings mean for the user and across chains, subject to policy and approval boundaries.**

The system becomes more capable by proving more—not by guessing more.
