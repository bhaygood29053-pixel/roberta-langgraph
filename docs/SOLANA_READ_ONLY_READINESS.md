# Solana Read-Only Production Readiness

Tracking: Roberta issue #78. First implementation slice: #79.

## Purpose

This milestone validates the configured read-only Solana path end to end:

```text
User -> Roberta -> Solana Scout -> CMIS -> Solana Provider
```

It is a deployment/readiness gate, not a feature-parity milestone and not an execution milestone.

## Current promoted Scout surface

Solana Scout currently plans and dispatches only these read-only CMIS operations:

- `market_report`
- `tokenomics`
- `risk_check`

The Solana provider path is disabled by default and must be explicitly enabled with `ROBERTA_SOLANA_PROVIDER_ENABLED=1` only against an accepted CMIS deployment whose Solana capabilities are configured.

Unsupported or unconfigured services remain unavailable. In particular, Solana pre-trade is not promoted by this milestone.

## Configured corpus

`evals/solana_readiness_v1.json` is the first Solana-only configured-readiness corpus. It covers:

1. current market report for an exact Solana mint;
2. tokenomics/authority facts for an exact Solana mint;
3. deterministic risk for an exact Solana mint;
4. symbol-only identity failing closed rather than silently guessing a mint;
5. X1/Solana cross-chain evidence isolation.

The corpus intentionally does not claim full #78 acceptance yet.

## Acceptance command

A configured Solana readiness run must not treat skipped scenarios as success:

```bash
roberta-readiness \
  --corpus evals/solana_readiness_v1.json \
  --require-no-skips \
  --output artifacts/readiness/solana-live.json
```

A production-readiness claim requires:

- `ROBERTA_SOLANA_PROVIDER_ENABLED=1`;
- configured production model credentials;
- configured CMIS endpoint/auth where required;
- all selected scenarios actually executed;
- zero failed scenarios;
- no cross-chain substitution;
- preserved CMIS status, evidence quality, freshness, warnings, limitations, and unresolved fields.

`--require-no-skips` exits non-zero when any selected scenario is skipped. This prevents a disabled Solana provider from being mistaken for a passing readiness run.

## Remaining #78 work

The following remain explicit follow-up gates before Solana can be called production-ready for the full issue scope:

- accepted Token-2022 exact-mint readiness fixture/case;
- deterministic degraded-provider replay for stale, partial, unavailable, conflict, insufficient-proof, timeout/error, and null-vs-zero states;
- technical/source follow-up coverage for only the Solana services actually promoted through Scout;
- configured operator-run evidence and blocker report;
- roadmap synchronization in `docs/LANGGRAPH_ROADMAP.md`;
- final scope statement naming exactly which Solana capabilities were proven.

## Safety boundary

This milestone does not authorize transaction construction, execution simulation as a precursor to execution, signing, broadcasting, custody, bridge transfer, autonomous trading, or any value movement. Phase 11 Controlled Execution remains locked.
