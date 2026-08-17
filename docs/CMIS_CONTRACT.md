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
- `verification_evidence(chain, evidence_id=...)`
- `verification_evidence(chain, fact_type=..., subject_id=...)`

Every operation names its target chain explicitly. Roberta/X1 Scout may have a narrower callable surface than CMIS itself; accepted CMIS runtime capability does not automatically become Roberta client eligibility.

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
      -> CMIS HTTP runtime
        -> CMISGateway
          -> X1 Provider
```

`MockCMISClient` remains a deterministic test adapter, not the production provider path.

Roberta must still preserve fact-level evidence limits. X1 Scout availability does not mean every X1 fact has complete independent verification, holder semantics, observation-scope/freshness proof, streaming coverage, or historical redundancy.

## Verification evidence status

CMIS has accepted the persisted verification-evidence trust and runtime stack:

```text
fact-specific verifier
  -> fail-closed verification_evidence wrapper
  -> sanitized content-addressed evidence ledger
  -> exact read-only lookup
  -> verification_evidence gateway
  -> composed CMIS HTTP runtime
```

CMIS PR #87 accepted the exact gateway boundary. CMIS PR #88 accepted the production HTTP runtime composition. The post-merge CMIS `main` test run for #88 passed on exact merge SHA `08ac97810163168048192665d314cce90f5b89fa`.

The CMIS HTTP runtime advertises `verification_evidence`. Selection is limited to exactly one of:

1. stable `evidence_id`; or
2. exact `fact_type + subject_id` for the latest stored record.

The HTTP caller cannot choose the SQLite path, inject a ledger, submit raw verifier/provider observations, or use a free-form asset selector. CMIS owns storage validation, content-address verification, fact/chain identity checks, timestamps, quality, and promotion state.

Runtime availability does not guarantee that a requested evidence record exists. CMIS does not invent or backfill evidence; an empty ledger or missing exact record remains explicit `unavailable`.

### Roberta client eligibility

Roberta PR #32 accepted the typed-client/X1 Scout eligibility boundary for `verification_evidence`. The post-merge Roberta `main` test run #100 passed on exact merge SHA `18b2b5bf499b23ee26b293c30442cd0dd762c6cb`.

The capability remains intentionally constrained:

- evidence lookup is an **explicit-only** X1 Scout operation;
- the autonomous X1 Scout planner allowlist remains `market_report`, `tokenomics`, and `risk_check`;
- model-proposed `verification_evidence` is rejected;
- the X1 Scout display/request asset is not sent to CMIS as evidence identity;
- the typed HTTP client sends only `service`, `chain`, and the exact evidence selector;
- Roberta must not bypass X1 Scout or call internal CMIS evidence helpers directly.

Roberta must preserve `AGREEMENT`, `CONFLICT`, `INSUFFICIENT_EVIDENCE`, data-quality reasons, freshness/semantics/identity state, warnings/errors, and `cmis_promotable` exactly as returned by CMIS.

## CMIS bounded pre-trade completion checkpoint

CMIS PRs #120-#124 completed the deterministic pre-trade analysis boundary that is supportable by currently verified evidence. The implementation checkpoint is CMIS main SHA `d4ac9044d087641f94eff3f0a6e693c89b878ca2`; its exact post-merge test run #408 (`32061851080`) passed. The source-of-truth integration contract refresh was subsequently accepted on CMIS main SHA `27b4be7ac1e1c7d52894a07a4d3537599aac81e9`, with exact post-merge run #410 (`32062177186`) passing.

CMIS now deterministically supplies, when the required evidence exists:

- the proposed USD notional;
- verified asset-wide liquidity used by the risk result;
- `notional_to_liquidity_ratio`;
- explicit warning/block notional thresholds when an explicit CMIS pre-trade policy supplies the corresponding ratios;
- explicit risk-evidence age analysis when an explicit freshness policy is configured;
- machine-readable execution-capability records for slippage, price impact, route quality, bridge dependency, fees, and transaction simulation;
- stable public projection fields under `data.market`, `data.trade_size`, `data.route_analysis`, and `data.execution_capabilities`.

CMIS does **not** invent universal trade-size thresholds or freshness windows. Verified stale evidence may produce deterministic `WARN`/`BLOCK`; missing required size/liquidity/timestamp evidence remains fail-closed and may make the service `partial`.

The current advanced execution capabilities are explicit `unavailable`/`null` until verified producers exist. Roberta must preserve that state. In particular, it must not turn missing slippage, price-impact, route, fee, bridge, or simulation evidence into zero or into an LLM estimate.

A CMIS pre-trade `PASS` remains analysis-only. CMIS returns `execution_authorized = false`; Roberta must not reinterpret it as permission to prepare, sign, broadcast, or autonomously execute a transaction.

### Current Roberta policy-pass-through caveat

Roberta's current typed `pre_trade_check(chain, asset, action, amount_usd)` path benefits automatically from the completed CMIS default analysis because it supplies the proposed notional and consumes the returned projection.

CMIS runtime also accepts a separate explicit `params.pre_trade_policy`, distinct from risk `params.policy`, for configurable trade-size/freshness/capability requirements. **Roberta's current typed client does not yet expose that custom `pre_trade_policy` mapping.** That is a future Roberta policy-integration task. Roberta must not synthesize threshold values locally to compensate.

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

Roberta can advance provider-neutral orchestration before every CMIS provider is live, but runtime capability must remain gated by accepted CMIS contracts and Roberta client eligibility.

Near-term coordination is:

```text
CMIS: bounded pre-trade analysis accepted -> verified advanced execution producers remain future -> continue trust/history work
Roberta: consume completed pre-trade projection without recomputation -> custom pre_trade_policy pass-through only when deliberately integrated -> continue specialist orchestration
```

Do not duplicate CMIS per chain. Add chain providers beneath shared deterministic contracts and add a Chain Scout only for chain-specific planning and interpretation.
