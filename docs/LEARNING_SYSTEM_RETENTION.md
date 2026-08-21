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
complete canonical contradiction snapshot
exact-duplicate handling
confidence basis
exact human retention approval
        ↓
RetentionDecision
        ↓ only when every mandatory gate passes
VerifiedLessonRecord
        ↓
provider-neutral Phase 10 retention store only
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

The first implementation is restricted to a narrow **procedural-learning** boundary: reusable methods, workflows, or operating practices demonstrated by accepted evaluation/retest evidence. Factual source claims, current market/blockchain facts, protected policy, permissions, credentials, and execution instructions are not eligible lesson types in this slice.

Every proposed procedural lesson must declare a canonical scope that includes the applicable domain/task boundary and exact approved source/corpus identities on which the lesson depends. Scope widening changes the retention proposal identity and requires a new contradiction snapshot and new human approval.

Generated candidate/reflection text remains generated material. Retention may preserve it as the proposed lesson body, but does not retroactively convert it into source evidence.

## Contradiction gate

The Learning System specification requires candidate lessons to be checked against existing verified lessons and source evidence before durable retention.

A caller-supplied list of convenient evidence is therefore **not** an accepted contradiction basis. Phase 10 v1 requires a provider-built, content-addressed `RetentionContradictionSnapshot` whose completeness is validated before contradiction scoring.

### Mandatory contradiction scope

For the proposed lesson's exact type/scope, the snapshot must contain both:

1. **Verified-lesson scope** — every active `VerifiedLessonRecord` enumerated by the canonical Phase 10 retention store whose type/scope can apply to or overlap the proposed lesson. The store, not the caller, performs the enumeration. The snapshot records the complete active-record count, ordered lesson ids/content hashes, lifecycle-state ids, and a deterministic store-snapshot id.
2. **Approved-source scope** — every canonical approved source/evidence unit in the exact declared source/corpus scope for the lesson, including the exact versions required by that scope and any accepted superseding source version that the source lifecycle says must replace an older active version. The trusted source/index boundary, not the caller, performs the enumeration. The snapshot records the complete source/evidence count, ordered source/chunk ids and content hashes, approval/lifecycle state, and a deterministic source-snapshot id.

The contradiction-snapshot id binds the proposed lesson identity, lesson type/scope, store-snapshot id, source-snapshot id, ordered member identities/hashes, counts, and the accepted contradiction-snapshot contract/version.

A `clear` contradiction result is valid only if the implementation proves that both mandatory scopes were completely enumerated from their trusted interfaces and the supplied snapshot exactly reconstructs. Missing store/source capability, failed enumeration, count/hash mismatch, caller-selected subsets, lifecycle ambiguity, stale/non-canonical snapshot state, or unvalidated source/lesson records produce `inconclusive` or fail closed; they can never become `clear`.

The first implementation should remain intentionally narrow enough that complete enumeration is deterministic and testable. If the repository cannot prove complete approved-source enumeration for a proposed lesson scope, that lesson is not retainable in v1.

The result remains explicit:

```text
clear | conflict | inconclusive
```

V1 must not use a free-form LLM opinion as deterministic proof that no contradiction exists.

## Duplicate handling

The Learning System specification requires duplicate/near-duplicate lessons to be handled with provenance preserved.

The first deterministic slice must support **exact duplicate** detection over a canonical lesson type/scope/body identity and prevent creation of parallel trusted duplicates that lose provenance. Exact-duplicate detection uses the same complete canonical active-lesson store snapshot required by the contradiction gate; callers cannot hide an existing duplicate by supplying a subset.

Near-duplicate semantic merging remains out of scope until a separately accepted deterministic or independently evaluated merge capability exists. It must not be guessed from model similarity alone.

## Confidence basis

A verified lesson must preserve the basis for its confidence without inventing a calibrated probability.

V1 may record only bounded categorical or evidence-derived confidence state supported by accepted verification/retest evidence. If no accepted calibrated confidence measure exists, the record must say so explicitly and must not manufacture a numeric score.

## Retention approval authority

Phase 9 Learning verification and Phase 10 deterministic checks do not self-authorize retention. **The only approval authority accepted by Phase 10 v1 is an explicit human reviewer acting through Roberta's existing LangGraph human-approval boundary.** Roberta, an LLM, a sub-agent, a tool, retrieved text, a candidate lesson, a Phase 9 verifier result, or a caller-constructed approval object cannot grant retention approval.

Phase 10 must construct a dedicated `ApprovalRequest` for the exact retention proposal and use the existing approval runtime described in `HUMAN_APPROVAL.md`. The request must use:

```text
action_type = retain_verified_lesson
scope = exact lesson type + exact lesson scope + exact retention-contract version
proposal = exact canonical retention proposal
```

The canonical retention proposal must include at minimum the proposed lesson identity/body hash, type/scope, exact Phase 8/9 provenance identities, contradiction-snapshot id/result, duplicate result, confidence basis, and all authority-denial fields. The existing proposal and binding hashes therefore change if any retention-relevant input changes.

### Issuer identity and trusted origin

The accepted approval artifact must originate from the existing LangGraph interrupt/resume workflow for the exact paused `ApprovalRequest`. Its authority is `human_review/v1`, and it must preserve the exact approval request id, proposal SHA-256, binding SHA-256, approval thread id, and the application-authenticated human principal identifier associated with the resume event.

The human principal identifier is trusted application/session metadata. It must not be accepted from candidate text, source text, model output, or an arbitrary resume-payload field. If the deployment cannot supply an authenticated human principal for the approval event, retention remains unapproved in Phase 10 v1.

### Validation and replay semantics

A retention decision may consume only `ApprovalOutcome(status="approved")` after revalidating:

- the exact paused request id;
- `action_type == "retain_verified_lesson"`;
- the exact proposal SHA-256;
- the exact binding SHA-256;
- the exact declared lesson type/scope;
- the exact retention contract/version;
- the authenticated human principal identity bound by the trusted application/session layer;
- that the approval thread completed with an explicit `approve` decision;
- that the exact approval binding has not already been consumed by another retention decision.

Booleans, yes-like strings, generated approval prose, free-form model text, or caller-reconstructed approval objects do not count as approval. Editing any proposal input creates a new proposal/binding and requires a fresh human review. Completed approval threads cannot be reused for a different request, and Phase 10 must record one-time consumption of the exact approval binding in the provider-neutral retention store so replay cannot create another trusted lesson or changed retention decision.

This approval authorizes only the exact Phase 10 retention proposal. It is not wallet authority, signing authority, HXMP write approval, protected-governance authority, or a reusable future authorization.

## RetentionDecision

A deterministic retention decision should preserve at minimum:

- retention contract/version;
- exact Phase 8/9 provenance identities;
- canonical proposed lesson type/scope/body identity;
- contradiction snapshot/result and exact evidence identities;
- duplicate result and any existing lesson identity;
- confidence basis/state;
- exact human approval request/proposal/binding/thread/principal identity and one-time consumption state;
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
- contradiction snapshot, dedup, confidence, and human-approval basis;
- version/lifecycle state;
- auditable creation metadata supplied by the accepted retention-store boundary;
- supersession/revocation linkage;
- authority flags that prevent live-state, source-truth, governance, CMIS/provider-trust, wallet, or execution escalation.

A verified lesson is trusted only within its recorded scope and lifecycle state. It is not automatically source truth.

## Lifecycle

Phase 10 must make later invalidation representable from the start.

At minimum, verified lessons need immutable state revisions supporting `active`, `superseded`, and `revoked`. A superseded/revoked state must bind its exact previous active state id and preserve the reason/evidence/decision identity that caused the lifecycle change. A later lesson must never silently overwrite or erase the evidence/history that justified the prior state.

Lifecycle transitions are retention-store state changes only. They do not modify source truth, protected governance, CMIS/provider trust, or wallet/execution state.

## Storage boundary

Persistent memory/knowledge infrastructure remains an external system of record, but **Phase 10 v1 is restricted to a provider-neutral retention store and must not write HXMP**.

The implementation must first prove the retention contract using an in-memory deterministic/test store behind a narrow typed `VerifiedLessonStore`-style interface. The interface may store Phase 10 retention decisions, verified lesson records, lifecycle revisions, canonical contradiction snapshots, and consumed approval bindings required for deterministic tests.

### HXMP is explicitly deferred

Roberta's accepted HXMP adapter contract defines HXMP writes as state-changing X1 transactions that spend XNT gas and require wallet-bound human approval, dry-run verification, signer/wallet binding, `write-soul`, and readback verification. Those operations conflict with this Phase 10 gate's no-wallet/no-transaction boundary.

Therefore Issue #133 and Phase 10 v1 **must not add, call, prepare, simulate-as-execution, approve, sign, broadcast, or otherwise exercise any HXMP write path**. No `HXMPPreparedWrite`, `execute_prepared_write`, `write-soul`, keypair/wallet binding, XNT gas spend, or equivalent external durable-memory transaction belongs in this slice.

Any future persistence of verified lessons into HXMP requires a **separate accepted roadmap/issue/spec gate** that explicitly reconciles the Learning System retention contract with the existing wallet-bound HXMP write and human-approval contract. Merging Phase 10 does not pre-authorize that future gate.

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
- HXMP writes or other blockchain-backed durable-memory transactions;
- wallet authority;
- transaction approval for value/state movement;
- transaction preparation/signing/broadcasting/custody/trading;
- Controlled Execution.

Controlled Execution remains locked.

## Required first-slice tests

The implementation must prove at minimum:

1. tampered or non-canonical Phase 9 verification state fails before retention gates run;
2. only `verified_for_learning` is retention-eligible;
3. unsupported lesson type/scope fails closed;
4. contradiction snapshots are built by trusted store/source interfaces, bind complete counts/member hashes/snapshot ids, and caller-selected subsets are rejected;
5. missing/failed/incomplete contradiction enumeration cannot become `clear`;
6. an explicit contradiction blocks retention;
7. exact duplicate detection uses the complete active-lesson snapshot, preserves provenance, and avoids a second trusted lesson;
8. missing confidence capability does not fabricate a numeric score;
9. only a validated exact human `ApprovalOutcome(status="approved")` from the existing approval runtime can authorize retention;
10. changed proposal/scope/contract/snapshot/provenance invalidates the approval binding and requires re-review;
11. missing/untrusted human-principal identity leaves retention unapproved;
12. replay of an already consumed approval binding cannot create another trusted lesson/decision;
13. successful retention preserves exact Phase 8/9 evaluation/verification provenance and the exact contradiction/dedup/confidence/approval basis;
14. retained lesson identity is deterministic/content-addressed and tamper-sensitive;
15. supersession/revocation lineage is immutable and auditable;
16. the Phase 10 store is provider-neutral/in-memory for v1 and no HXMP write path is imported, prepared, invoked, or authorized;
17. no retained lesson gains source-truth, live-state, governance, CMIS/provider-trust, wallet, or execution authority;
18. freshness-sensitive market facts remain subordinate to fresh accepted CMIS/provider evidence;
19. the full deterministic Roberta suite remains green.

## Explicit non-goals

Phase 10 does not add:

- automatic retention of every Phase 9 success;
- direct reflection/candidate-to-HXMP writes;
- **any HXMP write or blockchain-backed durable-memory transaction**;
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