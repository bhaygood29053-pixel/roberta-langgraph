# Roberta LangGraph Roadmap

Last updated: 2026-08-18

## Status legend

- ✅ Complete — implemented, tested, merged, and accepted
- 🟡 Bounded / partial — useful capability exists but evidence scope remains deliberately limited
- ⬜ Planned / locked — not started as a development milestone

## Current position

Roberta has completed the Phase 10 cross-chain specialist/provider milestone **and** the post-Phase-10 Evidence-Aware Intelligence & User Experience milestone merged in PR #46.

The accepted architecture supports a provider-neutral specialist registry with X1 Scout and Solana Scout above one shared CMIS service layer. The Scout → CMIS boundary is protected by a versioned machine-readable capability contract, and Roberta now preserves CMIS evidence receipts/proof scores through Chain Scout reports while producing answer-first user-facing synthesis.

The remaining X1 provider/evidence gaps are no longer treated as an ambiguous blocker. CMIS PR #167 established an explicit fail-closed X1 evidence capability boundary that classifies tracked facts as verified, bounded, or unavailable. Roberta must preserve those states rather than trying to fill provider gaps with model inference.

Phase 11 Controlled Execution is intentionally **not started**. Phase 9 human approval remains a review boundary only; neither approval, Phase 10, nor the evidence-aware UX milestone creates signing, broadcast, custody, autonomous execution, or value-movement authority.

```text
FOUNDATION
████████████████████  Phase 1  Core Agent Loop                 ✅
████████████████████  Phase 2  Provider-Neutral Model Loop     ✅
████████████████████  Phase 3  X1 Scout Boundary               ✅
████████████████████  Phase 4  CMIS / X1 Provider Integration  ✅
████████████████░░░░  Phase 5  X1 Evidence Completeness       🟡 BOUNDED
████████████████████  Phase 6  Agentic X1 Scout Planning       ✅
████████████████████  Phase 7A Thread / Checkpoint Persistence ✅
████████████████████  Phase 7B HXMP Durable Memory             ✅
████████████████████  Phase 8  Oracle Policy                   ✅
████████████████████  Phase 9  Human in the Loop               ✅
████████████████████  Phase 10 More Specialists / Providers   ✅
████████████████████  Post-10 Evidence-Aware Intelligence UX  ✅

NEXT — LOCKED / NOT STARTED
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
- bounded execution-state schema

### Result
Roberta can receive a user goal, choose whether a specialist/tool is required, execute through LangGraph, and finish deterministically.

---

## Phase 2 — Provider-Neutral Model / Tool Loop ✅ Complete

### Goal
Keep Roberta independent of one LLM provider while proving the runtime path.

### Delivered
- provider-neutral model injection and `bind_tools()` boundary
- deterministic fake models
- DeepSeek runtime integration
- opt-in live-model tests
- separate Oracle and specialist-planner model dependencies

### Result
LangGraph owns orchestration; the model provider remains an injected runtime dependency.

---

## Phase 3 — X1 Scout Boundary ✅ Complete

### Goal
Establish the specialist hierarchy so Roberta coordinates X1 work without directly owning chain-market tools.

### Delivered
- X1 Scout specialist graph/tool
- Roberta exposes X1 Scout rather than CMIS/provider HTTP tools
- structured specialist reports
- deterministic operation-routing guardrails
- CMIS status/provenance preservation

```text
Roberta
  ↓
X1 Scout
  ↓
CMIS
  ↓
X1 Provider
```

---

## Phase 4 — CMIS / X1 Provider Integration ✅ Complete

### Goal
Create the deterministic market-intelligence service boundary beneath X1 Scout.

### Delivered
- shared Cross-Chain Market Intelligence Service (CMIS) envelope
- CMIS HTTP boundary
- X1 Provider beneath CMIS
- X1 RPC / XDEX / X1.Ninja provider paths
- deterministic market, tokenomics, risk, pre-trade, ranking/history, activity, and verification contracts where promoted
- exact status/data/risk/confidence/source/warning/error preservation
- freshness/provenance and presentation guardrails

### Migration note
Existing `liquidity_scout` package/repository identifiers may remain while provider boundaries and deployments stabilize. That implementation detail does not change the architectural hierarchy.

---

## Phase 5 — X1 Evidence Completeness 🟡 Bounded / accepted capability boundary

### Goal
Improve deterministic X1 evidence coverage without inventing unavailable data.

### Completed foundation
- bounded mint/burn activity collection
- evidence-aware risk gateway
- historical snapshot comparison path
- read-only XDEX provider groundwork
- public XDEX pool discovery
- exact public-address identity for non-native token assets
- native XNT kept separate from wrapped-token assumptions
- fail-closed provider schema/error handling
- X1.Ninja trade-history/OHLCV contract work
- pool-specific reserve cross-check orchestration
- historical same-fact comparison primitives with explicit source-independence rules
- bridge candidate-URL provenance gating
- machine-readable X1 evidence capability classification

### Accepted remaining boundaries
CMIS now explicitly classifies remaining provider facts rather than leaving them as implicit roadmap promises. Examples include:

- wallet/beneficial-owner holder total: unavailable;
- token-account concentration: bounded;
- archival completeness: unavailable;
- direct XDEX history semantics: unavailable;
- direct XDEX quote semantics: unavailable;
- canonical native-XNT translation: verified;
- SSE handshake/access observation: bounded;
- live-event SSE semantics: unavailable;
- bridge candidate-URL provenance: bounded;
- bridge operational/route/fee/capacity/lifecycle state: unavailable.

These states are authoritative until CMIS accepts a new evidence contract and tests. Roberta must not infer a missing fact, rename token-account concentration as holder concentration, or treat UI/provider claims as verified machine-readable evidence.

### Result
Phase 5 remains **bounded**, not globally complete. The important architectural change is that the remaining limits are explicit and fail closed rather than functioning as unresolved ambiguity.

---

## Phase 6 — Agentic X1 Scout Planning ✅ Complete

### Goal
Let X1 Scout plan bounded multi-step investigations while deterministic code remains authoritative.

### Delivered
- separate planner-model dependency
- propose → enforce → CMIS calls → interpret graph
- autonomous read-only scope for accepted research operations
- deterministic required-operation enforcement, duplicate removal, and plan cap
- invalid planner-output fallback
- autonomous pre-trade rejection; explicit trade inputs remain caller-controlled

### Result
The LLM may propose research; deterministic policy decides what is allowed to execute.

---

# Phase 7 — Persistence and Durable Memory

## Phase 7A — LangGraph Thread / Checkpoint Persistence ✅ Complete

Delivered resumable current-task state with explicit `thread_id`, same-thread continuation, cross-thread isolation, fresh-graph resume, deterministic checkpoint tests, and the rule that checkpoints are historical execution context rather than authoritative current market truth.

## Phase 7B — HXMP Durable Memory Adapter ✅ Complete

Delivered a provider-neutral durable-memory contract, guarded relevance/category rules, HXMP adapter, deterministic serialization, read/dry-run paths, exact approval binding for write preparation, signer preflight, readback verification, and opt-in live contract probes without granting ordinary market-memory authority.

### Core rule

```text
Memory remembers what matters.
CMIS verifies what is happening now.
```

Fresh verified CMIS/provider evidence overrides remembered or checkpointed live-data snapshots.

---

## Phase 8 — Oracle Policy ✅ Complete

Tracking: Roberta issue #24 — completed.

### Delivered
- typed Oracle policy contracts
- explicit policy-document compiler
- hard constraints, preferences, thresholds, evidence requirements, and approval rules
- deterministic decision precedence
- explicit insufficient-evidence behavior
- structural hard-block enforcement before model synthesis
- provider-neutral policy facts
- missing-evidence → specialist research → deterministic re-evaluation loop

### Authority rule

```text
HXMP/Memory -> stable user policy
CMIS        -> current verified facts
Policy code -> deterministic rule result
LLM         -> explanation/synthesis, never override
```

---

## Phase 9 — Human in the Loop ✅ Complete

Tracking: Roberta issue #27 — completed.

### Delivered
- typed approval request/decision/outcome contracts
- approve/reject/edit/request-more-evidence decisions
- LangGraph interrupt/resume with same-thread isolation
- immutable reviewed proposal and canonical proposal hash
- exact approval binding to request/action/scope/proposal
- edits force a new proposal and re-review
- deterministic proceed/stop/re-review/research next-step classes
- secret-bearing approval fields rejected

### Rule
`approved` means a human reviewed one exact proposal/scope. It is not a reusable signing credential and does not authorize execution by itself.

---

## Phase 10 — More Specialists / Providers ✅ Complete

Tracking: Roberta issue #29, merged Roberta PR #43, Liquidity Scout/CMIS issue #78, and the accepted cross-repository capability-contract work.

### Goal
Expand Roberta beyond one chain specialist while preserving one hierarchy and one shared deterministic CMIS service layer.

### Accepted architecture

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

### Delivered — Roberta specialist layer
- stable provider-neutral specialist capability registry for X1 + Solana
- deterministic chain/capability → Scout dispatch
- Solana Scout LangGraph specialist subgraph
- Roberta-facing `solana_scout_investigate` tool
- shared CMIS client with explicit chain dispatch
- bounded Solana Scout planning for read-only `market_report`, `tokenomics`, and `risk_check`
- explicit autonomous `pre_trade_check` rejection
- strict Solana runtime configuration gate, disabled by default
- unconfigured Solana Scout makes zero CMIS service calls and returns explicit unavailable state
- standardized X1/Solana policy-fact adapters
- turn-scoped cross-chain evidence isolation
- end-to-end Oracle policy → Solana Scout → deterministic re-evaluation tests
- provider requirements/source-matrix documentation

### Delivered — shared Scout ↔ CMIS contract
- CMIS `GET /v1/cmis/capabilities`
- capability schema version 1 and versioned CMIS contract
- per-chain/per-service states: `supported`, `bounded`, `partial`, `unavailable`
- exact callable projection plus requirements/limitations
- Scout-side validation before service POST
- incompatible/missing/malformed capability manifests fail closed
- explicitly non-callable services fail before dispatch
- bounded/partial services remain callable without upgrading their evidence quality

### Delivered — Solana provider foundation beneath CMIS
The Solana implementation remains layered rather than monolithic. Accepted work includes:
- explicit provider registry/chain dispatch and unconfigured fail-closed state
- canonical read-only Solana RPC foundation, including legacy SPL Token and Token-2022 identity handling
- RPC → CMIS evidence normalization
- Jupiter source adapter
- Helius indexed source adapter
- DEX Screener pair-scoped independent market adapter
- explicit-tolerance Jupiter ↔ DEX Screener price cross-check
- explicit-slot-lag Solana RPC ↔ Helius supply cross-check
- exact-mint gated `asset_lookup`
- exact-mint gated `tokenomics`
- exact-mint gated `market_report`
- exact-mint gated `risk_check`
- provenance-safe Solana observation ledger
- narrow bounded Jupiter historical comparison support
- versioned CMIS capability manifest describing what Solana services are callable and their limitations

### Evidence and rollout boundary
Phase 10 completes the **architecture, deterministic contracts, provider foundation, and bounded read-only service path**. It does not claim that every Solana fact is verified or that every deployment should enable Solana live data.

Deployment/live promotion remains fail-closed and capability-specific:
- exact mint identity is required where promoted
- missing fields remain unavailable, never zero/false by default
- price/liquidity/volume scope and freshness limitations remain explicit
- DEX Screener data remains pair-scoped unless a separate aggregation contract is proven
- Helius/Jupiter labels remain provider evidence, not Roberta's final safety judgment
- Token-2022 behavior remains explicit
- credentials stay external to Git
- a deployment must explicitly configure providers and satisfy its live-probe/evidence gates before enabling corresponding live capability

### Phase 10 acceptance result
- final refreshed Solana Scout was based on the guarded CMIS baseline
- current-head deterministic CI passed
- no unresolved review threads remained
- Solana Scout merged as Roberta PR #43
- stale pre-guard PR #30 was closed without merge
- the CMIS provider workstream and machine-readable capability contract were advanced/merged
- no signing, transaction construction, broadcast, custody, autonomous execution, or value movement was added

### Rule
Do not duplicate CMIS per chain. Add chain providers beneath shared deterministic service contracts, and add a chain Scout only when chain-specific reasoning justifies one.

---

## Post-Phase-10 — Evidence-Aware Intelligence & User Experience ✅ Complete

Merged in Roberta PR #46. Detailed behavior is documented in [`EVIDENCE_AWARE_INTELLIGENCE.md`](./EVIDENCE_AWARE_INTELLIGENCE.md).

### Goal
Make Roberta evidence-aware and answer-first without turning the conversational layer into a second CMIS calculation engine.

### Delivered
- typed CMIS evidence receipt and proof metadata contracts
- Chain Scout `evidence_context` propagation for X1 and Solana
- preservation of verification status, proof strength, scope, freshness, disagreements, limitations, unresolved fields, and provenance
- risk kept separate from proof strength
- capability-handshake requirement for CMIS evidence receipt schema 1 and proof score schema 1
- deterministic recommendation evidence planning for buy/sell, trade-size, safer-asset, what-changed, liquidity-risk, LP, and price-move questions
- X1 Scout integration of the allowed read-only evidence requirements
- answer-first recommendation/pre-trade synthesis
- deterministic pre-trade finalization rather than a second free-form rewrite
- preservation of human-readable execution-estimate phrases returned by CMIS
- wallet interpretation safety contract that forbids unsupported insider/whale/bot/accumulator/distributor labels
- cross-chain evidence isolation: X1 and Solana evidence may be compared but not merged/recomputed into a synthetic proof or safety grade
- deterministic and HTTP-fixture tests for the evidence-aware contract

### Answer-first contract
Normal recommendation-style responses should prioritize:

1. conclusion/recommendation/blocker;
2. 2–4 important evidence-backed reasons;
3. risk when CMIS actually supplies a dedicated risk level;
4. evidence quality/proof strength;
5. important missing evidence;
6. technical evidence on request.

`PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk levels. If CMIS does not return a dedicated risk level, Roberta leaves risk unknown instead of inventing one.

### Wallet / whale boundary
Roberta may accept future deterministic wallet primitives from CMIS, but behavioral or identity labels remain unavailable until a later accepted classification contract explicitly permits them.

### Result
Roberta is now substantially better positioned as the normal user-facing voice: CMIS proves and scores evidence, Chain Scouts preserve the chain-specific context, and Roberta explains the result without overwriting deterministic facts.

---

## Current read-only analytical dependency — CMIS pre-trade sizing

CMIS GitHub Issue #99 is the current important analytical work item for questions such as `Is it ok to purchase $500 of AGI?`.

CMIS owns:
- deterministic `notional_usd` evaluation;
- notional-to-verified-liquidity ratio;
- versioned trade-size policy/classification;
- price-impact/slippage/route/fee analysis only where semantics are verified;
- explicit unavailable/insufficient states otherwise.

Roberta owns:
- concise user-facing explanation;
- evidence-aware synthesis;
- policy interpretation;
- preserving CMIS risk/proof/missing-evidence boundaries.

Roberta must not duplicate or invent the CMIS analytical calculations while Issue #99 is being completed.

---

## Phase 11 — Controlled Execution ⬜ Planned / locked

**Phase 11 has not started.**

### Goal
If explicitly authorized as a future milestone, add a tightly scoped Execution Agent only after policy, provider verification, and human-approval boundaries are revalidated for execution.

### Intended boundary

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
sign / broadcast only within the approved scope
```

### Required principle
CMIS remains read-only market/risk intelligence. Phase 9 approval is not itself execution authority. No execution code should be inferred from Phase 10 or the evidence-aware UX milestone.

---

# System hierarchy

```text
USER
  ↓
ROBERTA — Oracle / Coordinator / normal user-facing voice
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

Evidence quality flows upward without recomputation:

```text
CMIS evidence receipt / proof score
  → Chain Scout evidence_context
  → Roberta explanation
```

HXMP remains orthogonal to live market verification:

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
7. Preserve CMIS evidence receipts/proof strength; do not recompute them into a second authoritative score.
8. Keep risk separate from evidence quality.
9. Do not grant broad wallet authority to demonstrate autonomy.
10. Require explicit human approval before consequential blockchain actions.
11. Keep signing and memory-encryption keys local; never commit or print secret bytes.
12. Use GitHub issues/PRs/CI as the development checkpoint for each coherent milestone.

---

# Current stop boundary

**Phase 10 is complete. The post-Phase-10 Evidence-Aware Intelligence & User Experience milestone is complete. Phase 11 is planned/locked and has not been started.**

Remaining provider limitations are explicit CMIS capability states rather than permission for Roberta to guess. Near-term progress should deepen read-only analysis and intelligence—especially deterministic pre-trade sizing/impact, historical evidence, and future wallet primitives—without silently expanding into controlled execution.
