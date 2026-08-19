# Read-Only Decision Production Readiness

Tracking: issue #62

## Purpose

This evaluation layer proves whether the accepted Roberta Decision Quality stack behaves reliably under realistic read-only operating conditions. It observes the existing runtime; it does not add a new agent, provider, decision authority, or execution capability.

Authority remains:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

CMIS remains authoritative for freshness-sensitive facts, status, proof/evidence metadata, risk, provenance, warnings, conflicts, and unavailable states.

## Solution

The readiness harness has four parts:

1. **Versioned scenario corpus** — `evals/read_only_decision_v1.json`
2. **Transparent observation wrappers** — model and CMIS wrappers record calls, latency, retry instructions, service status, and transport errors without changing payloads.
3. **Existing LangGraph runtime** — scenarios run through the same `build_graph`, Chain Scout tools, capability handshake, CMIS HTTP client, and configured runtime model used by the live application.
4. **Historical JSON report** — every run records pass/fail checks, service coverage, chain isolation, model/CMIS timing, retry/fail-closed counts, final user answer, and deployment blockers.

The generated report is explicitly marked:

```text
authority = historical_evaluation_snapshot
live_market_authority = false
```

It must never be reused as current market truth.

## Representative corpus

Version 1 covers:

- X1 buy decision
- X1 sell decision
- explicit X1 trade-size/pre-trade question
- X1 token risk
- X1 safer-asset comparison
- X1 liquidity risk
- X1 LP decision
- X1 market change
- X1 price-move explanation
- technical/source/provenance follow-up
- non-market control question
- optional X1/Solana cross-chain risk/evidence comparison when the Solana runtime gate is enabled

The corpus names only the accepted read-only CMIS services. Corpus validation rejects unknown/execution-like service names.

## What is measured

For each scenario the harness records:

- total wall-clock latency
- Oracle model call count and model time
- Oracle decision-presentation retry count
- Scout planner model call count and model time
- CMIS service calls, chain, service status, service time, and transport error type
- expected service coverage
- chain isolation
- accepted answer-first presentation guard compliance
- Risk / Evidence quality separation when required
- whether material uncertainty appeared in specialist/CMIS evidence
- whether the final answer disclosed uncertainty when normal-mode evidence was degraded
- whether the answer promised signing/broadcast/execution
- whether the deterministic fail-closed response was used

Latency and retries are measured separately from decision correctness.

## Running the live evaluation

Prerequisites:

- Roberta installed with the configured model provider extras
- `DEEPSEEK_API_KEY`
- a running accepted CMIS gateway
- `CMIS_BASE_URL` if it is not the default local gateway
- `CMIS_API_KEY` when the gateway requires it
- optional `ROBERTA_SOLANA_PROVIDER_ENABLED=1` only when the deployed Solana CMIS path has passed its capability gates

Run:

```bash
roberta-readiness
```

Default corpus:

```text
evals/read_only_decision_v1.json
```

Default report:

```text
artifacts/readiness/latest.json
```

Run one scenario:

```bash
roberta-readiness --scenario x1-risk
```

Use a different output path:

```bash
roberta-readiness --output artifacts/readiness/2026-08-19.json
```

The command exits non-zero when a completed scenario fails deterministic readiness checks. Solana-required scenarios are recorded as skipped when the explicit Solana runtime gate is disabled.

## Interpreting results

A scenario can receive `partial`, `unavailable`, `ambiguous`, or other degraded CMIS states and still demonstrate correct Roberta behavior if the path completes and the answer preserves the uncertainty. A provider degradation is not permission to fabricate a cleaner conclusion.

A deployment blocker is recorded when an expected decision scenario violates one or more readiness checks, including:

- required service path not exercised
- silent chain substitution
- diagnostic/raw-first normal answer
- Risk and Evidence quality not kept separate
- degraded evidence hidden from the user
- execution-like promise in the answer
- graph not reaching a usable final response

CMIS `status=error` and transport exceptions are also counted separately as provider/runtime error events so infrastructure health does not get confused with answer correctness.

## Evidence needed to close issue #62

The harness is the measurement mechanism, not by itself the completion evidence. Issue #62 should close only after one or more reproducible live reports show:

1. all required X1 decision families complete through the configured Scout -> CMIS path;
2. the configured production model satisfies the normal answer-first contract at an acceptable rate;
3. observed retry/fail-closed frequency is understood;
4. degraded states remain explicit and do not become fabricated facts;
5. no silent chain substitution occurs;
6. enabled cross-chain scenarios preserve chain isolation;
7. technical follow-up preserves progressive disclosure;
8. latency and provider-error behavior are understood well enough for deployment;
9. no execution boundary is crossed.

Recurring failures should be fixed narrowly or recorded as deployment blockers before the roadmap advances.

## Explicit non-goals

This harness does not:

- calculate or correct market facts;
- compute risk or Proof Score;
- reconcile conflicts;
- turn missing evidence into zero;
- call CMIS directly from Roberta;
- add transaction simulation as an execution precursor;
- construct transactions;
- sign;
- broadcast;
- take custody;
- move value;
- authorize autonomous execution.

Completion of the readiness evaluation does not unlock Controlled Execution.
