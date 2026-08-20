# CMIS Contract Boundary

Last refreshed: 2026-08-20

CMIS is Roberta's deterministic cross-chain market-intelligence service layer. Roberta does not own provider collection, fact verification, Evidence Receipt generation, Proof Score calculation, deterministic market risk, or bounded pre-trade calculations. Chain specialists select and interpret allowed CMIS operations; CMIS and its chain providers remain authoritative for freshness-sensitive market facts.

For the current cross-project status snapshot, see `docs/CMIS_ROADMAP_SYNC_2026-08-17.md`.

## Authority path

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Verified information flows in the reverse direction.

Roberta may apply user policy and cross-chain reasoning to accepted CMIS results, but it must not recalculate live market truth, strengthen verification state, recompute proof/risk, or replace unavailable facts from memory or LLM inference.

## Current project status

The accepted boundary now reflects these completed milestones:

- Roberta Phase 10 — More Specialists / Providers: complete;
- Roberta Post-Phase-10 Evidence-Aware Intelligence & User Experience: complete;
- CMIS Phase 10 — Solana read-only provider foundation: complete;
- CMIS Evidence Receipts + Proof Score milestone: complete;
- CMIS deterministic pre-trade trade-size analysis: complete;
- CMIS Phase 11 — read-only Verified Intelligence foundation: complete.

Roberta Phase 11 — Controlled Execution remains **locked / not started**.

CMIS and Roberta use separate phase numbering. CMIS Phase 11 completion does not grant Roberta execution authority.

## Shared Roberta / Scout service surface

The shared CMIS contract includes, where the live chain capability manifest permits:

- `asset_lookup`
- `market_report`
- `rank`
- `historical_compare`
- `tokenomics`
- `risk_check`
- `pre_trade_check`
- `verification_evidence`

Roberta-facing specialist code may deliberately expose a narrower operation set than CMIS itself. A CMIS runtime capability does not become an autonomous Scout action merely because the service exists.

Every operation names its target chain explicitly. No unsupported-chain fallback is permitted.

## Capability handshake

The Chain Scout -> CMIS boundary validates runtime eligibility through:

```text
GET /v1/cmis/capabilities
```

The accepted boundary requires capability schema `1` and CMIS contract `1.8.0` or a compatible newer contract.

Scouts fail closed on:

- unsupported or malformed capability schema;
- an incompatible contract version;
- malformed or unclassified chain/service records;
- explicitly non-callable services;
- weakened Evidence Receipt / Proof Score declarations;
- missing or improperly promoted Phase 11 `intelligence_foundation` boundaries;
- unknown chains.

`intelligence_foundation` is read-only and remains outside ordinary `supported_services` unless a later accepted contract deliberately promotes a public Scout service.

Roberta does not bypass the Scout boundary to perform capability discovery or provider calls directly.

## Result and uncertainty preservation

Roberta preserves CMIS service status and uncertainty semantics, including as applicable:

- service and chain identity;
- status;
- asset/fact identity;
- data;
- deterministic risk;
- confidence;
- sources/provenance;
- observation time;
- warnings and errors;
- evidence scope and freshness;
- disagreements and limitations;
- unresolved fields;
- Evidence Receipt metadata;
- Proof Score / proof-strength metadata.

Unavailable facts remain unavailable. Provider/service failure must not authorize an LLM to invent a value.

Risk and proof quality are separate dimensions. Roberta may explain both but must not recompute them into a second authoritative score.

## X1 integration status

The provider-backed X1 runtime path is established:

```text
Roberta
  -> X1 Scout
    -> typed CMIS client
      -> CMIS HTTP runtime
        -> CMIS gateway/services
          -> X1 / XDEX providers
```

Deterministic mocks remain test adapters, not production provider truth.

X1 is the mature CMIS surface, but completeness is evidence- and scope-specific. X1 Scout availability does not mean every X1 fact has complete independent verification, beneficial-owner holder semantics, archival completeness, live-stream semantics, route semantics, bridge evidence, or historical redundancy.

Roberta must preserve CMIS classifications such as verified, bounded, partial, unavailable, conflict, or insufficient evidence.

## Solana integration status

The previous statement that Solana was only a draft/fake Scout path is obsolete.

Roberta Phase 10 and the CMIS Solana read-only provider foundation are complete. The accepted path is:

```text
Roberta
  -> Solana Scout
    -> typed CMIS client
      -> CMIS HTTP runtime
        -> CMIS gateway/services
          -> Solana providers
```

Accepted foundation includes, subject to live capability/configuration gates:

- Solana Scout specialist dispatch and bounded read-only planning;
- exact-mint identity where required;
- canonical Solana RPC token identity/supply/authority evidence;
- SPL Token and Token-2022 handling;
- Jupiter read-only evidence when configured;
- Helius indexed evidence when configured;
- DEX Screener pair-scoped market evidence;
- deterministic cross-source price and supply checks;
- provenance-safe observation history;
- bounded/partial market, tokenomics, risk, and historical services where advertised.

Solana production composition remains environment-controlled and fail-closed. Solana is not assumed to have X1 parity, and missing Solana capability may never fall back to X1.

Pair-scoped or provider-scoped Solana evidence must not be relabeled as asset-wide/global truth without an accepted aggregation contract.

## Verification evidence

CMIS has an accepted persisted verification-evidence stack and the public contract includes `verification_evidence` where the capability manifest permits it.

Roberta has an accepted constrained path through the appropriate Scout/typed client boundary. The old statement that Roberta does not expose this operation is obsolete.

Evidence lookup remains selector-bound. Roberta must not:

- bypass the typed Scout/client boundary;
- call internal CMIS verifier/ledger helpers directly;
- submit raw verifier/provider observations as if they were verified evidence;
- infer evidence identity from a free-form asset label;
- choose verification state, Proof Score, confidence, or promotion state.

Only accepted verified/promotable agreement may expose a promoted fact. Stale/non-promotable agreement, conflict, insufficient evidence, and missing records remain explicit.

Roberta and Scouts preserve source identity/role, verification state, proof strength, observation time/chain position where available, freshness, scope, disagreements, limitations, unresolved fields, warnings/errors, and promotion state.

## Evidence-aware intelligence boundary

The Post-Phase-10 Evidence-Aware Intelligence & User Experience milestone is complete.

Chain Scout reports can preserve CMIS `evidence_context` for X1 and Solana. Roberta uses that evidence context to produce answer-first synthesis without becoming a second CMIS calculation engine.

Recommendation-style responses prioritize:

1. conclusion / recommendation / blocker;
2. the most important evidence-backed reasons;
3. dedicated CMIS risk when actually supplied;
4. evidence quality / proof strength;
5. important missing evidence;
6. deeper technical evidence on request.

`PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk labels. If CMIS does not provide a dedicated risk level, Roberta keeps risk unknown rather than inventing one.

Cross-chain evidence may be compared, but X1 and Solana evidence contexts may not be merged into a synthetic source set, proof score, freshness state, risk calculation, or safety grade.

## CMIS Phase 11 Verified Intelligence

CMIS Phase 11 established a read-only Verified Intelligence foundation for deterministic primitives such as:

- exact top-account concentration observations and compatible numeric changes;
- neutral verified wallet-activity facts;
- sanitized sparse intelligence history/comparison;
- evidence-bound conclusions backed by Evidence Receipts and recomputed Proof Scores.

These primitives are not automatically promoted into public Scout services.

Roberta must not infer or present labels such as insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, common owner, or equivalent unless a later accepted evidence/classification contract explicitly permits that conclusion from proven evidence.

Facts and interpretations remain separate.

## Pre-trade analysis

The deterministic trade-size milestone previously tracked as CMIS Issue #99 is complete.

Where the required evidence and policy contract permit, `pre_trade_check` may include:

- requested USD notional;
- verified liquidity;
- notional-to-liquidity ratio;
- explicit versioned trade-size policy/classification;
- risk-evidence freshness handling;
- machine-readable capability records for advanced execution-related facts;
- stable structured projection for Roberta to explain.

CMIS does not invent universal trade-size thresholds or hidden freshness windows.

Advanced fields remain evidence-gated. Depending on the exact accepted route/evidence scope, selected price-impact or bounded fee evidence may exist; expected execution slippage, route quality, bridge dependency, fill quality, transaction simulation, generic execution quality, or other execution estimates remain unavailable unless separately proven.

Missing evidence is not converted into zero, false, a guessed value, or an LLM estimate.

Every current pre-trade result preserves the equivalent of:

```text
analysis_only = true
execution_authorized = false
```

A CMIS `PASS` means only that the deterministic checks actually performed did not produce WARN/BLOCK. It is not permission to trade.

Roberta explains the structured result; it does not recalculate replacement size ratios, proof, deterministic risk, price impact, fees, slippage, routes, or simulation.

## Memory and policy boundary

HXMP/durable memory may retain stable user policy, goals, preferences, approval rules, and structural contracts. It is not authoritative for current prices, liquidity, volume, holders, supply, authorities, risk, proof, or other freshness-sensitive market facts.

```text
HXMP / memory -> stable context and policy
CMIS          -> current verified facts and evidence
Policy code   -> deterministic rule result
LLM           -> explanation / synthesis only
```

Fresh accepted CMIS/provider evidence overrides remembered, checkpointed, or conversational market values.

## Human approval boundary

Phase 9 human review supports exact proposal/scope approval and resumable review state.

An approval means a human reviewed one exact proposal. It is not a reusable signing credential, wallet permission, or broad future authority.

Analysis and approval remain separate from execution.

## Controlled Execution boundary

Roberta Phase 11 Controlled Execution has **not started**.

No current CMIS result, Chain Scout report, Roberta policy decision, or human approval authorizes:

- transaction preparation as a live execution path;
- wallet signing;
- transaction broadcasting;
- custody;
- live swap execution;
- autonomous trading;
- bridge transfer;
- autonomous value movement;
- broad delegated wallet authority.

If Controlled Execution is ever promoted, it requires a separate accepted transaction-construction/simulation, exact approval-consumption/revalidation, signer/broadcast, replay-protection, precondition, and failure contract.

## Development coordination

The current coordination rule is no longer “build a Solana skeleton while waiting for CMIS.” That milestone is complete.

Near-term work should deepen read-only intelligence and provider evidence while preserving the completed shared architecture:

```text
CMIS
  -> deepen capability-specific X1/Solana verification
  -> deepen historical and Verified Intelligence primitives
  -> promote only evidence-backed public services
  -> remain analysis-only / read-only with respect to execution

Roberta
  -> consume capability-gated X1 and Solana Scout results
  -> preserve Evidence Receipts / Proof Scores / limitations
  -> improve policy and user-facing synthesis without recomputation
  -> keep Controlled Execution locked
```

Do not duplicate CMIS per chain. Add chain providers beneath shared deterministic contracts and add a Chain Scout only for chain-specific planning and interpretation.

## Core rule

**CMIS determines what verified evidence supports now.**

**Chain Scouts determine what those accepted facts mean within their chains.**

**Roberta coordinates, applies policy, and explains the result to the user.**

The system becomes more capable by proving more—not by guessing more.
