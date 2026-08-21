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
        ↓ deterministic retest-case derivation
approved golden labels + retest-observed evidence pins
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

Retest evidence is atomic in v1:

- if both the retest `EvidencePacket` and retest `GroundedAnswerResult` are absent, the applicable checks are `inconclusive`;
- if exactly one is supplied, verification fails closed before any supplied identity can be recorded in a verification result;
- if both are supplied, Phase 9 requires them to survive canonical Phase 7 reconstruction/evaluation before their identities can become observed retest provenance.

The caller does not supply a trusted retest `EvaluationResult`.

### Golden labels versus original evidence pins

The original approved `GoldenEvaluationCase` remains the provenance root for the labels being tested. Its question, expected behavior, relevant chunk labels, claim criteria, required/allowed limitations, forbidden/required answer substrings, calibration target, provenance, author, approval state, contract, and version are preserved exactly for retesting.

Some accepted Phase 7 golden cases may also pin `expected_packet_id` and/or `expected_retrieval_id` to the **original failed evidence**. A corrected retrieval can legitimately produce new packet/retrieval identities, so blindly reusing those original pins would make a valid retrieval correction impossible to score.

Phase 9 therefore derives a deterministic retest golden case:

- all approved golden labels and metadata remain unchanged;
- an original non-null `expected_packet_id` is rebound only to the supplied retest packet id;
- an original non-null `expected_retrieval_id` is rebound only to the supplied retest grounded-result retrieval id;
- an original null pin remains null;
- the derived retest case is content-addressed under the existing Phase 7 golden-case contract;
- the original `golden_case_id` and derived `retest_golden_case_id` are both preserved in Phase 9 output provenance.

This is evidence-pin rebinding for the independent retest, not free-form mutation of the approved labels and not a new authority source.

Malformed, tampered, or non-canonical complete retest evidence fails closed.

## VerificationCheckResult

Each Phase 8 `VerificationCheck` produces one immutable result preserving at minimum:

- exact `check_id` and `check_kind`;
- exact originating failure classification and diagnosed layer;
- exact required identity references from the Phase 8 plan;
- status: `pass`, `fail`, or `inconclusive`;
- exact derived retest golden-case id when a retest runs;
- exact observed retest packet/result/retrieval/evaluation ids when present;
- bounded deterministic details explaining the outcome;
- no live-state, memory-promotion, governance-mutation, or execution authority.

A check cannot be added, removed, reordered, or renamed by the verifier.

## Deterministic check semantics

The accepted verifier maps the Phase 8 retest-capable check kinds to Phase 7 dimensions as follows:

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
- any required dimension `not_evaluated` or `not_applicable` makes the check inconclusive unless the contract explicitly defines that state as successful (v1 defines no such exception).

The following Phase 8 check kinds remain intentionally `inconclusive` because the required independent accepted capability does not exist in the v1 verifier:

```text
require_calibration_evaluator_before_verification
require_evaluator_available
require_evaluator_disagreement_resolved
require_manual_or_new_deterministic_diagnosis
```

They must not be guessed, silently passed, or converted into verified learning.

### Coverage and current Phase 7 reachability

The Phase 9 regression suite exercises every Phase 8 verification check kind at its accepted verifier seam.

End-to-end canonical Phase 8 -> Phase 9 retest coverage is demonstrated for the failure classes the accepted deterministic Phase 7 adapter can currently emit through canonical inputs, including:

```text
retrieval_failure
unsupported_claim_failure
answer_correctness_failure
answer_completeness_failure
conflict_handling_failure
insufficiency_handling_failure
instruction_compliance_failure
```

Retrieval coverage includes a regression where the original approved golden case pins the failed packet/retrieval identities and the corrected retest necessarily changes them. The verifier preserves the original golden-case identity while deriving and recording a retest-case identity with only those original pins rebound to the observed retest evidence.

`citation_binding_failure` is exercised at the Phase 9 check seam against a canonical Phase 7 retest evaluation. Canonical Phase 6 validation normally rejects malformed citation state before it can become an accepted Phase 7 input, so Phase 9 does not fabricate a corrupted Phase 6 record merely to manufacture that original failure.

The calibration/evaluator/unknown check kinds remain explicitly inconclusive until separately accepted deterministic capabilities can satisfy them. The current Phase 7 deterministic adapter does not manufacture those failure states, and Phase 9 does not widen Phase 7 merely to create fixtures.

This distinction is intentional: contract coverage does not imply that every declared failure class is currently reachable from the accepted Phase 7 adapter.

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
- exact Phase 8 bundle, candidate, candidate-state, reflection, plan, original evaluation, original golden-case, packet, grounded-result, and retrieval ids;
- derived `retest_golden_case_id` when a retest runs;
- exact observed retest packet, grounded-result, retrieval, and evaluation ids when a retest runs;
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

## Required Phase 9 tests

The implementation proves at minimum:

1. the complete Phase 8 bundle/lifecycle is revalidated before verification;
2. rejected/superseded candidates cannot be verified;
3. required checks come only from the exact Phase 8 plan and preserve order/identity;
4. canonical retest evidence is independently evaluated rather than trusting caller-supplied scores;
5. a corrected retest can pass the exact applicable check and yield `verified_for_learning` only when every required check passes;
6. a repeated failure yields `rejected`;
7. missing retest evidence yields `inconclusive`, never success;
8. exactly-one-component retest evidence fails closed before unvalidated provenance can be published;
9. unsupported verifier capabilities remain `inconclusive`;
10. candidate/reflection generated text cannot supply replacement evidence or modify the plan;
11. verification identity is deterministic/content-addressed and tamper-sensitive;
12. malformed/tampered complete retest grounded state fails closed before check scoring;
13. a corrected retrieval can be scored when the original approved golden case pinned the failed packet/retrieval ids, with original and derived retest-case provenance both retained;
14. retrieval, citation-binding, unsupported-claim, correctness, completeness, conflict, insufficiency, instruction-compliance, calibration/evaluator, and unknown check semantics are covered without manufacturing unavailable Phase 7 authority;
15. all Phase 9 records deny source truth, live state, memory promotion, governance mutation, and execution;
16. the full deterministic Roberta suite remains green.

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
