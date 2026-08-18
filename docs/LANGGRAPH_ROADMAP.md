# Roberta LangGraph Roadmap

Last updated: 2026-08-17

## Status legend

- ✅ Complete — implemented, tested, merged, and accepted
- 🟡 Active / partial — current milestone or externally blocked work
- ⬜ Planned — not yet started as a development milestone

## Current position

Roberta has completed the core Oracle runtime, provider-neutral model/tool loop, X1 Scout boundary, CMIS/X1 Provider integration, constrained X1 Scout planning, LangGraph checkpoint persistence, verified HXMP durable memory, deterministic Oracle policy, and resumable human approval.

The active milestone is **Phase 10 — More Specialists / Providers**, beginning with the Solana Scout and a provider-neutral Solana CMIS path. The Solana Scout architecture is being built and tested with deterministic fixtures while the live Solana provider remains disabled until its provider contract and live evidence are verified.

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
████████████████████  Phase 8  Oracle Policy                   ✅
████████████████████  Phase 9  Human in the Loop               ✅
████████░░░░░░░░░░░░  Phase 10 More Specialists / Providers   🟡 CURRENT

NEXT
░░░░░░░░░░░░░░░░░░░░  Phase 11 Controlled Execution          ⬜
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
- X1.Ninja trade-history contract testing
- X1.Ninja OHLCV contract testing
- pool-specific X1.Ninja reserve ↔ X1 RPC cross-check orchestration

### Still open
- verify live XDEX chart/history response semantics against a real current non-XNT pool
- verify live XDEX quote response fields/units/route/freshness against a real current non-XNT pool
- promote verified XDEX history into CMIS `historical_compare` only after semantics are proven
- promote verified quote evidence into `pre_trade_check` only after its contract is proven
- verify provider-specific native XNT quote/market translation without substituting WXNT
- remaining provider gaps such as holder verification, streaming/SSE coverage, archival redundancy, and X1 bridge intelligence where tracked by CMIS/provider issues

### Current blocker
The public XDEX X1 pool surface has not provided the non-XNT live market needed to prove history/quote semantics. Provider groundwork is merged, but those data paths remain intentionally gated.

Tracking: Liquidity Scout issue #28 and provider-gap trackers.

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

## Phase 8 — Oracle Policy ✅ Complete

Tracking: Roberta issue #24 — completed.

### Goal
Make Roberta a policy-aware Oracle that deterministically applies durable user context to specialist evidence.

### Delivered
- typed Oracle policy contracts separate from memory and market evidence
- explicit policy-document compiler from durable memory
- hard constraints, soft preferences, threshold rules, evidence requirements, and approval rules
- deterministic rule evaluation and decision precedence
- explicit `insufficient_evidence` / `needs_evidence` behavior
- structural hard-block enforcement before model synthesis
- material policy warnings/preferences appended deterministically to final synthesis
- provider-neutral policy fact/evidence frame contract
- durable policy loader with bounded/fail-closed retrieval
- specialist-selection/routing hooks
- standardized X1 Scout policy facts
- full missing-evidence → X1 Scout research → deterministic re-evaluation loop
- policy document builder for owner-supplied rules without inventing user thresholds

### Authority rule

```text
HXMP/Memory -> stable user policy
CMIS        -> current verified facts
Policy code -> deterministic rule result
LLM         -> explanation/synthesis, never override
```

Free-form memory is context, not automatically executable policy. Only explicit policy documents activate deterministic enforcement.

---

## Phase 9 — Human in the Loop ✅ Complete

Tracking: Roberta issue #27 — closed completed.

### Goal
Add a resumable human-review boundary before consequential blockchain actions without creating execution authority.

### Delivered
- typed `ApprovalRequest`, `ApprovalDecision`, and `ApprovalOutcome`
- explicit decisions: `approve`, `reject`, `edit`, `request_more_evidence`
- dynamic LangGraph `interrupt()` + `Command(resume=...)`
- same-thread/checkpointer resume behavior
- deterministic pre-validation of resume input before it reaches the interrupted task
- cross-thread approval isolation
- completed-thread replay/refuse safeguards
- immutable reviewed proposal data
- canonical proposal SHA-256
- approval binding SHA-256 over request id + action type + declared scope + proposal hash
- edits create a new proposal/hash/request and require re-review
- deterministic next-step classes: `proceed`, `stop`, `re_review`, `research`
- Phase 8 `approval_required` → exact Phase 9 review request bridge
- common secret-bearing fields rejected from approval checkpoint/interrupt payloads
- no signing, broadcast, value movement, or wallet authority introduced

### Rule
`approved` means a human reviewed one exact proposal/scope. It is not a reusable signing credential or broad future authorization. Phase 11 must revalidate and consume an approval under its own execution safeguards.

---

## Phase 10 — More Specialists / Providers 🟡 Active

Tracking: Roberta issue #29 and PR #30.

### Goal
Expand Roberta beyond one chain specialist while preserving the hierarchy and one shared CMIS service layer.

### Target architecture

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

### Implemented on the active Phase 10 branch
- stable provider-neutral specialist capability registry for X1 + Solana
- deterministic chain/capability → Scout dispatch metadata
- Solana Scout LangGraph specialist subgraph
- Roberta-facing `solana_scout_investigate` tool
- one shared CMIS client with explicit `chain="solana"` dispatch
- bounded Solana Scout planning limited to `market_report`, `tokenomics`, and `risk_check` autonomously
- explicit rejection of autonomous `pre_trade_check`
- Solana provider/configuration gate disabled by default
- disabled Scout makes zero CMIS calls and returns `SOLANA_PROVIDER_NOT_CONFIGURED`
- standardized Solana Scout → policy fact adapter
- cross-chain policy fact dispatch that never falls back to stale evidence from another chain
- deterministic mock Solana CMIS tests only; no live-fact claims
- end-to-end Oracle policy → Solana Scout → policy re-evaluation tests
- Solana provider requirements/promotion-gate documentation based on current primary-source contracts

### Provider promotion boundary

The live Solana provider implementation belongs beneath CMIS, currently in the `liquidity-scout` migration codebase. Roberta's Solana provider gate must remain disabled until the provider has deterministic contract tests and read-only live acceptance evidence.

The provider should be layered rather than monolithic:

```text
Solana Provider
  |- canonical Solana RPC
  |- indexed token/account source
  |- aggregate market/price source
  |- venue-specific pool adapters
  `- CMIS normalization / cross-check logic
```

Candidate source classes documented for implementation include canonical Solana RPC, Jupiter market/token APIs, indexed Solana data such as Helius DAS/RPC, and venue-specific pool APIs such as Raydium, Orca, and Meteora. Candidate status is not live verification.

### Remaining Phase 10 acceptance work
- full deterministic CI on the final PR head
- PR-wide review / regression check
- confirm no unresolved review threads
- merge the Solana Scout skeleton
- create/advance the cross-repo CMIS Solana Provider implementation workstream
- implement and live-verify Solana provider services incrementally before enabling runtime live data

### Future specialists after the chain boundary is proven
- Wallet Sentinel
- Security Agent
- Treasury Agent
- Launch Scout

### Rule
Do not duplicate CMIS per chain. Add chain providers beneath shared deterministic service contracts, and add a chain Scout when chain-specific reasoning justifies one.

---

## Phase 11 — Controlled Execution ⬜ Planned

### Goal
Add a tightly scoped Execution Agent only after policy, provider verification, and human-approval boundaries are proven.

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
revalidate exact approval + current preconditions
  ↓
sign / broadcast within approved scope
```

### Execution Agent responsibilities
- route selection
- transaction simulation
- transaction preparation
- exact approval consumption/revalidation
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
CHAIN SCOUTS / SPECIALISTS
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

**Phase 10 — complete and merge the Solana Scout skeleton, then begin the CMIS Solana Provider implementation workstream.**

Active tracker:

```text
roberta-langgraph issue #29
roberta-langgraph PR #30
```

The Solana live-provider gate remains **off** until the CMIS/provider contract is implemented and read-only live evidence is verified.
