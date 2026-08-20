# CMIS Contract Boundary

Last refreshed: 2026-08-20

CMIS is Roberta's deterministic cross-chain market-intelligence service layer. Roberta does not own provider collection, fact verification, Evidence Receipt generation, Proof Score calculation, deterministic market risk, bounded pre-trade calculations, or trusted intelligence evidence. Chain specialists select and interpret allowed CMIS operations; CMIS and its chain providers remain authoritative for freshness-sensitive facts.

## Authority path

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Roberta may apply user policy and cross-chain reasoning to accepted CMIS results, but it must not recalculate live market truth, strengthen verification state, recompute proof/risk, or replace unavailable facts from memory or LLM inference.

## Current project status

- Roberta Phase 10 — More Specialists / Providers: complete.
- Roberta Post-Phase-10 Evidence-Aware Intelligence & User Experience: complete.
- CMIS Phase 10 — Solana read-only provider foundation: complete.
- CMIS Evidence Receipts + Proof Score: complete.
- CMIS deterministic pre-trade trade-size analysis: complete.
- CMIS Phase 11 — read-only Verified Intelligence foundation: complete.
- CMIS Phase 12 — first promoted read-only Verified Intelligence service: accepted for X1.
- Roberta Phase 11 — Controlled Execution: **locked / not started**.

CMIS and Roberta use separate phase numbering. CMIS Phase 12 does not grant Roberta execution authority.

## Shared Roberta / Scout service surface

CMIS contract `1.9.0` includes, where the live per-chain capability manifest permits:

- `asset_lookup`
- `market_report`
- `rank`
- `historical_compare`
- `tokenomics`
- `risk_check`
- `pre_trade_check`
- `verification_evidence`
- `concentration_change_intelligence`

Roberta-facing specialist code may deliberately expose a narrower/autonomy-limited operation set than CMIS itself. Every operation names its chain explicitly; no unsupported-chain fallback is permitted.

## Capability handshake

The Chain Scout → CMIS boundary validates runtime eligibility through `GET /v1/cmis/capabilities`.

The accepted boundary requires capability schema `1` and **CMIS contract `1.9.0` or a compatible newer contract**. Scouts fail closed on malformed/incompatible contracts, unknown chains, non-callable services, weakened evidence/proof requirements, or invalid promotion state.

The Phase 11 `intelligence_foundation` remains read-only and unpromoted as a whole (`public_service_promoted=false`, `scout_reliance_promoted=false`). Phase 12 separately promotes one narrow service rather than widening the foundation.

## Result and uncertainty preservation

Roberta preserves service/chain identity, status, facts, risk, confidence, provenance, observation time, warnings/errors, evidence scope/freshness, disagreements, limitations, unresolved fields, Evidence Receipt metadata, and Proof Score metadata. Risk, proof quality, and policy observations remain separate dimensions.

## X1 integration status

The provider-backed X1 runtime path is established:

```text
Roberta -> X1 Scout -> typed CMIS client -> CMIS runtime -> X1/XDEX providers
```

X1 is mature but evidence completeness remains scope-specific. Provider/program/pool/route/account/sample evidence is not automatically asset-wide/global truth.

### Phase 12 X1 concentration-change intelligence

CMIS `1.9.0` promotes:

```text
service: concentration_change_intelligence
contract: concentration_change_intelligence/v1
accepted conclusion: top_account_concentration_change
state: bounded
callable: true
read_only: true
public_service_promoted: true
scout_reliance_promoted: true
execution_authorized: false
```

The service resolves canonical CMIS-owned intelligence evidence by exact identity. Caller-supplied conclusions, complete intelligence bundles, Evidence Receipts, or Proof Scores are not trusted inputs.

The facts preserve observed **top-token-account** scope and must not be presented as unique-holder or beneficial-owner truth. Optional explicit/versioned threshold policy is policy evaluation only; possible threshold observations do not establish market risk, ownership, whale/insider behavior, accumulation, distribution, manipulation, relationship, or intent. `risk` remains separate/null.

## Solana integration status

Roberta Phase 10 and the CMIS Solana read-only provider foundation are complete:

```text
Roberta -> Solana Scout -> typed CMIS client -> CMIS runtime -> Solana providers
```

Accepted foundation includes exact-mint identity, SPL Token/Token-2022 handling, configured Jupiter/Helius/DEX Screener evidence, deterministic cross-source checks, provenance-safe history, and bounded/partial read-only services where advertised.

Solana remains fail-closed and is not assumed to have X1 parity. `concentration_change_intelligence` is currently **unavailable and non-callable on Solana**. No X1 fallback is permitted.

## Verification evidence and evidence-aware behavior

`verification_evidence` has an accepted constrained Scout/typed-client path. Roberta must not bypass CMIS evidence identity, submit raw provider observations as verified proof, choose verification state, or recompute Proof Scores.

The evidence-aware UX milestone remains complete. Roberta may explain evidence and risk but does not collapse them into a synthetic safety grade.

## Phase 11 foundation vs Phase 12 public service

Phase 11 established read-only primitives for concentration/change, neutral wallet activity, sanitized sparse history, and evidence-bound conclusions. Those primitives are **not automatically public Scout services**.

Phase 12 promotes only `concentration_change_intelligence/v1` for X1. It does not promote generic `verified_intelligence`, raw concentration snapshots as a separate service, wallet activity, generic sanitized history, public intelligence-evidence storage/upload, holder/beneficial-owner identity, or behavioral/intent labels.

Roberta must not label wallets/entities as insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, common owner, beneficial owner, or equivalent unless a later accepted deterministic classification contract explicitly permits that conclusion.

## Pre-trade analysis

The deterministic trade-size milestone previously tracked as CMIS Issue #99 is complete. `pre_trade_check` remains evidence-gated analysis only. Missing execution evidence remains unavailable and is never converted into zero, false, or an LLM estimate.

Every current pre-trade result preserves:

```text
analysis_only = true
execution_authorized = false
```

A CMIS `PASS` is not permission to trade.

## Memory and policy boundary

```text
HXMP / memory -> stable context and policy
CMIS          -> current verified facts and evidence
Policy code   -> deterministic rule result
LLM           -> explanation / synthesis only
```

Fresh accepted CMIS/provider evidence overrides remembered or checkpointed live-market values.

## Human approval and Controlled Execution

Phase 9 human approval is exact-proposal review, not a reusable signing credential or wallet permission.

Roberta Phase 11 Controlled Execution has **not started**. No current CMIS result—including the Phase 12 intelligence service—Chain Scout report, Roberta policy decision, or human approval authorizes transaction preparation as an execution path, signing, broadcasting, custody, live swaps, bridge transfer, autonomous trading, or value movement.

## Development coordination

Near-term work should deepen read-only evidence/intelligence while preserving explicit promotion boundaries:

```text
CMIS
  -> deepen X1/Solana evidence
  -> promote new intelligence services only through accepted service-specific contracts
  -> keep unsupported Phase 11 primitives non-public
  -> remain non-executing

Roberta
  -> consume capability-gated X1/Solana results
  -> preserve evidence/proof/risk/policy distinctions
  -> never infer cross-chain capability parity
  -> keep Controlled Execution locked
```

## Core rule

**CMIS determines what verified evidence supports now.**

**Chain Scouts determine what those accepted facts mean within their chains.**

**Roberta coordinates, applies policy, and explains the result to the user.**
