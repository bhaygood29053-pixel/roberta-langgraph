# Roberta LangGraph Roadmap

Last updated: 2026-08-15

## Status legend

- ✅ Complete — implemented, tested, merged, and accepted
- 🟡 Active / partial — current milestone or externally blocked work
- ⬜ Planned — not yet started as a development milestone

## Current position

Roberta has completed the core Oracle runtime, provider-neutral model/tool loop, X1 Scout boundary, CMIS/X1 Provider integration, constrained agentic X1 Scout planning, LangGraph thread/checkpoint persistence, and the HXMP durable-memory boundary including real read-only live verification.

The active milestone is **Phase 8 — Oracle Policy**.

```text
FOUNDATION
████████████████████  Phase 1  Core Agent Loop                 ✅
████████████████████  Phase 2  Provider-Neutral Model Loop     ✅
████████████████████  Phase 3  X1 Scout Boundary               ✅
████████████████████  Phase 4  CMIS / X1 Provider Integration  ✅
████████████░░░░░░░░  Phase 5  X1 Evidence Completeness       🟡 BLOCKED
████████████████████  Phase 6  Agentic X1 Scout Planning       ✅
████████████████████  Phase 7A Thread / Checkpoint Persistence ✅
████████████████████  Phase 7B HXMP Durable Memory             ✅
████░░░░░░░░░░░░░░░░  Phase 8  Oracle Policy                  🟡 CURRENT

NEXT
░░░░░░░░░░░░░░░░░░░░  Phase 9  Human in the Loop             ⬜
░░░░░░░░░░░░░░░░░░░░  Phase 10 More Specialists / Providers  ⬜
░░░░░░░░░░░░░░░░░░░░  Phase 11 Controlled Execution         ⬜
```

---

## Phase 1 — Core Agent Loop ✅ Complete

### Goal
Prove that Roberta can autonomously choose and call a tool through LangGraph.

### Delivered
- `RobertaState`
- START → Oracle → tool → Oracle → END loop
- model node and tool routing
- deterministic scripted tests
- small execution-state schema

### Result
Roberta can receive a user goal, choose whether a specialist/tool is required, execute through LangGraph, and finish deterministically.

---

## Phase 2 — Provider-Neutral Model / Tool Loop ✅ Complete

### Goal
Keep Roberta independent of one LLM provider while proving the real runtime path.

### Delivered
- provider-neutral model injection
- `bind_tools()` boundary
- deterministic fake models
- DeepSeek runtime integration
- opt-in live model tests
- separate Oracle and specialist-planner model dependencies

### Result
LangGraph owns orchestration; the model provider is an injected runtime dependency.

---

## Phase 3 — X1 Scout Boundary ✅ Complete

### Goal
Establish the specialist hierarchy so Roberta coordinates X1 work without directly owning chain-market tools.

### Delivered
- X1 Scout specialist graph/tool
- Roberta exposes X1 Scout, not CMIS/provider HTTP tools
- X1-only chain boundary
- structured specialist reports
- deterministic operation-routing guardrails
- CMIS status/provenance preservation

### Architecture

```text
Roberta
  ↓
X1 Scout
  ↓
CMIS
  ↓
X1 Provider
```

Roberta coordinates. X1 Scout interprets X1 evidence. CMIS verifies freshness-sensitive facts.

---

## Phase 4 — CMIS / X1 Provider Integration ✅ Complete

### Goal
Create the deterministic service boundary beneath X1 Scout and preserve the existing Liquidity Scout implementation during migration.

### Delivered
- Cross-Chain Market Intelligence Service (CMIS) public envelope
- CMIS HTTP boundary
- X1 Provider beneath CMIS
- X1 RPC / XDEX / X1.Ninja provider paths
- `market_report`, `tokenomics`, `risk_check`, and `pre_trade_check` service contracts
- exact service/status/data/risk/confidence/source/warning/error preservation
- canonical UTC observation-time handling
- deterministic risk-help and service-status help
- component-status presentation guardrails

### Migration rule
The architectural name **Liquidity Scout** is retired, but existing `liquidity_scout` package/repository identifiers may remain until provider boundaries and deployments are stable.

---

## Phase 5 — X1 Evidence Completeness 🟡 Partial / externally blocked

### Goal
Improve deterministic X1 evidence coverage without inventing unavailable market data.

### Completed
- bounded X1 token mint/burn activity collection
- evidence-aware risk gateway
- own historical snapshot comparison path
- read-only XDEX provider groundwork
- live XDEX token-price request contract verified
- public XDEX pool discovery
- exact public-address identity rule for non-native token assets
- native XNT kept separate from wrapped-token assumptions
- fail-closed XDEX schema and error handling

### Still open
- verify live XDEX chart/history response semantics against a real current non-XNT pool
- verify live XDEX quote response fields/units/route/freshness against a real current non-XNT pool
- promote verified XDEX history into CMIS `historical_compare` only after semantics are proven
- promote verified quote evidence into `pre_trade_check` only after its contract is proven
- verify provider-specific native XNT quote/market translation without substituting WXNT

### Current blocker
The public XDEX X1 pool surface currently exposes no usable non-XNT pool pair. Provider groundwork is merged, but history/quote promotion is intentionally gated until a real market exists.

Tracking: Liquidity Scout issue #28.

### Rule
An unavailable market is an explicit deterministic state, not permission to fabricate a pair, wrapped asset, quote, or historical series.

---

## Phase 6 — Agentic X1 Scout Planning ✅ Complete

### Goal
Let X1 Scout plan bounded multi-step investigations while deterministic code remains authoritative.

### Delivered
- separate X1 Scout planner-model dependency
- planner graph:

```text
START
  ↓
propose_plan
  ↓
enforce_plan
  ↓
cmis_calls
  ↓
interpret
  ↓
END
```

- autonomous planner scope limited to read-only `market_report`, `tokenomics`, and `risk_check`
- deterministic enforcement of required risk/tokenomics operations
- duplicate removal and plan-length cap
- invalid planner output fallback
- autonomous `pre_trade_check` rejection
- explicit pre-trade inputs remain caller-controlled
- per-investigation CMIS status/provenance preserved
- real DeepSeek planner probe passed

### Result
The LLM proposes investigations; deterministic policy decides what is allowed to execute.

---

# Phase 7 — Persistence and Durable Memory

Phase 7 is deliberately split because current thread execution state and durable long-term memory have different authority rules.

## Phase 7A — LangGraph Thread / Checkpoint Persistence ✅ Complete

### Goal
Give Roberta resumable current-task/thread state without turning checkpoints into durable truth.

### Delivered
- optional LangGraph checkpointer injection
- explicit `thread_id` runtime boundary
- same-thread continuation
- cross-thread isolation
- fresh graph instance resume against the same checkpoint backend
- deterministic `InMemorySaver` test path
- invalid/missing thread-id validation
- no-checkpointer stateless path preserved
- Oracle guardrail: checkpointed market snapshots are historical context only

### Authority rule
LangGraph checkpointing owns **current task/thread execution state**. It does not own permanent memory and is not authoritative for current market facts.

---

## Phase 7B — HXMP Durable Memory Adapter ✅ Complete

Tracking: Roberta issues #20 and #22 — closed completed.

### Goal
Add durable long-term memory beneath Roberta while retrieving only context relevant to the current task.

### Delivered
- provider-neutral `DurableMemoryStore` contract
- typed `MemoryRecord` and `MemoryCandidate`
- stable/freshness-sensitive memory categories
- deterministic write authorization
- deterministic relevance filtering
- guarded JSON memory context for the Oracle
- in-memory deterministic test adapter
- optional graph/runtime memory injection
- failure-safe no-memory degradation
- fresh-data override tests
- real `SyntharaLabs/HXMP` backend adapter
- deterministic whole-snapshot serialization in the `roberta-memory` lane
- verified `read-soul` path
- read-only `dry-run-soul` preparation path
- ordinary HXMP `upsert()` fail-closed behavior
- exact SHA-256 + wallet + lane approval binding
- signer-wallet preflight before `write-soul`
- `readback_verified` requirement before a write can be treated as committed
- opt-in real HXMP live contract probe

### Live acceptance completed
Using Roberta's AgentID wallet, the real local HXMP probe passed:

```text
test_real_hxmp_rpc_and_dry_run_contract_without_keypair_or_write  PASSED
test_real_hxmp_read_contract_when_memory_key_is_configured        PASSED
```

The live acceptance exercised X1 RPC, `dry-run-soul`, AgentID-aware preview behavior, and `read-soul` decryption/verification. It supplied no signing keypair and performed no `write-soul` transaction.

### Durable-memory candidates
- Roberta identity and role
- stable user preferences
- user risk policies
- long-term user goals
- specialist registry and structural capabilities
- CMIS service contracts
- approval rules
- important decisions and rationale

### Never authoritative as current truth
- token prices
- liquidity
- volume
- holder counts
- rankings
- current supply
- burns/mints
- wallet balances
- LP/pool counts
- freshness-sensitive authorities
- current risk scores

### Core rule

```text
Memory remembers what matters.
CMIS verifies what is happening now.
```

Fresh verified CMIS/provider data always overrides remembered or conversational live-data snapshots.

---

## Phase 8 — Oracle Policy 🟡 Active

Tracking: Roberta issue #24.

### Goal
Turn Roberta from a capable coordinator into a policy-aware Oracle that applies durable user context across specialist findings.

### Existing foundation
- final Oracle synthesis
- X1 specialist delegation
- CMIS status/provenance guardrails
- planner-diagnostic vs market-fact separation
- fresh-data override prompt guardrails
- durable HXMP retrieval for stable user context

### Active milestone scope
- typed Oracle policy contracts separate from memory and market evidence
- durable user risk policy compilation
- portfolio / exposure rules
- user-specific thresholds and constraints
- hard-constraint vs soft-preference distinction
- deterministic threshold evaluation where possible
- explicit `insufficient_evidence` state when required fresh inputs are missing
- specialist-selection/routing policy hooks
- cross-chain-ready policy interfaces without inventing Solana behavior before Solana Scout exists
- explainable rule-level policy results
- final synthesis that identifies which user constraints materially affected the recommendation

### First implementation slice

```text
Durable HXMP memory
  ↓
relevant user policy records
  ↓
policy compiler
  ↓
typed deterministic rules
  ↓
policy evaluator
  ↓
structured rule outcomes
  ↓
Oracle synthesis
```

Initial rule model:
- **hard constraint** — cannot be overridden by the LLM
- **preference** — influences synthesis but does not override hard constraints
- **threshold rule** — compares verified input to a user-defined bound
- **evidence requirement** — refuses pass/fail when required fresh evidence is unavailable
- **approval rule** — records that later user approval would be required; Phase 8 does not execute anything

### Rule
User policy belongs to Roberta, not CMIS and not chain providers. A policy result may use current facts only when those facts come from fresh verified specialists/CMIS/providers.

---

## Phase 9 — Human in the Loop ⬜ Planned

### Goal
Introduce LangGraph interrupt/resume approval flow before consequential blockchain actions.

### Planned
- LangGraph interrupt boundary
- proposed-action summary
- approve / edit / reject
- durable approval record where appropriate
- safe resume after approval
- cancellation without side effects

### Human approval required before
- signing transactions
- broadcasting value-moving transactions
- transferring assets
- changing wallet permissions
- granting execution authority
- HXMP durable-memory writes that spend gas
- other consequential blockchain actions

### Automatic actions remain allowed
- research
- read-only analysis
- memory retrieval
- specialist calls
- deterministic CMIS checks
- transaction simulation
- preparation of proposed transactions or HXMP write previews

---

## Phase 10 — More Specialists / Providers ⬜ Planned

### Goal
Expand Roberta using the same hierarchy instead of duplicating full intelligence stacks.

### First cross-chain expansion

```text
Roberta
  ├── X1 Scout
  │     ↓
  │    CMIS → X1 Provider
  │
  └── Solana Scout
        ↓
       CMIS → Solana Provider
```

### Planned specialists
- Solana Scout
- Wallet Sentinel
- Security Agent
- Treasury Agent
- Launch Scout

### Planned provider expansion
- Solana Provider beneath the existing CMIS contracts
- future chains follow the same provider model

### Rule
Do not duplicate CMIS per chain. Add chain providers beneath shared deterministic service contracts, and add a chain Scout only when chain-specific reasoning justifies one.

---

## Phase 11 — Controlled Execution ⬜ Planned

### Goal
Add a tightly scoped Execution Agent only after policy and human-approval boundaries are proven.

### Target flow

```text
research
  ↓
simulate
  ↓
prepare proposed transaction
  ↓
human approval
  ↓
sign / broadcast within approved scope
```

### Execution Agent responsibilities
- route selection
- transaction simulation
- transaction preparation
- execution only after required approval

### XDEX boundary
`/api/xendex/swap/prepare` belongs here, not in ordinary CMIS market intelligence.

CMIS may provide deterministic read-only pre-trade analysis; it does not sign or broadcast value-moving transactions.

---

# System hierarchy

```text
USER
  ↓
ROBERTA — Oracle / Coordinator
  ↓
CHAIN SCOUTS
  ↓
CROSS-CHAIN MARKET INTELLIGENCE SERVICE (CMIS)
  ↓
CHAIN PROVIDERS
```

Authority flows downward:

```text
Roberta → Chain Scout → CMIS → Chain Provider
```

Verified information flows upward:

```text
Chain Provider → CMIS → Chain Scout → Roberta
```

HXMP is orthogonal to live market verification:

```text
HXMP → durable stable context → Roberta
CMIS → fresh verified facts    → Roberta
```

---

# Development principles

1. Build and test one layer at a time.
2. Preserve working deterministic X1 functionality during migration.
3. Keep LLM planning separate from deterministic authority.
4. Do not manufacture unavailable live-data facts.
5. Fresh CMIS/provider evidence overrides memory or checkpoint snapshots.
6. Prefer shared CMIS contracts with chain-specific providers rather than duplicate intelligence stacks.
7. Do not grant broad wallet authority to demonstrate autonomy.
8. Require explicit human approval before consequential blockchain actions.
9. Keep HXMP signing and memory-encryption keys local; never commit or print secret bytes.
10. Use GitHub issues/PRs/CI as the development checkpoint for each coherent milestone.

---

# Current next action

**Phase 8 — Oracle Policy**

Active tracker:

```text
roberta-langgraph issue #24
```

First coding target:

```text
typed policy contracts
  + deterministic evaluator
  + durable-memory-derived risk-policy tests
```

Do not change X1 Scout, CMIS, provider behavior, or transaction execution in the first Phase 8 slice.
