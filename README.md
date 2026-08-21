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
- **Learning System Phase 1 Source Ingestion — complete**
- **Learning System Phase 2 Structure Detection — complete**
- **Learning System Phase 3 Structure-Aware Evidence Chunking — complete**
- **Learning System Phase 4 Indexing Foundation — complete**
- **Learning System Phase 5 Retrieval Foundation — complete**
- **Learning System Phase 6 Grounded Answer + Citation Foundation — complete**
- **Learning System Phase 7 Answer Evaluation Foundation — complete**
- **Learning System Phase 8 Provisional Reflection + Candidate Lesson Foundation — complete**
- **Learning System Phase 9 Candidate Lesson Verification — in progress**
- Phase 11 Controlled Execution — **locked / not started**

The **Roberta Learning System is the primary active development track**. Existing CMIS, Chain Scout, transport, policy, memory, and approval functionality should remain stable unless a change is directly required to support the Learning System or fix a proven defect.

See [`docs/LANGGRAPH_ROADMAP.md`](./docs/LANGGRAPH_ROADMAP.md) for the authoritative Roberta roadmap, [`docs/LEARNING_SYSTEM.md`](./docs/LEARNING_SYSTEM.md) for source ingestion, [`docs/LEARNING_SYSTEM_STRUCTURE.md`](./docs/LEARNING_SYSTEM_STRUCTURE.md) for structure parsing, [`docs/LEARNING_SYSTEM_CHUNKING.md`](./docs/LEARNING_SYSTEM_CHUNKING.md) for evidence chunking, [`docs/LEARNING_SYSTEM_INDEXING.md`](./docs/LEARNING_SYSTEM_INDEXING.md) for indexing, [`docs/LEARNING_SYSTEM_RETRIEVAL.md`](./docs/LEARNING_SYSTEM_RETRIEVAL.md) for retrieval, [`docs/LEARNING_SYSTEM_GROUNDING.md`](./docs/LEARNING_SYSTEM_GROUNDING.md) for grounding/citation, [`docs/LEARNING_SYSTEM_EVALUATION.md`](./docs/LEARNING_SYSTEM_EVALUATION.md) for answer evaluation, [`docs/LEARNING_SYSTEM_REFLECTION.md`](./docs/LEARNING_SYSTEM_REFLECTION.md) for the accepted provisional reflection/candidate-lesson contract, and [`docs/LEARNING_SYSTEM_VERIFICATION.md`](./docs/LEARNING_SYSTEM_VERIFICATION.md) for the active Phase 9 verification contract.

CMIS has its own execution-phase numbering. CMIS Phase 11 refers to its completed **read-only Verified Intelligence foundation**; that is separate from Roberta Phase 11 Controlled Execution.

## Engineering workflow

Meaningful Roberta changes follow the repository-authoritative workflow in [`docs/ENGINEERING_WORKFLOW.md`](./docs/ENGINEERING_WORKFLOW.md). It requires roadmap/issue gating, narrow tracer-bullet slices, behavior-first verification, exact-head deterministic testing, and independent **Spec**, **Code/Architecture**, and **Authority/Safety** review before merge.

Green CI alone is not sufficient if a required review axis fails. The workflow preserves `User -> Roberta -> Chain Scout -> CMIS -> Provider` and does not widen Controlled Execution.

## Learning System

Issue #106 / PR #107 established deterministic provenance-preserving ingestion for approved UTF-8 sources:

- exact original source bytes are retained behind a provider-neutral `SourceStore` interface;
- `content_hash` is SHA-256 over the exact source bytes;
- `source_id` is deterministic/content-addressed from canonical identity material;
- identical re-ingestion is idempotent;
- changed content creates a distinct immutable record rather than replacing prior source truth;
- malformed source identity/state/metadata/UTF-8 input fails closed;
- metadata is detached and recursively immutable;
- static Learning System source records never authorize live state.

Issue #109 / PR #110 added deterministic structure-first Markdown parsing:

- artifact hash is revalidated before parsing;
- ATX hierarchy, repeated headings, parents, paths, and exact 1-based source locations are preserved;
- exact block text and line endings are retained for preamble, paragraphs, simple lists, fenced code, and narrow pipe tables;
- heading-looking code remains code;
- every nonblank line is accounted exactly once;
- unclosed fences become explicit partial state with warnings;
- identities are deterministic/content-addressed;
- all records deny live-state authority.

Issue #112 / PR #113 added deterministic structure-aware evidence chunking with exact source coverage, zero overlap, atomic code/list/table handling, source-line-only splitting for oversize prose, deterministic chunk identities, and no live-state authority.

Issue #115 / PR #116 added deterministic indexing with Unicode NFKC/casefold lexical analysis, optional typed embedding-provider contracts, explicit partial states, finite/dimension validation, reproducible vector fingerprints, and no live-state authority.

Issue #118 / PR #119 added deterministic retrieval with canonical corpus revalidation, exact filters, separately observable lexical/vector channels, deterministic RRF, local-context diversity, explicit `ok`/`partial`/`no_match`, benchmark helpers, and no live-state authority.

Issue #121 / PR #122 added deterministic grounding/citation validation with canonical retrieval reconstruction, exact evidence anchors, untrusted-source-text serialization, typed supported/insufficient/conflict claims, explicit partial/insufficiency handling, and no live-state/memory-promotion/execution authority.

Issue #124 / PR #125 added deterministic independent answer evaluation with approved golden cases, separate retrieval/answer dimensions, explicit failure classifications, semantic groundedness left `not_evaluated` without an accepted semantic evaluator, and no live-state/memory-promotion/execution authority.

Issue #127 / PR #128 added deterministic provisional reflection + candidate-lesson construction from canonical failed evaluations. Candidate lessons remain generated/provisional hypotheses with exact provenance and deterministic verification plans; Phase 8 has no verified lifecycle state and cannot write trusted memory or authorize live state, governance, or execution.

Issue #129 / PR #131 is implementing **Learning System Phase 9 — Candidate Lesson Verification**. The active contract revalidates the exact Phase 8 bundle/lifecycle, executes only the deterministic checks already present in the accepted verification plan, computes fresh Phase 7 retest evaluations from canonical retest evidence, preserves per-check `pass`/`fail`/`inconclusive`, and permits `verified_for_learning` only when every required check passes. `verified_for_learning` remains verification evidence only: it does not authorize source truth, current market truth, CMIS/provider trust, HXMP/durable-memory promotion, governance mutation, wallet authority, or execution.

The Learning System does not replace CMIS for changing market/blockchain state. Fresh accepted CMIS/provider evidence remains authoritative for current prices, liquidity, supply, wallet state, risk, and other freshness-sensitive facts.

## Technology Radar design

Issue #100 defines a future read-only roadmap-aware Technology Radar in [`docs/TECHNOLOGY_RADAR.md`](./docs/TECHNOLOGY_RADAR.md).

The document is a **design/specification only**. No Radar runtime, source adapter, scheduler, dependency, autonomous adoption path, provider-trust change, or execution authority is currently authorized. The proposed Radar keeps trend strength, roadmap relevance, research-evidence quality, adoption risk, and license compatibility separate and routes any promising discovery back through the normal engineering workflow.

A future implementation requires a separate accepted roadmap gate and implementation issue. Technology Radar implementation is not the current primary development track while the Learning System is being built.

## Durable memory and policy

HXMP and LangGraph checkpoints are not authoritative sources for current market facts.

```text
HXMP / durable memory -> stable context and explicit policy
Learning System       -> static source knowledge and later verified learning state
CMIS                  -> current verified facts and evidence
Policy code           -> deterministic rule result
LLM                    -> explanation / synthesis only
```

Fresh verified CMIS/provider evidence overrides remembered, checkpointed, or Learning System live-market snapshots; the Learning System must not create such snapshots as trusted source knowledge.

## Controlled execution boundary

Roberta Phase 11 has **not started**.

Roberta currently has no authority for transaction construction as an execution path, wallet signing, transaction broadcasting, custody, swap execution, autonomous trading, autonomous value movement, or broad delegated wallet authority.

Research, recommendations, deterministic policy, human review, Learning System output, and CMIS pre-trade analysis must not be interpreted as execution authorization.

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

Live/model/provider tests remain separate evidence lanes and should not be substituted for deterministic CI.
