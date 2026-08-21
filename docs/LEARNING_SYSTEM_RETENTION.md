# Learning System Phase 10 — Verified Lesson Retention Foundation

Status: **proposed roadmap / implementation contract for Issue #133**. No runtime implementation is authorized until this gate is accepted.

## Purpose

Phase 10 starts the `RETAIN` step of the Roberta Learning System after Phase 9 verification.

A Phase 9 `CandidateVerificationResult(status="verified_for_learning")` is necessary evidence for retention, but it is **not itself durable-memory promotion authority**. Phase 10 defines the additional retention/curation boundary required before a generated candidate lesson may become a trusted reusable verified lesson.

The Learning System v1.1 requires the durable-learning path to preserve:

```text
FAILURE -> DIAGNOSIS -> REFLECTION -> CANDIDATE LESSON
  -> EVIDENCE CHECK -> CONTRADICTION CHECK -> DEDUPLICATION
    -> CONFIDENCE ASSESSMENT -> APPROVAL -> VERIFIED LESSON
```

## Architecture boundary

```text
canonical Phase 8 LearningCandidateBundle
  + canonical Phase 9 CandidateVerificationResult
        ↓ exact Phase 9 reconstruction / validation
verified_for_learning candidate
        ↓ retention gates
lesson type + scope eligibility
contradiction check
exact-duplicate handling
confidence basis
explicit retention approval state
        ↓
RetentionDecision
        ↓ only when every mandatory gate passes
VerifiedLessonRecord
```

Phase 10 must not create a direct candidate/reflection-to-memory shortcut.

## Proposed first contracts

The implementation issue may refine names before code, but the public seam must remain narrow and typed. The proposed v1 records are:

```text
retention_contract = verified-lesson-retention/v1
verified_lesson_contract = verified-lesson/v1
retention_version = 1.0.0
```

A retention decision is distinct from the verified lesson itself so blocked, rejected, duplicate, or inconclusive outcomes remain auditable without creating trusted lesson state.

## Canonical prerequisites

Before any retention gate runs, Phase 10 must:

1. require the exact Phase 8 bundle and Phase 9 verification inputs needed to reconstruct the supplied verification result;
2. run the accepted Phase 9 validator rather than trusting a supplied `CandidateVerificationResult` by identity alone;
3. require exact equality with the reconstructed Phase 9 result;
4. require `status == "verified_for_learning"`;
5. reject or block `rejected` / `inconclusive` verification results;
6. preserve the exact candidate, candidate-state, reflection, verification-plan, original/retest evaluation, golden-case, packet/result/retrieval, per-check, and Phase 9 verification identities required for audit.

## Lesson type and scope

A retained lesson is trusted only within a recorded type and scope.

V1 must define an explicit allowlist rather than treating arbitrary generated lesson text as semantic truth. Unsupported or ambiguous lesson types/scopes fail closed.

The first implementation should prefer a narrow **procedural-learning** boundary: reusable methods, workflows, or operating practices demonstrated by accepted evaluation/retest evidence. Factual source claims, current market/blockchain facts, protected policy, permissions, and execution instructions are not silently promoted into procedural knowledge.

Generated candidate/reflection text remains generated material. Retention may preserve it as the proposed lesson body, but does not retroactively convert it into source evidence.

## Contradiction gate

The Learning System specification requires contradiction checking before a lesson becomes durable.

Phase 10 must therefore expose an explicit contradiction outcome such as:

```text
clear | conflict | inconclusive
```

A lesson cannot be retained when the required contradiction evidence or accepted deterministic capability is unavailable. Missing capability/evidence becomes `inconclusive`, never an implicit clear state.

V1 must not use a free-form LLM opinion as deterministic proof that no contradiction exists.

## Duplicate handling

The Learning System specification requires duplicate/near-duplicate lessons to be handled with provenance preserved.

The first deterministic slice must support **exact duplicate** detection over a canonical lesson type/scope/body identity and prevent creation of parallel trusted duplicates that lose provenance.

Near-duplicate semantic merging remains out of scope until a separately accepted deterministic or independently evaluated merge capability exists. It must not be guessed from model similarity alone.

## Confidence basis

A verified lesson must preserve the basis for its confidence without inventing a calibrated probability.

V1 should record bounded categorical or evidence-derived confidence state only when supported by the accepted verification/retest evidence. If no accepted calibrated confidence measure exists, preserve that limitation explicitly rather than manufacturing a score.

## Retention approval

Phase 9 verification and Phase 10 deterministic gates do not self-authorize protected governance or permissions.

The retention contract must require an explicit retention approval state before a lesson receives trusted durable status. The approval mechanism must be typed, content-bound, auditable, and unable to authorize anything outside the exact retention proposal.

The implementation issue may choose the narrowest safe first approval seam. It must not treat model-generated approval text, a boolean-like free-form value, or Phase 9 `verified_for_learning` as equivalent to retention approval.

## RetentionDecision

A deterministic retention decision should preserve at minimum:

- retention contract/version;
- exact Phase 8/9 provenance identities;
- canonical proposed lesson type/scope/body identity;
- contradiction result and evidence identity references;
- duplicate result and any existing lesson identity;
- confidence basis/state;
- retention approval state/binding;
- status such as `retained`, `rejected`, `duplicate`, or `inconclusive`;
- producer identity/version;
- explicit authority boundaries.

The decision must be content-addressed and tamper-sensitive.

## VerifiedLessonRecord

A `VerifiedLessonRecord` may be created only when every mandatory gate passes.

It must preserve at minimum:

- deterministic lesson id/content hash;
- lesson type and exact scope;
- lesson body with generated/source distinction preserved;
- exact Phase 8/9 provenance and evaluation/verification basis;
- contradiction/dedup/confidence/approval basis;
- version/lifecycle state;
- `created_at` or equivalent deterministic/auditable record time supplied by the accepted storage boundary;
- supersession/revocation linkage;
- authority flags that prevent live-state, source-truth, governance, CMIS/provider-trust, or execution escalation.

A verified lesson is trusted only within its recorded scope and lifecycle state. It is not automatically source truth.

## Lifecycle

Phase 10 must make later invalidation representable from the start.

At minimum, verified lessons need a lifecycle that supports an active record plus explicit supersession/revocation linkage. A later lesson must never silently overwrite or erase the evidence/history that justified the prior state.

The exact v1 transition API belongs to the implementation contract, but immutable history is required.

## Storage boundary

Persistent memory/knowledge infrastructure remains an external system of record.

Phase 10 must use a narrow typed store/interface. It must not grant the LLM, Roberta graph, or a Memory Curator module unrestricted database/HXMP access.

The first implementation may prove the contract with an in-memory deterministic store. An external HXMP/durable-store adapter may be added only if the same PR/issue explicitly proves typed writes, provenance, versioning, authorization, exact readback/validation, and supersession/revocation behavior. If that cannot be proved safely, external persistence is deferred rather than weakening the retention gate.

## Authority boundary

Phase 10 does not change the authority hierarchy for freshness-sensitive facts:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

A retained lesson cannot become current authority for prices, liquidity, volume, holders, supply, tokenomics, wallet state, market risk, provider health, or other freshness-sensitive market/blockchain facts.

Phase 10 must not authorize:

- source approval or source-truth mutation;
- protected policy/governance mutation;
- CMIS/provider trust changes;
- new tool permissions or credentials;
- wallet authority;
- transaction approval;
- transaction preparation/signing/broadcasting/custody/trading;
- Controlled Execution.

Controlled Execution remains locked.

## Required first-slice tests

The implementation must prove at minimum:

1. tampered or non-canonical Phase 9 verification state fails before retention gates run;
2. only `verified_for_learning` is retention-eligible;
3. unsupported lesson type/scope fails closed;
4. missing contradiction capability/evidence cannot become success;
5. explicit contradiction blocks retention;
6. exact duplicate detection preserves provenance and avoids a second trusted lesson;
7. missing confidence capability does not fabricate a numeric score;
8. missing/invalid retention approval prevents trusted durable status;
9. successful retention preserves exact Phase 8/9 evaluation/verification provenance;
10. retained lesson identity is deterministic/content-addressed and tamper-sensitive;
11. supersession/revocation lineage is immutable and auditable;
12. no retained lesson gains source-truth, live-state, governance, CMIS/provider-trust, wallet, or execution authority;
13. freshness-sensitive market facts remain subordinate to fresh accepted CMIS/provider evidence;
14. the full deterministic Roberta suite remains green.

## Explicit non-goals

Phase 10 does not add:

- automatic retention of every Phase 9 success;
- direct reflection/candidate-to-HXMP writes;
- semantic near-duplicate merge by model intuition;
- broad semantic knowledge extraction from generated lessons;
- source-store writes from generated lesson text;
- source approval changes;
- autonomous protected-policy/governance mutation;
- CMIS/provider truth or trust changes;
- adaptive curriculum/skill scheduling;
- knowledge graph/concept expansion;
- production reranking/fine-tuning;
- transaction preparation/signing/broadcasting/custody/trading;
- Controlled Execution.

## Gate acceptance

If this roadmap/spec PR is accepted, Issue #133 becomes the active Learning System implementation gate. Implementation must still follow behavior-first tests, exact-head deterministic CI, and the independent **Spec Fidelity / Code-Architecture / Authority-Safety** review gate before merge.