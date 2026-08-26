# Roberta Project Status — 2026-08-25

Status re-verified: 2026-08-26 (America/New_York)

## Accepted on `main`

- Core LangGraph platform phases through Phase 10 and post-Phase-10 evidence-aware UX are complete.
- X1 Scout and Solana Scout operate under the Chain Scout -> CMIS authority boundary.
- X1 Scout adoption/readiness of CMIS `concentration_change_intelligence/v1` is complete.
- Learning System Phases 1-9 are complete; Phase 10 retention specification is accepted but implementation remains blocked pending correction/re-review.
- Blockchain Reasoning Pyramid source-specific mastery architecture is accepted, with a frozen 14-stage Mastering Blockchain 4e plan and canonical 300-question stage contract.
- MB4E source banks are accepted through Stage 8 / Market Structure: Stage 7 / Liquidity merged in PR #225 and Stage 8 / Market Structure merged in PR #227.
- Paired Roberta PR #226 and CMIS PR #269 architecture/source-sync reconciliation is merged on both `main` branches.
- Controlled Execution remains locked/not started.

## Target Learning Plane architecture

The Learning System is being formalized as a separate automated background **Roberta Learning Plane**. This is an architectural target; it does not widen accepted runtime authority merely by being documented.

The plane is layered as Source Intake -> Provenance -> Curriculum -> Training -> Examination -> Remediation -> Retention -> Knowledge Promotion. It is fault-isolated from the user-facing Runtime and should run under explicit concurrency/model/question/source/retention budgets with load-aware throttling and durable restart-safe jobs.

Knowledge moves through explicit **candidate -> verified learned -> operationally trusted** states. Promotion is separately gated. Raw model output cannot write directly into trusted runtime memory.

Fresh accepted CMIS/provider facts remain above remembered/checkpointed live values and all static learned knowledge for freshness-sensitive state. The Learning Plane cannot modify Scouts, CMIS contracts, provider authority, production prompts/tools/policies, wallet permissions, human-approval semantics, or execution authority as a consequence of learning.

See `docs/LEARNING_PLANE_ARCHITECTURE.md`.

## Active/pending work

- PR #228 proposes the first end-to-end autonomous Learning Plane controller (`roberta-train --source <file>`). It preserves existing Levels 1-8 and can generically generate missing later-stage banks, but remains open/unaccepted until independent implementation/provenance/authority review and merge gates pass.
- Build/accept MB4E Stages 9-14 and the final source capstone before declaring source mastery.
- Fix Learning System Phase 10 implementation PR #136 before general retained lessons or broad operational-knowledge promotion can be accepted.
- Add bounded background scheduling, retention cycles, worker telemetry, and explicit knowledge-promotion gates as implementation work after architecture acceptance.
- Fix XenBlocks source exact-byte provenance before onboarding is accepted.
- Future X1Labs Intelligence Scout planning remains unaccepted until its authority/freshness routing issues are resolved and separately gated.

## CMIS dependency

Current accepted CMIS contract is `1.9.0`. The core Phase 11 intelligence foundation remains non-promoted. The separately accepted promoted Verified Intelligence wrapper is X1 `concentration_change_intelligence/v1`; classification, direct wallet relationships, and concentration-threshold alert evidence remain internal/read-only/non-promoted. `pre_trade_check` remains analysis-only and promoted services remain `execution_authorized=false`.

## Current assessment

Roberta's main development bottleneck is no longer basic orchestration. It is safely scaling learning automation without weakening provenance, retention, or live-fact authority. The next maturity step is to make source mastery autonomous and durable while keeping learning failures isolated from Runtime and keeping all live chain truth behind Chain Scout -> CMIS -> Provider.
