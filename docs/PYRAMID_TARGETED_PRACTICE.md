# Pyramid remediation, targeted practice, and critical retention gates

Last reconciled: 2026-08-25 (America/New_York)

## Purpose

Pyramid remediation is the controlled path from a failed/partial canonical answer toward fresh source-grounded practice and, when required, a separate closed-book retention/transfer gate.

It does **not** rewrite historical checkpoints, mutate source truth, promote general Learning System retention, write HXMP, change CMIS/provider trust, mutate governance, or authorize execution.

## Accepted remediation sequence

```text
validated canonical/regraded checkpoint
  -> weakness analysis
  -> deterministic learning handoff
  -> source-grounded reconstruction
  -> source-grounded targeted practice
  -> supplemental grounded practice if fresh canonical practice is exhausted
  -> closed-book critical retention when critical-origin learning is involved
  -> curriculum-scoped learned concept only after its exact verification gates
  -> new canonical attempt only when the applicable gate authorizes it
```

## Source-grounded targeted practice

`roberta-pyramid-practice` consumes validated practice questions, remediation plan, checkpoint provenance, and source-grounded reconstruction evidence.

The practice question itself is always resolved back to the validated curriculum. Source evidence injected into the **practice answer path** must come from the exact accepted reconstruction/provenance scope for the matching weakness.

The grounded adapter must not expose the fresh question's expected answer, reference reasoning points, grader notes, or forbidden-inference checklist as hidden answer hints.

Canonical Pyramid answering remains closed-book; this source-evidence injection exists only in the explicitly grounded remediation path.

## Provenance before retrieval

For PDF-backed MB4E remediation, declared provenance is resolved before retrieval/ranking. Candidate chunks must be fully contained by the accepted PDF-page -> transcript-line alignment scope.

Missing, tampered, ambiguous, or out-of-range provenance fails closed. A lexically attractive chunk outside the exercise's declared source range cannot compete for selection.

## Cumulative freshness

Fresh practice selection excludes exercise IDs already observed in the current checkpoint set and any supplied prior canonical/practice checkpoint history.

The exclusion history is part of the remediation contract. Already-PASSed questions are excluded along with weak questions so repeated remediation does not teach Roberta by recycling previously seen prompts.

If an active weakness has no unseen canonical practice remaining, the normal path fails closed rather than silently reusing a question.

## Supplemental source-grounded practice

When the validated canonical practice pool is exhausted, separately accepted supplemental banks may supply new noncanonical questions.

Supplemental practice:

- uses IDs outside the canonical curriculum namespace;
- cannot overlap canonical exercise IDs;
- remains source-grounded and provenance-bound;
- preserves cumulative freshness;
- does not mutate the canonical ledger;
- cannot itself become source truth or a canonical exam result.

Command:

```text
roberta-pyramid-supplemental-practice
```

## Critical-origin lineage

A weakness that originated in a validated critical failure retains that critical origin across later remediation rounds while that same weakness remains active.

A later noncritical failure does not weaken the requirement from perfect critical remediation to an ordinary accuracy threshold.

Critical lineage is bound to prior remediation-plan identity/digests rather than inferred from a casual label.

## Verification policy

For ordinary/noncritical weakness groups, source-grounded practice must meet the accepted level/stage accuracy policy and group-specific gates before a later canonical attempt can be considered.

For **critical-origin** weakness groups, source-grounded practice is only a prerequisite. A perfect grounded result does **not** by itself authorize a new canonical attempt.

The next required gate is:

```text
closed_book_critical_retention
```

## Closed-book critical retention

`roberta-pyramid-critical-retention` verifies that the corrected concept survives without source/reconstruction context.

The retention answer payload must not contain:

- remediation context;
- source excerpts/evidence packets;
- expected answers;
- reference reasoning points;
- grader notes.

For the accepted Level-1 critical-origin gate, authorization requires:

```text
10 / 10 PASS
zero critical failures
```

A 9/10 result fails the gate even if it exceeds the ordinary Pyramid accuracy threshold.

Only a perfect source-free critical-retention result may authorize the next applicable canonical attempt. It does not authorize Phase 10 general lesson retention, HXMP writes, or any wallet/execution action.

## Critical blocker practice

The dedicated critical-only remediation path requires current validated critical semantics and can produce a derived read-only critical checkpoint view without modifying the source checkpoint directory.

Command:

```text
roberta-pyramid-critical-blocker-practice
```

This path preserves perfect-PASS requirements and can route to fresh supplemental critical practice when canonical practice is exhausted.

## Curriculum-scoped learned concepts

After the exact accepted source-grounded and closed-book/transfer gates pass, Roberta may persist a **Pyramid curriculum-scoped learned concept**.

The learned concept store is restricted by curriculum, level/stage, concept, and subconcept. Matching concepts may be provided to the canonical **answer path**; the canonical grader remains unchanged.

The learned-concept payload does not include source excerpts, expected answers, grader reference reasoning, or forbidden-inference lists.

This is not general durable memory. It does not become:

- HXMP state;
- Phase 10 `VerifiedLessonRecord` state;
- source truth;
- current blockchain/market truth;
- CMIS/provider verification;
- governance authority;
- execution authority.

`roberta-pyramid-critical-autofix` is a fail-closed convenience workflow around these already accepted gates. It never rewrites a failed canonical result.

## Main commands

```text
roberta-pyramid-remediate
roberta-pyramid-source-reconstruct
roberta-pyramid-practice
roberta-pyramid-supplemental-practice
roberta-pyramid-critical-blocker-practice
roberta-pyramid-critical-retention
roberta-pyramid-critical-autofix
```

Practice/remediation outputs are evidence about learning performance. They do not become trusted live facts or general retained lessons by implication.
