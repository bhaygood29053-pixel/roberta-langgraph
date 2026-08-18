# Solana Provider Requirements — Roberta / CMIS Boundary

Status: **provider path not yet production-enabled**

This document defines what the Solana provider beneath Cross-Chain Market Intelligence Service (CMIS) must prove before Roberta may treat Solana market/tokenomics/risk results as live provider-backed evidence.

The implementation belongs beneath CMIS (currently the `liquidity-scout` codebase during migration), not inside Roberta. Roberta should continue to see only:

```text
Roberta -> Solana Scout -> CMIS -> Solana Provider
```

`solana_provider_enabled=False` remains the safe default until the promotion gates below are satisfied.

## Authority boundary

- **Roberta** owns user goals, policy, cross-specialist coordination, and final synthesis.
- **Solana Scout** owns Solana-specific investigation planning and interpretation.
- **CMIS** owns deterministic freshness-sensitive service contracts, verification state, calculations, uncertainty, timestamps, and provenance.
- **Solana Provider** owns RPC/DEX/indexer/source integrations and raw source verification.
- No provider or Scout may silently manufacture missing price, liquidity, volume, holder, supply, authority, or risk values.

## Required provider capabilities

### 1. Asset identity / `asset_lookup`

The provider must resolve an input symbol/name/mint to a canonical Solana mint identity and preserve ambiguity.

Required evidence:

- canonical mint address
- token program identity (legacy SPL Token vs Token-2022 where applicable)
- decimals
- name/symbol/metadata provenance when available
- deterministic ambiguity handling when a symbol maps to multiple mints

A symbol alone is never sufficient identity for a freshness-sensitive market call.

### 2. Market report

CMIS should be able to produce, when verified and available:

- USD price
- aggregate or clearly-scoped liquidity
- 24h volume
- contributing pool/venue identities
- pool count only when the enumeration method is defined and complete enough to support that claim
- observation time / slot where available
- source-level provenance
- warnings when coverage is partial

The provider must distinguish:

- token-level aggregate metrics
- venue-specific metrics
- pool-specific reserves/liquidity

Those scopes must not be substituted for one another.

### 3. Tokenomics

Required deterministic/on-chain fields where available:

- total token supply
- decimals
- mint authority
- freeze authority
- token program / Token-2022 extensions relevant to transfer or authority risk

Holder count/distribution is a separate indexed capability. If the provider cannot establish complete-enough holder coverage, CMIS must return it as unavailable/partial rather than infer it from the largest-account list.

### 4. Risk check

Provider APIs may supply useful risk indicators, but CMIS remains the deterministic risk authority.

Risk checks should consume verified facts such as:

- mint/freeze authority state
- Token-2022 extension state where relevant
- holder concentration when verified
- liquidity depth/coverage
- market activity/volume
- suspicious-token indicators with explicit provenance
- source conflicts and missing evidence

A third-party `verified`, `organic`, `safe`, or similar label must remain source evidence, not Roberta's final risk decision.

### 5. Historical comparison

Historical data must identify:

- exact source
- metric semantics
- interval/window
- timestamp/slot boundaries
- retention/coverage limits

Deprecated APIs should not be chosen for a new history implementation when a supported replacement exists.

### 6. Pre-trade check

Phase 10 remains read-only. A Solana provider may later support quote/simulation inputs for deterministic pre-trade analysis, but:

- quote data must be freshness-bound and source-attributed
- simulation and quote semantics must be tested against the exact provider contract
- transaction construction/signing/broadcast is not part of the Solana market provider
- execution remains a later Phase 11 concern behind Phase 9 human approval

## Current primary-source candidates

These are candidates/verification inputs, not an automatic final provider selection.

### Solana JSON-RPC

Use canonical on-chain RPC data for chain truth that the protocol exposes directly. Examples include `getTokenSupply`, `getTransaction`, and program/account queries.

Primary documentation:

- https://solana.com/docs/rpc/http/gettokensupply
- https://solana.com/docs/rpc/http/gettransaction
- https://solana.com/docs/rpc/http/getprogramaccounts

Role: canonical on-chain supply/account/transaction evidence and cross-check source.

### Jupiter Price API V3

Jupiter Price V3 returns a single USD price with a block id and deliberately omits tokens when its reliability heuristics do not support a price.

Primary documentation:

- https://developers.jup.ag/docs/price

Important contract behavior:

- missing token keys are an explicit unavailable-price case, not zero
- `blockId` can support recency checks
- Jupiter documents that unreliable/illiquid/untraded tokens may be omitted

Role: candidate market-price source; omission must preserve uncertainty.

### Jupiter Tokens API V2

Jupiter Tokens V2 exposes mint identity/metadata and market/risk-adjacent fields including holder count, total/circulating supply, authority audit fields, liquidity, market cap, volume/activity statistics, and verification/organic indicators.

Primary documentation:

- https://developers.jup.ag/docs/tokens/token-information

Important contract behavior:

- source-provided audit/verification/organic fields remain evidence, not CMIS final policy/risk labels
- token responses are documented as evolving, so CMIS must validate fields fail-closed

Role: candidate indexed token/market evidence and cross-check source.

### Helius RPC / DAS

Helius DAS supports fungible tokens and Token-2022, metadata, ownership/account queries, and indexed asset data. Helius RPC remains compatible with standard Solana JSON-RPC methods.

Primary documentation:

- https://www.helius.dev/docs/api-reference/das
- https://www.helius.dev/docs/das/fungible-token-extension
- https://www.helius.dev/docs/api-reference/endpoints
- https://www.helius.dev/docs/das/get-tokens

Important contract behavior:

- Helius documents DAS token price coverage as limited and cached; cached price data must not be treated as a fresh CMIS market price without an independent freshness contract
- Enhanced Transactions is deprecated for new integrations; new history work should prefer the supported transaction-history/RPC paths documented by Helius

Role: candidate production RPC/indexer plus token/holder/metadata evidence.

### Orca Public API

Orca's public API exposes Whirlpool pool data, token information, protocol analytics, TVL/volume, and pool search without read authentication.

Primary documentation:

- https://docs.orca.so/api-reference/overview
- https://docs.orca.so/api-reference/whirlpools

Role: venue-specific pool/liquidity/volume evidence for Orca; never a complete Solana-wide liquidity claim by itself.

### Raydium API

Raydium documents API v3 as the recommended API generation for new integrations; API v1 is legacy.

Primary documentation:

- https://docs.raydium.io/api-reference/api-v1/overview
- https://docs.raydium.io/llms.txt

Role: candidate Raydium venue/pool evidence. The exact v3 endpoint schemas must be contract-tested before CMIS consumes them.

### Meteora Data APIs

Meteora exposes pool metadata/current state and time-window metrics for its pool families.

Primary documentation:

- https://docs.meteora.ag/api-reference/dlmm/pools/pools
- https://docs.meteora.ag/api-reference/damm-v2/pools/pool

Role: venue-specific pool/liquidity/volume evidence for Meteora; never a complete Solana-wide liquidity claim by itself.

## Verification / aggregation rules

Before CMIS labels Solana evidence as fully verified for a service, the implementation should define the exact verification recipe for that field.

Examples:

- **Supply:** canonical mint/RPC result is primary; indexed source may cross-check.
- **Mint/freeze authority:** decode canonical mint account/program state; indexer may cross-check.
- **Price:** freshness-bound market source plus explicit missing/unreliable handling; cross-source comparison when practical.
- **Liquidity:** aggregate only across explicitly enumerated venues/pools; publish coverage and do not call a single-venue value `Solana liquidity`.
- **Volume:** preserve venue/window semantics and avoid summing overlapping aggregator/venue values.
- **Holder count:** require a defined indexer/enumeration contract; do not equate `getTokenLargestAccounts` with holder count.

Conflicts must remain conflicts. A verifier may return `AGREEMENT`, `CONFLICT`, or `INSUFFICIENT_EVIDENCE`; the LLM must not smooth those states into a stronger claim.

## Promotion gates

Do **not** enable the Solana provider path in Roberta until all applicable gates pass:

1. Provider implementation exists beneath CMIS, not in Roberta.
2. Every supported CMIS operation has deterministic contract tests.
3. Every live response preserves `chain="solana"`, service identity, status, confidence, sources, warnings/errors, and observation time.
4. Asset identity is mint-address based after lookup; ambiguous symbols fail closed.
5. Missing provider fields remain missing/unavailable rather than defaulting to zero/false.
6. Token-2022 behavior is explicitly tested where a supported operation depends on it.
7. At least one read-only live acceptance probe succeeds against known Solana assets for each promoted service class.
8. Live probes contain no signing key and perform no transaction broadcast.
9. Provider/API credentials are environment/configuration secrets and are never committed.
10. CMIS/provider verification results, not remembered values or mock fixtures, are authoritative for current Solana facts.
11. Roberta's existing Phase 8 policy and Phase 9 human-approval tests remain green.
12. `solana_provider_enabled=True` is set only in a runtime whose configured CMIS deployment actually contains the verified Solana provider.

## Initial implementation recommendation

Build the provider incrementally rather than choosing one monolithic vendor:

```text
Solana Provider
  |- canonical Solana RPC layer
  |- indexed token/account layer (candidate: Helius DAS/indexing)
  |- aggregate market identity/price layer (candidate: Jupiter)
  |- venue adapters (Raydium / Orca / Meteora as needed)
  `- deterministic source cross-check / normalization beneath CMIS
```

This keeps CMIS provider-neutral at the service boundary and makes source replacement or redundancy possible without changing Solana Scout or Roberta.

## Non-goals for Phase 10

- wallet custody
- transaction signing
- transaction broadcasting
- autonomous execution
- treating provider marketing labels as Roberta risk policy
- treating a mock fixture as live Solana evidence
