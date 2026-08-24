# Roberta LangGraph

Roberta is the top-level Oracle, policy-aware coordinator, and normal user-facing voice for the multi-agent system.

## Canonical architecture

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

Roberta owns orchestration, user policy, specialist selection, cross-chain coordination, approval boundaries, learning workflow coordination, and final synthesis. Chain Scouts own chain-specific planning and interpretation. CMIS owns deterministic freshness-sensitive facts, evidence, Evidence Receipts, Proof Scores, risk, capability eligibility, historical intelligence, and bounded analysis-only pre-trade calculations.

Roberta does not call market providers directly and does not reproduce CMIS calculations to manufacture a second market fact.

## Repository boundary

CMIS is maintained separately at `bhaygood29053-pixel/cmis`.

The CMIS repository was historically named Liquidity Scout. Its internal Python namespace still uses `liquidity_scout` for compatibility; that namespace does not create a separate authority layer.

## Current accepted status — reconciled 2026-08-23

Core Roberta milestones are accepted through:

- Phase 1 Core Agent Loop;
- Phase 2 Provider-Neutral Model Loop;
- Phase 3 X1 Scout Boundary;
- Phase 4 CMIS / X1 Provider Integration;
- Phase 5 X1 Evidence Completeness as an explicitly bounded/fail-closed capability boundary;
- Phase 6 Agentic X1 Scout Planning;
- Phase 7A Thread / Checkpoint Persistence;
- Phase 7B HXMP Durable Memory;
- Phase 8 Oracle Policy;
- Phase 9 Human in the Loop;
- Phase 10 More Specialists / Providers;
- Post-Phase-10 Evidence-Aware Intelligence & User Experience;
- X1 decision-production readiness;
- Solana read-only production readiness for the currently promoted Scout surface;
- adoption/readiness of CMIS `concentration_change_intelligence/v1` through X1 Scout.

Roberta Phase 11 Controlled Execution remains **locked / not started**.

### Learning System

Accepted Learning System foundations:

1. Source ingestion — complete.
2. Structure detection — complete.
3. Structure-aware evidence chunking — complete.
4. Lexical/embedding indexing foundation — complete.
5. Retrieval + benchmark foundation — complete.
6. Grounded answer + citation foundation — complete.
7. Independent answer evaluation — complete.
8. Provisional reflection + candidate lesson foundation — complete.
9. Independent candidate-lesson verification — complete.
10. Verified lesson retention — **specification accepted under #133/#134; runtime implementation still unaccepted**.

`verified_for_learning` remains verification evidence only. It is not source truth, durable-memory promotion, governance authority, wallet authority, or execution authority.

The draft Phase 10 implementation PR #136 remains blocked by five unresolved P1 findings: procedural-body eligibility, actual source-contradiction evaluation, trusted source-scope completeness, evidence/decision-bound lifecycle transitions, and recoverable duplicate provenance. Green CI does not override those review blockers.

### Blockchain Reasoning Pyramid

The Pyramid training/evaluation track is now a major accepted Roberta subsystem, but it remains separate from trusted Learning System retention.

Accepted milestones include:

- #149 — 20-level Blockchain Reasoning Pyramid, 1,000-question level contract, integrity/Boss gates, SQLite performance ledger, and Learning Command Center dashboard;
- #150 — automated Pyramid exam/grading/checkpoint loop;
- #151/#152/#154 — semantic-equivalence calibration, PASS/PARTIAL/FAIL scoring, and question-first grading with checkpoint schema v3;
- #153 — bounded fenced-JSON response acceptance;
- #155 — remediation analyzer and fresh-practice CLI;
- #160 — 50-question Mastering Blockchain Level 1 smoke curriculum;
- #162 — question-first grader hardening against reference anchoring;
- #167 — one bounded missing-answer recovery for answer batches;
- #169 — Pyramid weakness -> deterministic Learning System remediation handoff;
- #171 — MB4E question-first grading semantics v2;
- #173 — historical checkpoint regrade without regenerating Roberta answers;
- #175 — one bounded corrective adjudication for invalid single-part `incomplete_reasoning`;
- #177 — source-grounded Pyramid reconstruction using the accepted Learning System source/retrieval/evidence-packet path.

Pyramid results are training/evaluation state. They do not automatically create Phase 8 candidates, Phase 9 verification results, Phase 10 retention decisions, verified lessons, source truth, HXMP writes, or execution authority.

### Active Roberta work

Current open work that is **not accepted yet**:

- **#179 — MB4E legacy Level 1 provenance migration:** open and CI-green, but two unresolved P2 review findings remain: PDF-page locator support must exist in the core reconstruction API rather than only the CLI, and nested output directories must fail closed to avoid recursive staging/copy behavior.
- **#141 — XenBlocks PoW source onboarding:** open and blocked by an unresolved P1 because the canonical Phase 1 artifact must preserve/hash the exact uploaded CRLF bytes rather than an LF-normalized derivative.
- **#136 — Learning System Phase 10 retention implementation:** draft and blocked by five unresolved P1 findings described above.

These branches must not be described as accepted `main` behavior until their review and merge gates pass.

## Accepted Learning System sources

The accepted static source registry is documented at [`docs/learning_sources/README.md`](./docs/learning_sources/README.md).

Current accepted source onboarding on `main` includes:

- X1 Blockchain Whitepaper v1.0;
- XDEX documentation snapshot;
- XEN Litepaper v1.7;
- XEN Torrent / XENFT Litepaper v0.3;
- XONE ERC20 Token v4;
- *Mastering Blockchain, Fourth Edition* as an external exact-transcript integrity contract;
- Solana whitepaper v0.8.13.

Static source inclusion never grants live-state authority. Freshness-sensitive prices, liquidity, supply, wallet state, provider health, validator state, risk, fees, software versions, and other changing blockchain facts still require the authorized Scout -> CMIS -> Provider path.

XenBlocks PoW documentation remains pending until #141 satisfies the exact-byte Phase 1 provenance contract and merges.

## Source-of-truth documentation

- [`docs/LANGGRAPH_ROADMAP.md`](./docs/LANGGRAPH_ROADMAP.md) — authoritative Roberta roadmap/status.
- [`docs/LEARNING_SYSTEM.md`](./docs/LEARNING_SYSTEM.md) — Learning System umbrella/status and phase map.
- [`docs/LEARNING_SYSTEM_STRUCTURE.md`](./docs/LEARNING_SYSTEM_STRUCTURE.md) — structure parsing contract.
- [`docs/LEARNING_SYSTEM_CHUNKING.md`](./docs/LEARNING_SYSTEM_CHUNKING.md) — evidence chunking contract.
- [`docs/LEARNING_SYSTEM_INDEXING.md`](./docs/LEARNING_SYSTEM_INDEXING.md) — indexing contract.
- [`docs/LEARNING_SYSTEM_RETRIEVAL.md`](./docs/LEARNING_SYSTEM_RETRIEVAL.md) — retrieval contract.
- [`docs/LEARNING_SYSTEM_GROUNDING.md`](./docs/LEARNING_SYSTEM_GROUNDING.md) — grounding/citation contract.
- [`docs/LEARNING_SYSTEM_EVALUATION.md`](./docs/LEARNING_SYSTEM_EVALUATION.md) — answer evaluation contract.
- [`docs/LEARNING_SYSTEM_REFLECTION.md`](./docs/LEARNING_SYSTEM_REFLECTION.md) — provisional reflection/candidate contract.
- [`docs/LEARNING_SYSTEM_VERIFICATION.md`](./docs/LEARNING_SYSTEM_VERIFICATION.md) — candidate verification contract.
- [`docs/LEARNING_SYSTEM_RETENTION.md`](./docs/LEARNING_SYSTEM_RETENTION.md) — accepted Phase 10 retention specification.
- [`docs/learning_sources/README.md`](./docs/learning_sources/README.md) — accepted/pending static-source registry.
- [`docs/ENGINEERING_WORKFLOW.md`](./docs/ENGINEERING_WORKFLOW.md) — repository-authoritative engineering workflow.
- [`docs/TECHNOLOGY_RADAR.md`](./docs/TECHNOLOGY_RADAR.md) — accepted design/specification only; no Radar runtime is authorized.

## Evidence and authority rules

Core rules remain unchanged:

1. Fresh accepted CMIS/provider evidence overrides remembered, checkpointed, book/RAG, Pyramid, or Learning System material for freshness-sensitive state.
2. Missing evidence remains unknown/unavailable; it is never zero-filled or guessed.
3. Proof Score and market risk are separate concepts.
4. Provider-reported facts remain provider-reported until CMIS establishes accepted verification.
5. Cross-chain evidence keeps chain-specific provenance and scope.
6. Human approval binds one exact proposal/scope and is not reusable wallet authority.
7. Learning, remediation, evaluation, policy, and pre-trade analysis do not imply execution permission.

## Durable memory, training, and live truth

```text
LangGraph checkpoints -> current thread/workflow state
HXMP durable memory    -> stable durable context under its own write/approval rules
Learning System        -> static sources + separately gated verified learning
Pyramid                -> training/evaluation/remediation state
CMIS                   -> current deterministic verified market/blockchain evidence
Policy code            -> deterministic rule results
LLM                     -> explanation/synthesis, not trust root
```

Phase 10 v1 is explicitly in-memory/provider-neutral and does **not** authorize HXMP writes. Any future verified-lesson persistence to HXMP requires a separate accepted gate reconciling the Learning System retention contract with wallet-bound HXMP write semantics.

## Controlled execution boundary

Roberta currently has no authority for:

- autonomous transaction construction as an execution path;
- wallet signing;
- broadcasting;
- custody;
- swaps/trading;
- bridge value transfer;
- autonomous value movement;
- broad delegated wallet authority.

Controlled Execution remains locked.

## Installation

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

Live/provider tests remain opt-in and separate from the deterministic gate.

## Pyramid commands

The repository exposes Pyramid commands for the accepted training path, including:

```text
roberta-pyramid-run
roberta-pyramid-dashboard
roberta-pyramid-remediate
roberta-pyramid-regrade
roberta-pyramid-source-reconstruct
```

Migration tooling proposed by PR #179 is not accepted until that PR merges.

## Provider-backed CMIS

Start CMIS from the separate repository using its compatibility module path:

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

## Model runtime

Set `DEEPSEEK_API_KEY` for the configured DeepSeek runtime path.

Opt-in live-model tests:

```bash
RUN_LIVE_MODEL_TESTS=1 python -m pytest -v -m live
```

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

The message endpoint is `POST /v1/roberta`. Transport callers provide user messages; they do not provide CMIS truth, proof scores, risk values, or execution controls.

## Local topology

```text
CMIS        127.0.0.1:8765
  ↓
Roberta     127.0.0.1:8766
  ↓
MoltGrid / Signal transport
```

Roberta is the normal conversational voice. If Roberta is unavailable, transport should report an availability failure rather than substitute raw CMIS output as the user-facing answer.

---

**Roberta coordinates and learns under evidence boundaries. CMIS verifies current facts. Controlled Execution remains locked.**
