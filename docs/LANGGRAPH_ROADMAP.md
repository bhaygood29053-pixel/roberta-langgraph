# Roberta LangGraph Roadmap

Last updated: 2026-08-21

## Current position

Roberta has completed:

- Phase 1 — Core Agent Loop;
- Phase 2 — Provider-Neutral Model Loop;
- Phase 3 — X1 Scout Boundary;
- Phase 4 — CMIS / X1 Provider Integration;
- Phase 6 — Agentic X1 Scout Planning;
- Phase 7A — Thread / Checkpoint Persistence;
- Phase 7B — HXMP Durable Memory;
- Phase 8 — Oracle Policy;
- Phase 9 — Human in the Loop;
- Phase 10 — More Specialists / Providers;
- Post-Phase-10 Evidence-Aware Intelligence & User Experience;
- X1 Decision Production Readiness (#62);
- adoption/readiness of the first separately promoted CMIS 1.9 Verified Intelligence service through X1 Scout (#73/#74);
- Solana Read-Only Production Readiness (#78) for the exact currently promoted Roberta Solana Scout surface;
- **Learning System Phase 1 — deterministic source-ingestion foundation (#106/#107);**
- **Learning System Phase 2 — deterministic structure-first Markdown parsing (#109/#110);**
- **Learning System Phase 3 — deterministic structure-aware evidence chunking (#112/#113);**
- **Learning System Phase 4 — deterministic lexical + embedding indexing foundation (#115/#116);**
- **Learning System Phase 5 — deterministic retrieval + benchmark foundation (#118/#119);**
- **Learning System Phase 6 — deterministic evidence packet + citation-bound answer foundation (#121/#122);**
- **Learning System Phase 7 — deterministic independent answer-evaluation foundation (#124/#125);**
- **Learning System Phase 8 — deterministic provisional reflection + candidate-lesson foundation (#127/#128);**
- **Learning System Phase 9 — deterministic independent candidate-lesson verification (#129/#131).**

The accepted active Learning System gate is:

- **Learning System Phase 10 — verified lesson retention foundation (#133/#134): ACCEPTED / ACTIVE; implementation not yet accepted.**

Phase 5 — X1 Evidence Completeness remains deliberately **bounded**, with explicit verified/bounded/partial/unavailable/conflict/insufficient-evidence states.

Roberta Phase 11 — Controlled Execution remains **locked / not started**.

The **Roberta Learning System remains the primary development track**. Phase 10 retention has an accepted contract under Issue #133 / PR #134, but its implementation must still pass exact-head deterministic verification and the independent Spec / Code-Architecture / Authority-Safety gate. Existing CMIS, Chain Scout, transport, policy, memory, and approval paths should remain stable unless a change is directly required to support the accepted Learning System gate or fix a proven defect.

## Canonical hierarchy

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Roberta owns orchestration, user policy, specialist selection, cross-chain coordination, approval boundaries, and final synthesis.

Chain Scouts own chain-specific planning and interpretation. They preserve CMIS facts/evidence/limitations and do not manufacture market facts.

CMIS owns deterministic verified facts, evidence, Evidence Receipts, Proof Scores, deterministic risk, historical intelligence, capability eligibility, and bounded analysis-only pre-trade calculations.

Providers remain beneath CMIS.

Fresh accepted CMIS/provider evidence overrides remembered, checkpointed, conversational, or Learning System source knowledge for freshness-sensitive market state. Missing evidence remains unknown/unavailable; it is never converted into zero, false, or an LLM estimate. Risk remains separate from Proof Score.

## Migration rule

The repository/project identity is CMIS, while working internal Python identifiers such as `liquidity_scout` may remain during incremental migration to avoid breaking imports, tests, entry points, and deployments. Compatibility identifiers do not create a second authority layer.

## Engineering governance

Meaningful Roberta changes are governed by [`ENGINEERING_WORKFLOW.md`](./ENGINEERING_WORKFLOW.md). That document is the repository authority for roadmap/issue gating, narrow tracer-bullet implementation, behavior-first verification, exact-head deterministic testing, and the independent three-axis PR gate: **Spec Fidelity**, **Code/Architecture Quality**, and **Authority/Safety Boundary**.

A roadmap item being active does not waive those gates. A PR is not merge-ready if any required axis fails, and acceptance must be followed by roadmap/source-of-truth reconciliation. This governance does not start or widen Controlled Execution.

## Learning System primary track

The Learning System follows the evidence-grounded design in [`LEARNING_SYSTEM.md`](./LEARNING_SYSTEM.md), [`LEARNING_SYSTEM_STRUCTURE.md`](./LEARNING_SYSTEM_STRUCTURE.md), [`LEARNING_SYSTEM_CHUNKING.md`](./LEARNING_SYSTEM_CHUNKING.md), [`LEARNING_SYSTEM_INDEXING.md`](./LEARNING_SYSTEM_INDEXING.md), [`LEARNING_SYSTEM_RETRIEVAL.md`](./LEARNING_SYSTEM_RETRIEVAL.md), [`LEARNING_SYSTEM_GROUNDING.md`](./LEARNING_SYSTEM_GROUNDING.md), [`LEARNING_SYSTEM_EVALUATION.md`](./LEARNING_SYSTEM_EVALUATION.md), [`LEARNING_SYSTEM_REFLECTION.md`](./LEARNING_SYSTEM_REFLECTION.md), [`LEARNING_SYSTEM_VERIFICATION.md`](./LEARNING_SYSTEM_VERIFICATION.md), [`LEARNING_SYSTEM_RETENTION.md`](./LEARNING_SYSTEM_RETENTION.md), and the broader Roberta Learning System Specification v1.1.

### Learning System Phase 1 — Source ingestion ✅ Complete

Issue #106 / PR #107 established the first narrow deterministic learning boundary:

- exact UTF-8 source bytes are preserved behind a provider-neutral `SourceStore` contract;
- `content_hash` is reproducible SHA-256 over original source bytes;
- `source_id` is deterministic/content-addressed from canonical source identity material;
- duplicate ingestion is idempotent;
- changed content creates a distinct immutable source record rather than overwriting prior source truth;
- malformed identity/state/metadata/UTF-8 input fails closed;
- stored metadata is detached and recursively immutable;
- static Learning System sources expose `live_state_authorized = false` and cannot replace CMIS/provider evidence for current state;
- no embeddings, retrieval, concepts, curriculum, reflection, lesson promotion, fine-tuning, or additional learning agents were added in this phase.

Accepted verification for PR #107 recorded 510 deterministic tests passing with 5 live/provider tests deselected, all three engineering review axes passing, and no unresolved review threads.

### Learning System Phase 2 — Structure detection ✅ Complete

Issue #109 / PR #110 established deterministic structure-first parsing for the first accepted source format:

```text
format = markdown
parser_contract = markdown-structure/v1
encoding = UTF-8
```

The accepted Phase 2 boundary:

- resolves the exact Phase 1 `SourceRecord` and revalidates the immutable source artifact SHA-256 before parsing;
- preserves ATX heading hierarchy, nearest-lower-level parents, repeated headings, structural paths, exact 1-based line locations, and exact heading source lines;
- preserves exact source text and original line endings in source-located `preamble`, `paragraph`, `list`, `code_fence`, and narrow `table` blocks;
- prevents heading-looking text inside fenced code from becoming document structure;
- validates that every non-blank source line is accounted for exactly once as either a heading or one structural block;
- produces deterministic/content-addressed document, section, block, and structure identities that bind parser contract/version;
- represents an unclosed code fence as explicit `partial` output with a warning rather than inventing closure;
- represents heading-level jumps with warnings and never synthesizes missing headings;
- fails closed on missing source/artifact state, source hash mismatch, invalid UTF-8, unsupported parser contract, or violated source-accounting invariants;
- structurally denies live-state authority on all derived records.

Accepted verification for PR #110 recorded **520 deterministic tests passing with 5 live/provider tests deselected**, all 10 new structure tests passing, all three engineering review axes passing, and no unresolved review threads.

### Learning System Phase 3 — Structure-aware evidence chunking ✅ Complete

Issue #112 / PR #113 established deterministic evidence chunks over canonical Phase 1/2 provenance:

```text
SourceRecord / exact artifact
  -> canonical ParsedDocument
    -> SectionRecord / StructuralBlock
      -> EvidenceChunk / ChunkManifest
```

The accepted first chunker contract is:

```text
chunker_contract = structure-aware-chunk/v1
chunker_version = 1.0.0
overlap_lines = 0
max_chars = explicit positive integer; implementation baseline 1600
```

The accepted Phase 3 boundary:

- resolves the exact Phase 1 source and revalidates retained artifact SHA-256;
- recomputes canonical Phase 2 structure using the declared parser contract/version and rejects a caller-supplied `ParsedDocument` that does not match exactly;
- treats `code_fence`, `list`, and `table` blocks as atomic in v1;
- groups only adjacent `preamble`/`paragraph` blocks with the same `section_id`, and only when the exact retained source span including blank separators stays within `max_chars`;
- never crosses section boundaries merely to fill a chunk;
- splits oversize prose only at source-line boundaries;
- preserves a source line longer than `max_chars` intact as `oversize_line` rather than truncating it;
- preserves an oversize atomic block intact as `oversize_atomic` rather than truncating it;
- forbids overlap in v1 until retrieval evaluation demonstrates a reason to add it;
- validates exact once-only coverage for every Phase 2 structural-block source line;
- preserves source/document/section/block provenance, structural paths, exact source line ranges/text, source authority/approval state, parser/chunker versions, parameters, fragment identity, and deterministic previous/next links;
- creates reproducible `chk_...` chunk ids and a content-addressed `cset_...` chunk-set manifest;
- emits structural chunk kinds only and does not infer concepts, truth, importance, ownership, behavior, or intent;
- structurally denies live-state authority for chunks and manifests.

Accepted verification for PR #113 recorded **534 deterministic tests passing with 5 live/provider tests deselected**, all 14 new chunking tests passing, all three engineering review axes passing, and no unresolved review threads.

### Learning System Phase 4 — Indexing foundation ✅ Complete

Issue #115 / PR #116 established replaceable lexical and optional embedding representations over canonical Phase 3 evidence chunks.

The accepted first index contracts are:

```text
index_contract = evidence-index/v1
index_version = 1.0.0
lexical_analyzer_contract = unicode-word-casefold/v1
lexical_analyzer_version = 1.0.0
embedding = optional typed EmbeddingProvider
```

The accepted Phase 4 boundary:

- does not trust a supplied `ChunkedDocument`; it recomputes canonical Phase 2 structure and Phase 3 chunking using the declared parser/chunker contracts, versions, and parameters and requires exact equality;
- creates deterministic lexical entries that preserve exact `chunk_id`, source/document/section provenance, structural path, chunk kind, line range, source authority/approval metadata, and content hash;
- version-controls deterministic Unicode NFKC normalization, casefolding, and ordered Unicode word tokenization while deliberately avoiding stemming, concept inference, synonym inference, or truth judgments;
- defines a typed provider-neutral `EmbeddingProvider` seam with explicit provider/model/version/dimension metadata;
- binds embedding requests and results to the exact `chunk_id` and chunk content hash;
- validates successful vectors for exact declared dimension, numeric non-boolean elements, and finite values;
- fails closed on malformed provider contracts, identity mismatch, wrong dimensions, or non-finite values;
- converts provider runtime failures or explicit unavailable states into diagnostic partial index state with no synthesized fallback vector;
- fingerprints validated vector output for derived reproducibility without treating a floating-point representation as source truth;
- exposes explicit `lexical_only`, `complete`, and `partial` manifest states;
- includes a deterministic SHA-256-based embedding adapter only to prove the provider/index contract in tests; it is not a semantic production embedding model and does not establish retrieval quality;
- keeps PostgreSQL full-text search + pgvector as an intended early production backend but does not couple the accepted index model to that backend yet;
- structurally denies live-state authority for all index/provider records.

Accepted verification for PR #116 recorded **548 deterministic tests passing with 5 live/provider tests deselected**, all new indexing regressions passing, all three engineering review axes passing, and no unresolved review threads.

### Learning System Phase 5 — Retrieval + benchmark foundation ✅ Complete

Issue #118 / PR #119 established deterministic retrieval over validated Phase 4 index representations.

The accepted first retrieval contracts are:

```text
retrieval_contract = evidence-retrieval/v1
retrieval_version = 1.0.0
fusion_contract = reciprocal-rank-fusion/v1
rrf_k = 60
```

The accepted Phase 5 boundary:

- revalidates each supplied corpus item through canonical Phase 1/2/3 reconstruction and Phase 4 lexical/index-integrity checks before retrieval;
- validates stored embedding provenance, provider/model/version/dimension metadata, finite vector values, vector fingerprints, entry ids, counts, manifest diagnostics, and manifest hash/id without inventing provider authenticity;
- normalizes corpus ordering by deterministic `index_id`, rejects duplicate index ids, and rejects duplicate canonical chunk ids that could inflate relevance scores;
- preserves exact query text separately from deterministic NFKC/casefold Unicode lexical tokens;
- supports exact-match source/document/section/authority/approval/chunk-kind filters, including explicit null/preamble section scope, without silently widening a supplied filter;
- ranks lexical candidates transparently by phrase match, matched distinct terms, matched occurrences, indexed token count, and stable chunk-id tie-breaking;
- allows an optional vector channel only when query and index embedding spaces match exact provider/model/version/dimension metadata;
- validates query vectors for dimension, finite numeric values, fingerprint, and non-zero magnitude and computes cosine similarity only for eligible stored `ok` vectors;
- preserves lexical and vector ranks/similarities as separate observable channels;
- fuses candidate channel ranks with Reciprocal Rank Fusion using exact rational arithmetic rather than an opaque model score;
- applies deterministic local-context diversity so adjacent fragments from one source/section do not crowd out independent alternatives when available, while preserving deferred chunk ids;
- preserves contradictory/disagreeing cross-source chunks independently rather than reconciling them inside retrieval;
- returns explicit `ok`, `partial`, or `no_match` state and never manufactures evidence when a requested channel is unavailable or nothing matches;
- preserves exact canonical evidence text and source/document/section/block/chunk provenance in every selected candidate;
- exposes deterministic first-slice benchmark helpers for Recall@K, Precision@K, reciprocal rank, binary nDCG@K, evidence coverage, redundancy rate, source diversity, and filter correctness;
- treats negative/no-relevant benchmark denominators as undefined rather than inventing favorable or unfavorable scores;
- uses the deterministic hash embedding adapter only to prove vector-channel mechanics and makes no semantic/paraphrase-quality claim from it;
- structurally denies live-state authority for all retrieval/query/metric records.

Accepted verification for PR #119 recorded **566 deterministic tests passing with 5 live/provider tests deselected**, all new retrieval regressions passing, all three engineering review axes passing, and no unresolved review threads.

### Learning System Phase 6 — Grounded answer + citation foundation ✅ Complete

Issue #121 / PR #122 established deterministic evidence-packet construction and citation/scope validation over canonical Phase 5 retrieval.

The accepted first grounding contracts are:

```text
evidence_packet_contract = grounded-evidence-packet/v1
answer_contract = citation-bound-answer/v1
prompt_safety_contract = retrieved-text-untrusted-data/v1
answer_validator_version = 1.0.0
```

The accepted Phase 6 boundary:

- reconstructs the exact Phase 5 retrieval from its typed query and requires exact equality before evidence packet construction;
- assigns deterministic local `E1...En` anchors that bind exact retrieval/chunk/source/document/section/block identities, structural paths, source line ranges, exact text/content hashes, authority/approval metadata, and retrieval rank evidence;
- content-addresses anchor, packet, and grounded-result identities so evidence-scope tampering is detectable;
- serializes retrieved text as `untrusted_evidence_data`, explicitly denying source text the ability to expand tool permissions, authorize memory writes, or authorize execution;
- accepts typed claims with explicit `supported`, `insufficient`, or `conflict` status rather than treating unconstrained prose as verified structure;
- requires supported claims to cite exact packet anchors and conflict claims to cite at least two exact anchors;
- rejects fabricated/unknown anchors, duplicate claim ids, packet-identity substitution, and tampered packet/retrieval state;
- converts `no_match` retrieval into explicit insufficiency and requires an `insufficient_evidence` disclosure marker;
- preserves partial retrieval and requires an explicit `retrieval_partial` limitation marker;
- does not infer semantic contradiction merely because multiple sources are present; an upstream explicit deterministic conflict signal is required before packet-level conflict state is asserted;
- preserves exact user-facing `EvidenceReference` records for cited anchors;
- deliberately separates structural citation validity from semantic verification: first-slice results retain `semantic_support_verified=false` and `claim_coverage_verified=false`;
- structurally denies live-state authority, verified-memory promotion, and execution authority for packet/candidate/result records.

Accepted verification for PR #122 recorded **582 deterministic tests passing with 5 live/provider tests deselected**, all 16 new grounding regressions passing, all three engineering review axes passing, and no unresolved review threads.

### Learning System Phase 7 — Answer evaluation foundation ✅ Complete

Issue #124 / PR #125 established an independent deterministic evaluator over accepted Phase 6 grounded answers.

The accepted first evaluation contracts are:

```text
answer_evaluation_contract = grounded-answer-evaluation/v1
golden_case_contract = grounded-answer-golden-case/v1
evaluator_adapter = deterministic-golden-label/v1
evaluator_version = 1.0.0
```

The accepted Phase 7 boundary:

- reconstructs supplied Phase 6 grounded answers through the accepted Phase 6 validator before any scoring occurs;
- content-addresses golden cases and binds explicit question/task, behavior, evidence, claim, limitation, provenance, author, approval, and version labels;
- scores only `approved` golden cases; pending/rejected labels fail closed;
- keeps retrieval coverage separate from answer correctness/completeness and marks answer dimensions `not_evaluated` when missing expected evidence would otherwise misattribute the failure;
- distinguishes structurally valid-but-irrelevant citations from fabricated citations by reducing citation precision rather than citation-binding integrity;
- measures citation correctness, citation precision, citation completeness, unsupported-claim rate, deterministic claim/answer correctness, answer completeness, limitation disclosure, insufficiency handling, conflict handling, and instruction compliance as separate dimensions;
- supports deterministic prompt-injection regression fixtures without granting retrieved source text instruction authority;
- preserves explicit failure classes including retrieval, citation binding, unsupported claim, answer correctness/completeness, conflict, insufficiency, uncertainty/calibration, instruction compliance, evaluator unavailable/disagreement, and unknown states;
- reports deterministic aggregate case-pass, citation, unsupported-claim, insufficiency/conflict, retrieval-failure, and answer-failure metrics without merging those dimensions;
- deliberately keeps `semantic_groundedness=not_evaluated`, `semantic_support_verified=false`, and `claim_coverage_verified=false` because deterministic citation/substring checks do not prove semantic entailment;
- keeps uncertainty calibration `not_applicable` or `not_evaluated` because the current grounded-answer contract does not expose a calibrated confidence field;
- denies live-state authority, verified-memory promotion, and execution authority for golden cases, dimensions, evaluation results, and aggregates.

Accepted verification for PR #125 recorded **599 deterministic tests passing with 5 live/provider tests deselected**, all 17 new Phase 7 evaluation regressions passing, all three engineering review axes passing, and no unresolved review threads.

### Learning System Phase 8 — Provisional reflection + candidate lesson foundation ✅ Complete

Issue #127 / PR #128 established deterministic, provenance-bound provisional learning candidates from canonical failed Phase 7 evaluations.

The accepted first Phase 8 contracts are:

```text
reflection_contract = evaluation-reflection/v1
candidate_lesson_contract = candidate-lesson/v1
verification_plan_contract = candidate-lesson-verification-plan/v1
learning_diagnosis_version = 1.0.0
```

The accepted Phase 8 boundary:

- re-runs the exact accepted deterministic Phase 7 evaluator over the supplied packet/result/golden case before a supplied failed evaluation may produce a reflection;
- requires exact equality with the supplied Phase 7 `EvaluationResult`, `aggregate_status = fail`, and at least one accepted failure classification;
- prevents passing evaluations from manufacturing reflections or candidate lessons;
- maps accepted Phase 7 failure classifications through a versioned deterministic diagnosis table into bounded layers such as retrieval, citation binding, answer support/correctness/completeness, conflict, insufficiency, uncertainty calibration, instruction compliance, evaluator, or unknown;
- preserves exact evaluation, golden-case, packet, grounded-result, retrieval, chunk, and evidence-reference provenance in the reflection/candidate path;
- labels reflection text, lesson text, and rationale as `generated_provisional` so generated output never becomes evidence or source truth merely by being reflected upon;
- content-addresses reflection, candidate core, candidate lifecycle state, verification plan, and complete learning-candidate bundle identities;
- creates deterministic verification checks directly from the exact failure classes and binds them to exact candidate/reflection/evaluation/golden-case/packet/result/retrieval identities;
- keeps `promotion_authorized = false` on every Phase 8 verification plan;
- limits candidate lifecycle to `provisional`, `rejected`, or `superseded`; there is no Phase 8 `verified` state;
- reconstructs the exact initial provisional candidate state during lifecycle validation and requires any terminal record to bind `previous_state_id` to that exact `candidate_state_id`, preventing a caller from forging a terminal predecessor chain by recomputing hashes;
- prevents self-supersession and preserves immutable state revisions;
- keeps prompt-injection/instruction-compliance failures traceable without granting retrieved/source text instruction authority;
- structurally denies live-state authority, verified-memory promotion, governance mutation, and execution authority for all Phase 8 records.

Accepted verification for PR #128 recorded **617 deterministic tests passing with 5 live/provider tests deselected** at exact final head `e08659ad15688530f421ea3b5fc5e9dbdbea2ec2`. The independent Codex review identified one valid lifecycle-predecessor integrity defect; that defect was fixed, adversarial regressions for missing/unrelated predecessor ids were added, exact-head CI passed, the review thread was resolved, and all three engineering review axes passed before merge.

### Learning System Phase 9 — Independent candidate lesson verification ✅ Complete

Issue #129 / PR #131 established a deterministic verification-only boundary over exact provisional Phase 8 `LearningCandidateBundle` state.

The accepted Phase 9 contracts are:

```text
candidate_verification_contract = candidate-lesson-verification/v1
verifier_adapter_id = deterministic-phase7-retest/v1
verifier_version = 1.0.0
```

The accepted Phase 9 boundary:

- canonically revalidates the complete Phase 8 bundle and lifecycle before any verification check runs;
- accepts only the exact `provisional` candidate state and refuses to resurrect rejected or superseded candidates;
- executes only checks already present in the exact canonical Phase 8 `VerificationPlan`, preserving order, check identity, failure classification, diagnosed layer, and required identity references;
- computes fresh deterministic Phase 7 retest evaluations rather than accepting caller-supplied verification scores;
- treats the retest packet/result as an atomic evidence pair: both absent yields explicit `inconclusive`, exactly one supplied fails closed before any unvalidated identity can be recorded, and both supplied must survive canonical evaluation;
- derives a deterministic content-addressed retest golden case when the approved original case pinned the failed packet/retrieval identities, preserving approved labels and rebinding only existing non-null evidence pins to the observed retest identities;
- records original `golden_case_id` separately from derived `retest_golden_case_id` so corrected evidence provenance does not rewrite the original approved case;
- maps retest-capable verification checks to accepted Phase 7 dimensions and preserves `pass`, `fail`, or `inconclusive` per check;
- makes `rejected` dominate when any mandatory check fails, `inconclusive` when no check fails but at least one remains unavailable, and `verified_for_learning` only when every mandatory check passes;
- keeps unavailable calibration/evaluator/disagreement/unknown verification capabilities explicitly inconclusive rather than inventing evaluator authority;
- prevents candidate/reflection generated text from self-verifying or replacing evidence/plan state;
- content-addresses verification/check results and requires exact rebuild equality for validation;
- structurally denies source-truth authority, live-state authority, durable-memory promotion, governance mutation, and execution authority throughout Phase 9.

Accepted verification for PR #131 recorded **640 deterministic tests passing with 5 live/provider tests deselected** at exact final head `f85b2083c6c939447b0a445fae6333753cd99a41`. Independent Codex review identified two valid P1 defects during development—partial retest provenance and corrected retrievals blocked by original evidence pins. Both were fixed with focused regressions, both review threads were resolved, exact-head CI passed, all three engineering review axes passed, and the final exact-head Codex review reported no major issues before merge.

A `verified_for_learning` result means only that the candidate passed the accepted Phase 9 verification contract. It does **not** itself write trusted durable memory, write source truth, change source approval, alter CMIS/provider trust, mutate protected policy/governance, or authorize wallet/transaction execution.

### Learning System Phase 10 — Verified lesson retention foundation 🟡 Active / implementation not yet accepted

Issue #133 / PR #134 accepted the first retention contract. The phase starts the `RETAIN` step without treating Phase 9 verification as automatic promotion.

The accepted first-slice boundary is:

```text
canonical Phase 8 LearningCandidateBundle
  + canonical Phase 9 CandidateVerificationResult(status=verified_for_learning)
        ↓ exact Phase 9 revalidation
procedural lesson type/scope eligibility
complete canonical contradiction/source snapshot
exact duplicate handling
categorical confidence basis
exact human retention approval
        ↓
RetentionDecision
        ↓ only when every mandatory gate passes
VerifiedLessonRecord
        ↓
provider-neutral in-memory Phase 10 store only
```

Phase 10 must preserve, at minimum:

- exact Phase 8/9 candidate, reflection, plan, evaluation, packet/result/retrieval, retest, check, and verification provenance;
- a narrow procedural-learning eligibility allowlist that excludes factual/current-market claims, protected policy, permissions, credentials, and execution instructions;
- a trusted, complete, content-addressed enumeration of every active overlapping verified lesson and every canonical approved source/evidence unit in the declared scope, including required lifecycle/superseding versions;
- inconclusive/fail-closed behavior when source enumeration, contradiction evaluation, lifecycle state, or other completeness evidence is unavailable;
- deterministic exact-duplicate handling without parallel trusted lessons or lost provenance;
- categorical confidence basis without fabricated calibrated probability;
- explicit human approval bound to `action_type=retain_verified_lesson`, exact proposal/binding hashes, scope/contract/provenance/snapshot/results/confidence/thread, and an application-authenticated human principal;
- one-time approval binding consumption so replay cannot create another trusted lesson;
- deterministic/content-addressed retention, lesson, decision, snapshot, and immutable lifecycle/audit identities;
- provider-neutral/in-memory storage only in v1.

Implementation PR #136 is currently **draft / not merge-ready** after independent review identified blockers in procedural-body eligibility, source contradiction evaluation, trusted source-scope completeness enumeration, lifecycle transition evidence/decision binding, and duplicate provenance retention. Green deterministic CI does not override these failed review axes. The implementation must resolve those boundaries, rerun exact-head CI, and pass the independent three-axis review before merge.

Phase 10 does not authorize HXMP writes or any external durable-memory write. It also does not authorize source-store writes from generated text, source truth, current market/blockchain truth, source approval changes, CMIS/provider trust changes, protected governance mutation, wallet authority, transaction preparation/signing/broadcasting, custody, trading, or Controlled Execution. Any future HXMP verified-lesson persistence requires a separate accepted gate.

## Technology Radar design boundary — Issue #100

Issue #100 defines a **specification-only** future roadmap-aware Technology Radar in [`TECHNOLOGY_RADAR.md`](./TECHNOLOGY_RADAR.md).

The proposed Radar is a read-only technology-research and recommendation capability. It keeps trend strength, roadmap relevance, research-evidence quality, adoption/maintenance risk, and license compatibility as separate dimensions; preserves source provenance and explicit unknowns; and routes any promising discovery back through the normal engineering workflow.

This design does **not** authorize a Radar runtime, live source adapters, schedulers, package installation, autonomous code or architecture changes, roadmap mutation, provider-trust changes, or execution authority. Any future implementation requires a separate accepted roadmap gate and implementation issue. Controlled Execution remains locked.

Technology Radar implementation is not the current primary development track while the Learning System is being built.

## Phase 10 — More Specialists / Providers ✅ Complete

Roberta supports separate X1 Scout and Solana Scout paths above one shared CMIS layer:

```text
Roberta
  ├── X1 Scout
  │     -> CMIS -> X1 / XDEX providers
  └── Solana Scout
        -> CMIS -> Solana providers
```

The Scout -> CMIS boundary validates the live machine-readable capability manifest before dispatch. Missing, malformed, incompatible, or non-callable capability state fails closed. No unsupported chain silently falls back to another chain.

Solana Phase 10 remains read-only, capability-specific, and not assumed to have X1 parity.

## Completed readiness gates

### X1 Decision Production Readiness (#62) ✅ Complete

The X1 read-only decision-quality production gate is complete. Representative live/configured and degraded-evidence cases proved answer-first presentation, uncertainty preservation, risk/evidence separation, freshness handling, null-versus-zero preservation, provider-error handling, and read-only execution boundaries.

### First promoted CMIS intelligence adoption (#73/#74) ✅ Complete

Roberta adopted the first separately promoted CMIS 1.9 read-only intelligence service, `concentration_change_intelligence/v1`, through X1 Scout. The operation remains explicit-only and evidence-id-bound; it does not authorize broader intelligence promotion or execution.

### Solana Read-Only Production Readiness (#78) ✅ Complete

The configured production-model/provider path is accepted for the exact current Roberta Solana Scout surface:

- `market_report`;
- `tokenomics`;
- `risk_check`;
- exact-mint identity preservation and symbol-only fail-closed handling required by those services;
- X1/Solana evidence isolation.

The final configured operator run on 2026-08-20 executed all five corpus cases with `--require-no-skips` and recorded:

```text
total: 5
completed: 5
passed: 5
failed: 0
skipped: 0
oracle_retry_calls: 1
provider_error_events: 1
```

The nonzero provider-error count is preserved as an operational measurement rather than hidden; readiness blockers are based on failed deterministic scenario checks, and the accepted run had zero failures. The symbol-only case required one presentation retry after PR #94 and then passed with separate Risk/Evidence quality disclosure.

This is **not** an X1/Solana parity claim. Solana `historical_compare`, `rank`, `pre_trade_check`, `concentration_change_intelligence`, broader Verified Intelligence primitives, and all execution capabilities remain outside the accepted Roberta Solana production-ready scope unless separately promoted and evaluated.

The separately accepted live Token-2022 fixture from CMIS #244 proves only the exact-mint read-only RPC contract for that fixture; it does not promote a broader Token-2022 market or holder/ownership claim.

## Evidence-aware intelligence ✅ Complete

Roberta preserves CMIS Evidence Receipts, Proof Scores, source/provenance, scope, freshness, disagreements, limitations, unresolved fields, and risk through Chain Scout reports.

Roberta may explain those results but does not recompute CMIS proof/risk or upgrade provider-reported evidence to independently verified truth.

Cross-chain evidence may be compared but not merged into a synthetic source set, Proof Score, freshness state, deterministic risk result, or safety grade.

Behavioral/ownership labels such as insider, whale, bot, accumulator, distributor, market maker, manipulator, common owner, or intent remain unavailable unless a separately accepted deterministic classification contract explicitly permits them.

## CMIS Phase 11 foundation versus Phase 12 promotion

CMIS Phase 11 established the read-only Verified Intelligence foundation. The core `intelligence_foundation` remains non-promoted as a group:

```text
read_only = true
public_service_promoted = false
scout_reliance_promoted = false
```

Its broader primitives—top-account concentration snapshots, neutral wallet activity, sanitized sparse history, and generic evidence-bound conclusions—do not automatically become public Scout services.

CMIS **Phase 12** separately promoted exactly one narrow X1 wrapper under current CMIS contract `1.9.0`:

```text
service = concentration_change_intelligence
service_contract = concentration_change_intelligence/v1
chain = x1
state = bounded
callable = true
read_only = true
public_service_promoted = true
scout_reliance_promoted = true
accepted_conclusion_type = top_account_concentration_change
promotion_scope = cmis_owned_top_account_concentration_change_evidence_by_id
execution_authorized = false
```

Solana is unavailable/non-callable/non-promoted for this service.

## Roberta adoption of the Phase 12 service ✅ Complete

Roberta has adopted `concentration_change_intelligence/v1` through **X1 Scout** with a service-specific CMIS `>=1.9.0` promotion gate.

The operation is explicit-only; it is not an autonomous X1 Scout planning action merely because CMIS advertises it.

Roberta/X1 Scout validates the live capability record before dispatch and requires the exact service contract, bounded/callable/read-only state, public-service promotion, Scout reliance, accepted conclusion type, promotion scope, and `execution_authorized=false`.

The public request uses exact X1 asset context plus a canonical CMIS-owned intelligence evidence id. CMIS resolves/revalidates trusted stored evidence internally. Caller-supplied intelligence bundles, Evidence Receipts, Proof Scores, provider assertions, behavioral labels, or replacement verification state are not accepted as trust shortcuts.

Exact canonical asset/evidence binding remains a CMIS/request-contract requirement unless and until Roberta adds a stronger local canonical-identity validator; documentation must not claim Roberta itself proves more identity semantics than the current client enforces.

The service does not establish total unique holders or beneficial owners. Token-account concentration remains token-account concentration. Optional threshold output is deterministic policy evaluation, not risk, and Proof Score remains separate from risk.

## CMIS post-Phase-12 internal foundations — not promoted to Roberta

CMIS has additionally completed deterministic descriptive concentration-direction classification, direct wallet-relationship evidence with explicit non-ownership semantics, and the first concentration-threshold alert evidence foundation under CMIS #263/#264. These remain internal/read-only/non-promoted and do not create Roberta or Chain Scout operations by implication.

The concentration-alert foundation consumes canonical CMIS concentration-change evidence and deterministic threshold/comparator/freshness/persistence rules. It is not a risk score and does not authorize public alert delivery, Scout reliance, Roberta planner behavior, behavioral/ownership labels, or execution. Any future CMIS alert promotion and any Roberta adoption/readiness work require separately accepted gates.

## X1 evidence boundary 🟡 Bounded

X1 is the mature CMIS surface, but completeness remains field- and scope-specific.

Recent bounded provider-gap observations include:

- X1.Ninja SSE handshake access currently denied for the tested repository credential; no event semantics are promoted from that result;
- holder-looking provider/RPC/account-authority counts disagree and remain insufficient evidence for holder/beneficial-owner semantics;
- Warp Bridge machine-readable operational facts remain unavailable until an exact provenance-approved contract is accepted;
- historical redundancy/source-independence evidence remains a separate proof obligation.

Roberta must preserve these unavailable/partial/insufficient states rather than guessing.

## Pre-trade analysis ✅ Bounded analysis-only foundation complete

The deterministic pre-trade trade-size milestone previously tracked as CMIS Issue #99 is complete and is no longer a current roadmap dependency.

CMIS owns deterministic trade-size analysis. Roberta explains the returned structured result without recomputing replacement ratios, risk, proof, price impact, fees, slippage, route quality, or simulation.

Advanced fields remain available only where exact semantics/evidence are independently proven. Missing advanced evidence is not zero-filled.

Every current pre-trade result preserves:

```text
analysis_only = true
execution_authorized = false
```

A `PASS` is not permission to trade.

## Memory and policy

```text
HXMP / memory -> stable context and policy
Learning System -> static source knowledge and later verified learning state
CMIS          -> current verified facts and evidence
Policy code   -> deterministic rule result
LLM           -> explanation / synthesis only
```

Fresh accepted CMIS/provider evidence overrides remembered or Learning System live-market snapshots; the Learning System must not create live-market snapshots as trusted source knowledge.

## Human approval

Phase 9 human approval is exact-proposal review. Approval is not a reusable signing credential and does not grant broad future wallet authority.

## Phase 11 — Controlled Execution ⬜ Locked / not started

No current CMIS result, Chain Scout report, Roberta policy decision, readiness result, human approval, Learning System result, or Technology Radar recommendation authorizes:

- transaction preparation for execution;
- wallet signing;
- transaction broadcasting;
- custody;
- live swap execution;
- autonomous trading;
- bridge/value transfer;
- autonomous value movement;
- broad delegated wallet authority.

If Controlled Execution is ever promoted, it requires a separate accepted transaction-construction/simulation, exact approval-consumption/revalidation, signer/broadcast, replay-protection, precondition, and failure contract.

## Deferred / maintenance intelligence boundary

The first narrow CMIS 1.9 promotion/adoption, the current Solana read-only readiness gate, and the first internal concentration-threshold alert evidence foundation are complete. Additional read-only intelligence work remains valid but is not the primary Roberta development track while the Learning System is being built. Future CMIS/Scout work should proceed only through separately accepted deterministic contracts, especially:

1. deeper X1 provider-gap and historical redundancy verification;
2. field-by-field Solana maturity beyond the currently accepted Scout surface;
3. any public alert service / Scout-reliance promotion and later Roberta adoption under separate gates;
4. future Ethereum support only under an explicit capability/verification plan.

None of these items starts Controlled Execution or widens the accepted Learning System Phase 10 retention gate.

## Core rule

**Roberta learns from preserved evidence without turning generated output into truth. CMIS verifies changing market/blockchain state. Chain Scouts investigate and interpret without inventing facts. Roberta coordinates, applies policy, and explains. The system becomes more capable by proving more—not by guessing more.**