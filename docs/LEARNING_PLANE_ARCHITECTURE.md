# Roberta Learning Plane Architecture

Last reconciled: 2026-08-25 (America/New_York)

## Purpose

Roberta's Learning System is a separate automated background **Learning Plane**. It may study approved static sources, construct source-grounded curricula, train, examine, remediate, retest, and perform retention work without blocking the user-facing Roberta runtime.

The Learning Plane improves knowledge and reasoning. It does **not** acquire authority to modify Roberta's runtime architecture, prompts, tools, Scouts, CMIS contracts, wallet permissions, provider authority, or execution permissions.

## System boundary

```text
User
  -> Roberta Runtime
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified live source

Approved static sources
  -> Roberta Learning Plane
    -> candidate knowledge
      -> verified learned knowledge
        -> separately gated operational knowledge

Roberta Runtime may consume accepted learned knowledge, but freshness-sensitive facts remain governed by Chain Scout -> CMIS -> Provider.
```

CMIS remains outside the Learning Plane and remains the deterministic authority for verified freshness-sensitive facts, evidence, risk, capability state, and bounded analysis-only pre-trade calculations.

## Layered workers

The Learning Plane is intentionally layered rather than implemented as one unrestricted autonomous loop:

1. **Source Intake Worker** — accepts explicitly approved source bytes, hashes them, registers immutable source identity, and rejects unsupported/unsafe source forms.
2. **Provenance Worker** — verifies exact source identity, locator/page boundaries, evidence containment, and source-scope contracts.
3. **Curriculum Worker** — maps source scope to a frozen source-mastery plan and constructs or proposes source-grounded learning targets/question banks under deterministic validation.
4. **Training Worker** — runs bounded source-plan-bound practice/training jobs without mutating live-fact authority.
5. **Examination Worker** — runs canonical exams and records immutable attempts/results.
6. **Remediation Worker** — derives source-grounded weakness/remediation work and fresh practice while preserving lineage.
7. **Retention Worker** — schedules delayed closed-book retention checks and sends weakened concepts back through remediation.
8. **Knowledge Promotion Worker** — promotes only independently verified knowledge through explicit state transitions; it cannot promote runtime authority or execution capability.

Each layer produces auditable artifacts consumed by the next layer. Raw model output never writes directly into trusted runtime memory.

## Knowledge states

Learning artifacts use explicit trust states:

- **Candidate knowledge** — encountered/proposed but not independently proven.
- **Verified learned knowledge** — provenance-bound and independently verified through accepted learning/exam/retention gates.
- **Operationally trusted knowledge** — separately promoted for use by Roberta's runtime within a defined static-knowledge scope.

Promotion between these states is explicit and auditable. `verified_for_learning` alone does not imply general operational trust.

## Freshness and authority precedence

For freshness-sensitive state:

```text
fresh accepted CMIS/provider evidence
  > remembered/checkpointed live values
  > operationally trusted static learned knowledge
  > verified learned knowledge
  > candidate knowledge
```

Missing evidence remains unknown/unavailable, never zero. Proof Score remains separate from risk. Static source material never becomes current chain state merely because Roberta mastered it.

## Background scheduling and budgets

"Downtime training" means background scheduling, not an unrestricted idle-time self-modification loop. Runtime user work and accepted Scout/CMIS work have priority over learning jobs.

The scheduler must support bounded resource policies such as:

- maximum concurrent learning jobs;
- model/token budget;
- question/exam budget;
- source-ingestion budget;
- retention-test budget;
- pause/throttle under runtime load;
- durable checkpoints and restart-safe job state.

Learning failures must not impair the user-facing runtime.

## Retention lifecycle

Verified learning is revisited on scheduled retention horizons. Exact intervals are policy/configuration rather than architectural authority, but the lifecycle is:

```text
learn -> verify -> retain -> delayed retention check
                    ^              |
                    |              v
                    +-- remediate <-+
```

A retention failure weakens or revokes the affected learned-knowledge state according to the accepted lifecycle contract; it does not silently preserve stale confidence.

## Autonomous training controller

PR #228 is the current implementation proposal for end-to-end `roberta-train --source <file>` automation. Its source hashing, generic bank generation, evidence validation, exams, remediation, durable jobs, and capstone concepts fit inside this Learning Plane.

PR #228 remains **pending/unaccepted** until review, CI, authority review, and merge gates pass. Acceptance of the Learning Plane architecture does not automatically accept every implementation detail of #228.

## Hard prohibitions

The Learning Plane may autonomously improve knowledge, generate bounded curricula, train, remediate, and test retention under accepted contracts. It may **not** autonomously:

- alter the User -> Roberta -> Chain Scout -> CMIS -> Provider hierarchy;
- manufacture or promote freshness-sensitive chain facts;
- bypass CMIS or call providers as a replacement live-truth authority;
- modify Scout or CMIS capability contracts;
- promote a new public intelligence service;
- change wallet permissions or human-approval semantics;
- authorize trading or transaction execution;
- unlock Controlled Execution;
- silently rewrite production prompts/tools/policies as a consequence of learning.

Any such change remains a separate engineering/architecture/contract decision.

## Current implementation status

Accepted today:

- Learning System Phases 1-9;
- source-specific Blockchain Reasoning Pyramid architecture;
- MB4E frozen 14-stage source plan;
- MB4E banks through Stage 8 / Market Structure;
- canonical 300-question new-stage exam contract;
- source-grounded remediation, provenance, and learned-concept gates.

Pending:

- Learning System Phase 10 verified lesson retention implementation (#136 remains blocked pending correction/re-review);
- autonomous Learning Plane controller implementation (#228 remains open/unaccepted);
- MB4E Stages 9-14 and final source capstone.

Controlled Execution remains locked/not started.