# CMIS Contract Boundary

Last refreshed: 2026-08-21

CMIS is Roberta's deterministic cross-chain market-intelligence service layer. Roberta does not own provider collection, fact verification, Evidence Receipt generation, Proof Score calculation, deterministic market risk, or bounded pre-trade calculations. Chain Scouts select and interpret allowed CMIS operations; CMIS and its providers remain authoritative for freshness-sensitive market facts.

For the cross-project status snapshot, see `docs/CMIS_ROADMAP_SYNC_2026-08-17.md`.

## Authority path

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Verified information flows upward in the reverse direction.

Roberta may apply user policy and cross-chain reasoning to accepted CMIS results, but it must not recalculate live market truth, strengthen verification state, recompute proof/risk, or replace unavailable facts from memory or LLM inference.

## Current project and contract status

Accepted milestones include:

- Roberta Phase 10 — More Specialists / Providers: complete;
- Roberta Post-Phase-10 Evidence-Aware Intelligence & User Experience: complete;
- CMIS Phase 10 — Solana read-only provider foundation: complete;
- CMIS Evidence Receipts + Proof Score: complete;
- CMIS deterministic pre-trade trade-size analysis: complete;
- CMIS Phase 11 — read-only Verified Intelligence foundation: complete;
- CMIS Phase 12 — first narrow public-service / Scout-reliance promotion: complete for one X1 service;
- Roberta adoption and readiness replay for that service: complete;
- CMIS deterministic descriptive intelligence classification foundation: complete, internal/read-only/non-promoted;
- CMIS deterministic wallet relationship evidence foundation: complete with explicit non-ownership semantics, internal/read-only/non-promoted;
- CMIS Issue #263 concentration-threshold alert-evidence milestone: active, internal/read-only/non-promoted.

Roberta Phase 11 — Controlled Execution remains **locked / not started**.

CMIS currently advertises capability contract **1.9.0**. Roberta keeps a global existing-service minimum of **1.8.0**, while the promoted concentration operation has a service-specific minimum of **1.9.0**.

## Shared public service surface

The shared CMIS contract includes, where the live chain capability manifest permits:

- `asset_lookup`
- `market_report`
- `rank`
- `historical_compare`
- `tokenomics`
- `risk_check`
- `pre_trade_check`
- `verification_evidence`
- `concentration_change_intelligence` — X1-only bounded promoted service under CMIS 1.9.0

A CMIS runtime capability does not become an autonomous Scout action merely because the service exists. Every operation names its target chain explicitly. No unsupported-chain fallback is permitted.

The accepted deterministic classification, wallet-relationship, and active alert-evidence foundations are intentionally **not** listed as shared public operations because no public-service/Scout-reliance promotion has been accepted for them.

## Capability handshake

The Chain Scout -> CMIS boundary validates runtime eligibility through:

```text
GET /v1/cmis/capabilities
```

Scouts fail closed on unsupported/malformed capability schema, incompatible contract versions, malformed/unclassified chain/service records, explicitly non-callable services, weakened Evidence Receipt / Proof Score declarations, unknown chains, or a promotion record that does not match the accepted service-specific contract.

The core Phase 11 `intelligence_foundation` remains read-only and non-promoted as a group:

```text
public_service_promoted = false
scout_reliance_promoted = false
```

The first promoted service is a separate wrapper and does not change that foundation-level state. Later internal descriptive-classification, wallet-relationship, and alert-evidence foundations also remain non-promoted and do not change the live public service surface.

Roberta does not bypass the Scout boundary to perform provider calls or internal CMIS intelligence-helper calls directly.

## First promoted read-only intelligence service

Accepted X1 service:

```text
service = concentration_change_intelligence
service_contract = concentration_change_intelligence/v1
minimum_cmis_contract = 1.9.0
accepted_conclusion_type = top_account_concentration_change
promotion_scope = cmis_owned_top_account_concentration_change_evidence_by_id
read_only = true
execution_authorized = false
```

Roberta consumes this service only through **X1 Scout**.

The operation is explicit-only; it is not added to autonomous X1 Scout planning. A valid request requires exact X1 asset context plus an exact canonical CMIS-owned `ie_<64 lowercase hex>` intelligence evidence id from the user or trusted current context. Exact canonical asset/evidence binding remains a CMIS/request-contract requirement unless and until Roberta adds a stronger local canonical-identity validator.

The request must not carry caller-supplied intelligence bundles, Evidence Receipts, Proof Scores, provider assertions, behavioral labels, or substitute verification state.

Roberta/X1 Scout requires the live capability record to prove:

- `state=bounded`;
- `callable=true`;
- `read_only=true`;
- `public_service_promoted=true`;
- `scout_reliance_promoted=true`;
- exact service contract and promotion scope;
- exactly the accepted concentration-change conclusion type;
- `execution_authorized=false`.

Solana remains unavailable/non-promoted for this service.

## Result and uncertainty preservation

Roberta preserves CMIS service status and uncertainty semantics, including as applicable:

- service and chain identity;
- status;
- asset/fact identity;
- data;
- deterministic risk when actually supplied;
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

## Verified Intelligence interpretation boundary

CMIS Phase 11 foundations include top-account concentration observations and compatible numeric changes, neutral wallet-activity facts, sanitized sparse intelligence history/comparison, and evidence-bound conclusions.

CMIS has also accepted:

- a deterministic descriptive-classification foundation that may state only the exact concentration direction proven by canonical CMIS evidence;
- a deterministic wallet-relationship foundation that may state only verified observed direct token-transfer interactions between exact chain identities within a compatible bounded evidence set.

Those internal foundations preserve behavior, ownership, intent, fraud/manipulation, risk, public-service, Scout-reliance, and execution boundaries. The wallet-relationship contract specifically does not establish common ownership, beneficial ownership, coordinated control, or complete wallet/graph history.

The promoted concentration-change wrapper and the internal foundations do **not** establish or authorize:

- total unique-holder coverage;
- beneficial-owner identity;
- whale, insider, bot, accumulator, distributor, market-maker, manipulator, dumper, scam, or common-owner labels;
- intent or behavioral claims;
- risk inferred from Proof Score alone.

Token-account scope remains token-account scope. Missing evidence remains missing.

## Active CMIS alert-evidence boundary — Issue #263

CMIS #263 is the active next Verified Intelligence milestone: a deterministic concentration-threshold alert-evidence contract built from accepted canonical concentration evidence plus explicit threshold/comparator policy.

The current milestone is internal/read-only/non-promoted. It must preserve exact chain/asset/evidence identity, scope, freshness, comparator/equality semantics, threshold/policy identity, triggering observations, persistence/repetition semantics where used, provenance, limitations, deterministic content-addressed alert identity, and Proof Score/risk separation.

It does not create a public alert service, grant Scout reliance, change Roberta runtime behavior, imply ownership/behavior/manipulation/fraud/risk severity/imminent price movement, or authorize execution. Any future Roberta alert adoption requires a separate CMIS promotion contract and a separate Roberta roadmap/adoption/readiness gate.

## X1 integration and provider-gap boundary

X1 remains the mature CMIS surface, but completeness is evidence- and scope-specific.

Recent read-only provider-gap observations remain non-promotional:

- the current repository X1.Ninja credential received HTTP `403` / `access_denied` on the bounded SSE handshake probe; no event body or stream semantics were consumed/inferred;
- the same-run XENCAT holder-looking probe observed provider candidate `116`, RPC token-account candidate `180`, and unique token-account-authority candidate `174`; holder semantics, coverage, wallet identity, and beneficial ownership remain unverified;
- Warp Bridge operational state remains unavailable until an exact provenance-approved machine-readable read URL and response contract are accepted.

Roberta must preserve CMIS classifications such as verified, bounded, partial, unavailable, conflict, or insufficient evidence.

## Solana integration status

Roberta Phase 10 and the CMIS Solana read-only provider foundation are complete.

Accepted foundation includes, subject to live capability/configuration gates:

- Solana Scout specialist dispatch and bounded read-only planning;
- exact-mint identity where required;
- canonical Solana RPC token identity/supply/authority evidence;
- SPL Token and Token-2022 handling;
- Jupiter evidence where configured;
- Helius indexed evidence where configured;
- DEX Screener pair-scoped market evidence;
- deterministic cross-source price/supply checks;
- provenance-safe observation history;
- bounded/partial market, tokenomics, risk, and historical services where advertised.

Solana is not assumed to have X1 parity, and missing Solana capability may never fall back to X1.

## Verification evidence

`verification_evidence` is accepted where the manifest permits it. Evidence lookup remains selector-bound.

Roberta must not bypass the typed Scout/client boundary, call internal CMIS verifier/ledger/intelligence helpers directly, submit raw provider observations as verified evidence, infer evidence identity from a free-form label, or choose verification state/Proof Score/promotion state.

Only accepted verified/promotable agreement may expose a promoted fact. Conflict, stale/non-promotable agreement, insufficient evidence, and missing records remain explicit.

## Evidence-aware intelligence boundary

Roberta preserves CMIS evidence context through Chain Scout reports and produces answer-first synthesis without becoming a second CMIS calculation engine.

Normal responses prioritize the conclusion/blocker, important evidence-backed reasons, dedicated CMIS risk when supplied, evidence quality/proof strength, important missing evidence, and deeper technical detail on request.

`PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk labels. If CMIS does not provide a dedicated risk level, Roberta keeps risk unknown rather than inventing one.

## Pre-trade analysis

Where evidence permits, `pre_trade_check` may include requested notional, verified liquidity, notional-to-liquidity ratio, explicit versioned trade-size policy, risk-evidence freshness, and exact route-scoped facts that pass their own evidence gates.

Missing advanced evidence is not converted into zero, false, a guessed value, or an LLM estimate.

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

Fresh accepted CMIS/provider evidence overrides remembered, checkpointed, or conversational market values.

## Human approval and execution boundary

Phase 9 human review is an exact proposal/scope review boundary. It is not a reusable signing credential, wallet permission, or broad future authority.

Roberta Phase 11 Controlled Execution has **not started**.

No current CMIS result, Chain Scout report, Roberta policy decision, or human approval authorizes transaction preparation as a live execution path, wallet signing, broadcasting, custody, live swaps, autonomous trading, bridge transfer, autonomous value movement, or broad delegated wallet authority.

## Development coordination

The promoted read-only concentration service, Roberta adoption/readiness gate, deterministic descriptive classification foundation, and deterministic wallet-relationship evidence foundation are complete at their accepted boundaries.

The active upstream intelligence milestone is **CMIS #263 — deterministic concentration-threshold alert evidence**, internal/read-only/non-promoted. Public-service/Scout-reliance promotion and Roberta adoption remain separate later steps.

X1 provider-gap verification under CMIS #30 and Solana coverage can deepen in parallel. Controlled Execution stays locked.

## Core rule

**CMIS determines what verified evidence supports now.**

**Chain Scouts determine what those accepted facts mean within their chains.**

**Roberta coordinates, applies policy, and explains the result to the user.**

The system becomes more capable by proving more—not by guessing more.
