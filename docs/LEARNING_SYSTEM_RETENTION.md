# Roberta Learning System — Phase 10 Verified Lesson Retention

Last reconciled: 2026-08-26 (America/New_York)

Status: **accepted contract and hardened implementation on `main`.** The historical draft PR #136 remains open but is no longer the implementation source of truth.

## Purpose

Phase 10 is the narrow boundary that permits an exact independently verified Learning System lesson to become a retained lesson without converting model output, repetition, source text, or training success into self-authorizing truth.

The retention layer is intentionally smaller than a general memory system. It retains only the exact lesson material allowed by the accepted Phase 9 -> Phase 10 contract and preserves complete verification, source, contradiction, and human-approval lineage.

## Authority boundary

Phase 10 retention does **not** authorize:

```text
source truth
current/live blockchain truth
CMIS/provider trust
operational trust
prompt/tool/policy mutation
governance mutation
HXMP writes
wallet authority
transaction construction/signing/broadcasting
trading/custody/bridge transfer
Controlled Execution
```

Fresh accepted Scout -> CMIS -> Provider evidence remains authoritative for freshness-sensitive facts regardless of any retained lesson.

## Eligible input

Retention starts from one exact accepted Phase 9 verification result. A retention attempt fails closed unless the verification result:

- uses the accepted Phase 9 verification contract/version;
- is structurally valid and fully bound to its candidate/evaluation/source lineage;
- has status `verified_for_learning`;
- identifies a procedural lesson that is eligible for narrow learning retention;
- has not been altered, partially reconstructed, or detached from its original verification evidence.

Model repetition, confidence, exam success, grader notes, candidate lessons, or source inclusion do not substitute for Phase 9 eligibility.

## Retention preparation

Before human approval can be requested, Phase 10 creates a deterministic retention preparation bound to the exact verified lesson.

The preparation includes the exact lesson scope, provenance, verification identity, contradiction state, and any information required to prove that approval later applies to the same prepared retention object.

A preparation does not itself retain anything.

## Contradiction gates

Phase 10 requires complete contradiction evaluation before retention.

The accepted implementation checks both:

1. the applicable approved/source evidence needed to establish whether the lesson conflicts with its source lineage; and
2. the active retained-lesson set needed to detect conflicts or exact duplicates with already retained lessons.

The contradiction snapshot is complete and deterministic for the retention decision. Missing or incomplete contradiction evidence blocks retention rather than being interpreted as no conflict.

Unresolved contradiction blockers fail closed.

## Duplicate rule

An exact active duplicate is not silently retained again.

Duplicate handling is deterministic and must preserve the identity of the already-active retained lesson. A repeated model output or repeated human approval cannot create a second independent authority record for the same lesson.

## Human approval

Retention requires explicit human approval of the exact prepared retention object.

Approval is:

- specific to one preparation/lesson;
- non-reusable for altered material;
- bound into the retained lesson lineage;
- invalid if the approved material, source/verification identity, or applicable retention state changes before retention.

Human approval authorizes only the narrow retention decision. It does not authorize operational trust, HXMP promotion, wallet activity, or execution.

## Retained lesson record

An accepted retained lesson preserves at least the exact identities needed to reconstruct its trust lineage, including:

```text
lesson_id
lesson_hash
lesson scope / procedural content
source ids
Phase 9 verification id
retention preparation id
contradiction snapshot id
human approval id
lifecycle state
```

The record is deterministic and immutable as a historical decision object.

## Lifecycle state

Retained lessons have explicit lifecycle state rather than being silently overwritten.

Accepted states include:

```text
active
superseded
revoked
```

A lifecycle transition produces new state/audit material while preserving the historical lesson and prior state lineage.

Only an exact active retained lesson is eligible for the separate `verified_learned_knowledge` classification boundary.

## Storage contract

The accepted core Phase 10 implementation is provider-neutral and uses an in-memory retained-lesson store.

This is deliberate. Adding HXMP, database, vector-store, or other durable persistence is not a storage-only refactor if it changes authority, retrieval, conflict, or lifecycle semantics. Any durable/provider-backed general retained-lesson store requires a separate accepted persistence contract.

Autonomous-training job files and Pyramid curriculum-scoped learned-concept stores are separate mechanisms and do not silently become the Phase 10 general retention store.

## Relationship to Pyramid learned concepts

Pyramid learned concepts and Phase 10 retained lessons are distinct:

- Pyramid learned concepts are curriculum-scoped and require Pyramid-specific source-grounded practice, closed-book retention/transfer gates, and matching source references.
- Phase 10 retained lessons are general Learning System procedural lessons admitted only through Phase 9 verification, contradiction checks, and exact human approval.

Neither mechanism is general operational memory or live-state authority.

## Relationship to knowledge classification

The accepted Learning Plane classification boundary may classify one exact active retained lesson as:

```text
verified_learned_knowledge
```

The classification preserves the retained lesson hash, lifecycle state, retention decision/preparation, Phase 9 verification, source IDs, contradiction snapshot, and approval ID.

Every accepted classification has:

```text
operational_trust_authorized = false
source_truth_authorized = false
live_state_authorized = false
cmis_provider_trust_authorized = false
governance_mutation_authorized = false
wallet_authorized = false
execution_authorized = false
```

The core Learning Plane exposes no operational-trust promotion wrapper. Attempts to authorize operational trust fail closed until a separately accepted wrapper exists.

## Relationship to autonomous source mastery

Merged PR #228 automates source intake, curriculum generation, canonical exams, remediation, curriculum-scoped retention/transfer, and the final source capstone.

That controller does not bypass Phase 10. Its Pyramid learned-concept mechanism remains curriculum-scoped and independently gated. It cannot write arbitrary model conclusions into the Phase 10 retained-lesson store and cannot convert a training result into operational trust.

The autonomous controller's durable `state.json`, events, checkpoints, remediation evidence, and capstone results are workflow/audit state, not retained operational truth.

## Freshness and source conflict

A retained lesson can be useful only inside its accepted procedural/static scope.

If a user question depends on current chain or market state, Roberta must obtain fresh evidence through the accepted Scout -> CMIS -> Provider path. A retained lesson cannot override fresh provider evidence, resolve missing live evidence by guessing, or turn an old source statement into a current fact.

If later accepted learning evidence contradicts an active retained lesson, the conflict must be represented through the retention/lifecycle process rather than silently modifying the old record.

## Failure behavior

Retention fails closed when, among other conditions:

- the Phase 9 verification is invalid or not `verified_for_learning`;
- the lesson scope is ineligible;
- provenance or verification lineage is incomplete;
- contradiction coverage is incomplete;
- an unresolved contradiction exists;
- exact duplicate handling cannot be determined safely;
- approval is missing, malformed, stale, or bound to different material;
- lifecycle state is inconsistent;
- retained-lesson material cannot be canonicalized deterministically.

Failure to retain does not erase the Phase 9 verification result; it simply means the candidate did not cross the retention boundary.

## Current implementation status

Accepted on `main`:

- deterministic Phase 10 retention contracts and validation;
- exact eligible Phase 9 input gate;
- source and active-lesson contradiction snapshots;
- duplicate handling;
- exact human approval binding;
- provider-neutral in-memory retained-lesson store;
- active/superseded/revoked lifecycle state;
- regression coverage for retention integrity and failure modes;
- fail-closed `verified_learned_knowledge` classification in the separate promotion boundary.

Historical note: PR #136 originally proposed Phase 10 and accumulated blocker feedback. The hardened implementation was subsequently integrated to `main` through a separate merge path. Therefore PR #136's open/draft state must not be cited as evidence that Phase 10 remains unimplemented.

## Future work requiring separate acceptance

Not authorized by Phase 10 completion:

- HXMP-backed general lesson persistence;
- arbitrary automatic retention without exact human approval;
- operational-trust promotion;
- current-state fact retention as authority;
- prompt/tool/policy self-modification;
- wallet or execution authority;
- a generalized background retention scheduler that changes retention semantics.

## Core rule

**Retention is a narrow, provenance-bound, human-approved learning decision. A retained lesson may become verified learned knowledge, but it never becomes operational trust, current truth, or execution authority by implication.**
