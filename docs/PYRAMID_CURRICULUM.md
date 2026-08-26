# Roberta Blockchain Reasoning Pyramid — Curriculum and Source-Mastery Contract

Last reconciled: 2026-08-26 (America/New_York)

Status: **accepted living contract**. The original 20-level Pyramid is the reusable global capability taxonomy; source-specific mastery plans define which capabilities an individual source must actually prove.

## Purpose

The Pyramid is a training and evaluation environment for Roberta. It converts approved reference material into source-traceable, progressively harder reasoning exercises and measures whether Roberta generalizes across unseen questions.

It is not source-truth authority, a replacement for RAG, a replacement for CMIS, or an execution system.

```text
approved source material
  -> exact source/provenance contract
  -> source mastery plan
  -> required source stages mapped to global capabilities
  -> learning objectives
  -> large source-grounded exercise banks
  -> canonical stage exam
  -> grading / failure analysis
  -> remediation / source-grounded practice when needed
  -> source-stage ledger
  -> final source capstone
```

The accepted autonomous Learning Plane can now execute this source-mastery loop end to end after an explicit source selection. Automation does not change any Pyramid authority boundary.

## Authority boundary

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider / verified source
```

The Pyramid may teach static concepts and reusable procedures. It cannot turn book text, expected answers, learned concepts, checkpoints, or training scores into current blockchain truth.

Fresh accepted CMIS/provider evidence overrides static learning material for freshness-sensitive facts. Missing evidence remains unknown. Proof Score remains separate from risk.

No Pyramid operation grants transaction construction, signing, broadcasting, custody, trading, bridge transfer, wallet authority, HXMP write authority, or Controlled Execution.

## Curriculum package

A source-aware curriculum may contain:

```text
curricula/<curriculum_id>/
  manifest.json
  source_mastery_plan.json
  source_map*.json
  objectives*.json
  exercises.jsonl
  provenance.jsonl
  rubrics / failure-policy material where applicable
```

The manifest/source contracts preserve source identity, edition/version, approved source key, immutable hashes, chapter/section/page-location mapping, authority/approval state, and known limitations.

Generated exercise text is transformed curriculum material. It does not become source evidence merely because it was derived from the source.

The autonomous controller validates complete existing banks, refuses unsafe partial-bank overwrite, and atomically publishes generated stages only after source/provenance/bank/canonical-selection checks pass.

## Exercise contract

Exercises bind at minimum:

```text
exercise_id
curriculum_id
level / mapped capability
concept
subconcept
question
expected_answer
required_reasoning_points
forbidden_inferences
source_refs
grading_rubric_id
integrity_question
boss_question
requires_live_data
```

Required rules include:

1. exercise IDs are unique within the curriculum;
2. the mapped global capability level is valid;
3. question text is non-empty;
4. exercises trace to approved source refs or an explicitly approved synthetic/adversarial transformation of sourced concepts;
5. `requires_live_data=true` requires the normal Scout -> CMIS path rather than a stored source value;
6. exercises cannot encode wallet/execution authority;
7. expected answers/reasoning points are grader guidance, not source evidence.

For autonomously generated targets, exact source evidence is additionally enforced before exercise construction: the evidence quote must occur on the cited page, the page must belong to the cited chapter, and every assigned generation chunk must retain an independently accepted target.

## Global 20-capability taxonomy

| Capability | Domain | Pass accuracy |
|---:|---|---:|
| 1 | Fundamentals | 85% |
| 2 | Blockchain mechanics | 85% |
| 3 | Transactions | 85% |
| 4 | Cryptography | 85% |
| 5 | Smart contracts | 85% |
| 6 | Tokenomics | 88% |
| 7 | Liquidity | 88% |
| 8 | Market structure | 88% |
| 9 | DeFi | 88% |
| 10 | Advanced DeFi | 88% |
| 11 | On-chain analysis | 90% |
| 12 | Wallet relationships | 90% |
| 13 | Risk reasoning | 90% |
| 14 | Adversarial analysis | 90% |
| 15 | Evidence forensics | 90% |
| 16 | Intelligence synthesis | 92% |
| 17 | Cross-chain reasoning | 92% |
| 18 | Complex investigations | 92% |
| 19 | Red-team mastery | 92% |
| 20 | Grandmaster | 95% |

These are reusable capabilities. They are not a mandatory 20-step syllabus for every source.

## Source-specific mastery plan

Before a source-aware run progresses, Roberta freezes a `source_mastery_plan.json` that accounts for the **full source scope**.

A valid plan requires:

- exact source/curriculum identity;
- planner contract/version and basis;
- contiguous source-stage ordinals `1..N`;
- one unique global capability per required stage;
- source chapters supporting every stage;
- explicit excluded global capabilities;
- 300 canonical questions per required stage;
- complete-source coverage assertion;
- deterministic plan hash;
- source-capstone requirement state.

Required and excluded capabilities together account for all 20 capability levels.

For newly created autonomous curricula, the frozen plan is persisted in durable job storage **before** authoritative ledger binding or first package publication. This prevents interruption from forcing a nondeterministic re-plan with a different hash.

A source cannot be declared mastered merely because the currently built banks passed if the frozen full-source plan still has required stages or a required capstone outstanding.

## Canonical stage exam

Every **new** canonical source-stage attempt uses exactly:

```text
300 scored questions
249 ordinary
50 integrity
1 Boss Question, last
```

A stage passes only when all accepted gates succeed:

- weighted/accepted accuracy at or above the mapped capability threshold;
- integrity accuracy at least 90%;
- Boss PASS;
- zero validated critical failures.

Critical failures include evidence fabrication, converting missing evidence into a fact, overriding fresh CMIS/provider evidence with memory/source text, Proof Score/risk confusion, unsupported ownership claims, or invented execution/authorization.

## Autonomous remediation before retry

In the accepted autonomous controller, a failed stage cannot simply be resampled until it passes.

A failed attempt produces immutable weakness evidence. Before another canonical attempt, Roberta must run the accepted verified remediation sequence:

```text
source-bound weak concepts
  -> source-grounded practice
  -> unaugmented closed-book retention check
  -> learned-concept transfer verification
  -> curriculum-scoped promotion only if every gate passes
  -> canonical retry
```

Only matching verified curriculum-scoped learned concepts may support a later answer model. They are not source evidence, general HXMP memory, live state, or answer keys.

## Legacy 1,000-question compatibility

Historical canonical Level 1/2 attempts used 1,000 questions. Those results/checkpoints remain immutable audit history.

Explicit legacy reconstruction preserves:

```text
949 ordinary
50 integrity
1 Boss
```

New q300 checkpoints are namespaced separately so they cannot collide with legacy checkpoint layouts. Historical results may be mapped into source-stage history but are never rewritten as 300-question attempts.

## Randomization and anti-memorization

A run and stage selection are deterministic from the exact curriculum snapshot plus seed. Reusing the same inputs reproduces the selection; a new seed produces a new sample where the bank permits.

Exercise banks should be larger than the 300-question canonical exam so later attempts can draw different questions.

Remediation uses cumulative seen-ID exclusions. Already-seen PASS questions are excluded along with failed questions. If canonical fresh practice is exhausted, only separately accepted supplemental practice may continue; silent question reuse is not allowed.

## Remediation and critical learning

```text
canonical failure
  -> weakness analysis
  -> source-grounded reconstruction
  -> source-grounded fresh practice
  -> supplemental fresh practice if needed
  -> closed-book critical retention when critical-origin learning is involved
  -> curriculum-scoped learned concept only after exact gates
```

A perfect **source-grounded** critical practice run is a prerequisite, not authority for a new canonical attempt. Critical-origin learning must also pass the accepted source-free closed-book retention gate.

Curriculum-scoped learned concepts can support matching canonical answer generation only after their exact verification/transfer gates. They do not become general HXMP memory, source truth, current live truth, or CMIS truth.

## Failure taxonomy

Canonical failure categories include factual/calculation errors, unsupported inference, missing evidence treated as zero, Proof Score/risk confusion, account/owner confusion, stale facts, source-conflict mishandling, excessive certainty, failure to request evidence, hallucinated facts, misunderstood questions, chain/temporal semantics errors, incomplete reasoning, authority-boundary violations, and execution-boundary violations.

Failure codes are observations for remediation/evaluation. They do not authorize durable retention.

## Training ledger

The SQLite ledger records training/evaluation state, not trusted source/live truth.

Accepted source-aware ledger behavior preserves historical `pyramid_runs` / `level_results` and adds source-mastery run/stage state. Historical results are mapped into source stages rather than rewritten.

The bound source-plan hash is immutable for a run. Failed autonomous attempts do not erase the completed source-stage prefix and are not promoted into authoritative passing source-stage results.

The final source-capstone pass is a separate ledger gate.

## Final source capstone

When every frozen required source stage has passed, a capstone-required source must pass a separate 60-question exam:

```text
49 cross-stage synthesis
10 integrity
1 final Boss
```

The capstone requires at least 90% overall accuracy or the higher applicable capability threshold, at least 90% integrity, Boss PASS, and zero critical failures.

Verified curriculum-scoped learned concepts may be routed only to capstone exercises supported by matching source-stage references; the final Boss may use verified concepts across the frozen plan. Passing the capstone is still a training/mastery result, not live-state authority.

## Dashboard

The Learning Command Center is read-only over the ledger/source plan/curriculum metadata and autonomous-training job state. It may show source title, stage progress, mapped capability, contributing chapters/pages, what is being learned, scores/failures/history, autonomous job activity, and capstone state.

It cannot modify the source plan, ledger, autonomous job, Learning System retention, CMIS/provider state, policy, or execution authority.

## Current Mastering Blockchain 4e source plan

The deterministic MB4E planner defines **14 required source stages**:

| Stage | Capability | Chapters |
|---:|---|---|
| 1 | Fundamentals | 1, 2 |
| 2 | Blockchain Mechanics | 1, 5, 6, 9, 13, 14 |
| 3 | Transactions | 6, 9, 13, 14 |
| 4 | Cryptography | 3, 4, 18 |
| 5 | Smart Contracts | 8, 11, 12 |
| 6 | Tokenomics | 15 |
| 7 | Liquidity | 21 |
| 8 | Market Structure | 21 |
| 9 | DeFi | 21 |
| 10 | Advanced DeFi | 19, 21 |
| 11 | On-chain Analysis | 7, 10, 12 |
| 12 | Risk Reasoning | 18, 19, 21 |
| 13 | Adversarial Analysis | 19 |
| 14 | Cross-chain Reasoning | 17, 19, 21 |

Excluded from this source: capabilities `12,15,16,18,19,20`.

Final source capstone: **required**.

Accepted **prebuilt** bank construction is currently present through **Stage 8 / Market Structure**:

- Stage 1 — Fundamentals;
- Stage 2 — Blockchain Mechanics;
- Stage 3 — Transactions;
- Stage 4 — Cryptography;
- Stage 5 — Smart Contracts;
- Stage 6 — Tokenomics;
- Stage 7 — Liquidity (PR #225);
- Stage 8 — Market Structure (PR #227).

Stages 9-14 are not yet separately accepted prebuilt repository banks. The accepted `roberta-train` controller can generate a missing later-stage bank from the exact selected source if its complete-source plan and source/provenance/evidence gates pass.

This is curriculum availability, not a claim that Roberta has mastered through Stage 8.

## Core rule

**The Pyramid measures source-grounded reasoning under strict provenance and authority boundaries. A source is mastered only by passing its frozen required stages and capstone; autonomous generation and training improve capability without relabeling generated material as truth.**
