# Learning System Phase 9 — Candidate Lesson Verification

Status: implementation contract for Issue #129.

## Purpose

Phase 9 independently verifies or rejects a **provisional Phase 8 `CandidateLesson`** against its exact canonical provenance and deterministic `VerificationPlan`.

Verification is a measurement/decision boundary. It is **not** durable-memory promotion, source truth, current market truth, protected-governance authority, CMIS/provider trust, wallet authority, transaction approval, or Controlled Execution authorization.

## Architecture boundary

```text
canonical Phase 8 LearningCandidateBundle
  + original EvidencePacket
  + original GroundedAnswerResult
  + original approved GoldenEvaluationCase
  + original failed EvaluationResult
        ↓ exact Phase 8 revalidation
provisional CandidateLesson + exact VerificationPlan
        ↓ independent retest evidence
canonical retest EvidencePacket + GroundedAnswerResult
        ↓ deterministic Phase 7 evaluation
per-check VerificationCheckResult
        ↓
CandidateVerificationResult
  -> verified_for_learning | rejected | inconclusive
```

A later separate retention/promotion phase must decide whether a `verified_for_learning` result may enter reusable durable learning state.

## Contracts

```text
candidate_verification_contract = candidate-lesson-verification/v1
verifier_adapter_id = deterministic-phase7-retest/v1
verifier_version = 1.0.0
```

The verifier must not accept arbitrary caller-selected checks. Required checks come only from the exact canonical Phase 8 `VerificationPlan`.

## Canonical Phase 8 prerequisite

Before any check runs, the verifier must:

1. require the original `EvidencePacket`, `GroundedAnswerResult`, approved `GoldenEvaluationCase`, failed `EvaluationResult`, and `LearningCandidateBundle`;
2. call the accepted Phase 8 canonical bundle validator;
3. require exact equality of the reconstructed Phase 8 records;
4. require the candidate lifecycle state to be exactly `provisional`;
5. reject rejected/superseded candidates rather than resurrecting them;
6. preserve the exact candidate/reflection/evaluation/golden-case/packet/result/retrieval/plan identities.

## Independent retest evidence

Candidate text and reflection text are never verification evidence.

When retest evidence is supplied, Phase 9 computes a fresh deterministic Phase 7 `EvaluationResult` from the supplied canonical retest `EvidencePacket`, retest `GroundedAnswerResult`, and the original approved `GoldenEvaluationCase`.

The caller does not supply a trusted retest `EvaluationResult`.

If required retest evidence is unavailable, the applicable checks become `inconclusive`; unavailable evidence must never be converted into success.

Malformed, tampered, or non-canonical retest evidence fails closed.

## VerificationCheckResult

Each Phase 8 `VerificationCheck` produces one immutable result preserving at minimum:

- exact `check_id` and `check_kind`;
- exact originating failure classification and diagnosed layer;
- exact required identity references from the Phase 8 plan;
- status: `pass`, `fail`, or `inconclusive`;
- exact observed retest packet/result/retrieval/evaluation ids when present;
- bounded deterministic details explaining the outcome;
- no live-state, memory-promotion, governance-mutation, or execution authority.

A check cannot be added, removed, reordered, or renamed by the verifier.

## First-slice deterministic check semantics

The first accepted verifier maps Phase 8 check kinds to Phase 7 retest dimensions as follows:

```text
retest_retrieval_against_golden_case
  -> retrieval_coverage

revalidate_phase6_packet_and_citations
  -> citation_correctness

rerun_golden_case_unsupported_claim_check
  -> unsupported_claim_rate

rerun_golden_case_answer_correctness
  -> answer_correctness + limitation_disclosure

rerun_golden_case_answer_completeness
  -> answer_completeness

rerun_golden_conflict_case
  -> conflict_handling

rerun_golden_insufficiency_case
  -> insufficiency_handling

rerun_instruction_compliance_fixture
  -> instruction_compliance
```

For these checks:

- all required dimensions must be `pass` for the check to pass;
- any required dimension `fail` makes the check fail;
- any required dimension `not_evaluated` or `not_applicable` makes the check inconclusive unless the contract explicitly defines that state as successful (the first slice defines no such exception).

The following Phase 8 check kinds remain intentionally `inconclusive` in this first slice because the required independent accepted capability does not yet exist:

```text
require_calibration_evaluator_before_verification
require_evaluator_available
require_evaluator_disagreement_resolved
require_manual_or_new_deterministic_diagnosis
```

They must not be guessed, silently passed, or converted into verified learning.

## Aggregate decision

The Phase 9 result status is deterministic:

```text
if any required check == fail:
    rejected
elif any required check == inconclusive:
    inconclusive
elif every required check == pass:
    verified_for_learning
else:
    fail closed
```

`verified_for_learning` means only that the candidate passed the accepted verification contract. It does not authorize promotion.

## CandidateVerificationResult

The result preserves at minimum:

- deterministic `verification_id` and SHA-256 content hash;
- verification contract/version/adapter identity;
- exact Phase 8 bundle, candidate, candidate-state, reflection, plan, original evaluation, golden-case, packet, grounded-result, and retrieval ids;
- ordered per-check results matching the exact Phase 8 plan order;
- aggregate status: `verified_for_learning`, `rejected`, or `inconclusive`;
- verifier producer identity/version;
- explicit authority denials.

The result is content-addressed so mutation changes identity.

## Authority boundary

Every Phase 9 result exposes:

```text
live_state_authorized = false
memory_promotion_authorized = false
governance_mutation_authorized = false
execution_authorized = false
source_truth_authorized = false
```

No Phase 9 function writes HXMP/durable memory, writes source records, changes source approval, changes CMIS/provider trust, changes protected policy, prepares/signs/broadcasts transactions, or grants execution authority.

Freshness-sensitive market/blockchain truth continues to flow only through:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

## Required first-slice tests

The Phase 9 implementation must prove at minimum:

1. the complete Phase 8 bundle/lifecycle is revalidated before verification;
2. rejected/superseded candidates cannot be verified;
3. required checks come only from the exact Phase 8 plan and preserve order/identity;
4. canonical retest evidence is independently evaluated rather than trusting caller-supplied scores;
5. a corrected retest can pass the exact applicable check and yield `verified_for_learning` only when every required check passes;
6. a repeated failure yields `rejected`;
7. missing retest evidence yields `inconclusive`, never success;
8. unsupported verifier capabilities remain `inconclusive`;
9. candidate/reflection generated text cannot supply replacement evidence or modify the plan;
10. verification identity is deterministic/content-addressed and tamper-sensitive;
11. all Phase 9 records deny source truth, live state, memory promotion, governance mutation, and execution;
12. the full deterministic Roberta suite remains green.

## Explicit non-goals

Phase 9 does not add:

- durable lesson retention/promotion;
- HXMP writes from verified candidates;
- source-store writes from generated candidate/reflection text;
- adaptive curriculum or skill scheduling;
- autonomous policy/governance mutation;
- concepts/knowledge graph;
- production reranking or fine-tuning;
- CMIS/provider truth or trust changes;
- transaction preparation/signing/broadcasting/custody/trading;
- Controlled Execution.
