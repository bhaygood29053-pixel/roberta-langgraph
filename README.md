# Roberta LangGraph

Roberta is the top-level Oracle, policy-aware coordinator, and normal user-facing voice for the multi-agent system.

Current accepted hierarchy:

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Current chain specialists:

```text
Roberta
  ├── X1 Scout
  │     -> CMIS -> X1/XDEX providers
  └── Solana Scout
        -> CMIS -> Solana providers
```

Roberta does not call provider APIs directly and does not reproduce CMIS market, risk, verification, evidence-receipt, proof-score, or deterministic pre-trade calculations.

## Repository boundary

CMIS is maintained in the separate GitHub repository:

```text
bhaygood29053-pixel/cmis
```

That repository was historically named `liquidity-scout`. The canonical project identity is now **CMIS — Cross-Chain Market Intelligence Service**.

The CMIS implementation still uses the internal Python namespace `liquidity_scout` for compatibility. Repository identity and Python package identity are intentionally separate during the staged migration.

## Current roadmap status

- Phase 1 Core Agent Loop — complete
- Phase 2 Provider-Neutral Model Loop — complete
- Phase 3 X1 Scout Boundary — complete
- Phase 4 CMIS / X1 Provider Integration — complete
- Phase 5 X1 Evidence Completeness — bounded by explicit CMIS capability states
- Phase 6 Agentic X1 Scout Planning — complete
- Phase 7A Thread / Checkpoint Persistence — complete
- Phase 7B HXMP Durable Memory — complete
- Phase 8 Oracle Policy — complete
- Phase 9 Human in the Loop — complete
- Phase 10 More Specialists / Providers — complete
- Post-Phase-10 Evidence-Aware Intelligence & User Experience — complete
- Cross-project engineering governance (#97/#98) — complete
- Deterministic HXMP provenance/reconciliation hardening (#97/#99) — complete
- Technology Radar design/specification (#97/#100) — complete; runtime implementation deferred
- Phase 11 Controlled Execution — **locked / not started**

See [`docs/LANGGRAPH_ROADMAP.md`](./docs/LANGGRAPH_ROADMAP.md) for the authoritative Roberta roadmap.

CMIS has its own execution-phase numbering. CMIS Phase 11 refers to its completed **read-only Verified Intelligence foundation**; that is separate from Roberta Phase 11 Controlled Execution.

The active upstream intelligence milestone is now **CMIS #263**, a deterministic concentration-threshold alert evidence contract. It remains CMIS-internal/read-only/non-promoted; Roberta has no new alert capability unless a later CMIS promotion contract and Roberta roadmap gate explicitly authorize adoption.

## Engineering workflow

Meaningful Roberta changes follow the repository-authoritative workflow in [`docs/ENGINEERING_WORKFLOW.md`](./docs/ENGINEERING_WORKFLOW.md). It requires roadmap/issue gating, narrow tracer-bullet slices, behavior-first verification, exact-head deterministic testing, and independent **Spec**, **Code/Architecture**, and **Authority/Safety** review before merge.

Green CI alone is not sufficient if a required review axis fails. The workflow preserves `User -> Roberta -> Chain Scout -> CMIS -> Provider` and does not widen Controlled Execution.

## Technology Radar design

Issue #100 defines a future read-only roadmap-aware Technology Radar in [`docs/TECHNOLOGY_RADAR.md`](./docs/TECHNOLOGY_RADAR.md). The specification was accepted through PR #103 as the third and final slice of parent #97.

The document is a **design/specification only**. No Radar runtime, source adapter, scheduler, dependency, autonomous adoption path, provider-trust change, or execution authority is currently authorized. The proposed Radar keeps trend strength, roadmap relevance, research-evidence quality, adoption risk, and license compatibility separate and routes any promising discovery back through the normal engineering workflow.

A future implementation requires a separate accepted roadmap gate and implementation issue.

## Evidence-aware intelligence

Roberta consumes the CMIS evidence-quality and capability contracts.

Chain Scout reports preserve CMIS evidence context including, where available:

- verification status;
- proof strength and category reasons;
- evidence scope;
- freshness;
- source disagreements;
- limitations;
- unresolved fields;
- source provenance;
- risk separately from proof strength.

Roberta requires the CMIS capability manifest to advertise the accepted evidence receipt/proof-score contract and the read-only intelligence-foundation boundary required by the current Scout client.

Provider-reported information remains provider-reported until CMIS records independent verification. Missing evidence remains unknown/unproven.

Detailed behavior is documented in [`docs/EVIDENCE_AWARE_INTELLIGENCE.md`](./docs/EVIDENCE_AWARE_INTELLIGENCE.md).

## Answer-first user experience

Recommendation-style responses prioritize:

1. conclusion / recommendation / blocker;
2. the most important evidence-backed reasons;
3. risk when CMIS actually provides a dedicated risk level;
4. evidence quality / proof strength;
5. important missing evidence;
6. deeper technical evidence on request.

Pre-trade responses use deterministic finalization rather than passing the structured result through a second free-form rewrite.

`PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk levels. If CMIS does not provide a dedicated risk level, Roberta keeps risk unknown rather than inventing one.

## Recommendation evidence planning

Roberta deterministically identifies evidence needs for common questions such as:

- buy/sell recommendations;
- trade-size questions;
- safer-asset comparisons;
- what-changed questions;
- liquidity-risk questions;
- LP questions;
- price-move questions.

Chain Scouts incorporate allowed read-only evidence requirements into their deterministic planning. Recommendation wording cannot silently enable execution capability.

## X1 evidence capability boundary

Remaining X1 provider limitations are explicit CMIS capability states rather than facts Roberta may guess.

Examples include facts that are:

- independently verified;
- bounded to a narrower evidence scope;
- unavailable until semantics are proven.

Roberta preserves those boundaries and does not upgrade missing or partial provider evidence through model interpretation.

## Wallet / behavioral safety boundary

CMIS now has a read-only Verified Intelligence foundation for neutral wallet-activity and concentration primitives plus an accepted internal deterministic direct wallet-relationship evidence foundation with explicit non-ownership semantics. Those primitives/foundations are not automatically promoted into public Scout services.

Roberta may not label a wallet as an insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, common owner, beneficial owner, or equivalent unless a later accepted CMIS classification contract and service promotion explicitly permit the label from proven evidence.

Facts and interpretations remain separate.

## Cross-chain evidence boundary

X1 and Solana Scout reports preserve separate chain-specific evidence contexts.

Roberta may compare evidence returned by each chain, but it may not:

- merge source lists into one synthetic source set;
- apply one chain's scope/freshness to another chain;
- recompute CMIS proof strength;
- recompute CMIS market risk;
- create a synthetic cross-chain safety grade;
- substitute X1 facts for missing Solana facts or vice versa.

## Durable memory and policy

HXMP and LangGraph checkpoints are not authoritative sources for current market facts.

```text
HXMP / durable memory -> stable context and explicit policy
CMIS                  -> current verified facts and evidence
Policy code           -> deterministic rule result
LLM                    -> explanation / synthesis only
```

Fresh verified CMIS/provider evidence overrides remembered or checkpointed live-market snapshots.

The accepted deterministic reconciliation seam may classify compatible accepted historical context as `superseded`, `evolution`, `conflict`, or `unknown`. Incompatible semantics/category/chain/scope, missing or ambiguous time, unaccepted evidence, or reversed observation order fail closed to `unknown`. A conflict or insufficient historical context may justify stronger fresh verification; it may not override fresh CMIS truth or become a new market/risk fact.

## Human approval boundary

Phase 9 supports resumable human review with exact proposal/scope binding.

An approval means a human reviewed one exact proposal. It is not a reusable signing credential and does not grant broad future wallet authority.

## Controlled execution boundary

Roberta Phase 11 has **not started**.

Roberta currently has no authority for:

- transaction construction as an execution path;
- wallet signing;
- transaction broadcasting;
- custody;
- swap execution;
- autonomous trading;
- autonomous value movement;
- broad delegated wallet authority.

Research, recommendations, deterministic policy, human review, and CMIS pre-trade analysis must not be interpreted as execution authorization.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,deepseek]'
```

## Deterministic tests

```bash
python -m pytest -v -m 'not live and not cmis_live'
```

The deterministic suite covers the Oracle/tool loop, provider-neutral model injection, Chain Scout boundaries, CMIS capability validation, X1 and Solana evidence isolation, policy, persistence, durable-memory adapters, human approval, evidence-aware response contracts, and deterministic memory reconciliation.

## Provider-backed CMIS

The CMIS implementation is maintained in the separate `bhaygood29053-pixel/cmis` repository.

Start CMIS there with its current compatibility module path:

```bash
python -m liquidity_scout.cmis.http
```

Roberta defaults to:

```text
CMIS_BASE_URL=http://127.0.0.1:8765
```

Optional settings include:

```text
CMIS_TIMEOUT_SECONDS=30
CMIS_API_KEY=...
```

A non-loopback CMIS deployment should require Bearer authentication.

Run explicit CMIS integration tests while CMIS is running:

```bash
RUN_LIVE_CMIS_TESTS=1 python -m pytest -v -m cmis_live
```

Live tests should verify contracts/provenance rather than hard-code current market values.

## Model runtime

Set `DEEPSEEK_API_KEY` for the configured DeepSeek runtime path.

Opt-in live-model tests:

```bash
RUN_LIVE_MODEL_TESTS=1 python -m pytest -v -m live
```

Model-provider tests remain separate from deterministic provider/CMIS evidence verification.

## Local Roberta HTTP bridge

Start CMIS first, configure the model runtime, then start Roberta:

```bash
roberta-serve
```

Defaults:

```text
ROBERTA_HOST=127.0.0.1
ROBERTA_PORT=8766
```

Health check:

```bash
curl -s http://127.0.0.1:8766/healthz
```

The message endpoint is `POST /v1/roberta`. Transport callers provide the user message; they do not provide tool names, CMIS operations, market facts, proof scores, risk values, or execution controls.

A non-loopback bind should require `ROBERTA_API_KEY` and Bearer authentication.

## MoltGrid / Signal topology

The accepted user-facing topology is:

```text
CMIS        127.0.0.1:8765
  ↓
Roberta     127.0.0.1:8766
  ↓
MoltGrid / Signal listener
```

Roberta is the normal conversational voice. The transport layer owns admission/reply linkage/duplicate protection; Chain Scouts own chain-specific investigation; CMIS owns deterministic facts, evidence, proof quality, and risk.

If Roberta is unavailable, the normal user-facing transport should report availability failure rather than exposing raw CMIS output as the conversational response.

## Near-term boundary

The deterministic pre-trade trade-size milestone, descriptive intelligence-classification foundation, direct wallet-relationship evidence foundation, Roberta governance/HXMP reconciliation work, and Technology Radar specification are complete.

The active upstream CMIS milestone is #263, the first deterministic concentration-threshold alert evidence contract. It remains internal/read-only/non-promoted. Roberta should not add alert planning, presentation, or reliance merely because the CMIS internal foundation exists; that requires a later accepted CMIS service promotion and a Roberta adoption gate.

Future broader alert intelligence, additional provider/historical verification, field-by-field Solana maturity, future Ethereum expansion, any Technology Radar runtime, and any eventual Controlled Execution must each be promoted through explicit evidence, contract, and safety gates rather than inferred from the existing read-only foundation.