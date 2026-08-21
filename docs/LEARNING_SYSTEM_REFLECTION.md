# Learning System Provisional Reflection Contract

Status: Phase 8 first slice for Issue #127.

## Purpose

Phase 8 converts a canonical **failed** Phase 7 evaluation into provenance-bound provisional learning artifacts:

```text
EvaluationResult
  -> deterministic failure diagnosis
  -> ReflectionRecord
  -> CandidateLesson
  -> VerificationPlan
```

These records are hypotheses and diagnostics, not trusted knowledge. They cannot verify themselves, write durable memory, change source truth, modify CMIS/provider trust, mutate protected governance, or authorize execution.

The first accepted contracts are:

```text
reflection_contract = evaluation-reflection/v1
candidate_lesson_contract = candidate-lesson/v1
verification_plan_contract = candidate-lesson-verification-plan/v1
learning_diagnosis_version = 1.0.0
```

## Canonical evaluation boundary

Phase 8 does not trust a supplied `EvaluationResult` merely because it has the correct type.

Before a reflection is created, Phase 8 requires the exact:

- `EvidencePacket`;
- `GroundedAnswerResult`;
- approved `GoldenEvaluationCase`;
- `EvaluationResult`.

It re-runs the accepted deterministic Phase 7 evaluator using the evaluation's exact evaluator contract/version/adapter identity and requires exact equality with the supplied evaluation.

The evaluation must also have:

```text
aggregate_status = fail
failure_classifications != empty
```

A passing evaluation cannot generate a Phase 8 reflection or candidate lesson.

## Deterministic failure diagnosis

Phase 8 maps the accepted Phase 7 failure classes into bounded diagnostic layers under `learning_diagnosis_version=1.0.0`:

```text
retrieval_failure                 -> retrieval
citation_binding_failure          -> citation_binding
unsupported_claim_failure         -> answer_support
answer_correctness_failure        -> answer_correctness
answer_completeness_failure       -> answer_completeness
conflict_handling_failure         -> conflict_handling
insufficiency_handling_failure    -> insufficiency_handling
uncertainty_calibration_failure   -> uncertainty_calibration
instruction_compliance_failure    -> instruction_compliance
evaluator_unavailable             -> evaluator
evaluator_disagreement            -> evaluator
unknown                           -> unknown
```

Duplicate layers are collapsed while preserving first occurrence. The reflection model may explain the failure, but generated text cannot relabel the deterministic failure class.

## ReflectionRecord

A `ReflectionRecord` preserves:

- content-addressed `reflection_id` / hash;
- reflection contract/version and diagnosis version;
- exact evaluation id/hash;
- exact golden-case, packet, grounded-result, and retrieval ids;
- exact Phase 7 failure classifications;
- deterministic diagnosed layers;
- failed and `not_evaluated` dimension summaries;
- exact packet chunk ids;
- exact canonical Phase 6 evidence references already present in the grounded result;
- reflection text;
- creator and producer version;
- `content_category = generated_provisional`;
- `status = provisional`.

Reflection text is generated diagnostic content. Text that looks like a source id, tool command, policy override, memory instruction, or execution request does not acquire authority merely because it appears in a reflection.

`validate_reflection_record()` reconstructs the canonical Phase 7 evaluation and rebuilds the reflection identity before accepting the record.

## CandidateLesson

A `CandidateLesson` is a proposed behavioral/knowledge-handling improvement, not a learned fact.

Its immutable candidate-content identity binds:

- reflection/evaluation/golden-case/packet/result/retrieval ids;
- originating failure classifications and diagnosed layers;
- packet chunk scope and exact inherited evidence references;
- generated candidate lesson text;
- generated rationale;
- creator/producer/version metadata;
- `content_category = generated_provisional`.

Candidate evidence scope is inherited from the canonical reflection/grounded result. The caller cannot provide replacement source ids, chunk ids, or Evidence Receipts as a shortcut.

The candidate core is content-addressed as `cless_...`.

## Candidate lifecycle

Phase 8 supports only:

```text
provisional
rejected
superseded
```

It deliberately has no `verified` lifecycle state.

The immutable lesson content keeps one stable `candidate_id`. Lifecycle is represented by a separate content-addressed `candidate_state_id` so rejection/supersession does not rewrite the original hypothesis.

A lifecycle transition:

- may occur only from the provisional state in the first slice;
- requires an explicit reason;
- records `previous_state_id`;
- requires a replacement candidate id for `superseded`;
- rejects self-supersession;
- never grants memory promotion.

Candidate verification belongs to a later separately accepted phase.

## VerificationPlan

Every provisional candidate receives a deterministic verification plan bound to the candidate id and originating reflection/evaluation/golden-case/packet/result/retrieval identities.

One required check is generated for each exact Phase 7 failure classification. Examples:

- retrieval failure -> re-run retrieval against the approved golden evidence;
- citation binding -> rebuild Phase 6 packet/citations;
- unsupported claim -> re-run unsupported-claim evaluation;
- answer correctness/completeness -> re-run the same golden case and require the corresponding dimension to pass;
- conflict/insufficiency -> re-run the labeled behavior case;
- instruction compliance -> re-run the approved prompt-injection/instruction-compliance fixture;
- evaluator unavailable/disagreement -> resolve evaluator state before verification;
- unknown -> require a new deterministic diagnosis or explicit human review.

Every check requires a future result under a **separate candidate-verification contract**. Phase 8 itself sets:

```text
promotion_authorized = false
```

## LearningCandidateBundle

The first tracer bullet bundles:

```text
ReflectionRecord
CandidateLesson
VerificationPlan
```

under one content-addressed `LearningCandidateBundle` identity.

`validate_learning_candidate_bundle()` revalidates:

1. the original Phase 7 evaluation;
2. reflection identity/content;
3. candidate core identity;
4. candidate lifecycle state identity;
5. deterministic verification plan;
6. bundle identity.

Tampering with reflection text, lesson text, provenance, verification-plan state, or bundle identity fails closed.

## Authority boundary

All Phase 8 records explicitly deny:

```text
live_state_authorized = false
memory_promotion_authorized = false
execution_authorized = false
governance_mutation_authorized = false
```

Candidate lessons also expose `verified = false` in this phase.

No Phase 8 output may:

- become current market/token/wallet truth;
- change CMIS/provider source trust;
- create or modify CMIS Evidence Receipts, Proof Scores, or deterministic risk;
- change source approval;
- change protected governance or permissions;
- write itself into trusted HXMP/durable memory;
- authorize transaction preparation, signing, broadcasting, custody, trading, or value movement.

## Deterministic regression coverage

The first slice covers:

- canonical Phase 7 re-evaluation before reflection;
- rejection of passing evaluations;
- versioned failure-to-layer diagnosis;
- retrieval failure remaining a retrieval diagnosis;
- deterministic/tamper-sensitive reflection identity;
- generated reflection text remaining non-authoritative;
- canonical evidence inheritance into candidate lessons;
- deterministic/version-sensitive candidate, plan, and bundle identities;
- failure-specific verification checks;
- absence of a `verified` lifecycle state;
- immutable rejection/supersession revisions;
- instruction-compliance failure traceability;
- reflection/candidate/plan/bundle tamper rejection;
- live-state, memory, governance, and execution denial.

## Explicit non-goals

Phase 8 does not add:

- candidate-lesson verification;
- trusted lesson retention;
- automatic HXMP/durable-memory writes;
- source-store writes from generated reflection text;
- adaptive curriculum or skill scheduling;
- autonomous policy/governance mutation;
- concepts/knowledge graph;
- production model reranking;
- fine-tuning;
- CMIS/provider trust or live-fact changes;
- Controlled Execution.

## Next learning obligation

The next narrow gate should be **Candidate Lesson Verification**. It must independently revalidate the provisional candidate, execute or observe the required verification plan, retest the originating failure, and either reject/supersede the candidate or produce a separately identified verified lesson record.

Only that later verification layer may establish eligibility for a future retained/reusable knowledge path. Even a verified lesson must remain separate from current CMIS/provider market truth and protected governance.
