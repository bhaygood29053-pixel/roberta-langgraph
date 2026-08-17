# Roberta–CMIS Pre-Trade UX Ownership Contract

## Purpose

Roberta owns the human conversation. CMIS owns deterministic pre-trade market/risk analysis. This document records the accepted boundary after the CMIS bounded pre-trade completion work on 2026-08-17.

The architecture remains:

```text
User
  ↓
Roberta
  ↓
X1 Scout / Solana Scout
  ↓
CMIS
  ↓
Structured deterministic evidence
  ↓
Roberta conversational synthesis
  ↓
Normal human answer
```

CMIS answers:

> What do the verified numbers and deterministic policies say?

Roberta answers:

> What does that mean for the person who asked the question?

Roberta must not become a second market/risk engine. CMIS must not become a conversational assistant.

---

## Accepted CMIS checkpoint

CMIS PRs #120-#124 completed the bounded pre-trade analysis supported by currently verified evidence.

Accepted implementation checkpoint:

- CMIS main SHA: `d4ac9044d087641f94eff3f0a6e693c89b878ca2`
- exact post-merge test run: #408 / `32061851080`, successful

Accepted CMIS integration-contract checkpoint:

- CMIS main SHA: `27b4be7ac1e1c7d52894a07a4d3537599aac81e9`
- exact post-merge test run: #410 / `32062177186`, successful

This is **bounded completion**, not a claim that verified AMM slippage, price impact, routing, fees, or transaction simulation now exist.

---

# Roberta Responsibilities

## R1 — Conversational response synthesis

For a user question such as:

> Is it ok to purchase $500 of AGI?

Roberta should lead with the returned CMIS recommendation/caution in normal language, explain the most important returned evidence, identify material missing evidence, and preserve the analysis-only boundary.

The default response should sound like Roberta, not an internal service dump.

## R2 — Preserve CMIS truth without recomputation

Roberta may:

- summarize deterministic results;
- prioritize returned facts;
- translate `PASS`, `WARN`, `BLOCK`, `partial`, or unavailable evidence into normal language;
- explain uncertainty;
- request additional Scout/CMIS analysis;
- provide practical next steps grounded in the CMIS result.

Roberta must not:

- calculate a replacement notional/liquidity ratio;
- invent slippage, price impact, route quality, bridge dependency, fees, or simulation results;
- turn unavailable execution estimates into zero;
- recalculate or strengthen CMIS confidence;
- convert incomplete evidence into `PASS`;
- manufacture live market facts;
- treat `PASS` as execution authorization.

## R3 — Hide internal diagnostics by default

Normal replies should not lead with service envelopes, verified-check counts, `cmis_promotable`, or implementation diagnostics. Those details belong in explicit technical mode.

## R4 — Preserve technical mode

When the user explicitly asks for technical details, Roberta may show the structured CMIS fields as returned, including null/unavailable execution capabilities. Technical mode still must not invent values.

## R5 — Keep the final voice as Roberta

Do not prefix normal responses with `Liquidity Scout reply:`. The final answer remains Roberta's synthesis of specialist evidence.

## Roberta accepted presentation status

Roberta already has a deterministic `pretrade_ux` presentation layer that copies returned CMIS fields rather than recomputing them. CMIS PR #124 now projects its completed bounded analysis into the stable fields this presenter consumes:

- `data.market`
- `data.trade_size`
- `data.route_analysis`
- `data.execution_capabilities`

Roberta regression coverage must continue to prove that the returned liquidity and size ratio are copied exactly and that unavailable price-impact/slippage/fee fields remain absent/null rather than synthesized.

---

# CMIS Responsibilities — Current Status

## C1 — Make proposed trade amount analytically meaningful — COMPLETE

CMIS now evaluates the requested USD notional against verified asset-wide liquidity when that liquidity is available.

The deterministic quantity is:

```text
notional_to_liquidity_ratio = requested_notional_usd / verified_liquidity_usd
```

The ratio is calculated by CMIS, returned as structured evidence, and projected to `data.trade_size.notional_to_liquidity_ratio` for Roberta.

Missing notional or unverified liquidity remains fail-closed; Roberta does not fill the gap.

## C2 — Explicit trade-size/freshness policy — BOUNDED COMPLETE IN CMIS

CMIS runtime accepts a separate explicit `pre_trade_policy`, distinct from risk policy.

Supported policy fields include:

- `warn_notional_to_liquidity_ratio`
- `block_notional_to_liquidity_ratio`
- `warn_on_missing_notional`
- `block_on_unverified_liquidity_for_sized_trade`
- `warn_risk_age_seconds`
- `block_risk_age_seconds`
- `block_on_unverified_timestamp_when_age_policy_set`
- `required_capabilities`

CMIS deliberately provides **no universal default numeric size ratio or freshness threshold**.

When explicit ratios are provided, CMIS deterministically derives warning/hard-block USD notionals from verified liquidity. When explicit age thresholds are provided, CMIS compares the upstream risk-evidence timestamp to an internal evaluation clock.

Roberta's current typed `pre_trade_check(chain, asset, action, amount_usd)` call uses the CMIS default policy. It does **not yet expose custom `pre_trade_policy` pass-through**. That future integration belongs to Roberta's policy/client layer and must not be approximated with local LLM-generated thresholds.

## C3 — Pool/route-level price-impact analysis — VERIFIED PRODUCER STILL FUTURE

CMIS now exposes a machine-readable `price_impact` capability record. Until a verified route quote or verified pool-depth/curve producer is implemented:

- capability status is `unavailable`;
- value is `null`;
- an explicit reason/evidence requirement is returned.

No price-impact percentage is inferred from asset-wide liquidity alone.

## C4 — Slippage analysis — VERIFIED PRODUCER STILL FUTURE

CMIS now exposes a machine-readable `slippage` capability record. Until verified route/reserve/quote semantics exist:

- capability status is `unavailable`;
- value is `null`;
- the required supporting evidence is explicit.

Missing slippage evidence is not zero.

## C5 — Route quality, bridge dependency, fees, simulation — EXPLICITLY GATED

CMIS now reports explicit capability records for:

- route quality;
- bridge dependency;
- fees;
- transaction simulation.

These remain unavailable/null until verified producers exist.

If an explicit CMIS `pre_trade_policy.required_capabilities` requires an unavailable capability, CMIS fails closed with a `BLOCK` analysis and a `partial` service result rather than manufacturing an answer.

## C6 — Freshness evidence — BOUNDED COMPLETE

With an explicit freshness policy active:

- verified stale evidence may produce deterministic `WARN`/`BLOCK`;
- missing/invalid/future-dated timestamps fail closed as incomplete evidence;
- caller display timestamps cannot replace the risk-evidence timestamp;
- caller `evaluated_at` cannot replace the CMIS runtime clock.

CMIS does not assert a universal freshness window.

## C7 — Public pre-trade projection — COMPLETE

CMIS projects only already-computed evidence into stable user-facing fields:

```text
data.market.verified_liquidity_usd
data.market.verified_volume_24h_usd
data.trade_size.assessment
data.trade_size.notional_usd
data.trade_size.notional_to_liquidity_ratio
data.trade_size.warn_threshold_notional_usd
data.trade_size.hard_block_notional_usd_threshold
data.route_analysis
data.execution_capabilities
```

Unavailable route/slippage/fee values remain `null`.

This projection is not a second market calculation.

## C8 — Execution remains separate — COMPLETE BOUNDARY

Every pre-trade result remains analysis-only:

```text
analysis_only = true
execution_authorized = false
```

No pre-trade `PASS`, size ratio, or freshness result authorizes:

- transaction preparation;
- signing;
- broadcasting;
- wallet custody;
- autonomous live execution;
- value movement.

---

# Shared Interface Contract

Roberta consumes CMIS evidence without recomputing trust.

The accepted public projection now contains fields conceptually equivalent to:

```text
trade:
  side
  notional_usd

market:
  verified_liquidity_usd
  verified_volume_24h_usd

trade_size:
  assessment
  notional_usd
  notional_to_liquidity_ratio
  warn_threshold_notional_usd
  hard_block_notional_usd_threshold
  assessment_complete

route_analysis:
  status
  route_scope
  estimated_price_impact_percent
  estimated_slippage_percent
  estimated_fees

execution_capabilities:
  slippage
  price_impact
  route_quality
  bridge_dependency
  fees
  transaction_simulation

risk:
  recommendation
  confidence
  missing/partial evidence via flags/warnings
```

The ownership rule remains:

- CMIS determines/verifies/calculates the facts.
- Roberta explains them.

---

# Regression Scenarios

Both projects should retain coverage for:

1. `Is it ok to purchase $50 of AGI?`
2. `Is it ok to purchase $500 of AGI?`
3. `Would $2,000 move the AGI market too much?`
4. `Should I sell $1,000 of AGI?`
5. `Show me the technical analysis for that trade.`
6. Missing or unverified liquidity evidence.
7. Stale/missing temporal evidence under an explicit freshness policy.
8. Explicitly required but unavailable slippage/route/simulation capabilities.
9. Conflicting or partial underlying market evidence.

Roberta tests evaluate presentation/truth preservation.

CMIS tests evaluate deterministic calculations, evidence scope, policy behavior, and fail-closed status.

---

# Completion/Handoff State

## Roberta conversational layer

Accepted and already merged. The new CMIS public projection is structurally compatible with its existing deterministic presenter.

## CMIS bounded pre-trade analysis

Accepted and merged through the implementation checkpoint above.

## Remaining future work

The following are future evidence-producer capabilities, not values Roberta or CMIS may guess today:

- verified AMM/pool depth-curve simulation;
- verified slippage calculation;
- verified price-impact calculation;
- route candidate generation/comparison;
- verified fee modeling or quote capture;
- canonical representation/bridge route constraints;
- read-only unsigned transaction simulation.

Roberta custom `pre_trade_policy` pass-through is also a separate future policy/client integration task.

---

## Non-goal

Do not solve missing execution intelligence by making Roberta calculate it or by making CMIS write conversational prose.

**CMIS owns deterministic truth. Roberta owns the human conversation.**
