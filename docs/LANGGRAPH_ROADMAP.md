# Roberta LangGraph Roadmap

Last updated: 2026-08-20

## Status legend

- ✅ Complete — implemented, tested, merged, and accepted
- 🟡 Bounded / partial — useful capability exists but evidence scope remains deliberately limited
- ⬜ Planned / locked — not started as a development milestone

## Current position

Roberta has completed the Phase 10 cross-chain specialist/provider milestone and the Post-Phase-10 Evidence-Aware Intelligence & User Experience milestone.

The accepted architecture supports X1 Scout and Solana Scout above one shared CMIS service layer. The Scout -> CMIS boundary is protected by a versioned machine-readable capability contract. Roberta preserves CMIS Evidence Receipts, Proof Scores, risk, provenance, limitations, and uncertainty through Chain Scout reports while producing answer-first user-facing synthesis.

CMIS has also completed its separately numbered Phase 11 read-only Verified Intelligence foundation and the deterministic pre-trade trade-size milestone previously tracked as CMIS Issue #99.

Roberta Phase 11 Controlled Execution remains intentionally **locked / not started**. Phase 9 human approval is a review boundary only; no completed milestone creates signing, broadcasting, custody, autonomous execution, or value-movement authority.

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
- START -> Oracle -> tool -> Oracle -> END loop
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
  -> X1 Scout
    -> CMIS
      -> X1 Provider
```

---

## Phase 4 — CMIS / X1 Provider Integration ✅ Complete

### Goal
Create the deterministic market-intelligence service boundary beneath X1 Scout.

### Delivered
- shared Cross-Chain Market Intelligence Service envelope
- CMIS HTTP boundary
- X1 Provider beneath CMIS
- X1 RPC / XDEX / X1.Ninja provider paths
- deterministic market, tokenomics, risk, pre-trade, ranking/history, activity, and verification contracts where promoted
- exact status/data/risk/confidence/source/warning/error preservation
- freshness/provenance and presentation guardrails

### Migration note
The CMIS implementation still uses the internal Python namespace `liquidity_scout` for compatibility. Repository/project identity and Python package identity are intentionally separate during migration.

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

### Accepted remaining boundary
CMIS explicitly classifies remaining provider facts rather than leaving them as implicit roadmap promises. Facts may be verified, bounded, partial, unavailable, conflicting, or insufficiently evidenced depending on the exact contract and runtime capability.

Examples of areas that can remain scope-limited include beneficial-owner holder semantics, token-account concentration, archival completeness, selected direct XDEX quote/history semantics, live-stream semantics, and bridge operational/route state.

Roberta must preserve those classifications. It must not infer a missing fact, rename account concentration as beneficial-owner concentration, or treat UI/provider claims as verified machine-readable evidence.

### Result
Phase 5 remains **bounded**, not globally complete. The important architectural result is that remaining limits fail closed and are machine-readable.

---

## Phase 6 — Agentic X1 Scout Planning ✅ Complete

### Goal
Let X1 Scout plan bounded multi-step investigations while deterministic code remains authoritative.

### Delivered
- separate planner-model dependency
- propose -> enforce -> CMIS calls -> interpret graph
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

Fresh accepted CMIS/provider evidence overrides remembered or checkpointed live-data snapshots.

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
- missing-evidence -> specialist research -> deterministic re-evaluation loop

### Authority rule

```text
HXMP / memory -> stable user policy
CMIS          -> current verified facts
Policy code   -> deterministic rule result
LLM           -> explanation / synthesis only
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

Tracking: Roberta issue #29 and merged Roberta PR #43, together with the accepted CMIS cross-chain provider/capability-contract work.

### Goal
Expand Roberta beyond one chain specialist while preserving one hierarchy and one shared deterministic CMIS service layer.

### Accepted architecture

```text
Roberta
  ├── X1 Scout
  │     -> CMIS -> X1 / XDEX providers
  └── Solana Scout
        -> CMIS -> Solana providers
```

### Delivered — Roberta specialist layer
- stable provider-neutral specialist capability registry for X1 + Solana
- deterministic chain/capability -> Scout dispatch
- Solana Scout LangGraph specialist subgraph
- Roberta-facing `solana_scout_investigate` tool
- shared CMIS client with explicit chain dispatch
- bounded Solana Scout planning for accepted read-only research services
- explicit autonomous `pre_trade_check` rejection
- strict Solana runtime configuration gate
- unconfigured Solana Scout fails closed with no unauthorized CMIS calls
- standardized X1/Solana policy-fact adapters
- turn-scoped cross-chain evidence isolation
- end-to-end Oracle policy -> Solana Scout -> deterministic re-evaluation tests
- provider requirements/source-matrix documentation

### Delivered — shared Scout <-> CMIS contract
- `GET /v1/cmis/capabilities`
- capability schema version 1 and versioned CMIS contract
- per-chain/per-service states such as `supported`, `bounded`, `partial`, `unavailable`
- exact callable projection plus requirements/limitations
- Scout-side validation before service POST
- incompatible/missing/malformed capability manifests fail closed
- explicitly non-callable services fail before dispatch
- bounded/partial services remain callable only without upgrading their evidence quality

### Delivered — Solana provider foundation beneath CMIS
Accepted components include:
- explicit provider registry/chain dispatch and unconfigured fail-closed state
- canonical read-only Solana RPC foundation
- legacy SPL Token and Token-2022 identity handling
- RPC -> CMIS evidence normalization
- Jupiter source adapter
- Helius indexed source adapter
- DEX Screener pair-scoped independent market adapter
- deterministic cross-source price/supply checks
- exact-mint gated service paths where required
- provenance-safe Solana observation history
- bounded historical comparison support
- versioned CMIS capability manifest describing callable Solana services and limitations

### Evidence and rollout boundary
Phase 10 completes the **architecture, deterministic contracts, provider foundation, and bounded read-only service path**. It does not claim that every Solana fact is verified or that every deployment should enable every live Solana capability.

Deployment/live promotion remains fail-closed and capability-specific:
- exact mint identity is required where promoted;
- missing fields remain unavailable, never zero/false by default;
- price/liquidity/volume scope and freshness limitations remain explicit;
- pair-scoped data remains pair-scoped without a proven aggregation contract;
- provider labels remain provider evidence, not Roberta's final safety judgment;
- Token-2022 behavior remains explicit;
- credentials stay external to Git;
- deployments must satisfy configuration and evidence gates before enabling a capability.

### Rule
Do not duplicate CMIS per chain. Add chain providers beneath shared deterministic service contracts, and add a Chain Scout only when chain-specific planning/interpretation justifies one.

---

## Post-Phase-10 — Evidence-Aware Intelligence & User Experience ✅ Complete

Merged in Roberta PR #46. Detailed behavior is documented in [`EVIDENCE_AWARE_INTELLIGENCE.md`](./EVIDENCE_AWARE_INTELLIGENCE.md).

### Goal
Make Roberta evidence-aware and answer-first without turning the conversational layer into a second CMIS calculation engine.

### Delivered
- typed CMIS Evidence Receipt and proof metadata contracts
- Chain Scout `evidence_context` propagation for X1 and Solana
- preservation of verification status, proof strength, scope, freshness, disagreements, limitations, unresolved fields, and provenance
- risk kept separate from proof strength
- capability-handshake requirement for accepted Evidence Receipt / Proof Score schemas
- deterministic recommendation evidence planning for common recommendation/research questions
- allowed read-only evidence requirements integrated into Scout planning
- answer-first recommendation/pre-trade synthesis
- deterministic pre-trade finalization rather than a second free-form rewrite
- wallet interpretation safety contract forbidding unsupported behavioral/ownership labels
- cross-chain evidence isolation
- deterministic and HTTP-fixture tests for the evidence-aware contract

### Answer-first contract
Normal recommendation-style responses should prioritize:

1. conclusion / recommendation / blocker;
2. 2–4 important evidence-backed reasons;
3. dedicated CMIS risk when actually supplied;
4. evidence quality / proof strength;
5. important missing evidence;
6. technical evidence on request.

`PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk levels. If CMIS does not return a dedicated risk level, Roberta leaves risk unknown rather than inventing one.

### Wallet / behavioral boundary
Roberta may consume deterministic wallet/concentration primitives from CMIS where accepted, but behavioral or ownership labels remain unavailable until a later deterministic classification contract explicitly permits them.

### Result
Roberta is the normal user-facing voice: CMIS proves and scores evidence, Chain Scouts preserve chain-specific context, and Roberta explains the result without overwriting deterministic facts.

---

## Current read-only analytical baseline — CMIS pre-trade sizing ✅ Complete

The deterministic pre-trade trade-size milestone previously tracked as CMIS Issue #99 is complete.

CMIS now owns and supplies, where the evidence/policy contract permits:
- deterministic proposed `notional_usd` evaluation;
- verified liquidity context;
- notional-to-verified-liquidity ratio;
- explicit versioned trade-size policy/classification;
- evidence-freshness handling;
- price-impact/fee/route-related facts only where exact semantics are independently proven;
- explicit unavailable/insufficient states for unsupported advanced estimates.

Roberta owns:
- concise user-facing explanation;
- evidence-aware synthesis;
- policy interpretation;
- preservation of CMIS risk/proof/missing-evidence boundaries.

Roberta must not duplicate or invent CMIS calculations.

Every current pre-trade result remains analysis-only and preserves the equivalent of:

```text
analysis_only = true
execution_authorized = false
```

A `PASS` is not permission to trade.

---

## Current CMIS dependency — Phase 11 Verified Intelligence ✅ Read-only foundation complete

CMIS's separately numbered Phase 11 established read-only deterministic primitives for areas including:

- exact top-account concentration observations and compatible numeric changes;
- neutral verified wallet-activity facts;
- sanitized sparse historical intelligence storage/comparison;
- evidence-bound conclusions backed by Evidence Receipts and Proof Scores.

These primitives are not automatically public Scout services. The live capability contract remains authoritative.

Roberta must not infer labels such as insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, or common owner unless a later accepted classification contract explicitly permits such a conclusion.

---

## Phase 11 — Controlled Execution ⬜ Planned / locked

**Phase 11 has not started.**

### Goal
If explicitly authorized as a future milestone, add a tightly scoped Execution Agent only after policy, provider verification, simulation, and human-approval boundaries are revalidated for execution.

### Intended boundary

```text
research
  -> simulate
  -> prepare exact proposed transaction
  -> human approval
  -> revalidate exact approval + current preconditions
  -> sign / broadcast only within approved scope
```

### Required principle
CMIS remains read-only market/risk intelligence. Phase 9 approval is not itself execution authority. No execution code or wallet authority should be inferred from Phase 10, CMIS Phase 11, pre-trade analysis, or the evidence-aware UX milestone.

A future execution milestone would require its own accepted transaction-construction/simulation, exact approval-consumption/revalidation, signer/broadcast, replay-protection, precondition, and failure contracts.

---

# System hierarchy

```text
USER
  -> ROBERTA — Oracle / Coordinator / normal user-facing voice
    -> CHAIN SCOUTS / SPECIALISTS
      -> CROSS-CHAIN MARKET INTELLIGENCE SERVICE (CMIS)
        -> CHAIN PROVIDERS
```

Authority flows downward:

```text
Roberta -> Chain Scout -> CMIS -> Chain Provider
```

Verified information flows upward:

```text
Chain Provider -> CMIS -> Chain Scout -> Roberta
```

Evidence quality flows upward without recomputation:

```text
CMIS Evidence Receipt / Proof Score
  -> Chain Scout evidence_context
  -> Roberta explanation
```

HXMP remains orthogonal to live market verification:

```text
HXMP -> durable stable context -> Roberta
CMIS -> fresh verified facts   -> Roberta
```

---

# Development principles

1. Build and test one layer at a time.
2. Preserve working deterministic X1 and Solana boundaries during further expansion.
3. Keep LLM planning separate from deterministic authority.
4. Do not manufacture unavailable live-data facts.
5. Fresh accepted CMIS/provider evidence overrides memory or checkpoint snapshots.
6. Prefer shared CMIS contracts with chain-specific providers rather than duplicate intelligence stacks.
7. Preserve CMIS Evidence Receipts and Proof Scores; do not recompute them into a second authoritative score.
8. Keep risk separate from evidence quality.
9. Keep chain evidence contexts isolated when doing cross-chain reasoning.
10. Do not grant broad wallet authority to demonstrate autonomy.
11. Human review is not execution authority.
12. Keep signing and memory-encryption keys local; never commit or print secret bytes.
13. Use GitHub issues/PRs/CI as the checkpoint for each coherent milestone.

---

# Current stop boundary

**Phase 10 is complete. Post-Phase-10 Evidence-Aware Intelligence & User Experience is complete. CMIS Phase 11 read-only Verified Intelligence is complete. Roberta Phase 11 Controlled Execution is planned/locked and has not started.**

Near-term progress should deepen read-only X1/Solana evidence, historical intelligence, wallet/concentration primitives, provider coverage, and policy/user experience without reopening completed architecture or silently expanding into controlled execution.
