# CMIS Roadmap Sync — refreshed 2026-09-01

This document is Roberta's current CMIS integration snapshot. It is a consumption guide, not a second CMIS roadmap. The authoritative CMIS living roadmap remains in the CMIS repository.

## Canonical hierarchy

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Roberta owns orchestration, user policy, specialist selection, cross-chain synthesis, learning-workflow coordination, approval boundaries, and the final user-facing answer.

Chain Scouts own chain-specific planning and interpretation.

CMIS owns deterministic freshness-sensitive facts, evidence, Evidence Receipts, Proof Scores, risk, capability state, historical intelligence, and bounded analysis-only pre-trade calculations.

Fresh accepted CMIS/provider evidence overrides remembered values and static-learning state when freshness matters. Missing evidence remains unknown/unavailable. Proof Score remains separate from risk.

## Current synchronized CMIS state

Accepted CMIS state consumed by Roberta includes:

- CMIS capability contract `1.13.0`;
- Solana read-only provider foundation complete;
- Evidence Receipts + Proof Score complete;
- deterministic pre-trade trade-size analysis complete;
- Phase 11 Verified Intelligence foundation complete, read-only/non-promoted as a group;
- first narrow X1 promoted intelligence service complete: `concentration_change_intelligence/v1`;
- X1 all-available historical comparison complete from CMIS `1.10.0`;
- exact-mint normalized X1 identity complete under `x1_asset_identity/v1` from CMIS `1.11.0`;
- bounded verified-provider historical price backfill semantics complete under CMIS `1.12.0`;
- bounded X1 `instant_x1_scan/v1` composition complete under CMIS `1.13.0`;
- deterministic X1 burn metrics, scanner time-coverage wiring, circulating-supply evidence, and exact historical burn-time valuation accepted in CMIS tokenomics;
- Roberta/X1 Scout `x1_burn_intelligence/v1` accepted as a non-recomputing product projection over that CMIS tokenomics evidence;
- Oracle V2 structural/timestamp/freshness governance complete for the accepted evidence policy, with current-price use still unauthorized because the latest accepted live relay slots were stale;
- CMIS public-shell/private-core migration and historical Git cleanup complete.

Controlled Execution remains locked/not started.

## Service-specific compatibility

```text
global existing-service minimum = 1.8.0
concentration_change_intelligence minimum = 1.9.0
all_available history minimum = 1.10.0
x1_asset_identity/v1 minimum = 1.11.0
verified provider-price backfill semantics = 1.12.0
instant_x1_scan/v1 minimum = 1.13.0
```

Roberta/Scouts must use the live capability manifest and fail closed on incompatible or weakened service-specific contracts.

## Promoted X1 concentration intelligence

The accepted promoted service remains exactly bounded:

```text
service = concentration_change_intelligence
service_contract = concentration_change_intelligence/v1
chain = x1
read_only = true
public_service_promoted = true
scout_reliance_promoted = true
accepted_conclusion_type = top_account_concentration_change
promotion_scope = cmis_owned_top_account_concentration_change_evidence_by_id
execution_authorized = false
```

It does not establish beneficial ownership, behavioral labels, intent, fraud/manipulation, or risk by implication.

Solana remains unavailable/non-promoted for this service.

## Instant X1 Scan

CMIS `1.13.0` adds:

```text
service = instant_x1_scan
service_contract = instant_x1_scan/v1
chain = x1
read_only = true
composition_only = true
execution_authorized = false
```

The service composes already accepted identity, market, tokenomics, CMIS-stored verified history, deterministic risk, and runtime evidence-quality metadata.

It does not create new underlying fact authority. Missing/unverified holder or current-concentration fields remain explicit unknown/partial values.

Roberta should consume it only through the accepted X1 Scout -> CMIS path.

## X1 burn intelligence

CMIS has accepted deterministic burn metrics, compatible scanner fact-time coverage, deterministic circulating-supply evidence, and exact historical burn-time valuation. Valuation completeness remains denomination-specific and fails closed when compatible burn-time price evidence is missing; no current-price, nearest-price, or interpolation substitute is accepted.

Roberta public `main` now includes X1 Scout `x1_burn_intelligence/v1`, a deterministic projection over the accepted CMIS `tokenomics` envelope. It preserves exact mint identity, burn windows/comparisons, circulation/valuation completeness, evidence and limitations, and `execution_authorized=false` without recomputing CMIS facts.

The next product gate is to map that Scout projection into the Canonical ROBERTA Decision Object and Human/Machine BURN renderers. That integration remains a Roberta-layer concern, not a new CMIS service.

## X1 history and identity

### Historical compare

Accepted X1 modes:

- `window`;
- `all_available`;
- `all_available_pair`.

“All available” means every verified observation currently available to CMIS, not automatically complete token lifetime.

For CMIS `>=1.12.0`, bounded provider backfill may extend price only. Provider source independence, archive completeness, continuous coverage, historical USD-stable behavior, and complete asset lifetime remain unverified unless separately proven.

### Exact-mint identity

For address-shaped X1 requests, exact mint remains the fungible identity root. Metaplex and XDEX descriptors remain separately sourced observations. Descriptor agreement does not establish legitimacy or safety, and provider unavailability is not token absence.

## Oracle V2 provider-gap state

Accepted read-only Oracle V2 evidence establishes:

- verified X1 program/state ownership and structure;
- six assets × five relay slots;
- verified decimals and stored Oracle key;
- Unix-millisecond timestamp semantics;
- explicit freshness policy:

```text
max_age_ms = 60000
max_future_skew_ms = 5000
minimum_eligible_slots = 3
```

The latest accepted live run classified all 30 observed relay slots stale. Therefore:

```text
current_price_use_authorized = false
price_correctness_verified = false
source_independence_verified = false
cmis_provider_promoted = false
public_service_promoted = false
scout_reliance_promoted = false
execution_authorized = false
```

Do not weaken freshness policy to manufacture eligibility. Relay count is not independent-source count.

## Roberta Learning Plane dependency

Roberta Learning System Phases 1-10 and the autonomous source-grounded Learning Plane controller are accepted.

MB4E operator-local source mastery is complete:

```text
required stages passed = 14 / 14
final source capstone = passed
```

Repository-accepted prebuilt banks remain through Stage 8 / Market Structure. Runtime-generated Stages 9-14 are valid mastery evidence under the accepted controller but are not thereby promoted into separately accepted prebuilt repository banks.

Authoritative read-only autonomous-training telemetry is accepted under `roberta-autonomous-training-telemetry/v1` and preserves `execution_authorized=false`.

Learning remains a separate authority plane. It cannot self-authorize CMIS contracts, provider trust, Scout promotion, fresh chain truth, wallet permissions, or execution.

## Public/private CMIS runtime boundary

The six-phase CMIS public-shell/private-core migration is complete.

The public package fails closed when protected private-core implementation is unavailable. No public reconstruction fallback is accepted.

This source/deployment boundary does not change the authority hierarchy or service semantics.

## Internal non-promoted CMIS foundations

Accepted internal/read-only foundations include:

- deterministic descriptive concentration-direction classification;
- direct wallet-relationship evidence with explicit non-ownership/non-beneficial-owner semantics;
- concentration-threshold alert evidence.

These do not become Scout-callable or public services by implication.

## Execution boundary

No Learning Plane result, source material, retained lesson, learned concept, CMIS result, Scout report, Evidence Receipt, Proof Score, risk result, alert, pre-trade `PASS`, policy decision, or human approval authorizes transaction construction, signing, broadcasting, custody, trading, bridge transfer, or autonomous value movement.

## Core sync rule

**Roberta may learn from static evidence and CMIS may verify changing chain facts, but neither learning nor analysis self-promotes into a new authority boundary. Fresh accepted CMIS/provider evidence wins for freshness-sensitive state, and every public-service, operational-trust, wallet, or execution promotion remains separately gated.**
