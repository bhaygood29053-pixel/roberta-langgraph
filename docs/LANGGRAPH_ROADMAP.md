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
- **Learning System Phase 5 — deterministic retrieval + benchmark foundation (#118/#119).**

Phase 5 — X1 Evidence Completeness remains deliberately **bounded**, with explicit verified/bounded/partial/unavailable/conflict/insufficient-evidence states.

Roberta Phase 11 — Controlled Execution remains **locked / not started**.

The **Roberta Learning System is the primary active development track**. Existing CMIS, Chain Scout, transport, policy, memory, and approval paths should remain stable unless a change is directly required to support the Learning System or fix a proven defect.

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

The Learning System follows the evidence-grounded design in [`LEARNING_SYSTEM.md`](./LEARNING_SYSTEM.md), [`LEARNING_SYSTEM_STRUCTURE.md`](./LEARNING_SYSTEM_STRUCTURE.md), [`LEARNING_SYSTEM_CHUNKING.md`](./LEARNING_SYSTEM_CHUNKING.md), [`LEARNING_SYSTEM_INDEXING.md`](./LEARNING_SYSTEM_INDEXING.md), [`LEARNING_SYSTEM_RETRIEVAL.md`](./LEARNING_SYSTEM_RETRIEVAL.md), and the broader Roberta Learning System Specification v1.1.

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

### Learning System Phase 6 — Grounded answer + citation foundation ⬜ Next

The next narrow target is to turn an accepted `RetrievalResult` into a bounded evidence packet that a model can explain without converting generated language into evidence.

The first accepted slice should establish:

```text
RetrievalResult
  -> deterministic EvidencePacket
  -> bounded answer request
  -> model-generated answer candidate
  -> deterministic citation / evidence-binding validation
  -> GroundedAnswerResult
```

Phase 6 should preserve, at minimum:

- exact retrieval/query identity and selected `chunk_id` set as the only static evidence scope for one answer attempt;
- stable evidence labels/anchors that bind citations to exact source/document/section/chunk identity and source line range;
- explicit packet status for `ok`, `partial`, conflict-present, and insufficient/no-evidence conditions;
- source authority/approval metadata as evidence context, not a model-computed truth score;
- a model-facing contract that treats retrieved source text as untrusted data/evidence rather than system instructions;
- deterministic validation that every answer citation references an evidence anchor actually present in the packet;
- explicit unsupported-claim / missing-citation handling rather than silently accepting generated statements;
- explicit disclosure when retrieved sources disagree or when retrieval is partial/insufficient;
- strict separation between static Learning System evidence and freshness-sensitive CMIS/provider facts;
- no automatic write from generated answer/reflection text into trusted source knowledge or durable verified memory;
- evaluation fixtures for citation correctness, unsupported claims, contradictory evidence, no-answer cases, and prompt-injection-looking source text.

Phase 6 should **not** yet add autonomous reflection-to-lesson promotion, concepts/knowledge graph, adaptive curriculum, fine-tuning, or a production pgvector dependency. Model reranking should remain deferred unless retrieval benchmarks identify a concrete failure mode that deterministic candidate generation cannot address.

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

The first narrow CMIS 1.9 promotion/adoption and the current Solana read-only readiness gate are complete. Additional read-only intelligence work remains valid but is not the primary Roberta development track while the Learning System is being built. Future CMIS/Scout work should proceed only through separately accepted deterministic contracts, especially:

1. deterministic inference/classification contracts before behavioral/ownership labels;
2. wallet relationship evidence with explicit non-ownership semantics;
3. evidence-backed alerts with explicit scope/freshness/threshold/persistence rules;
4. deeper X1 provider-gap and historical redundancy verification;
5. field-by-field Solana maturity beyond the currently accepted Scout surface;
6. future Ethereum support only under an explicit capability/verification plan.

None of these items starts Controlled Execution or overrides the Learning System's current priority.

## Core rule

**Roberta learns from preserved evidence without turning generated output into truth. CMIS verifies changing market/blockchain state. Chain Scouts investigate and interpret without inventing facts. Roberta coordinates, applies policy, and explains. The system becomes more capable by proving more—not by guessing more.**