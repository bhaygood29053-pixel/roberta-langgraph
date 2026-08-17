# CMIS Contract Boundary

CMIS is Roberta's deterministic cross-chain market-intelligence service layer. Roberta does not own provider collection or fact verification. Chain specialists such as X1 Scout select and interpret CMIS operations, while CMIS and its chain providers remain authoritative for freshness-sensitive market facts.

For the current CMIS roadmap integration snapshot, see `docs/CMIS_ROADMAP_SYNC_2026-08-17.md`.

## Authority path

```text
Roberta -> Chain Scout -> CMIS -> Chain Provider
```

Verified information flows in the reverse direction.

Roberta may apply user policy and cross-chain reasoning to accepted CMIS results, but it must not recalculate live market truth, strengthen verification state, or replace unavailable facts from memory or LLM inference.

## Current Roberta operations

The Roberta-side typed client currently defines:

- `market_report(chain, asset)`
- `tokenomics(chain, asset)`
- `risk_check(chain, asset)`
- `pre_trade_check(chain, asset, action, amount_usd)`

Every operation names its target chain explicitly. Roberta/X1 Scout may have a narrower callable surface than CMIS itself; internal CMIS capability does not automatically become Roberta runtime eligibility.

`pre_trade_check` is analysis only. It does not authorize signing, broadcasting, or value movement.

## Result envelope

Roberta preserves the CMIS service envelope and its uncertainty semantics, including:

- `service`
- `chain`
- `status`
- `asset`
- `data`
- `risk`
- `confidence`
- `sources`
- `observed_at`
- `warnings`
- `errors`

Unavailable facts remain unavailable. Provider/service failure must not authorize an LLM to invent a value.

## X1 integration status

The provider-backed X1 runtime path is established through the separate Liquidity Scout/CMIS deployment:

```text
Roberta
  -> X1 Scout
    -> CMISHTTPClient
      -> CMISGateway
        -> X1 Provider
```

`MockCMISClient` remains a deterministic test adapter, not the production provider path.

Roberta must still preserve fact-level evidence limits. X1 Scout availability does not mean every X1 fact has complete independent verification, holder semantics, observation-scope/freshness proof, streaming coverage, or historical redundancy.

## Verification evidence status

CMIS has accepted the internal trust stack for persisted verification evidence:

```text
fact-specific verifier
  -> fail-closed verification_evidence wrapper
  -> sanitized content-addressed evidence ledger
  -> exact read-only lookup
```

Accepted internal lookup selectors are:

1. stable `evidence_id`; or
2. exact `fact_type + subject_id` for the latest stored record.

This internal acceptance does **not** yet make `verification_evidence` a production Roberta-callable operation. CMIS pull request #87 is the current draft gateway-eligibility slice. Until that slice is accepted, deployed, and reflected in Roberta runtime eligibility, Roberta must not call internal evidence helpers directly or submit raw provider/verifier objects.

Roberta must preserve `AGREEMENT`, `CONFLICT`, `INSUFFICIENT_EVIDENCE`, data-quality reasons, freshness/semantics/identity state, warnings/errors, and `cmis_promotable` exactly as returned by CMIS.

## Solana boundary

Solana Provider work is in CMIS development, but Solana is not yet a production Roberta market-data path.

Roberta Phase 10 may build provider-neutral specialist contracts and a Solana Scout skeleton using deterministic fake or explicit unavailable CMIS results. It must not make direct Solana RPC/DEX/indexer calls or manufacture live Solana facts while the CMIS Solana Provider remains unaccepted/unconfigured.

No fallback from a Solana request to X1 is permitted.

## Memory and policy boundary

HXMP/durable memory may retain stable user policy, goals, preferences, approval rules, and CMIS structural contracts. It is not authoritative for current prices, liquidity, volume, holders, supply, authorities, risk, or other freshness-sensitive market facts.

```text
Memory remembers what matters.
CMIS verifies what is happening now.
```

Fresh accepted CMIS/provider evidence overrides remembered or conversational market values.

## Development coordination

Roberta can advance provider-neutral orchestration before every CMIS provider is live, but runtime capability must remain gated by accepted CMIS contracts.

Near-term coordination is:

```text
CMIS: finish X1 trust gaps -> provenance-aware history -> provider maturity
Roberta: Phase 10 specialist registry -> Solana Scout skeleton -> live eligibility after CMIS acceptance
```

Do not duplicate CMIS per chain. Add chain providers beneath shared deterministic contracts and add a Chain Scout only for chain-specific planning and interpretation.
