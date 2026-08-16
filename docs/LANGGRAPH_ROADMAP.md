# Roberta LangGraph Roadmap

Last updated: 2026-08-15

## Status legend

- ✅ Complete — implemented, tested, and merged
- 🟡 Active / partial — implementation exists but milestone is still in progress or externally blocked
- ⬜ Planned — not yet started as a development milestone

## Current position

Roberta has completed the core Oracle runtime, provider-neutral model/tool loop, X1 Scout boundary, CMIS/X1 Provider integration, constrained agentic X1 Scout planning, and LangGraph thread/checkpoint persistence.

The active milestone is **Phase 7B — HXMP/HMPX Durable Memory Adapter**.

```text
FOUNDATION
████████████████████  Phase 1  Core Agent Loop                 ✅
████████████████████  Phase 2  Provider-Neutral Model Loop     ✅
████████████████████  Phase 3  X1 Scout Boundary               ✅
████████████████████  Phase 4  CMIS / X1 Provider Integration  ✅
████████████░░░░░░░░  Phase 5  X1 Evidence Completeness       🟡
████████████████████  Phase 6  Agentic X1 Scout Planning       ✅
████████████████████  Phase 7A Thread / Checkpoint Persistence ✅
████░░░░░░░░░░░░░░░░  Phase 7B HXMP/HMPX Durable Memory       🟡 CURRENT

NEXT
░░░░░░░░░░░░░░░░░░░░  Phase 8  Oracle Policy                 ⬜
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
- small state schema with explicit execution status

### Completion condition
Roberta can receive a user goal, decide whether a tool is required, execute it through LangGraph, and finish deterministically.

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
- separate Oracle and specialist-planner model injection paths

### Architectural result
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
- deterministic operation routing guardrails
- CMIS status/provenance preservation

### Architectural result

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
- public XDEX pool discovery added
- exact public-address identity rule for non-native token assets
- native XNT kept separate from wrapped-token assumptions
- fail-closed XDEX schema and error handling

### Still open
- verify live XDEX chart/history response semantics against a real current non-XNT pool
- verify live XDEX quote response fields/units/route/freshness against a real current non-XNT pool
- promote verified XDEX history into CMIS `historical_compare` only after those semantics are proven
- promote verified quote evidence into `pre_trade_check` only after its contract is proven
- verify provider-specific native XNT quote/market translation without substituting WXNT

### Current blocker
The public XDEX X1 pool surface currently exposes no usable non-XNT pool pair. The provider groundwork is merged, but history/quote promotion is intentionally gated until a real market exists.

Tracking: Liquidity Scout issue #28.

### Rule
An unavailable market is an explicit deterministic state, not permission to fabricate a pair, wrapped asset, quote, or historical series.

---

## Phase 6 — Agentic X1 Scout Planning ✅ Complete

### Goal
Let X1 Scout plan bounded multi-step investigations while deterministic code remains authoritative.

### Delivered
- separate X1 Scout planner-model dependency
- graph flow:

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

- autonomous planner scope limited to read-only:
  - `market_report`
  - `tokenomics`
  - `risk_check`
- deterministic enforcement of required risk/tokenomics operations
- duplicate removal and plan-length cap
- invalid planner output fallback
- autonomous `pre_trade_check` rejection
- explicit pre-trade inputs remain caller-controlled
- per-investigation CMIS status/provenance preserved
- real DeepSeek planner probe passed

### Architectural result
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
LangGraph checkpointing owns **current task/thread execution state**.

It does not own permanent memory and it is not authoritative for current market facts.

---

## Phase 7B — HXMP/HMPX Durable Memory Adapter 🟡 Active

Tracking: Roberta issue #20.

### Goal
Add durable long-term memory beneath Roberta while retrieving only context relevant to the current task.

### Implementation order
1. provider-neutral memory contracts
2. deterministic in-memory test adapter
3. typed memory records and stable keys
4. relevance-filtered retrieval
5. deterministic write policy
6. graph/runtime injection boundary
7. Oracle context integration
8. fresh-data override and failure-mode tests
9. bind the stable contracts to the real HXMP/HMPX client

### Permanent-memory candidates
- Roberta identity and role
- stable user preferences
- user risk policies
- long-term user goals
- specialist registry and structural capabilities
- CMIS service contracts
- approval rules
- important decisions
- decision rationale

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

## Phase 8 — Oracle Policy ⬜ Planned

### Goal
Turn Roberta from a capable coordinator into a policy-aware Oracle that applies durable user context across specialists.

### Existing foundation already complete
- final Oracle synthesis
- X1 specialist delegation
- CMIS status/provenance guardrails
- planner-diagnostic vs market-fact separation
- fresh-data override prompt guardrails

### Remaining milestone scope
- durable user risk policy
- portfolio / exposure rules
- user-specific thresholds and constraints
- specialist selection policy
- cross-chain routing policy
- comparison of findings across chain Scouts
- explainable decision factors and rationale
- deterministic policy enforcement where possible

### Rule
User policy belongs to Roberta, not CMIS and not chain providers.

---

## Phase 9 — Human in the Loop ⬜ Planned

### Goal
Introduce interrupt/resume approval flow before consequential blockchain actions.

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
- other consequential blockchain actions

### Automatic actions remain allowed
- research
- read-only analysis
- memory retrieval
- specialist calls
- deterministic CMIS checks
- transaction simulation
- preparation of proposed transactions

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
Add a tightly scoped Execution Agent only after policy and human approval boundaries are proven.

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
9. Use GitHub issues/PRs/CI as the development checkpoint for each coherent milestone.

---

# Current next action

**Phase 7B — HXMP/HMPX Durable Memory Adapter**

Active branch:

```text
agent/hxmp-durable-memory-adapter
```

Active tracker:

```text
roberta-langgraph issue #20
```

First coding target: provider-neutral memory contracts plus a deterministic in-memory adapter, before binding Roberta to the real HXMP/HMPX implementation.
