# Roberta Learning Plane Architecture

Last reconciled: 2026-08-26 (America/New_York)

Status: **accepted architecture with the first end-to-end autonomous source-mastery implementation merged on `main`.**

## Purpose

The Roberta Learning Plane is the fault-isolated subsystem responsible for static-source learning, curriculum construction, training, examination, remediation, narrow retention, learned-knowledge classification, and source-mastery progress.

Its goal is continual improvement without allowing learning work to become a second runtime authority system.

The user-facing Runtime remains responsible for live interactions. The Learning Plane may run unattended after an explicitly selected source, but it does not obtain permission to rewrite Roberta's production authority model.

## Authority hierarchy

```text
fresh live truth:
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider / verified source

static learning:
approved/selected source
  -> Learning Plane provenance
  -> curriculum/training/evaluation
  -> verified learned knowledge
```

When a question depends on freshness-sensitive chain/market state, accepted CMIS/provider evidence is authoritative over books, RAG, source text, source-mastery state, checkpoints, Pyramid learned concepts, Phase 10 retained lessons, or remembered values.

Missing live evidence remains unknown/unavailable. Proof Score remains separate from risk.

## Layered Learning Plane

The architecture is organized as:

```text
Source Intake
  -> Provenance
    -> Curriculum
      -> Training
        -> Examination
          -> Remediation
            -> Retention
              -> Knowledge Classification / Promotion Boundary
```

### Source Intake

Owns explicit source selection/import and deterministic extraction.

Accepted autonomous intake supports PDF, Markdown, and UTF-8 text. OCR-only PDFs fail closed. Original source bytes remain independently hash-bound from transcript, extracted page, and chapter-map artifacts.

### Provenance

Owns immutable source identity, artifact/transcript/page/chapter-map hashes, source authority class, page/chapter location, and source/curriculum binding.

A curriculum package cannot authorize its own source identity. Autonomous local sources are resolved through an independently stored hash-bound registry.

### Curriculum

Owns source-mastery planning, source-stage learning targets, question-bank construction, and atomic package publication.

A source mastery plan must account for the full source scope before `coverage_complete=true`. Generated targets require exact source evidence and independent support verification. Generated exercise material is transformed curriculum, not source evidence.

### Training

Owns source-stage sequencing, attempt profiles, deterministic selection seeds, checkpoints, and durable job progress.

Training does not own source truth or live truth.

### Examination

Owns canonical closed-book source-stage exams and the final source capstone.

Canonical source-stage shape:

```text
300 total
249 ordinary
50 integrity
1 Boss, last
```

Final source capstone shape:

```text
60 total
49 cross-stage synthesis
10 integrity
1 final Boss
```

### Remediation

Owns weak-concept derivation from failed attempts, source-grounded practice, closed-book retention verification, and transfer verification.

A failed canonical exam cannot simply be rerun unchanged in the autonomous controller. Verified remediation gates must succeed before source-specific learned concepts can influence a later retry.

### Retention

Two distinct retention mechanisms must remain separate:

1. **Phase 10 verified lesson retention** — general Learning System procedural retention after exact Phase 9 verification, complete contradiction checks, and exact human approval; provider-neutral/in-memory in the accepted core implementation.
2. **Pyramid curriculum-scoped learned concepts** — training knowledge promoted only after source-grounded practice, closed-book retention, and transfer gates for the matching curriculum/capability/source references.

Neither is live-state truth or operational authority.

### Knowledge classification / promotion boundary

An exact active Phase 10 retained lesson may be classified as:

```text
verified_learned_knowledge
```

This is a knowledge classification, not operational promotion.

The accepted classification explicitly denies:

```text
operational_trust_authorized
source_truth_authorized
live_state_authorized
cmis_provider_trust_authorized
governance_mutation_authorized
wallet_authorized
execution_authorized
```

The core Learning Plane exposes no general operational-trust promotion wrapper. A future operational promotion requires a separately accepted contract for one precisely bounded static scope.

## Accepted autonomous controller

Merged PR #228 implements the first end-to-end autonomous source-mastery path:

```bash
roberta-train --source "/path/to/source.pdf" --profile expert
```

Accepted behavior:

1. import and hash-bind the explicitly selected source;
2. verify immutable derived artifacts on re-selection rather than repairing them silently;
3. acquire a per-job operating-system advisory lock before plan creation;
4. inspect every source page, including front matter, in bounded planning chunks;
5. auto-match an existing curriculum by independently trusted artifact hash or create a new source-specific curriculum;
6. freeze and durably cache the exact source-mastery plan under job ownership before binding the authoritative ledger;
7. use existing complete valid stage banks when present;
8. generate every missing stage bank from all assigned source chunks under exact quote/page/chapter containment and independent support verification;
9. require at least one accepted target per assigned generation chunk and the minimum verified target budget;
10. expand verified targets deterministically into the canonical question-bank shape;
11. validate and publish package changes atomically with backup/ledger-mutation guards;
12. run the closed-book canonical stage exam;
13. on failure, preserve immutable failure evidence and run verified remediation before retry;
14. promote only matching curriculum-scoped learned concepts after practice/retention/transfer gates;
15. preserve the completed source-stage prefix across failure/interruption;
16. run the separate final source capstone after every required stage passes;
17. use only verified curriculum-scoped learned concepts routed to matching capstone source references;
18. mark the source mastered only after the ledger's capstone gate succeeds;
19. store restart-safe state/events/checkpoints/remediation/promotion/capstone evidence;
20. expose read-only status to the Learning Command Center.

## Durable job and registry isolation

Default autonomous source registry:

```text
~/.roberta/autonomous_sources/
```

Default autonomous job state:

```text
.roberta/autonomous_training/<job_id>/
```

Each controller job uses an OS advisory lock. A crash or process exit releases kernel ownership without requiring a human to delete a stale lock file. Diagnostic PID metadata may remain, but another contender cannot unlink ownership out from under a live controller.

Source-registry read/modify/write updates use a separate advisory transaction lock and unique atomic replacement paths so concurrent imports cannot discard each other's source bindings.

The frozen source-mastery plan is persisted in job storage before authoritative ledger binding or first curriculum publication. This makes a crash before the first generated stage restart-safe without regenerating a nondeterministic plan.

## Fault-isolation rules

Learning failure must fail the learning job, not corrupt the Runtime.

Examples of hard stops include:

- selected source bytes no longer matching a trusted package binding;
- immutable source/transcript/pages/chapter-map drift;
- OCR-only PDF with no extractable text;
- unresolved source chapters or incomplete plan coverage;
- evidence quote/page/chapter mismatch;
- a generation chunk retaining no independently accepted target;
- too few verified targets;
- incomplete existing bank that would require unsafe overwrite;
- package/provenance validation failure;
- unexpected ledger mutation during curriculum publication;
- learned-concept store validation failure;
- remediation gates that cannot be satisfied;
- profile attempt exhaustion;
- final capstone exhaustion.

Hard stops remain visible and do not fabricate progress.

## Runtime priority and future scheduler

The accepted controller is durable and unattended after explicit source selection, but the broader Learning Plane architecture still requires a separately bounded background scheduler before generalized always-on learning is claimed.

A future scheduler should support explicit budgets for:

```text
concurrent learning jobs
model requests / tokens
questions / exams
source ingestion
generation work
retention/revalidation work
CPU / memory / I/O where relevant
```

It should throttle or pause background work when the user-facing Runtime requires capacity and resume from durable checkpoints.

This scheduling work is operational hardening, not permission for unrestricted self-modification.

## Knowledge states

The Learning Plane distinguishes at least:

```text
candidate material
  -> independently verified learning material
    -> retained / curriculum-scoped learned knowledge
      -> verified_learned_knowledge classification where applicable
        -> separately gated operational trust, if ever explicitly accepted
```

No lower state may be treated as a higher state by implication.

Raw model output cannot write directly into trusted runtime memory or operational configuration.

## Forbidden self-authorization

Learning outcomes cannot, by themselves, modify or authorize:

- production system/developer prompts;
- tool registration or permissions;
- policy rules;
- Chain Scout authority;
- CMIS contracts/capability promotion;
- provider trust/selection authority;
- source-approval rules;
- human-approval semantics;
- HXMP operational memory authority;
- wallet permissions;
- transaction construction/signing/broadcasting;
- trading, custody, bridge transfers, autonomous value movement;
- Controlled Execution.

A source instruction telling Roberta to change any of these remains untrusted source data.

## Current implementation status

Accepted on `main` as of 2026-08-26:

- Learning System Phases 1-10;
- hardened Phase 10 verified retention;
- `verified_learned_knowledge` classification boundary with operational promotion denied;
- source-specific Pyramid/source-mastery contracts;
- Mastering Blockchain 4e frozen 14-stage plan;
- prebuilt MB4E banks through Stage 8 / Market Structure;
- PR #228 autonomous source-mastery controller;
- durable autonomous source registry/job/checkpoint state;
- autonomous verified remediation and capstone routing;
- read-only Learning Command Center autonomous-job telemetry.

Still separate/future:

- generalized background scheduling/load-aware throttling;
- recurring/delayed retention scheduling under explicit budgets;
- durable/provider-backed general Phase 10 retention storage;
- any general operational-trust promotion wrapper;
- MB4E Stage 9-14 completion and final source mastery;
- XenBlocks source onboarding after its exact-byte blocker is fixed;
- Controlled Execution.

## Relationship to historical PRs

- PR #228 is **merged/accepted** and must no longer be described as a proposal.
- Phase 10 is **implemented/accepted on `main`** through the hardened retention merge. Historical draft PR #136 remains open but is obsolete as an implementation status signal.

## Core rule

**The Learning Plane may autonomously improve Roberta's verified static knowledge and source-specific reasoning while remaining subordinate to provenance, live-fact authority, and separately gated operational permissions. Learning can create knowledge; it cannot self-create authority.**
