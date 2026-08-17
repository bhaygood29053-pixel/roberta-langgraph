# Oracle Policy — Phase 8

## Purpose

Phase 8 makes Roberta a policy-aware Oracle without moving live-data authority into the LLM.

HXMP stores stable user policy. Chain Scouts and CMIS supply current structured evidence. Deterministic code compiles and evaluates rules. Roberta explains the result and coordinates additional research when evidence is missing.

```text
HXMP durable memory
        ↓
explicit policy documents
        ↓
PolicyRule compiler
        ↓
explicit PolicyFact evidence ← Chain Scout / supported service adapters
        ↓
deterministic evaluator
        ↓
PolicyDecision
        ↓
structural Oracle enforcement
        ↓
final synthesis + deterministic material policy notes
```

The policy compiler/evaluator do not make model calls or fetch market data.

## Ordinary memory vs executable policy

Phase 7B free-form memories remain ordinary context. Roberta never invents a hard rule from a sentence such as:

```text
I prefer conservative trades.
```

A memory becomes executable policy only when it explicitly opts into the policy schema. The normal path is a versioned JSON document plus the `oracle_policy` topic marker. A JSON record carrying `policy_version` is also recognized as explicit policy for compatibility.

Once a record opts into policy, malformed or unsupported structure fails closed. A malformed explicit rule cannot silently disappear and turn into permission.

## Policy document version 1

Example only — the numeric value is a test/example value, not a user default:

```json
{
  "policy_version": 1,
  "rule_id": "minimum_liquidity",
  "kind": "threshold_rule",
  "effect": "block",
  "description": "Require the configured minimum liquidity.",
  "fact_key": "market.liquidity",
  "operator": "gte",
  "expected": 10000,
  "requires_fresh": true
}
```

Eligible durable-memory mappings:

- `user_risk_policy` → `hard_constraint`, `threshold_rule`, `evidence_requirement`
- `stable_preference` → `preference`
- `approval_rule` → `approval_rule`

Historical-context records cannot become enforceable policy.

`build_policy_memory_candidate()` creates a correctly typed candidate but never writes it. HXMP write execution remains separately dry-run/approval gated.

## Rule effects and precedence

Effects:

- `block` — violated hard/threshold rule blocks the recommendation/action.
- `warn` — missed threshold is surfaced but is not a hard block.
- `preference` — affects ranking/synthesis but cannot override a block.
- `evidence` — requires usable verified evidence.
- `approval` — records an approval boundary; it never authorizes execution.

Aggregate decision precedence is deterministic:

1. any hard block → `blocked`
2. otherwise missing/unusable required evidence → `needs_evidence`
3. otherwise matched approval rule → `approval_required`
4. otherwise → `allowed`

The LLM cannot change that precedence.

## Evidence authority

Every `PolicyFact` carries:

Evidence status:

- `verified`
- `unverified`
- `conflict`
- `insufficient_evidence`

Freshness:

- `fresh`
- `historical`
- `unknown`

Missing facts, non-verified evidence, stale/unknown evidence for a `requires_fresh` rule, explicit nulls, and invalid comparisons produce `insufficient_evidence` rather than guessed pass/fail results.

`EvidenceFrame` and `FactPathSpec` require adapters to declare exact field paths. The generic policy layer does not inspect provider prose or infer that a field is trusted because its name sounds authoritative.

## X1 Scout fact adapter

X1-specific translation lives inside the X1 Scout boundary. Roberta's generic policy engine does not import Liquidity Scout/provider internals.

Current standardized X1 fact keys include:

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

The adapter examines every investigation in an X1 Scout report rather than trusting only the final/primary operation.

For the currently accepted CMIS envelope, an X1 investigation with `cmis_status=ok` can provide `verified` facts. `partial` remains `unverified`; unavailable/error-like states become `insufficient_evidence`. An observation is labeled `fresh` by this adapter only for an `ok` investigation carrying the Scout's normalized current observation timestamp. Null values remain insufficient evidence and are never coerced to zero/false.

This mapping does not create a new Roberta-facing CMIS verification service. The accepted CMIS trust-layer boundary remains unchanged.

## Missing evidence can trigger research

The policy context provider is reevaluated on each Oracle pass.

Typical X1 flow:

```text
explicit durable rule requires fresh market.liquidity
        ↓
no X1 Scout ToolMessage yet
        ↓
PolicyDecision = needs_evidence
        ↓
Oracle may call x1_scout_investigate
        ↓
X1 Scout returns structured CMIS report
        ↓
X1 adapter creates PolicyFact(s)
        ↓
policy reevaluates
        ↓
allowed / blocked / still needs_evidence
```

If the model tries to produce a final answer while a required fact remains unresolved, the graph replaces that answer with the deterministic needs-evidence result.

## Structural Oracle enforcement

Policy is not only prompt guidance.

- `blocked`: the Oracle model is not called for a final recommendation; deterministic block text is returned.
- `needs_evidence`: read-only specialist research may proceed, but an unsupported final answer is rejected.
- `approval_required`: model analysis may be shown only under an explicit non-authorizing approval notice.
- policy-provider failure: fails closed; Roberta cannot claim policy compliance.
- `allowed`: model synthesis may proceed.

Material warnings and preference outcomes are appended deterministically to final synthesis, so the model cannot silently omit policy factors that affected the recommendation.

## Durable policy loading

`build_policy_context_provider()` reads the three policy-capable memory categories through the existing provider-neutral `DurableMemoryStore` contract. It is compatible with HXMP verified reads without introducing a new persistence system.

Loading is bounded and fails closed if the bound is exceeded rather than silently truncating an unknown rule set. Free-form Phase 7B records do not activate executable policy.

## Specialist routing hooks

Phase 8 also defines provider-neutral deterministic specialist selection:

- stable chain/capability registry
- optional allow/block lists
- optional preferred specialist order
- deterministic priority/tie breaking

The registry describes stable capability, not current service health. X1 Scout is the implemented chain specialist today; future Solana Scout can use the same routing contract without changing the policy engine.

## Portfolio and future specialist facts

The policy engine supports arbitrary explicit fact keys, including portfolio/exposure rules, but it does not fabricate a portfolio source. Until a Wallet Sentinel/Treasury or another approved fact provider exists, a portfolio-dependent rule correctly remains `needs_evidence`.

This preserves the architecture: deterministic rules can exist before the specialist that supplies their evidence, without substituting remembered balances or guessed values.

## Human approval boundary

An `approval_rule` records that approval is required. It does not invoke LangGraph human interrupt/resume, sign, broadcast, transfer assets, or change permissions.

Interactive approve/reject/edit/resume behavior belongs to Phase 9. Transaction execution belongs to Phase 11.

## No user defaults

The repository intentionally contains no production financial thresholds for the user. Test values are fixtures only. Actual limits, preferences, wallet scope, and approval choices remain owner configuration and should be stored as explicit durable policy only after the user supplies them.
