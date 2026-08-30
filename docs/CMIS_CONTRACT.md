# CMIS Contract Boundary

Last refreshed: 2026-08-26

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
- CMIS Phase 11 — read-only Verified Intelligence foundation: complete and non-promoted as a group;
- CMIS Phase 12 — first narrow public-service / Scout-reliance promotion: complete for X1 `concentration_change_intelligence/v1`;
- post-Phase-12 deterministic descriptive classification: complete, internal/read-only/non-promoted;
- post-Phase-12 direct wallet-relationship evidence: complete, internal/read-only/non-promoted;
- post-Phase-12 concentration-threshold alert evidence: complete, internal/read-only/non-promoted;
- Roberta adoption and readiness replay for the promoted X1 service: complete.

Roberta Phase 11 — Controlled Execution remains **locked / not started**.

CMIS currently advertises capability contract **1.13.0**. Roberta keeps a global existing-service minimum of **1.8.0**; the promoted concentration intelligence operation keeps its service-specific minimum of **1.9.0**, legacy X1 all-available historical modes remain compatible from **1.10.0**, normalized exact-mint X1 identity requires **1.11.0**, verified provider-price backfill semantics require the **1.12.0** historical limitation contract, and the upstream Instant X1 Scan promotion requires **1.13.0**.

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
- `instant_x1_scan` — X1-only read-only composition service promoted by CMIS under `instant_x1_scan/v1` / CMIS 1.13.0

A CMIS runtime capability does not become an autonomous Scout action merely because the service exists. Every operation names its target chain explicitly. No unsupported-chain fallback is permitted.

As of 2026-08-30, `instant_x1_scan/v1` is upstream-promoted by CMIS but is **not yet accepted as a Roberta/X1 Scout dispatch operation**. Adoption requires an explicit Scout/client seam and deterministic integration coverage; documentation of the upstream service must not be mistaken for implementation acceptance.

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

The promoted service is a separate Phase 12 wrapper and does not change that foundation-level state.

Roberta does not bypass the Scout boundary to perform provider calls directly.

## X1 normalized exact-mint identity — CMIS 1.11

For address-shaped X1 asset requests, X1 Scout may perform a CMIS `asset_lookup` identity preflight only after the live capability contract proves:

```text
CMIS >= 1.11.0
identity_contract_version = x1_asset_identity/v1
exact_mint_normalization = true
normalized_identity_root = mint
metaplex_xdex_reconciliation = true
```

CMIS remains the only authority that decodes Token Metadata or reconciles Metaplex and XDEX descriptors. X1 Scout validates the returned contract and exact requested mint, then preserves CMIS's normalized identity and reconciliation state without recalculating them.

The accepted reconciliation states are `agreement`, `metaplex_only`, `descriptor_conflict`, `xdex_unavailable`, and `metadata_unavailable`. Same-mint descriptor conflict does not change the mint. XDEX provider unavailability is not treated as proven mint absence. Symbol or name equality never establishes identity across different mints.

Roberta keeps the original requested asset separately from the normalized CMIS identity. On-chain metadata agreement does not become safety, legitimacy, ownership, or project-truth evidence, and URI contents are not treated as verified merely because the URI string is stored on-chain.

If the live CMIS contract is older or weakened, X1 Scout skips normalized-identity reliance rather than substituting its own resolver.

## X1 all-available historical comparison — CMIS 1.10

The public service remains `historical_compare`; no new service or authority layer is introduced.

Accepted X1 modes are:

- `window` — existing explicit period comparison and backward-compatible payload behavior;
- `all_available` — one asset across every verified observation currently available to CMIS;
- `all_available_pair` — two assets compared by CMIS only over their overlapping verified observation window.

Roberta delegates these requests through X1 Scout. For pair history, the second asset is an explicit `compare_asset` copied from the user request/trusted current context. X1 Scout sends a single CMIS pair request and preserves the returned data, warnings, coverage boundaries, Evidence Receipt, Proof Score, and uncertainty state.

Before using either all-available mode, the Scout-side client requires CMIS contract `>=1.10.0` plus the exact accepted X1 historical limitations. It fails closed without a POST if the version or limitations are missing/weakened.

“All available” must never be restated as proven complete token lifetime unless CMIS explicitly proves that stronger claim. `full_asset_lifetime_verified=false` and `continuous_coverage_verified=false` remain authoritative when returned. For CMIS `>=1.12.0`, X1 Scout accepts the narrower verified provider-price backfill contract only when the manifest preserves price-only promotion, non-independence, non-archive-completeness, non-continuity, and historical stable-quote uncertainty. The Scout projects CMIS coverage into deterministic presentation metadata; if verified history exists, Roberta must not describe overall history as zero. Missing history is unknown/unproven, never zero.

## Instant X1 Scan — upstream CMIS 1.13 promotion, Roberta adoption pending

CMIS advertises the exact upstream promotion:

```text
service = instant_x1_scan
service_contract_version = instant_x1_scan/v1
chain = x1
read_only = true
public_service_promoted = true
scout_reliance_promoted = true
execution_authorized = false
```

The wrapper is composition-only and does not create a new provider truth path. Roberta must not call it directly; the accepted path remains `Roberta -> X1 Scout -> CMIS`. Until the X1 Scout/client integration is implemented and reviewed, Roberta must not represent Instant X1 Scan as an available Roberta capability.

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

The operation is explicit-only; it is not added to autonomous X1 Scout planning. A valid request requires exact X1 asset identity plus an exact canonical CMIS-owned `ie_<64 lowercase hex>` intelligence evidence id from the user or trusted current context.

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

Accepted post-Phase-12 internal deterministic foundations also include descriptive concentration-direction classification, direct wallet-relationship evidence with explicit non-ownership semantics, and concentration-threshold alert evidence. These foundations remain internal/read-only/non-promoted and do not become Scout-callable services by implication.

The promoted concentration-change wrapper does **not** establish or authorize:

- total unique-holder coverage;
- beneficial-owner identity;
- whale, insider, bot, accumulator, distributor, market-maker, manipulator, dumper, or common-owner labels;
- intent or behavioral claims;
- risk inferred from Proof Score alone.

Token-account scope remains token-account scope. Missing evidence remains missing.

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

Recent CMIS readiness work accepts a PYUSD Token-2022 fixture contract while keeping largest-account evidence subject to its dedicated RPC/readiness proof.

Solana is not assumed to have X1 parity, and missing Solana capability may never fall back to X1.

## Verification evidence

`verification_evidence` is accepted where the manifest permits it. Evidence lookup remains selector-bound.

Roberta must not bypass the typed Scout/client boundary, call internal CMIS verifier/ledger helpers directly, submit raw provider observations as verified evidence, infer evidence identity from a free-form label, or choose verification state/Proof Score/promotion state.

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

The Phase 12 promoted X1 concentration-change service and Roberta adoption/readiness gate are complete. Deterministic descriptive classification, direct wallet-relationship evidence, and concentration-threshold alert evidence are also complete as internal/read-only/non-promoted CMIS foundations.

There is currently **no accepted next public intelligence/alert service or Scout-reliance promotion**. X1 provider-gap verification and Solana coverage may deepen in parallel under read-only/fail-closed contracts. Any new public wrapper requires a separate CMIS promotion contract plus a separate Roberta/Scout adoption-readiness gate. Controlled Execution stays locked.

## Core rule

**CMIS determines what verified evidence supports now.**

**Chain Scouts determine what those accepted facts mean within their chains.**

**Roberta coordinates, applies policy, and explains the result to the user.**

The system becomes more capable by proving more—not by guessing more.
