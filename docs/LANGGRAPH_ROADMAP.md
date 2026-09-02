# ROBERTA — Verified On-Chain Intelligence Roadmap

Last reconciled: 2026-08-30 (America/New_York)

Status source: accepted code and contracts on `main`. Open PRs are not current truth unless explicitly identified as pending.

## Product identity

The canonical public-facing product name is **ROBERTA — Verified On-Chain Intelligence**. The former working name **X1 Intelligence Service** is retired. X1 Scout, Solana Scout, and CMIS remain architectural component names; the repository/package name `roberta-langgraph` remains a technical identifier. See [`PRODUCT_IDENTITY.md`](./PRODUCT_IDENTITY.md).

## Canonical authority model

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Roberta owns orchestration, policy coordination, specialist selection, cross-chain synthesis, learning coordination, approval boundaries, and the final user-facing answer. Chain Scouts own chain-specific planning and interpretation. CMIS owns deterministic freshness-sensitive blockchain/market facts, evidence, Evidence Receipts, Proof Scores, risk, capability state, historical intelligence, and bounded analysis-only pre-trade calculations.

Fresh accepted CMIS/provider evidence overrides books, RAG, source-mastery state, Pyramid checkpoints, learned concepts, retained lessons, and remembered live values for freshness-sensitive facts. Missing evidence remains unknown/unavailable; it is never converted into zero or a model guess. Proof Score remains separate from risk.

Controlled Execution remains locked/not started. No Learning System result, CMIS result, Scout result, pre-trade PASS, policy decision, or human approval grants transaction construction, signing, broadcasting, custody, trading, bridge transfer, or autonomous value movement.

## Current accepted platform state

Accepted on `main`:

- core LangGraph platform work through Roberta Phase 10 plus the post-Phase-10 evidence-aware user experience;
- X1 Scout decision-production readiness under the accepted CMIS boundary;
- Solana Scout read-only readiness for its accepted surface;
- X1 Scout adoption of CMIS `concentration_change_intelligence/v1`;
- X1 Scout adoption of the current CMIS `1.13.0` contract boundary, including CMIS `1.10.0` all-available history, CMIS `1.11.0` exact-mint X1 identity, bounded CMIS `1.12.0` verified-provider historical price-backfill semantics, and bounded X1 `instant_x1_scan/v1` composition;
- Learning System Phases 1-10;
- fail-closed `verified_learned_knowledge` classification with no general operational-trust promotion wrapper;
- source-specific Blockchain Reasoning Pyramid architecture and source-mastery ledger;
- Mastering Blockchain 4e frozen 14-stage source plan;
- accepted prebuilt MB4E banks through Stage 8 / Market Structure;
- operator-local MB4E source mastery complete: the authoritative source-plan-bound ledger records all 14 required stages passed plus the required final capstone;
- autonomous source-grounded Learning Plane controller from PR #228;
- read-only Learning Command Center telemetry for source mastery and autonomous-training jobs;
- authoritative autonomous-training telemetry/diagnostics from private `roberta-core` PR #9, with ledger-backed mastery/completion reconciliation, validated frozen-plan identity checks, controller/event diagnostics, and explicit `execution_authorized=false`.
- autonomous remediation hardening through PRs #241-#243: complete Boss synthesis routing, candidate-only retention memory, and bounded candidate-memory retention;
- autonomous target-generation hardening through PRs #244-#245: bounded zero-valid-target retries and fail-closed normalization of malformed optional defensive metadata.

`main` includes the hardened Phase 10 verified-retention implementation and the separate knowledge-classification boundary. The old draft PR #136 remains open historical work and is no longer the implementation source of truth.

## Learning System — accepted Phases 1-10

The accepted Learning System pipeline is:

1. **Source ingestion** — exact approved bytes/source identity are preserved and hashed.
2. **Structure detection** — deterministic document structure is extracted without inventing source semantics.
3. **Structure-aware chunking** — evidence chunks retain source location and lineage.
4. **Indexing** — lexical indexing is accepted; optional embeddings remain an implementation choice behind the same evidence boundaries.
5. **Retrieval** — deterministic source filtering/ranking and benchmark foundations.
6. **Grounding** — evidence packets and citations are bound to retrieved source material.
7. **Evaluation** — answers are independently evaluated against evidence-aware criteria.
8. **Reflection** — provisional lessons/candidates are generated without self-authorizing trust.
9. **Verification** — candidate lessons are independently rechecked and may become `verified_for_learning`.
10. **Verified retention** — only exact eligible Phase 9 results can enter the narrow, provenance-bound retention contract after complete contradiction checks and exact human approval.

Phase 10 is accepted as a deterministic provider-neutral/in-memory retention layer. It does **not** authorize HXMP writes, source truth, live-state truth, CMIS/provider trust, governance mutation, wallet authority, or execution.

The accepted Learning Plane classification boundary can classify an exact active retained lesson as:

```text
verified_learned_knowledge
```

That classification preserves the retention/verification/source/approval lineage and explicitly sets `operational_trust_authorized=false`. General operational promotion remains unavailable until a separately reviewed wrapper is accepted.

## Autonomous Learning Plane — accepted

PR #228 merged on 2026-08-26 and is now accepted `main` behavior.

One selected PDF, Markdown, or UTF-8 text source can be handled by:

```bash
roberta-train --source "/path/to/source.pdf"
```

The controller can:

- hash and durably register the selected source, transcript, extracted pages, and chapter map;
- reject OCR-only PDFs and provenance mismatches;
- inspect every source page, including front matter, before declaring plan coverage complete;
- auto-match an existing curriculum by immutable artifact hash or create a source-specific curriculum;
- freeze and durably cache the exact source-mastery plan before authoritative ledger binding;
- generate missing stage banks from every assigned source chunk under exact quote/page/chapter validation and independent support verification;
- publish validated curriculum changes atomically while guarding against unexpected ledger mutation;
- run 300-question canonical stage exams automatically;
- derive source-bound weaknesses after failure;
- require source-grounded practice, closed-source bounded candidate-memory retention, provenance-bound `LearnedConcept` conversion, and transfer verification before learned-concept persistence/promotion and retry;
- preserve failed attempts as immutable evidence without erasing the completed source-stage prefix;
- run a separate 60-question final source capstone;
- resume from durable state after interruption with advisory locking and source-registry transaction safety;
- expose authoritative read-only job/status telemetry to the Learning Command Center, reconciling durable state with source-mastery ledger evidence and surfacing deterministic conflicts instead of trusting stale job JSON.

The accepted controller is autonomous source mastery, **not** unrestricted self-modification. It cannot change Roberta prompts, tools, policies, Scouts, CMIS contracts, provider authority, human-approval semantics, wallet permissions, or execution permissions as a consequence of learning.

A broader background scheduler with explicit concurrency/model/token/question/source/retention budgets and load-aware throttling remains a separate operational hardening milestone. The current accepted controller is durable and unattended after source selection, but that does not imply an unrestricted always-on self-modification daemon.

### Authoritative autonomous-training telemetry

Private `roberta-core` PR #9 is accepted as protected-runtime behavior, squash-merged as `08f693ae820b073435fd3b2388bc8f0f13cb3ab0`.

The telemetry contract is `roberta-autonomous-training-telemetry/v1`. It is read-only and non-authorizing. Source mastery/completion claims are reconciled against the authoritative source-mastery ledger; durable job state remains operational state. The reader validates the frozen source-mastery plan for package-bound source identity, reports controller/event/remediation/checkpoint/resume information, and fails closed on true identity conflicts.

Exact-head operator validation passed with 20 focused tests, 20 full private functional tests, 1083 retained public/private split-runtime tests (5 deselected), and a real MB4E read-only proof showing mastered 14/14 plus capstone, clean diagnostics, `telemetry.authoritative=true`, `execution_authorized=false`, and unchanged state/ledger hashes.

## Blockchain Reasoning Pyramid

The reusable 20-level Pyramid is a global capability taxonomy. Each source receives a frozen source-specific plan containing only the capabilities materially supported by that source.

New canonical source-stage attempts use:

```text
300 questions
249 ordinary
50 integrity
1 Boss, last
```

Historical 1,000-question Level 1/2 runs remain immutable audit history and are reconstructed only through explicit legacy paths.

For *Mastering Blockchain, Fourth Edition*, the frozen plan requires 14 source stages mapped to global capabilities:

```text
1,2,3,4,5,6,7,8,9,10,11,13,14,17
```

Explicitly excluded for this source:

```text
12,15,16,18,19,20
```

Accepted prebuilt curriculum-bank construction reaches:

- Stage 1 — Fundamentals;
- Stage 2 — Blockchain Mechanics;
- Stage 3 — Transactions;
- Stage 4 — Cryptography;
- Stage 5 — Smart Contracts;
- Stage 6 — Tokenomics;
- Stage 7 — Liquidity (PR #225);
- Stage 8 — Market Structure (PR #227).

Stages 9-14 do not yet exist as separately accepted prebuilt repository banks. The accepted autonomous controller may generate missing later-stage banks at runtime from the exact selected source under its validation contract. Generated bank availability still does not equal mastery.

The operator-local authoritative MB4E source-mastery ledger now satisfies the complete frozen plan: **14 of 14 required source stages passed and the required final source capstone passed**. Stage 14 / Cross-chain Reasoning passed canonical Attempt 3 at **99.33% accuracy**, **100% integrity**, **Boss PASS**, and **0 critical failures**. This is runtime mastery evidence; it does not relabel runtime-generated Stages 9-14 as separately accepted prebuilt repository banks.

During post-mastery validation, the pre-fix controller created an accidental fresh run because it searched only for an active run and did not treat a verified mastered run as terminal. That was a resume-safety/controller defect, not a source-knowledge failure. Private `roberta-core` PR #8 (`d86aff9617c975fc9420847cd1d7f8e74d9d7da9`) makes verified mastery terminal/idempotent, requires the exact passed-stage prefix plus capstone, fails closed on mastered/active split-brain or ledger identity mismatch, and repairs stale durable state instead of replaying completed stages. Private PR #7 (`2ba2873878dc88ab58b81efbaff4cecbb91a9f68`) separately hardened Stage 14 support-verified target retries without relaxing evidence or mastery gates.

**MB4E source mastery is closed. Do not start a new MB4E training run for learning purposes unless the source/mastery contract is intentionally changed under a new reviewed plan.**

## Static source registry

Accepted curated static sources currently include:

- X1 Blockchain Whitepaper v1.0;
- XDEX documentation snapshot;
- XEN Litepaper v1.7;
- XEN Torrent / XENFT Litepaper v0.3;
- XONE ERC20 Token v4;
- *Mastering Blockchain, Fourth Edition* under its exact external transcript integrity contract;
- Solana whitepaper v0.8.13.

The autonomous source registry additionally provides an accepted mechanism for explicitly selected local PDF/Markdown/text sources to receive an independent hash-bound `local_<digest>` trusted binding. That mechanism does not silently add a local source to the curated named catalog and never creates live-state authority.

XenBlocks PoW documentation PR #141 remains open/unaccepted. Its current review blocker is the exact-byte Phase 1 rule: the canonical ingested artifact still represents the LF-normalized derivative instead of the exact uploaded CRLF bytes. Until fixed and merged, XenBlocks must not be listed as accepted.

## CMIS public/private runtime migration

CMIS has completed its six-phase public-shell/private-core migration and historical Git cleanup. The public package boundary now fails closed when the required protected private core is unavailable; no public reconstruction fallback is accepted. This changes deployment/source protection, not the Roberta → Scout → CMIS → Provider authority model.

## CMIS synchronization

Current accepted CMIS capability contract is `1.13.0`.

The existing X1 `historical_compare` service is accepted for `window`, `all_available`, and `all_available_pair` use through X1 Scout. All-available modes require the service-specific CMIS `>=1.10.0` guard and exact limitation semantics. Pair requests preserve the second user/trusted-context asset explicitly and issue one CMIS pair-history call; Roberta does not recompute two independent histories. For CMIS `>=1.12.0`, Scout reliance additionally requires the accepted price-only provider-backfill limitations: provider source independence, archive completeness, continuous coverage, historical USD-stable peg behavior, and complete asset lifetime remain unverified. Returned lifetime/continuous-coverage limits remain authoritative.

The core Phase 11 `intelligence_foundation` remains internal/non-promoted. The separately accepted X1 wrapper is exactly `concentration_change_intelligence/v1`, read-only, with `execution_authorized=false`.

Classification, direct wallet-relationship evidence, and concentration-threshold alert evidence remain internal/read-only/non-promoted. There is no accepted next public intelligence/alert promotion by implication.

## Retired transport work

The ChatGPT Gateway v1 and MCP transport edge introduced by PRs #262 and #266
were removed by project decision on 2026-08-30. They are not part of the
current Roberta architecture or deployment plan. Issue #269 is closed as not
planned.

The pre-existing loopback Roberta HTTP bridge at `/v1/roberta` remains for
local integrations such as MoltGrid/Signal; it is not an external ChatGPT
gateway. Any future external gateway or MCP transport requires a new explicit
architecture and security review.

## Human ROBERTA + Machine ROBERTA product architecture — planned

The X1 productization track will expose **one ROBERTA intelligence core through two presentation faces** rather than creating separate truth systems.

```text
                     User / client
                         |
              +----------+----------+
              |                     |
        Human ROBERTA         Machine ROBERTA
              |                     |
              +----------+----------+
                         |
                      ROBERTA
                policy/orchestration
                         |
                     Chain Scout
                         |
                       CMIS
                         |
             verified provider/source
```

The architectural rule is:

> **Human ROBERTA makes verified intelligence understandable. Machine ROBERTA makes the same intelligence programmable. Neither face becomes a second fact authority.**

### Shared canonical decision layer

Before the two faces diverge in presentation, Roberta should introduce a shared internal **Canonical ROBERTA Decision Object**. It must carry the already-established decision basis without recomputing CMIS facts.

Planned fields include:

- request and exact subject identity;
- user intent / workflow;
- recommendation or blocker;
- stable machine reason codes;
- accepted facts returned through Scout -> CMIS;
- deterministic risk as returned by the accepted contract;
- evidence quality / Proof Score summary without collapsing proof into risk;
- missing evidence and explicit unknowns;
- historical limitations;
- policy identity/version;
- capability state;
- `execution_authorized=false`.

Human and Machine renderers must be tested against the same canonical object. A release should fail if they disagree on underlying facts, ratios, policy state, risk, missing evidence, timestamps, or execution authority.

### Human ROBERTA

Human ROBERTA is the default individual-trader/research experience.

Product rule:

> **Answer first. Evidence underneath.**

The default answer should avoid requiring users to understand Evidence Receipts, capability manifests, route-evidence contracts, semantic verification, exact-mint normalization, or other internal engineering vocabulary.

Planned answer order:

1. recommendation / conclusion / blocker;
2. 2-4 most important evidence-backed reasons;
3. risk, only when a dedicated accepted risk contract supports it;
4. human-readable evidence quality;
5. important missing evidence;
6. optional **View Evidence** drill-down.

Human recommendation labels may include `BUY CANDIDATE`, `WAIT`, `CAUTION`, `AVOID`, `BLOCK`, and `INSUFFICIENT EVIDENCE`, but these are Roberta presentation/policy outputs and must never be relabeled as CMIS market facts.

Human evidence language should map technical states into understandable wording such as:

- **Strong evidence**;
- **Moderate evidence**;
- **Limited evidence**;
- **Insufficient evidence**;
- **Stale evidence**;
- **Partially verified**.

Advanced users should be able to expand the same result into market, trade, risk, history, concentration, freshness, source, Evidence Receipt, Proof Score, disagreement, and unresolved-field detail without switching to a separate product.

### Human flagship workflows

The X1 Human ROBERTA product should converge on seven primary workflows:

1. **SCAN** — “Analyze this token.” Consume accepted `instant_x1_scan/v1` plus only separately accepted supplemental Scout/CMIS evidence.
2. **TRADE CHECK** — “Can this market handle my $500 buy?” Present deterministic trade-size policy, route-scoped price impact/fee evidence where accepted, slippage status, risk, and missing execution evidence.
3. **COMPARE** — “Compare AGI and XNT.” Use first-class CMIS-returned current/history evidence and preserve per-dimension differences instead of inventing a universal score.
4. **WHAT CHANGED?** — explain verified changes in price, liquidity, activity, concentration, token burns, risk/evidence quality, and important unknowns.
5. **BURN** — “How much of this token has been burned?” After CMIS Issue #368 is explicitly promoted through X1 Scout, present cumulative verified-observed burns plus trailing **24h, 7d, and 30d** burn amounts/event counts and the **period-over-period percentage change for each window** (current 24h vs prior 24h, current 7d vs prior 7d, current 30d vs prior 30d), with exact coverage/completeness limits. Never relabel partial observed coverage as definitive lifetime burn or an undefined zero-denominator comparison as an infinite percentage.
6. **EARLY WARNING** — surface only separately accepted warning contracts for liquidity, concentration, activity, identity, evidence degradation, burn-rate changes where supported, or future execution-quality signals; never infer manipulation/intent by implication.
7. **X1 BRIEF** — synthesize accepted ecosystem/network evidence into one coherent daily/periodic X1 intelligence brief.

### Human personalization and policy

Future Human ROBERTA may support user decision policies such as:

- maximum trade/notional-to-liquidity ratio;
- minimum verified liquidity;
- minimum evidence strength;
- minimum verified-history depth;
- authority/mutability exclusions;
- user watchlists and saved comparison sets.

Personal policy may change **the user's decision threshold**, but it may not change CMIS facts, verification state, Proof Score, risk semantics, or source provenance.

### Machine ROBERTA

Machine ROBERTA is the structured intelligence interface for agents, DApps, developers, monitoring systems, wallets, research systems, and other AI clients.

Product rule:

> **Structure first. Evidence attached.**

Machine ROBERTA belongs to the Roberta layer, not CMIS. CMIS remains the deterministic verification backend. Machine ROBERTA composes accepted Scout/CMIS outputs into stable versioned machine contracts without creating a second fact layer.

Planned machine envelope:

```json
{
  "schema": "roberta_intelligence/v1",
  "request_id": "...",
  "chain": "x1",
  "subject": {},
  "decision": {},
  "facts": {},
  "risk": {},
  "history": {},
  "evidence": {},
  "limitations": [],
  "policy": {},
  "capabilities": {},
  "execution": {
    "authorized": false
  }
}
```

Machine output must preserve explicit unavailable/null states. Missing execution slippage, history, holder, concentration, or other evidence must never be serialized as zero/false merely to simplify client logic.

With CMIS 1.15.0 `burn_intelligence/v1` accepted, Machine ROBERTA preserves Burn Intelligence as structured canonical evidence rather than prose, including exact mint, cumulative verified-observed burn, 24h/7d/30d burned amounts and event counts, **current-vs-prior equal-period absolute and percentage changes**, exact prior-period denominators, comparison-state/reason codes, coverage bounds for both periods, as-of time, unresolved timed events, and `lifetime_total_burn_verified`.

Stable reason codes should be preferred over prose for machine policy. Initial candidates include:

- `TRADE_SIZE_LOW`;
- `TRADE_SIZE_MODERATE`;
- `TRADE_SIZE_HIGH`;
- `TRADE_SIZE_BLOCK`;
- `LIQUIDITY_UNVERIFIED`;
- `PRICE_STALE`;
- `PRICE_IMPACT_UNAVAILABLE`;
- `EXECUTION_SLIPPAGE_UNAVAILABLE`;
- `HISTORY_INCOMPLETE`;
- `IDENTITY_CONFLICT`;
- `PROVIDER_DISAGREEMENT`;
- `RISK_UNKNOWN`.

Exact enums require their own accepted schema review before becoming compatibility commitments.

### Machine capability discovery and evidence depth

Machine clients must not assume a feature exists. Roberta should expose a versioned capability-discovery surface derived from accepted Scout/CMIS capability state.

Machine responses should support at least two evidence depths:

- **Standard** — decision, facts, risk, evidence summary, limitations, capability state;
- **Full Evidence** — Evidence Receipts, Proof Scores, exact source provenance, verification methods, freshness, scope, disagreements, and accepted contract identities.

### Human/Machine consistency gate

For the same request and canonical evidence, Human and Machine ROBERTA must preserve the same:

- exact asset;
- numeric facts;
- policy/version;
- notional-to-liquidity ratio;
- risk;
- evidence state;
- missing/unknown evidence;
- timestamps/freshness;
- historical limitations;
- execution denial.

The Human renderer may simplify language. It may not simplify away material uncertainty or create facts absent from the Machine/canonical representation.

### No universal ROBERTA score

Do not collapse the product into a single “ROBERTA score.”

Prefer separate dimensions such as:

- market depth;
- activity;
- historical evidence;
- concentration;
- deterministic risk;
- evidence quality;
- execution evidence.

Roberta may synthesize those dimensions into a recommendation while keeping the underlying axes inspectable.

### Performance and reliability

Human ROBERTA should feel fast enough for interactive use, while Machine ROBERTA must be stable enough for programmatic dependence.

Track at minimum:

- median and p95 end-to-end latency;
- provider latency;
- CMIS latency;
- Scout latency;
- Roberta orchestration/render latency;
- stale/unavailable-field rate;
- provider disagreement rate;
- machine schema/error rate.

Machine contracts should add versioning, deterministic errors, request IDs, idempotent read semantics where applicable, rate-limit guidance, capability discovery, and operational status/observability before broad external release.

### Authentication and access direction

Future access separation may include:

- Human: sessions, saved policies, watchlists, preferences;
- Machine: API keys or agent identity, scoped permissions, quotas, and audit logs.

Authentication, subscriptions, or premium access must never alter blockchain truth, verification, Proof Score, deterministic risk, or evidence semantics.

### Product/access model direction

Potential future packaging may include Human Free, Human Pro, Developer, Agent, and ecosystem/enterprise tiers. This remains a commercialization concern above the evidence layer. Payment or access policy must never sit inside CMIS fact authority.

### Implementation sequence

Recommended Roberta-side sequence:

1. Canonical ROBERTA Decision Object;
2. Human SCAN;
3. Human TRADE CHECK;
4. Machine SCAN contract;
5. Machine TRADE CHECK contract;
6. COMPARE;
7. WHAT CHANGED?;
8. Advanced Human Evidence View;
9. consume accepted CMIS Token Burn Intelligence from Issue #368 and add Human BURN + Machine burn fields;
10. consume accepted CMIS realized-slippage/statistical execution evidence when promoted;
11. consume accepted Discovery Ledger;
12. consume accepted Early Warning services;
13. X1 Brief;
14. agent-scale Machine ROBERTA API / SDK and monitoring integrations.

This sequence is roadmap intent only. A downstream CMIS dependency remains unavailable until its explicit CMIS public-service / Scout-reliance contract is accepted.

## Near-term roadmap

### Strategic priority — X1 productization

Roberta's primary near-term product objective is to become the leading verified X1 intelligence analyst. X1 productization is the main cross-project priority. Roberta should turn accepted X1 Scout + CMIS capabilities into a coherent, evidence-aware user experience without bypassing the canonical authority path:

```text
User
  -> Roberta
    -> X1 Scout
      -> CMIS
        -> X1 Provider / verified source
```

Solana remains an accepted read-only specialist surface for maintenance, regression coverage, and portability. Learning Plane hardening remains important supporting infrastructure, but it is not the primary product objective while X1 productization is underway.

### 1. Productize the X1 intelligence experience

- make X1 the flagship Roberta intelligence experience;
- use X1 Scout as the chain-specific interpretation layer for all freshness-sensitive X1 investigations;
- consume bounded CMIS `instant_x1_scan/v1` through X1 Scout and present its verified identity, market, tokenomics, local-history, deterministic-risk, and evidence-quality fields clearly;
- preserve CMIS statuses, timestamps, Evidence Receipts, Proof Scores, limitations, warnings, and explicit unknowns rather than smoothing partial evidence into confident prose;
- build the user-facing X1 workflows around **Instant X1 Scan**, **Compare**, **Token Burn Intelligence (total verified-observed + 24h/7d/30d)**, **Discovery / first-observation history**, **Early Warning**, and **X1 ecosystem/network brief** outputs as their underlying CMIS contracts become accepted;
- keep Proof Score separate from risk and never turn a risk `PASS` into execution permission;
- prefer one coherent X1 intelligence response over disconnected specialist dumps.

### 2. Harden Roberta ↔ X1 Scout ↔ CMIS product integration

- keep the live capability manifest and accepted service-specific minimum contracts authoritative for Scout dispatch;
- adopt new X1 CMIS services only after their explicit public-service / Scout-reliance gates are accepted;
- do not call X1 providers directly from Roberta as a trust shortcut;
- preserve exact-mint identity and all-available-history limitations from CMIS without recomputation;
- support first-class deterministic X1 comparisons using CMIS-returned history/evidence rather than constructing a second fact layer in Roberta;
- consume accepted first-class CMIS Token Burn Intelligence through X1 Scout and the Canonical Decision Object without recomputation; prepare Discovery Ledger and Early Warning only after their separate contracts are accepted;
- continue evidence-aware UX work so unavailable, partial, ambiguous, stale, or unverified data remains visible to the user.

### 3. Keep the Learning Plane operationally strong as a supporting track

- MB4E authoritative runtime mastery is complete: 14/14 required stages plus the final capstone;
- do not replay MB4E merely to exercise the controller; verified mastery is terminal/idempotent under the accepted mastered-run safety contract;
- exercise `roberta-train` against new approved sources when that improves X1 intelligence quality or validates Learning Plane reliability;
- preserve deterministic provenance/integrity hard stops;
- operate the accepted authoritative telemetry/diagnostics surface and extend it only when evidence shows a concrete gap;
- add bounded background scheduling/load-throttling only under a separate accepted contract;
- define delayed/recurrent retention scheduling without weakening the Phase 10 authority boundary;
- keep runtime-generated source mastery, retained lessons, and learned concepts subordinate to fresh Scout -> CMIS -> Provider evidence for freshness-sensitive X1 facts.

### 4. Maintain Solana as the secondary portability/read-only track

- preserve accepted Solana Scout read-only capability and regression coverage;
- keep Solana chain/provider semantics isolated from X1;
- use Solana work when it materially strengthens shared Scout/CMIS abstractions or cross-chain portability;
- defer broader Solana product expansion while X1 productization remains the flagship priority.

### 5. Repository and specialist housekeeping

- PR #136 remains an obsolete draft relative to the hardened Phase 10 implementation now on `main`; close/supersede it when repository housekeeping is performed;
- PR #141 remains blocked until its exact-byte ingestion issue is fixed and re-reviewed;
- PR #190 remains documentation/planning only. Any future X1Labs Intelligence Scout or remote-agent design must remain subordinate to X1 Scout -> CMIS for freshness-sensitive truth and must not gain independent verification, Learning System/HXMP, wallet, or execution authority by implication.

### 6. Controlled Execution

Still locked/not started. X1 productization does not authorize transaction construction, signing, broadcasting, custody, trading, swaps, bridge transfer, or autonomous value movement. Any future execution work requires a new explicit architecture, contract, safety, approval, and readiness gate.

## Definition of done for the current learning milestone

The core autonomous-learning implementation milestone is complete on `main` when evaluated as:

```text
approved/static source selection
  -> immutable source/provenance registration
  -> complete frozen source plan
  -> source-grounded curriculum generation
  -> canonical exams
  -> verified remediation/retention/transfer
  -> curriculum-scoped learned concepts
  -> final source capstone
  -> durable restart-safe job state
```

The Learning Plane implementation milestone is complete enough to support the flagship roadmap. Its next work is bounded operational hardening and new approved-source validation in support of X1 productization, not replaying completed MB4E mastery or rebuilding the autonomous controller from scratch.

## Core rule

**Roberta may learn autonomously from accepted static evidence, but learning never self-authorizes truth or operational power. Fresh chain facts remain behind Chain Scout -> CMIS -> Provider, and operational/execution authority remains separately gated.**

## Live reconciliation — 2026-09-02 12:18 America/New_York

Current product order:

1. **BURN — COMPLETE.** CMIS public #389 and protected `cmis-core` #12 are accepted; ROBERTA public #295 and #304 are merged; protected `roberta-core` #23/#24 provide and validate the shared Human/Machine Decision Object path. X1 Scout now consumes dedicated CMIS `burn_intelligence/v1`, and `/burn <asset>` is a first-class Human ROBERTA workflow.
2. **DISCOVERY — ACTIVE GATE.** CMIS public #391 has merged `discovery_intelligence/v1` under capability contract 1.16.0. ROBERTA PR #306 is open, clean, and mergeable to promote the accepted service through X1 Scout. This is the immediate productization priority.
3. **WHAT CHANGED? — NEXT.** Build only after Discovery is accepted in ROBERTA, using canonical Discovery/history evidence rather than a second fact layer.
4. **EARLY WARNING — AFTER WHAT CHANGED?.** Promote warning families one at a time with explicit persistence, freshness, replay/deduplication, severity, and evidence contracts.
5. **Decision Object expansion:** continue one workflow at a time so Human and Machine ROBERTA preserve the same facts, unknowns, evidence state, and execution denial.
6. **Learning operations:** keep private-core CI/background scheduling hardening as a supporting track; it should not displace the X1 intelligence product gates.
7. **Telegram:** remains lower priority than Discovery / WHAT CHANGED? / Early Warning.
8. **Controlled Execution:** locked/not started; `execution_authorized=false`.

### Cross-project status note

CMIS PR #363 remains an open delayed-vault evidence investigation. It may continue in parallel, but it is no longer treated as a blocker for the main ROBERTA product roadmap. Historical Coverage Proof v1 (#383) is complete, and CMIS Discovery Intelligence v1 (#391) is accepted.
