# CMIS Roadmap Sync — refreshed 2026-08-20

This document is Roberta's current integration snapshot of **CMIS — Cross-Chain Market Intelligence Service**. It is a consumption guide for Roberta and Chain Scouts, not a second CMIS roadmap and not authority to promote unaccepted CMIS work.

## Source-of-truth rule

CMIS remains authoritative for freshness-sensitive market, liquidity, tokenomics, verification, provenance, proof-quality, deterministic risk, historical intelligence, and bounded pre-trade facts. Roberta may interpret accepted CMIS results but must not manufacture stronger facts, override fresher CMIS data, recompute CMIS proof/risk, or infer production capability from draft work.

Authority continues to flow:

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Verified information flows upward in the reverse direction.

## Current project position

The earlier Phase-10/Solana draft assumptions in this snapshot are obsolete.

Current accepted state:

- **Roberta Phase 10 — More Specialists / Providers: complete.**
- **Roberta Post-Phase-10 Evidence-Aware Intelligence & User Experience: complete.**
- **CMIS Phase 10 — Solana read-only provider foundation: complete.**
- **CMIS Evidence Receipts + Proof Score milestone: complete.**
- **CMIS X1 evidence-capability boundary: complete and fail-closed.**
- **CMIS deterministic pre-trade trade-size analysis: complete.**
- **CMIS Phase 11 — read-only Verified Intelligence foundation: complete.**
- **Roberta Phase 11 — Controlled Execution: locked / not started.**

CMIS and Roberta use different phase numbering. CMIS Phase 11 completion does **not** mean Roberta Controlled Execution has started.

## Shared Scout / CMIS architecture

Roberta now has two separate supported chain-specialist paths above the same deterministic CMIS layer:

```text
Roberta
  ├── X1 Scout
  │     -> CMIS -> X1 / XDEX providers
  └── Solana Scout
        -> CMIS -> Solana providers
```

The design rule remains: **do not duplicate CMIS per chain**. Chain-specific providers belong beneath shared CMIS contracts; a Chain Scout exists only where chain-specific planning and interpretation are justified.

The Scout -> CMIS boundary is guarded by the machine-readable capability manifest:

```text
GET /v1/cmis/capabilities
```

A chain/service combination is callable only when the live manifest and accepted contract permit it. Missing, malformed, incompatible, or non-callable capability state fails closed.

## X1 status

X1 is the more mature CMIS surface, but evidence completeness remains fact- and scope-specific. Roberta must preserve CMIS classifications such as verified, bounded, partial, unavailable, conflict, or insufficient evidence rather than treating Scout availability as proof that every X1 fact is globally complete.

Examples of deliberately bounded or unavailable areas may include holder/beneficial-owner semantics, archival completeness, selected direct XDEX quote/history semantics, streaming semantics, bridge operational facts, and other provider-specific gaps until CMIS promotes a tested contract.

Provider-reported information remains provider-reported until CMIS establishes the accepted independent-verification basis.

## Solana status

Solana is no longer a fake-only Scout skeleton or an unaccepted draft provider path.

Roberta Phase 10 and the CMIS Solana read-only foundation are complete. Accepted architecture includes:

- a Solana Scout LangGraph specialist path;
- shared typed CMIS client dispatch by explicit chain;
- bounded read-only Scout planning for accepted research services;
- strict runtime/provider configuration gates;
- exact-mint identity where required;
- canonical Solana RPC foundations including SPL Token and Token-2022 handling;
- Jupiter, Helius, and pair-scoped DEX Screener adapters where configured;
- deterministic cross-source checks;
- provenance-safe observation history;
- bounded/partial Solana market, tokenomics, risk, and historical capabilities where advertised.

Solana remains fail-closed and capability-specific. It is not assumed to have X1 parity, and no Solana request may silently fall back to X1.

## Verification evidence and proof quality

The old statement that Roberta's typed client does not expose `verification_evidence` is obsolete.

Roberta has an accepted constrained `verification_evidence` path through the appropriate Scout/typed client boundary. Evidence lookup remains selector-bound and must not become a free-form verifier bypass.

Roberta and Chain Scouts preserve CMIS evidence context including, where available:

- verification state;
- Evidence Receipt identity/provenance;
- Proof Score / proof strength and category reasons;
- scope;
- freshness;
- source disagreements;
- limitations;
- unresolved fields;
- data-quality reasons;
- promotion state.

Risk and proof quality remain separate dimensions. Roberta may explain both but must not recompute either into a new authoritative score.

## Evidence-aware Roberta behavior

The Post-Phase-10 Evidence-Aware Intelligence & User Experience milestone is complete.

Roberta now preserves CMIS evidence context through Chain Scout reports and uses deterministic evidence planning for common recommendation/research questions. Normal answer-first synthesis prioritizes the conclusion, important evidence-backed reasons, actual CMIS risk when supplied, evidence quality, and important missing evidence.

`PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk labels. If CMIS does not return a dedicated risk level, Roberta keeps risk unknown rather than inventing one.

Cross-chain evidence may be compared, but X1 and Solana evidence contexts remain isolated. Roberta must not merge source lists, borrow one chain's freshness/scope for another, recompute a synthetic proof score, or manufacture a cross-chain safety grade.

## CMIS Phase 11 — Verified Intelligence

CMIS Phase 11 established a **read-only Verified Intelligence foundation**. Current accepted primitives include bounded deterministic support for areas such as:

- exact top-account concentration observations and compatible numeric changes;
- neutral verified wallet-activity facts;
- sanitized sparse historical intelligence storage/comparison;
- evidence-bound conclusions backed by Evidence Receipts and Proof Scores.

These primitives are not automatically public Scout services merely because the foundation exists. The capability contract remains authoritative for what Scouts may call.

Roberta must not label wallets/entities as insider, whale, bot, accumulator, distributor, market maker, manipulator, common owner, or equivalent unless a later accepted deterministic classification contract explicitly permits that conclusion from proven evidence.

## Pre-trade analysis status

The deterministic trade-size milestone previously tracked as CMIS Issue #99 is complete.

CMIS can now provide bounded analysis-only pre-trade results using accepted evidence, including requested notional, verified liquidity, notional-to-liquidity ratio, versioned policy where supplied, evidence freshness handling, and explicit capability records for advanced execution-related estimates.

Advanced fields such as expected slippage, price impact, route quality, fees, bridge dependency, fill quality, and simulation remain available only where their exact semantics and evidence gates are independently proven. Missing evidence remains unavailable; it is never converted into zero or an LLM estimate.

Every current pre-trade result preserves the execution boundary equivalent to:

```text
analysis_only = true
execution_authorized = false
```

A CMIS `PASS` is not permission to trade.

## Memory, policy, and approval boundaries

HXMP/LangGraph checkpoints are not authoritative sources for current market facts.

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

No current CMIS/Scout result, Roberta policy decision, or human-review state authorizes:

- transaction construction as an execution path;
- wallet signing;
- transaction broadcasting;
- custody;
- live swap execution;
- autonomous trading;
- bridge/value transfer;
- autonomous value movement;
- broad delegated wallet authority.

If Controlled Execution is ever promoted, it requires a separate accepted transaction-construction/simulation, exact approval-consumption/revalidation, signer/broadcast, replay-protection, precondition, and failure contract.

## Current coordination rule

Near-term work should deepen **read-only** intelligence and provider evidence rather than reopen completed Phase 10 architecture or silently cross into execution.

```text
CMIS
  -> deepen verified X1/Solana evidence and historical intelligence
  -> promote only proven capability-specific contracts
  -> keep Phase 11 intelligence primitives read-only

Roberta
  -> consume capability-gated X1 and Solana Scout results
  -> preserve Evidence Receipts / Proof Scores / limitations
  -> improve policy and user-facing synthesis without recomputation
  -> keep Controlled Execution locked
```

## Core integration principle

**CMIS determines what verified evidence supports now.**

**Chain Scouts determine what those accepted CMIS facts mean within their respective chains.**

**Roberta determines what those specialist findings mean for the user and across chains, subject to policy and approval boundaries.**

The system becomes more capable by proving more—not by guessing more.
