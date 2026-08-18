# Solana Provider Source Matrix

Status: **design input / contract verification required before production promotion**

This matrix records the provider roles supplied for Phase 10 and how they should fit beneath CMIS. It is intentionally a source-selection map, not a claim that every API contract has already been live-verified.

## Provider roles

| Provider | Intended primary role | Candidate data | Access model | CMIS authority treatment |
|---|---|---|---|---|
| **Solana RPC** | Canonical chain truth | supply, accounts, balances, transactions, program accounts, largest token accounts | RPC | Primary evidence for protocol-exposed on-chain state |
| **Helius** | Primary RPC/indexer | RPC, parsed transactions, wallet history, DAS, historical data, streaming | API key | Indexed/RPC evidence; cross-check canonical state where applicable |
| **Jupiter** | Discovery / price / routes | token metadata, verification indicators, organic score, prices, trading metrics, swap routes | API key | Discovery/market/route evidence; provider labels remain source evidence, not final CMIS risk truth |
| **Birdeye** | Market intelligence | price, market cap, FDV, supply, liquidity, holders, trades, OHLCV, history | API key | Strong market/indexed candidate; scope/freshness must be contract-tested |
| **DEX Screener** | Independent market cross-check | pools, price, liquidity, volume, transactions, changes | Public API | Independent cross-check; not canonical on-chain truth |
| **Raydium** | Direct DEX truth | pools, reserves, pool type, fees, APR, pool vaults | Public API + RPC | Venue-specific direct evidence |
| **Orca** | Direct DEX truth | Whirlpools, TVL, liquidity, volume, fees, tokens | Public API | Venue-specific direct evidence |
| **Meteora** | Direct DEX truth | DLMM/DAMM/DBC pools, liquidity, bins, positions | Public API / SDK | Venue-specific direct evidence |
| **RugCheck** | Security opinion | risk scores and token/market risk information | API | Opinion/evidence only; never final deterministic risk authority |
| **GoPlus** | Security opinion | Solana SPL / SPL-2022 security analysis | API | Opinion/evidence only; never final deterministic risk authority |
| **Bitquery** | Deep index / history | trades, holders, supply, transfers, pools, historical data | GraphQL / API | Historical/indexed evidence; semantics and coverage must be explicit |
| **Allium** | Institutional history | long-horizon Solana datasets, prices, wallets, DEX activity | API / data | Historical/indexed evidence; useful redundancy/deep history |
| **Dune** | Historical analytics / research | decoded transactions, DEX trades, Jupiter routes, SQL research | API / SQL | Analytical/research evidence; query definitions must be versioned/provenanced |
| **Triton** | RPC / real-time / archive | Yellowstone gRPC, historical archive | RPC / gRPC | Candidate low-latency/archive transport and redundancy source |
| **Shyft** | Indexing / streaming | GraphQL program indexes, Yellowstone data | API / gRPC | Candidate indexed/streaming redundancy source |

## Recommended implementation order

The provider should be layered. Do not make one vendor the entire Solana Provider.

### Tier 1 — canonical and core production path

1. **Solana RPC**
   - canonical mint/account/program state
   - total supply / decimals
   - mint and freeze authorities
   - transaction/account observations
   - Token-2022-aware decoding where relevant

2. **Helius**
   - production RPC/indexing candidate
   - parsed transaction/history and DAS-style indexed data
   - holder/account/history/streaming capabilities as separately verified

3. **Jupiter**
   - asset discovery and metadata
   - market price candidate
   - route/quote evidence for later pre-trade work
   - source-provided verification/organic indicators remain non-authoritative inputs

### Tier 2 — market cross-check and aggregate intelligence

4. **Birdeye**
   - broad market/holder/trade/OHLCV candidate
   - useful cross-check for market report and historical comparison

5. **DEX Screener**
   - public independent market cross-check
   - useful for pool/price/liquidity/volume disagreement detection

### Tier 3 — direct venue truth

6. **Raydium**
7. **Orca**
8. **Meteora**

Direct venue adapters should expose pool-scoped facts and vault/reserve semantics. CMIS may aggregate only across explicitly enumerated, non-overlapping scopes. A single venue value must never be labeled as complete `Solana liquidity`.

### Tier 4 — security opinion inputs

9. **RugCheck**
10. **GoPlus**

These sources may contribute flags, scores, or analysis, but they do not own Roberta or CMIS risk policy. CMIS should preserve their exact provenance and compare their claims against canonical/indexed evidence where possible.

### Tier 5 — deep history, archive, and streaming redundancy

11. **Bitquery**
12. **Allium**
13. **Dune**
14. **Triton**
15. **Shyft**

These providers become most valuable for historical comparison, archive redundancy, wallet/transfer research, decoded DEX activity, and streaming. Their cost/credential requirements should not block the read-only core provider.

## Field verification recipes

Initial target recipes should be explicit and field-specific.

### Asset identity

```text
canonical mint address
  + Solana RPC program/account state
  + Helius/Jupiter metadata cross-check when configured
```

Symbols are discovery aliases, not canonical identity.

### Supply / authorities

```text
Solana RPC canonical mint state
  ↔ indexed cross-check (Helius / Birdeye / Bitquery when configured)
```

RPC wins for protocol-exposed current state. A disagreement becomes `CONFLICT`, not an average.

### Price

```text
Jupiter or Birdeye freshness-bound price
  ↔ DEX Screener independent cross-check
  ↔ direct venue pool-implied evidence when semantics are proven
```

Missing/unreliable provider results remain unavailable. Do not substitute zero.

### Liquidity

```text
direct Raydium + Orca + Meteora pool evidence
  + clearly-scoped aggregator/indexed evidence
  → CMIS coverage-aware aggregation
```

Aggregation requires deduplication and explicit venue/pool coverage.

### Volume / trades

```text
venue-specific/direct trades
  ↔ Birdeye / DEX Screener aggregate metrics
  ↔ Bitquery / Dune / Allium historical query when needed
```

Do not sum overlapping aggregate and venue volume.

### Holders

```text
indexed complete-enough holder enumeration
  ↔ alternative indexer/history source
```

`getTokenLargestAccounts` is concentration evidence, not a holder-count substitute.

### Security

```text
canonical authority/program facts
  + liquidity/holder/activity facts
  + RugCheck opinion
  + GoPlus opinion
  → deterministic CMIS risk rules
```

Security-provider scores never directly become Roberta's final risk decision.

## Credential strategy

Provider credentials are runtime dependencies, never repository content.

The engineering order should avoid making credentials a blocker:

- build narrow provider interfaces and deterministic fixture tests first
- use public/canonical sources for initial read-only live probes where practical
- add keyed providers behind explicit configuration
- a missing key yields `unconfigured` / `unavailable`, never fallback to fabricated data
- never log or persist API keys in HXMP, LangGraph state, source provenance, or GitHub

## Promotion principle

A provider can be **registered** before it is **trusted for a CMIS field**. Promotion happens per capability/field only after its exact response schema, units, scope, freshness, error behavior, and provenance have been contract-tested and, where required, read-only live-verified.
