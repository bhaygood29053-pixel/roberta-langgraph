# Learning System Answer Evaluation Contract

Status: Phase 7 first slice for Issue #124.

## Purpose

Phase 7 independently evaluates accepted Phase 6 `GroundedAnswerResult` records against explicit golden labels. It measures answer quality without converting retrieval scores, citation presence, evaluator opinion, or model confidence into source truth.

The first accepted contracts are:

```text
answer_evaluation_contract = grounded-answer-evaluation/v1
golden_case_contract = grounded-answer-golden-case/v1
evaluator_adapter = deterministic-golden-label/v1
evaluator_version = 1.0.0
```

The first slice is deliberately deterministic. It does not add a model-based semantic judge.

## Architecture boundary

```text
canonical EvidencePacket
  + canonical GroundedAnswerResult
  + approved GoldenEvaluationCase
    -> deterministic Answer Evaluation
      -> per-dimension measurements
      -> failure classification
      -> EvaluationResult
      -> optional corpus aggregate
```

Retrieval quality remains separately measured by Phase 5. Phase 7 may identify that expected evidence was absent, but it does not rewrite retrieval history or call an answer failure a retrieval failure merely to improve scores.

Freshness-sensitive market/blockchain truth remains:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

No evaluation score can replace current CMIS/provider evidence.

## Canonical Phase 6 validation

Evaluation does not trust caller-supplied grounded results.

`validate_grounded_result_for_evaluation()` reconstructs the Phase 6 `AnswerCandidate` from the supplied result, re-runs Phase 6 citation/scope validation against the exact `EvidencePacket`, and requires exact equality with the supplied `GroundedAnswerResult`.

This catches tampering in answer text, claims, citations, limitations, statuses, result identities, semantic flags, or evidence references before any score is produced.

## GoldenEvaluationCase

Golden cases are versioned evaluation labels, not source truth.

Each case is content-addressed and preserves:

- `case_id` and `case_hash`;
- golden-case contract/version;
- question/task text;
- expected behavior: `answer`, `insufficient`, or `conflict`;
- optional exact packet/retrieval binding;
- expected relevant `chunk_id` values;
- structured claim criteria;
- required answer substrings where deterministic reference criteria are appropriate;
- required/allowed limitations;
- forbidden answer substrings for instruction-compliance fixtures;
- optional calibration target metadata;
- provenance URI;
- author;
- approval status.

Only `approved` golden cases may be scored. Pending or rejected labels fail closed.

Changing a case label, version, provenance field, or expected criterion changes the content-addressed case identity.

## GoldenClaimCriterion

A criterion labels one expected structured claim by exact `claim_id` and may define:

```text
required = true | false
allowed_statuses = supported | insufficient | conflict
allowed_evidence_chunk_ids = (...)
required_text_substrings = (...)
```

The substring mechanism is intentionally narrow and deterministic. It is not a general semantic-equivalence engine.

## Evaluation dimensions

Phase 7 keeps measurements separate.

### Retrieval coverage

If a golden case labels relevant chunk ids, Phase 7 measures whether those chunks were present in the Phase 6 packet.

Missing expected evidence produces `retrieval_failure` and blocks answer-correctness/completeness dimensions that would otherwise incorrectly blame reasoning for absent evidence.

### Citation correctness

Phase 6 already requires citations to exact packet anchors. Phase 7 revalidates that each `EvidenceReference` still matches the exact anchor id, chunk id, and content hash.

### Citation precision

When relevant chunks are labeled:

```text
relevant cited chunk ids / all cited chunk ids
```

A citation may be structurally valid but irrelevant to the golden case. That reduces precision; it is not mislabeled as a fabricated citation.

### Citation completeness

For expected relevant evidence that was actually retrieved:

```text
cited relevant chunks / retrieved relevant chunks
```

If expected evidence was not retrieved at all, citation completeness is `not_evaluated` and the failure remains classified at retrieval.

### Unsupported-claim rate

Structured claims that lack a corresponding golden claim criterion, use a disallowed claim status, cite disallowed evidence for that criterion, or fail explicit deterministic text criteria are counted separately as unsupported/mislabeled claims.

This metric does not claim to detect arbitrary semantic hallucinations.

### Answer correctness

Deterministic correctness checks are limited to explicit golden claim criteria and optional required answer substrings.

When retrieval has already failed, answer correctness is `not_evaluated` rather than automatically failing.

### Answer completeness

Required golden claim ids must be present. Missing expected claims reduce completeness when retrieval supplied the evidence needed to evaluate them.

### Limitation disclosure

Required limitations must be present. When a case supplies an explicit allowed-limitation set, unapproved extra limitations are also surfaced.

### Insufficiency handling

A golden `insufficient` case passes only when the Phase 6 result is explicitly insufficient, all structured claims remain `insufficient`, and `insufficient_evidence` is disclosed.

### Conflict handling

A golden conflict case requires at least one structured `conflict` claim. Phase 7 does not reconcile the conflict or certify that the cited passages are semantically contradictory.

### Instruction compliance

Golden cases may provide deterministic forbidden answer substrings. This supports reproducible prompt-injection regression fixtures without granting instruction-looking source text any authority.

### Semantic groundedness

The deterministic first slice always reports:

```text
semantic_groundedness = not_evaluated
semantic_support_verified = false
claim_coverage_verified = false
```

Citation presence is not semantic entailment. A future semantic evaluator, if justified, requires a separately accepted adapter, provenance, calibration tests, and disagreement handling.

### Uncertainty calibration

If no calibration label exists, the dimension is `not_applicable`.

If a case provides a calibration target, the first slice reports `not_evaluated` because Phase 6 has no calibrated confidence field. Phase 7 does not invent one.

## Failure classification

The first slice preserves explicit failure classes:

```text
retrieval_failure
citation_binding_failure
unsupported_claim_failure
answer_correctness_failure
answer_completeness_failure
conflict_handling_failure
insufficiency_handling_failure
uncertainty_calibration_failure
instruction_compliance_failure
evaluator_unavailable
evaluator_disagreement
unknown
```

Only classes actually justified by the deterministic evaluation are emitted.

## EvaluationResult

Every result preserves:

- content-addressed `evaluation_id` / `evaluation_hash`;
- exact golden-case, packet, grounded-result, and retrieval identities;
- evaluator contract/version/adapter identity;
- per-dimension status, score, numerator/denominator, and details;
- explicit failure classifications;
- aggregate pass/fail under deterministic acceptance rules;
- warnings/errors;
- semantic/calibration evaluation state;
- authority-denial flags.

A Phase 7 `pass` means the answer satisfied the explicit deterministic golden labels. It is not source truth, CMIS verification, permission to promote a lesson, or permission to execute anything.

## Aggregate reporting

`aggregate_evaluation_results()` reports a deterministic corpus summary over unique evaluation ids:

- case pass rate;
- mean citation precision;
- mean citation completeness;
- mean unsupported-claim rate;
- insufficiency accuracy where applicable;
- conflict accuracy where applicable;
- retrieval-failure rate;
- answer-failure rate.

Retrieval failures and answer failures remain separate.

## Authority boundary

All golden cases, dimensions, evaluation results, and aggregates expose or preserve the equivalent of:

```text
live_state_authorized = false
memory_promotion_authorized = false
execution_authorized = false
```

Evaluation cannot:

- certify current market/token/wallet state;
- change CMIS/provider trust;
- create or modify Evidence Receipts, Proof Scores, or deterministic risk;
- promote generated answer text into verified durable memory;
- authorize transaction preparation, signing, broadcasting, custody, trading, or value movement.

## Explicit non-goals

Phase 7 does not add:

- model-based semantic judging;
- automatic reflection or lesson promotion;
- automatic durable-memory writes;
- adaptive curriculum or skill scheduling;
- concepts/knowledge graph;
- production model reranking;
- fine-tuning;
- production PostgreSQL/pgvector coupling;
- CMIS/provider authority changes;
- Controlled Execution.

## Next learning obligation

After this deterministic evaluation foundation is accepted, the next narrow learning milestone should use evaluation failures to create **provisional diagnostic/reflection records** while keeping them outside trusted memory. A later verification gate must exist before any candidate lesson becomes reusable verified knowledge.
