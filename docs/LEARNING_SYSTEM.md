# Roberta Learning System

Last reconciled: 2026-08-23 (America/New_York)

Status: **Phases 1-9 accepted; Phase 10 retention specification accepted but implementation still blocked/unaccepted.**

## Purpose

The Roberta Learning System gives Roberta an evidence-grounded path from approved static sources through retrieval, evaluation, reflection, verification, and eventually separately gated retention.

It is not a replacement for CMIS live truth and it is not an automatic self-training or self-authorizing memory path.

## Canonical authority boundary

The live-data hierarchy remains:

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Learning-system source records are static source knowledge. They are not authoritative for changing market, blockchain, wallet, validator, provider-health, software-version, fee, supply, liquidity, price, or risk state.

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

Accepted contract:

- exact original UTF-8 bytes are preserved;
- `content_hash` is SHA-256 over those exact bytes;
- source identity is deterministic/content-addressed;
- identical re-ingestion is idempotent;
- changed content creates a new immutable source record;
- malformed/conflicting source state fails closed;
- metadata is canonical JSON-compatible state;
- `InMemorySourceStore` is a deterministic development/test adapter, not a production trust shortcut;
- static source records never authorize live state.

A `SourceRecord` preserves:

```text
source_id
origin
title
version
content_hash
authority_class
approval_status
ingested_at
parser_version
artifact_ref
status
metadata
```

Accepted authority classes:

```text
primary
secondary
internal
unknown
```

Accepted approval states:

```text
approved
pending_review
rejected
quarantined
```

Accepted source statuses:

```text
approved
pending_review
rejected
quarantined
superseded
```

For a plain UTF-8 source upload, normalized/derived text must not replace the exact uploaded bytes as the canonical Phase 1 artifact. This exact-byte rule is why XenBlocks PoW onboarding PR #141 remains blocked until it preserves the original CRLF upload as the canonical artifact.

### Phase 2 — Structure detection ✅

See [`LEARNING_SYSTEM_STRUCTURE.md`](./LEARNING_SYSTEM_STRUCTURE.md).

The accepted Markdown parser revalidates the Phase 1 artifact and deterministically preserves headings, hierarchy, blocks, structural paths, exact source locations/text, and explicit partial/warning states without inventing structure.

### Phase 3 — Structure-aware evidence chunking ✅

See [`LEARNING_SYSTEM_CHUNKING.md`](./LEARNING_SYSTEM_CHUNKING.md).

Canonical source/structure state is recomputed before chunking. Chunks preserve exact provenance and source coverage, avoid silent truncation, and remain content-addressed derived evidence units rather than source truth.

### Phase 4 — Indexing foundation ✅

See [`LEARNING_SYSTEM_INDEXING.md`](./LEARNING_SYSTEM_INDEXING.md).

Deterministic lexical indexing is accepted. Embeddings remain behind an exact provider/model/version/dimension/request contract. The deterministic hash embedding adapter proves interface mechanics only and does not establish semantic retrieval quality.

### Phase 5 — Retrieval + benchmark foundation ✅

See [`LEARNING_SYSTEM_RETRIEVAL.md`](./LEARNING_SYSTEM_RETRIEVAL.md).

Retrieval revalidates canonical corpus/index state, preserves filters/provenance and separate lexical/vector channels, exposes explicit degraded/no-match states, and keeps contradictory evidence visible rather than silently reconciling it.

### Phase 6 — Grounded answer + citation foundation ✅

See [`LEARNING_SYSTEM_GROUNDING.md`](./LEARNING_SYSTEM_GROUNDING.md).

Evidence packets and citations are content-addressed and bound to exact retrieval/source/chunk state. Retrieved text is serialized as untrusted evidence data and cannot authorize tools, memory writes, policy changes, or execution.

Structural citation validity is not automatically semantic entailment.

### Phase 7 — Independent answer evaluation ✅

See [`LEARNING_SYSTEM_EVALUATION.md`](./LEARNING_SYSTEM_EVALUATION.md).

Accepted evaluation uses canonical Phase 6 reconstruction plus explicit approved golden cases. Retrieval failures remain distinct from reasoning/answer failures. Unsupported semantic/calibration capabilities stay `not_evaluated`/`not_applicable` rather than being fabricated.

### Phase 8 — Provisional reflection + candidate lesson ✅

See [`LEARNING_SYSTEM_REFLECTION.md`](./LEARNING_SYSTEM_REFLECTION.md).

Only canonical failed Phase 7 evaluations can produce Phase 8 reflection/candidate state. Generated reflection/lesson/rationale material remains explicitly provisional, content-addressed, lifecycle-bound, and non-authorizing.

### Phase 9 — Independent candidate verification ✅

See [`LEARNING_SYSTEM_VERIFICATION.md`](./LEARNING_SYSTEM_VERIFICATION.md).

Canonical Phase 8 state is revalidated before verification. The exact verification plan drives fresh deterministic retest evaluation. Results are:

```text
verified_for_learning
rejected
inconclusive
```

`verified_for_learning` does not mean retained, source-truth, or current live truth.

### Phase 10 — Verified lesson retention ⚠️ Spec accepted; implementation blocked

See [`LEARNING_SYSTEM_RETENTION.md`](./LEARNING_SYSTEM_RETENTION.md).

Issue #133 / PR #134 accepted the v1 retention specification. The accepted first slice is provider-neutral/in-memory and explicitly excludes HXMP writes.

Mandatory gates include:

- exact Phase 8/9 revalidation;
- deterministic procedural-lesson eligibility;
- complete trusted source/verified-lesson contradiction scope;
- exact duplicate handling without lost provenance;
- evidence-derived categorical confidence basis;
- exact human retention approval through the existing approval graph;
- authenticated human principal binding;
- one-time approval-binding consumption;
- content-addressed retention/lesson identities;
- immutable evidence/decision-bound lifecycle transitions.

Draft PR #136 remains unaccepted because five P1 review blockers are unresolved:

1. procedural eligibility is not deterministically proven from the lesson body;
2. source contradictions are not actually evaluated by an accepted deterministic capability;
3. canonical source-scope completeness is not proven through trusted enumeration;
4. lifecycle transitions are not bound to exact accepted evidence/decision identities;
5. duplicate outcomes do not persist recoverable Phase 8/9/proposal provenance.

No `VerifiedLessonRecord` capability should be described as accepted runtime behavior until these blockers are fixed, exact-head CI passes, independent review passes, and the PR merges.

## Blockchain Reasoning Pyramid relationship

The Pyramid is a separate training/evaluation subsystem. It may produce evidence about Roberta's performance and deterministic remediation handoffs, but it cannot skip Learning System gates.

Accepted Pyramid sequence:

```text
Pyramid answer/grade
  -> weakness/remediation analysis
  -> content-addressed learning handoff
  -> source-grounded reconstruction
  -> later separately accepted Learning System evaluation/reflection/verification/retention path
```

Accepted bridge milestones include:

- #169 deterministic Pyramid learning handoffs;
- #173 historical regrade without regenerating Roberta answers;
- #177 source-grounded reconstruction through the accepted Phase 1-6 source/retrieval/evidence-packet path.

Pyramid grader notes are diagnostic-only. Expected/reference answers are evaluation guidance, not source evidence. Practice questions are remediation scaffolding, not trusted lessons.

## Accepted static source registry

The canonical human-readable registry is [`learning_sources/README.md`](./learning_sources/README.md).

Accepted source onboarding on `main` includes:

- X1 Blockchain Whitepaper v1.0;
- XDEX documentation snapshot;
- XEN Litepaper v1.7;
- XEN Torrent / XENFT Litepaper v0.3;
- XONE ERC20 Token v4;
- *Mastering Blockchain, Fourth Edition* as an external exact-transcript integrity contract;
- Solana whitepaper v0.8.13.

The full copyrighted *Mastering Blockchain* transcript is not republished by the repository. Runtime use must satisfy the pinned exact external transcript integrity contract.

XenBlocks PoW documentation remains pending under PR #141 and must not be treated as accepted until its Phase 1 exact-byte blocker is resolved and the PR merges.

## MB4E curriculum/provenance state

The accepted Pyramid MB4E training path includes a 50-question Level 1 smoke curriculum and later canonical Level 1 training/remediation artifacts.

PR #179 proposes a migration seam for the legacy MB4E Level 1 curriculum provenance. It is not accepted yet. The migration intends to:

- preserve historical curriculum/exercise semantic identity;
- add canonical source key `mastering_blockchain_4e_2023`;
- preserve explicit PDF-page basis rather than relabel PDF coordinates as printed book pages;
- leave historical checkpoints unchanged;
- allow provenance-bound remediation artifacts to be regenerated later from the same accepted historical/regraded checkpoints.

#179 currently has passing CI but remains blocked by two unresolved P2 findings: core reconstruction must support migrated PDF-page locators without CLI-only setup, and nested migration outputs must fail closed to avoid recursive staging/copy behavior.

## Source truth vs generated material

The following distinction is mandatory:

```text
approved source artifact/chunk -> evidence data
model answer                  -> generated answer
Phase 7 result                -> evaluation state
Phase 8 reflection/lesson     -> generated provisional material
Phase 9 verification result   -> verification evidence
Pyramid grader note           -> diagnostic material
Pyramid practice question     -> remediation scaffolding
Phase 10 retained lesson      -> only after every accepted retention gate
```

Generated material never retroactively becomes source evidence merely because it was useful, graded highly, or verified under a narrower evaluation contract.

## Storage boundaries

```text
Phase 1 SourceStore           -> source artifacts/provenance
LangGraph checkpoint          -> current workflow/thread state
Pyramid SQLite ledger         -> training performance/history
Phase 10 v1 retention store   -> proposed provider-neutral/in-memory retention state only
HXMP                           -> separate durable-memory system with wallet-bound write semantics
```

Phase 10 v1 must not import, prepare, simulate-as-execution, approve, sign, broadcast, or exercise HXMP writes. Any verified-lesson-to-HXMP persistence requires a separate accepted roadmap/spec/implementation gate.

## Human approval boundary

Phase 10 retention may use the existing LangGraph human-approval runtime only for the exact retention proposal/binding/scope/principal accepted by the retention specification.

Retention approval is not:

- wallet signing authority;
- HXMP write authority;
- protected-governance authority;
- source-approval authority;
- reusable future authorization.

## Non-goals / authority denial

The Learning System does not by itself authorize:

- current price/liquidity/supply/wallet/risk claims;
- source approval changes from generated text;
- CMIS/provider trust changes;
- protected governance mutation;
- credentials/tool-permission expansion;
- wallet signing;
- transaction preparation/broadcasting;
- custody/trading/bridge value transfer;
- Controlled Execution.

Controlled Execution remains locked.

## Engineering gate

Every new Learning System capability follows [`ENGINEERING_WORKFLOW.md`](./ENGINEERING_WORKFLOW.md): roadmap/issue ownership, contract-before-code when semantics change, behavior-first deterministic tests, exact-head/full applicable CI, independent Spec/Code-Architecture/Authority-Safety review, and post-merge source-of-truth reconciliation.

Green CI alone is not acceptance.
