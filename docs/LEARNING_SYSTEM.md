# Roberta Learning System

Last reconciled: 2026-08-25 (America/New_York)

Status: **Phases 1-9 accepted; Phase 10 retention specification accepted but implementation still blocked/unaccepted.**

## Purpose

The Roberta Learning System provides an evidence-grounded path from approved static sources through retrieval, evaluation, reflection, candidate verification, and separately gated retention.

It is not a replacement for CMIS live truth. It is not an automatic self-training, memory-promotion, or execution-authority path.

## Canonical authority boundary

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Learning System source records are static source knowledge. They are not authoritative for changing prices, liquidity, supply, wallet state, validator state, provider health, software versions, fees, risk, or other freshness-sensitive blockchain state.

Fresh accepted CMIS/provider evidence remains authoritative for freshness-sensitive facts.

## Accepted Learning System pipeline

```text
exact approved source artifact
  -> Phase 1 source ingestion
  -> Phase 2 structure detection
  -> Phase 3 evidence chunking
  -> Phase 4 indexing
  -> Phase 5 retrieval
  -> Phase 6 evidence packet + grounded citations
  -> Phase 7 independent answer evaluation
  -> Phase 8 provisional reflection + candidate lesson
  -> Phase 9 independent candidate verification
  -> Phase 10 separately gated verified-lesson retention
```

### Phase 1 — Source ingestion ✅

Accepted properties include exact original UTF-8 byte preservation, SHA-256 content identity, deterministic/content-addressed source identity, immutable records, idempotent re-ingestion, fail-closed malformed/conflicting state, and `live_state_authorized=false`.

For an original UTF-8 upload, a normalized derivative cannot replace the exact uploaded bytes as the canonical artifact. This remains the blocker on XenBlocks PoW PR #141.

### Phase 2 — Structure detection ✅

See [`LEARNING_SYSTEM_STRUCTURE.md`](./LEARNING_SYSTEM_STRUCTURE.md). The accepted Markdown parser preserves source hierarchy, block structure, exact source locations/text, warnings/partial state, and content-addressed identities without inventing structure.

### Phase 3 — Structure-aware evidence chunking ✅

See [`LEARNING_SYSTEM_CHUNKING.md`](./LEARNING_SYSTEM_CHUNKING.md). Canonical source/structure state is revalidated before chunking. Chunks preserve provenance and exact source coverage and are derived evidence units, not source truth.

### Phase 4 — Indexing foundation ✅

See [`LEARNING_SYSTEM_INDEXING.md`](./LEARNING_SYSTEM_INDEXING.md). Deterministic lexical indexing is accepted. Embeddings remain behind an exact provider/model/version/dimension/request contract; the deterministic hash adapter proves interface mechanics only.

### Phase 5 — Retrieval + benchmark foundation ✅

See [`LEARNING_SYSTEM_RETRIEVAL.md`](./LEARNING_SYSTEM_RETRIEVAL.md). Retrieval revalidates canonical corpus/index state, preserves filters/provenance and separate lexical/vector channels, exposes explicit degraded/no-match states, and leaves contradictions visible.

### Phase 6 — Grounded answer + citation foundation ✅

See [`LEARNING_SYSTEM_GROUNDING.md`](./LEARNING_SYSTEM_GROUNDING.md). Evidence packets/citations are content-addressed and bound to exact retrieval/source/chunk state. Retrieved text is untrusted evidence data and cannot authorize tools, memory writes, policy changes, or execution.

### Phase 7 — Independent answer evaluation ✅

See [`LEARNING_SYSTEM_EVALUATION.md`](./LEARNING_SYSTEM_EVALUATION.md). Accepted evaluation reconstructs Phase 6 state, uses approved golden cases, separates retrieval failures from answer failures, and refuses to fabricate semantic/calibration signals that lack an accepted evaluator.

### Phase 8 — Provisional reflection + candidate lesson ✅

See [`LEARNING_SYSTEM_REFLECTION.md`](./LEARNING_SYSTEM_REFLECTION.md). Only canonical failed Phase 7 evaluations can create provisional reflection/candidate state. Generated material remains non-authorizing.

### Phase 9 — Independent candidate verification ✅

See [`LEARNING_SYSTEM_VERIFICATION.md`](./LEARNING_SYSTEM_VERIFICATION.md). Canonical Phase 8 state is revalidated; the exact verification plan drives fresh deterministic retest evaluation. Results are `verified_for_learning`, `rejected`, or `inconclusive`.

`verified_for_learning` is verification evidence only. It does not mean source truth, durable-memory promotion, or current live truth.

### Phase 10 — Verified lesson retention ⚠️ specification accepted; implementation blocked

See [`LEARNING_SYSTEM_RETENTION.md`](./LEARNING_SYSTEM_RETENTION.md).

Issue #133 / PR #134 accepted the provider-neutral/in-memory v1 retention specification. Draft implementation PR #136 remains unaccepted with five P1 blockers: deterministic procedural-body eligibility, actual source-contradiction evaluation, trusted source-scope completeness, evidence/decision-bound lifecycle transitions, and recoverable duplicate provenance.

No general `VerifiedLessonRecord` runtime capability should be described as accepted until those blockers are fixed, exact-head CI passes, independent review passes, and the PR merges.

## Blockchain Reasoning Pyramid relationship

The Pyramid is a separate source-mastery training/evaluation subsystem. It may generate evidence about Roberta's performance and curriculum-scoped learned concepts, but it cannot skip the Learning System authority gates.

Accepted learning bridge:

```text
Pyramid answer/grade
  -> weakness/remediation analysis
  -> deterministic learning handoff
  -> source-grounded reconstruction
  -> source-grounded targeted practice
  -> closed-book retention/transfer gates when required
  -> curriculum-scoped learned concept when exact Pyramid gates pass
```

That curriculum-scoped learned-concept mechanism is **not** Phase 10 general verified-lesson retention. It is restricted to the Pyramid answer path for matching curriculum/concept/subconcept and does not become HXMP, source truth, current live truth, CMIS/provider trust, governance authority, or execution authority.

Grader notes remain diagnostic-only. Expected/reference answers remain evaluation guidance. Practice questions remain remediation scaffolding. Source excerpts are used only in the explicitly source-grounded practice path and are not injected into canonical closed-book exams.

## Source-specific mastery plans

The Pyramid now uses a frozen source-specific plan where present. See [`ROBERTA_SOURCE_MASTERY_PLAN.md`](./ROBERTA_SOURCE_MASTERY_PLAN.md) and [`PYRAMID_CURRICULUM.md`](./PYRAMID_CURRICULUM.md).

A source mastery plan binds:

- exact curriculum and source identity;
- sequential source-stage ordinals;
- unique mappings to the reusable 20-capability Pyramid taxonomy;
- source chapters/rationale per required stage;
- explicit excluded capabilities;
- 300 canonical questions per required stage;
- complete-source coverage assertion;
- deterministic plan hash;
- source-capstone requirement.

The plan cannot silently change after a run is bound. Historical fixed-level results are mapped, not rewritten.

For *Mastering Blockchain, Fourth Edition*, the accepted deterministic plan has 14 required stages mapped to capabilities `1,2,3,4,5,6,7,8,9,10,11,13,14,17`, with capabilities `12,15,16,18,19,20` explicitly excluded and a final source capstone required.

Accepted curriculum-bank construction currently reaches Stage 6 / Tokenomics. Bank construction is not evidence that the source stage has been passed.

## MB4E provenance and reconstruction state

The legacy Level 1 provenance migration in #179 is accepted. It preserves historical exercise semantics/checkpoints while adding canonical source binding and explicit PDF-page coordinate basis.

Accepted source-grounded Pyramid provenance hardening additionally includes:

- basis-aware `pdf_pages` / `book_pages` locator handling;
- exact source/transcript hash binding;
- verified PDF-page -> transcript-line alignment for the Level 1 remediation windows;
- provenance scope resolution before retrieval/ranking;
- strict full containment so selected chunks/evidence anchors cannot extend outside the declared PDF-page range.

These are Pyramid reconstruction/remediation safeguards. They do not convert the book into current blockchain truth.

## Accepted static source registry

See [`learning_sources/README.md`](./learning_sources/README.md).

Accepted on `main`:

- X1 Blockchain Whitepaper v1.0;
- XDEX documentation snapshot;
- XEN Litepaper v1.7;
- XEN Torrent / XENFT Litepaper v0.3;
- XONE ERC20 Token v4;
- *Mastering Blockchain, Fourth Edition* under an external exact-transcript integrity contract;
- Solana whitepaper v0.8.13.

The full copyrighted *Mastering Blockchain* transcript is not republished. Runtime source-grounded operations must satisfy the pinned external transcript integrity contract.

XenBlocks PoW documentation remains pending under PR #141 until its exact-byte Phase 1 blocker is resolved and the PR merges.

## Source truth vs generated material

```text
approved source artifact/chunk -> evidence data
model answer                   -> generated answer
Pyramid expected answer        -> evaluation guidance
Pyramid grader note            -> diagnostic material
Pyramid practice question      -> remediation scaffolding
Pyramid learned concept        -> curriculum-scoped answer aid after exact practice/retention gates
Phase 7 result                 -> evaluation state
Phase 8 reflection/lesson      -> generated provisional material
Phase 9 verification result    -> verification evidence
Phase 10 retained lesson       -> only after every accepted retention gate
```

Generated material never retroactively becomes source evidence merely because it was useful, graded highly, or verified under a narrower contract.

## Storage boundaries

```text
Phase 1 SourceStore              -> source artifacts/provenance
LangGraph checkpoint             -> workflow/thread state
Pyramid SQLite ledger            -> training/source-stage performance history
Pyramid learned-concept store    -> curriculum-scoped static training concepts only
Phase 10 v1 retention store      -> proposed provider-neutral/in-memory general retention state
HXMP                              -> separate durable-memory system with wallet-bound write semantics
CMIS                              -> current deterministic blockchain/market evidence
```

## Non-goals / authority denial

The Learning System and Pyramid do not by themselves authorize:

- current price/liquidity/supply/wallet/risk claims;
- source approval changes from generated text;
- CMIS/provider trust changes;
- protected governance mutation;
- credential/tool-permission expansion;
- wallet signing;
- transaction preparation/broadcasting;
- custody/trading/bridge value transfer;
- Controlled Execution.

Controlled Execution remains locked.
