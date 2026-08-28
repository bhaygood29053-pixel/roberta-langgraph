# Roberta Autonomous Source Mastery

Last reconciled: 2026-08-28 (America/New_York)

Status: **accepted on `main`; runtime hardening through merged PR #245**.

Roberta can run a source-mastery job from one selected local source without normal stage-by-stage operator intervention.

## One-command workflow

```bash
roberta-train --source "/path/to/source.pdf" --profile expert
```

Roberta hashes and durably registers the selected source, extracted pages, transcript, and chapter map; auto-matches an existing curriculum by immutable artifact SHA-256 when possible; resumes its active Pyramid/source-mastery run; and creates a new autonomous curriculum when no matching package exists.

For an explicitly selected existing package:

```bash
roberta-train \
  --source "/path/to/source.pdf" \
  --curriculum "$HOME/.roberta/curricula/<curriculum>" \
  --profile expert
```

The selected source bytes must match the existing package's independently trusted source artifact digest. A mismatch is a hard stop; the controller does not reinterpret or replace the package source.

## Profiles

- `standard`: up to 2 canonical stage attempts, 1 capstone attempt.
- `deep`: up to 3 canonical stage attempts, 2 capstone attempts.
- `expert` (default): up to 4 canonical stage attempts, 2 capstone attempts.
- `research`: up to 5 canonical stage attempts, 3 capstone attempts.

Profiles change retry depth, not provenance or passing standards.

## Autonomous stage loop

For every next source stage Roberta:

1. validates the immutable source and frozen source-mastery plan;
2. sends every source page, including front matter before the first detected chapter, through bounded planning chunks before asserting complete coverage;
3. uses any already-installed valid stage bank;
4. if the bank is missing, reads only the stage's declared source chapters;
5. asks the model for a bounded set of candidate learning targets;
6. requires a short verbatim evidence quote and exact page for every target;
7. deterministically rejects candidates whose quote is absent from that page or whose page is outside the cited chapter;
8. runs a separate support-verification pass, requires at least 20 accepted targets, and requires every assigned source chunk to retain a verified target;
9. expands accepted targets with deterministic question templates;
10. creates 50 integrity exercises and one Boss exercise;
11. validates the generated package and canonical 300-question selection before atomic publication;
12. runs the closed-book canonical exam;
13. on failure, derives only source-bound weak concepts, runs source-grounded practice, then a separate closed-source bounded candidate-memory retention lane, then a learned-concept transfer probe;
14. converts unpromoted candidate concepts into verified curriculum-scoped learned concepts only after perfect retention plus provenance binding, then promotes them only if transfer also passes perfectly;
15. retries the canonical exam with the verified learned-concept store, or records a passing source stage in the authoritative Pyramid ledger.

A failed autonomous attempt does **not** erase the completed source-stage prefix and is not promoted into the authoritative source-stage result table. A weakness report alone cannot trigger another identical retry: verified remediation must complete first. Only a passing canonical attempt advances source mastery.

The autonomous retention lane is intentionally **closed-source**, not source-free. Raw source excerpts, expected answers, grader material, and verified durable memory are excluded from the answer path. An unpromoted candidate lesson may be injected only as candidate memory; retention answers are bounded to that candidate principle so pretrained model knowledge cannot silently replace or contradict the lesson being tested. Candidate memory remains unverified and cannot become source truth, live truth, general durable memory, or execution authority. Perfect retention is required before provenance binding and transfer verification.

## Frozen-plan restart safety

For a newly created autonomous curriculum, the controller acquires the job lock and freezes the source-mastery plan before authoritative ledger binding.

The exact plan is written to durable job storage:

```text
.roberta/autonomous_training/<job_id>/source_mastery_plan.json
```

before the first generated curriculum stage is published. If target generation, package publication, or the process fails before the curriculum directory exists, the next invocation reloads this exact cached plan rather than generating a new nondeterministic model plan. Once a curriculum package exists, the job-cached plan and package plan must agree by plan hash or the controller fails closed.

## Final source capstone

When every frozen source stage passes, Roberta runs a separate 60-question source capstone:

- 49 cross-stage synthesis questions;
- 10 integrity questions;
- 1 final Boss.

The capstone answer lane can use only previously verified, curriculum-scoped learned concepts routed from the source-stage references represented by each synthesis question; the final Boss may use all verified concepts from the frozen plan. The capstone requires at least 90% overall accuracy (or the higher applicable capability threshold), at least 90% integrity, Boss PASS, and zero critical failures. Only then does the existing source-mastery ledger `mark_source_capstone_passed` contract mark the source mastered.

## Durable local state

Default source registry:

```text
~/.roberta/autonomous_sources/
```

Default training jobs:

```text
.roberta/autonomous_training/<job_id>/
```

Each job contains restart-safe `state.json`, append-only `events.jsonl`, the frozen job plan, checkpoint directories, remediation/retention/promotion evidence, and capstone results.

An operating-system advisory lock is acquired before plan creation and prevents two controller processes from advancing the same job concurrently. The kernel releases ownership automatically after crashes or termination; the persistent lock file records diagnostic PID metadata but is never unlinked for ownership changes.

Source-registry updates use a separate advisory transaction lock and unique atomic replacement files so concurrent imports cannot discard one another.

Check the latest state with:

```bash
roberta-train --status
```

## Learning Command Center

`roberta-pyramid-dashboard` reads autonomous state without mutating it and displays the selected source, profile, job status, current activity, source-stage progress, capability, chapters, question progress, and whether human intervention is required.

The dashboard does not advance or repair the job.

## Current MB4E runtime validation

Operator-local validation of the frozen *Mastering Blockchain, Fourth Edition* plan has passed Stages 9, 10, and 11. Stage 11 / On-chain Analysis passed canonical Attempt 3 with 99.33% accuracy, 100% integrity, Boss PASS, and zero critical failures. Stage 12 / Risk Reasoning is the next active stage.

Recent accepted runtime hardening includes:

- PR #241 — complete stage-bound Boss synthesis routing and lineage;
- PR #242 — candidate-only retention memory type and promotion boundary;
- PR #243 — bounded retention answers so pretrained knowledge cannot override the candidate principle;
- PR #244 — bounded regeneration when a source chunk produces zero deterministically valid targets;
- PR #245 — malformed optional `forbidden_inferences` metadata is discarded rather than allowed to erase an otherwise valid exact-evidence target.

These changes do not lower any canonical, retention, transfer, provenance, support-verification, or authority gate.

## Hard-stop rules

Autonomous training stops rather than fabricates or silently broadens authority when, for example:

- selected source bytes do not match an existing curriculum source binding;
- an immutable source/transcript/pages/chapter-map artifact changed;
- a PDF has no extractable text;
- required source chapters cannot be resolved;
- too few exact-evidence learning targets survive verification;
- a source chunk still yields zero valid exact-evidence targets after the bounded generation-attempt limit;
- any assigned generation chunk retains no independently accepted target;
- a package or provenance validation fails;
- an existing partial stage bank would need to be overwritten;
- the durable job plan and package plan disagree;
- learned-concept memory fails its existing verification contract;
- verified remediation cannot satisfy its gates;
- the stage exhausts the selected profile's autonomous attempts;
- the final source capstone exhausts its attempts.

Normal academic misses are handled automatically up to the profile limit. Provenance/integrity failures remain visible hard stops.

## Accepted scope versus future scheduler

The merged controller is autonomous after explicit source selection and is restart-safe. It is not yet a claim that Roberta runs an unrestricted always-on background learning daemon.

A generalized Learning Plane scheduler with explicit concurrency/model/token/question/source/retention budgets and load-aware Runtime throttling remains separate future operational hardening.

## Authority boundary

Autonomous source material remains static learning evidence only. It does not authorize current market state, wallet state, transactions, execution, governance changes, CMIS/provider claims, prompt/tool/policy mutation, Scout changes, or other live facts.

Generated curriculum installation hashes the Pyramid ledger before and after and refuses unexpected ledger mutation.

Verified curriculum-scoped learned concepts remain training knowledge, not source evidence, live truth, general HXMP memory, or operational trust.

## Core rule

**Roberta may autonomously master an explicitly selected static source under immutable provenance and verification gates; that autonomy ends at the learning boundary and never self-creates live or operational authority.**
