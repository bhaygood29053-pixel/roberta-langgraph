# Oracle Policy — Phase 8

## Purpose

Phase 8 gives Roberta a deterministic policy layer between durable user context and final Oracle synthesis.

The policy layer does **not** own live market facts. It evaluates explicit rules against facts supplied by specialist/CMIS-facing code. HXMP durable memory stores stable policy documents; CMIS remains authoritative for freshness-sensitive market, tokenomics, and risk evidence.

## Boundary

```text
HXMP durable memory
        ↓
explicit structured policy documents
        ↓
policy compiler
        ↓
typed PolicyRule objects
        ↓
verified PolicyFact inputs
        ↓
deterministic evaluator
        ↓
rule-level PolicyEvaluation results
        ↓
Roberta synthesis
```

The compiler and evaluator make no model calls and perform no network access.

## No hidden policy inference

Free-form durable memory is not silently converted into an enforceable rule.

For example, a memory containing only:

```text
I prefer conservative trades.
```

is useful conversational context, but it is not enough to define a deterministic threshold. Roberta must not invent a liquidity floor, portfolio percentage, or risk score from that sentence.

An enforceable policy document is explicit JSON, for example:

```json
{
  "policy_version": 1,
  "rule_id": "max_single_asset_pct",
  "kind": "threshold_rule",
  "effect": "block",
  "description": "Do not exceed the configured single-asset exposure.",
  "fact_key": "portfolio.single_asset_pct",
  "operator": "lte",
  "expected": 25,
  "requires_fresh": true
}
```

The numeric value above is an example/test fixture, **not a default user policy**.

## Memory-category restrictions

Only durable records in these categories can compile into deterministic rules:

- `user_risk_policy` → `hard_constraint`, `threshold_rule`, `evidence_requirement`
- `stable_preference` → `preference`
- `approval_rule` → `approval_rule`

Historical-context records cannot become enforceable policy. Other memory categories remain context, not rules.

## Rule effects

- `block` — a violated hard/threshold constraint blocks the policy outcome.
- `warn` — a missed threshold surfaces a warning without becoming a hard block.
- `preference` — records whether a soft preference matched; it cannot override a block.
- `evidence` — requires suitable verified evidence.
- `approval` — records that approval is required when a declared condition matches. Phase 8 does not execute anything.

Threshold rules require an explicit `block` or `warn` effect. Roberta does not choose one implicitly.

## Evidence authority

Every policy fact has explicit evidence status and freshness:

Evidence status:

- `verified`
- `unverified`
- `conflict`
- `insufficient_evidence`

Freshness:

- `fresh`
- `historical`
- `unknown`

A rule that requires fresh evidence cannot be satisfied by historical memory. A conflicting or unverified fact cannot satisfy a deterministic rule even when its raw value appears favorable.

CMIS verification states may later be mapped into this provider-neutral contract by a supported Roberta-facing wrapper. Phase 8 must not import Liquidity Scout provider internals directly.

## Fail-closed outcomes

The evaluator emits rule-level outcomes:

- `pass`
- `block`
- `warn`
- `preference_met`
- `preference_missed`
- `insufficient_evidence`
- `approval_required`

Missing facts, stale evidence for a fresh rule, conflicting/unverified evidence, and invalid comparisons produce `insufficient_evidence` rather than guessed pass/fail results.

## Human approval boundary

An `approval_rule` only records that approval would be required. It does not interrupt LangGraph, sign, broadcast, transfer value, or change permissions. Interactive approval belongs to Phase 9; controlled execution belongs to Phase 11.

## Current implementation slice

The first Phase 8 slice consists of:

- typed provider-neutral policy contracts
- deterministic JSON compiler from eligible durable memories
- deterministic evaluator
- aggregate summary helpers that preserve every rule-level result
- tests for hard-vs-soft precedence, stale/missing/conflicting evidence, category restrictions, approval marking, and no free-form inference

Oracle prompt/graph integration follows only after this contract is stable.
