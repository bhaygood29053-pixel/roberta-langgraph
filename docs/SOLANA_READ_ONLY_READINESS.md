# Solana Read-Only Production Readiness

Tracking: Roberta issue #78. Foundation slice: #79. Degraded-evidence slice: #82. Token-2022 slice: #84. Live Token-2022 blocker resolution: #89 after CMIS #244.

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

`evals/solana_readiness_v1.json` is the Solana configured-readiness corpus. It covers:

1. current market report for an exact Solana mint;
2. tokenomics/authority facts for an exact Solana mint;
3. deterministic risk for an exact Solana mint;
4. symbol-only identity failing closed rather than silently guessing a mint;
5. X1/Solana cross-chain evidence isolation.

The corpus still does not make a production-ready claim by itself. A production-ready claim requires a configured operator run with all selected cases executed, zero failures, and zero deployment blockers.

Corpus-level `readiness_blockers` remain available for unresolved prerequisites. `roberta-readiness` writes declared blockers into `deployment_blockers` and exits non-zero. After CMIS #244 acceptance, the previously declared `accepted_token_2022_live_mint_required` blocker is resolved and the corpus blocker list is empty.

## Token-2022 boundary

CMIS has accepted deterministic tests for:

- canonical Token-2022 owner/program identity;
- `program_kind=token_2022`;
- Token-2022 extension-name preservation;
- tokenomics supply and authority preservation under Token-2022;
- no silent equivalence with legacy SPL Token.

Roberta mirrors that deterministic contract with the evaluation-only replay case:

`solana-token-2022-tokenomics-fixture`

The replay fixture remains synthetic and evaluation-only. It is not a live asset claim and remains useful for degraded-evidence/model behavior tests.

CMIS #244 separately accepted a live read-only Token-2022 readiness fixture:

- asset: PYUSD on Solana;
- exact mint: `2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo`;
- program: Token-2022;
- decimals: 6;
- acceptance scope: exact-mint read-only RPC contract only.

The final dedicated-RPC acceptance used QuickNode and passed `getTokenLargestAccounts` after CMIS PR #249 normalized provider-extended results to Solana's canonical top-20 scope. The accepted live observation preserved:

- `account_count_observed=20`;
- `provider_account_count_returned=100`;
- `canonical_account_limit=20`;
- `provider_extended_result_truncated=true`;
- `counted_entity=token_accounts`;
- `coverage=largest_token_accounts_only`;
- `total_holder_count_verified=false`.

This acceptance removes the earlier Token-2022 identity prerequisite. It does not make PYUSD a general market benchmark, does not establish holder or beneficial-owner counts, and does not by itself make the full Roberta Solana path production-ready.

## Controlled degraded-evidence replay

`roberta-solana-readiness-replay` runs the configured production model against deterministic evaluation-only CMIS evidence through the normal Roberta -> Solana Scout tool path. It enables the Solana Scout only inside the harness; no live provider is used.

The replay covers:

- explicitly stale evidence;
- cross-source conflict;
- insufficient proof;
- unavailable provider fields;
- provider error;
- null field versus verified zero;
- exact case-sensitive Solana mint preservation;
- deterministic Token-2022 tokenomics/program/extension preservation.

Accepted operator evidence for #78 is 8/8 passing with zero deployment blockers. One stale-evidence case required one model retry, demonstrating the Decision Quality guard corrected an incomplete first draft rather than accepting it.

Run it with:

```bash
roberta-solana-readiness-replay \
  --output artifacts/readiness/solana-replay-local.json
```

The report authority is `historical_evaluation_snapshot` and `live_market_authority=false`.

## Configured acceptance command

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
- a synchronized accepted CMIS deployment;
- configured CMIS endpoint/auth where required;
- all selected scenarios actually executed;
- zero failed scenarios;
- zero corpus-declared readiness blockers;
- no cross-chain substitution;
- preserved CMIS status, evidence quality, freshness, warnings, limitations, and unresolved fields.

`--require-no-skips` exits non-zero when any selected scenario is skipped. Corpus-declared blockers also exit non-zero. This prevents either a disabled Solana provider or a future unresolved prerequisite from being mistaken for a passing readiness run.

## Remaining #78 work

The explicit remaining gates are:

- synchronize/restart the local CMIS deployment to a current accepted contract and verify its capability manifest;
- run the configured live Solana corpus through the normal Roberta -> Solana Scout -> CMIS path with `--require-no-skips`;
- record the live readiness report and exact proven capability scope;
- synchronize `docs/LANGGRAPH_ROADMAP.md` with the completed #62/#73/#74 milestones and current #78 status;
- close #78 only if the configured live report has zero failures and zero deployment blockers.

## Safety boundary

This milestone does not authorize transaction construction, execution simulation as a precursor to execution, signing, broadcasting, custody, bridge transfer, autonomous trading, or any value movement. Phase 11 Controlled Execution remains locked.
