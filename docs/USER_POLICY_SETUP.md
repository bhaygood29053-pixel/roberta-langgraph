# User Policy Setup — Owner Inputs for Roberta

## Purpose

Roberta's policy engine is intentionally built without guessing the owner's financial rules. This document is the handoff checklist for converting explicit owner choices into typed Phase 8 policy records.

Nothing in this file is a default recommendation. Blank choices should remain unset rather than being filled by code or an LLM.

## What the owner may configure

### Risk and eligibility

Decide only the rules you actually want Roberta to enforce, for example:

- assets/chains that are always allowed, blocked, or preferred
- minimum liquidity requirement
- minimum volume requirement
- LP-count or other market-structure thresholds if desired
- acceptable deterministic risk outcomes/scores once a verified fact contract exists
- tokenomics conditions such as mint/freeze authority requirements where verified data exists
- whether a threshold is a hard `block` or only a `warn`

### Portfolio/exposure

Possible future rules include:

- maximum single-asset exposure
- maximum chain exposure
- maximum action/trade notional
- maximum daily or rolling allocation change
- reserve/cash floor

These rules should not be activated until an approved portfolio/wallet fact source exists. Remembered wallet balances must never satisfy a current exposure rule.

### Preferences

Preferences may guide ranking but cannot override a hard rule. Examples:

- preferred chain
- preferred specialist when multiple equivalent specialists exist
- preferred liquidity/risk profile
- preferred holding/strategy constraints

### Approval rules

Choose which consequential conditions always require explicit approval. The architecture already requires human approval for signing, broadcasting, value movement, transfers, permission changes, and execution authority. Additional owner rules may be stricter.

Phase 8 only records `approval_required`. Phase 9 implements interactive approval/resume. Phase 11 controls execution.

### Wallet/portfolio scope

When portfolio specialists are introduced, identify which public wallets/accounts Roberta may observe. Do not put private keys, seed phrases, or secret material in durable policy.

## How a choice becomes policy

An owner-confirmed choice is converted to a typed `PolicyRule`, then `build_policy_memory_candidate()` produces the canonical durable-memory candidate. Example shape:

```json
{
  "policy_version": 1,
  "rule_id": "owner_defined_rule",
  "kind": "threshold_rule",
  "effect": "block",
  "description": "Owner-confirmed description",
  "fact_key": "market.liquidity",
  "operator": "gte",
  "expected": "OWNER_SUPPLIED_VALUE",
  "requires_fresh": true
}
```

`OWNER_SUPPLIED_VALUE` is deliberately not chosen by the repository.

The candidate is marked with the `oracle_policy` topic so it is distinguishable from free-form memory. HXMP still requires its separate dry-run and explicit write approval before an on-chain durable-memory update can execute.

## Currently available X1 policy facts

The X1 Scout adapter can expose these standardized facts when the corresponding structured CMIS investigation supplies usable evidence:

- `asset.chain`
- `asset.symbol`
- `market.price`
- `market.liquidity`
- `market.lp_count`
- `market.volume_24h`
- `market.risk_outcome`
- `market.risk_score`
- `tokenomics.total_supply`
- `tokenomics.mint_authority`
- `tokenomics.freeze_authority`
- `trade.side`
- `trade.notional_usd`

A rule can be defined before its fact provider exists, but it will remain `needs_evidence` until a supported provider supplies the fact.

## Owner handoff checklist

When ready, supply decisions in plain language. They can then be translated into explicit rules for review before any HXMP write.

Useful inputs are:

1. hard asset/chain exclusions, if any
2. desired market/risk thresholds and whether each is `block` or `warn`
3. soft preferences
4. portfolio/exposure limits, once wallet scope is decided
5. any approval requirements stricter than the architectural minimum
6. public wallet/account scope for future portfolio specialists

Credentials, seed phrases, private keys, encryption-key contents, and signing secrets are **not** policy inputs and must not be pasted into this document or durable memory.
