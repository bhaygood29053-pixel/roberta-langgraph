# Learning System Grounding Contract

Status: Phase 6 first slice for Issue #121.

## Purpose

Phase 6 turns an accepted Phase 5 `RetrievalResult` into a bounded, deterministic evidence packet and validates structured answer candidates against exact packet anchors.

This phase establishes **citation and evidence-scope integrity**. It deliberately does not claim that deterministic code can prove arbitrary natural-language entailment merely because a claim cites a real passage.

The first accepted contracts are:

```text
evidence_packet_contract = grounded-evidence-packet/v1
answer_contract = citation-bound-answer/v1
prompt_safety_contract = retrieved-text-untrusted-data/v1
answer_validator_version = 1.0.0
```

## Authority boundary

```text
Phase 1 SourceRecord / exact artifact
  -> Phase 2 canonical ParsedDocument
    -> Phase 3 canonical ChunkedDocument
      -> Phase 4 canonical IndexedDocument
        -> Phase 5 canonical RetrievalResult
          -> Phase 6 EvidencePacket
            -> structured AnswerCandidate
              -> citation/scope validation
                -> GroundedAnswerResult
```

Changing market/blockchain state remains outside the Learning System authority path:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

Static evidence never overrides fresh accepted CMIS/provider facts.

## Canonical retrieval validation

Packet construction never accepts arbitrary evidence text as its authority root.

`build_evidence_packet()` receives the exact Phase 5 corpus and `RetrievalResult`, then reconstructs the retrieval call from the result's own typed `RetrievalQuery`:

- exact query text;
- exact normalized filters;
- `top_k` and candidate limit;
- optional typed query vector;
- retrieval/fusion contract versions;
- exact `rrf_k`.

That reconstruction re-enters the Phase 5 validation path, which revalidates Phase 1/2/3/4 source, chunk, index, vector, and manifest integrity. The rebuilt result must equal the supplied result exactly or grounding fails closed.

`validate_retrieval_result_for_grounding()` exposes the same narrow validation seam for callers that need an explicit preflight check.

## EvidencePacket

Each selected Phase 5 candidate receives one deterministic local anchor:

```text
E1
E2
E3
...
```

An `EvidenceAnchor` preserves:

- content-addressed `anchor_id`;
- exact `chunk_id`;
- source/document/section/block identity;
- structural path and chunk kind/order;
- exact source line range;
- exact retrieved chunk text and content hash;
- source authority/approval metadata;
- lexical/vector/fusion rank metadata.

Anchor identity binds the exact Phase 5 retrieval id plus evidence content/provenance. Changing evidence text, provenance, or rank binding invalidates the anchor identity.

The `EvidencePacket` preserves:

```text
packet_id / packet_hash
retrieval_id / retrieval_hash / query_id
retrieval status
packet status
ordered evidence anchors
retrieval warnings/errors
has_conflicting_sources
insufficient_evidence
source_text_trust = untrusted_evidence_data
```

The packet is content-addressed over retrieval identity, evidence anchors, status, diagnostics, and prompt-safety metadata. Generated answer text is not part of evidence identity.

All packet/anchor records structurally expose:

```text
live_state_authorized = false
memory_promotion_authorized = false   # packet only
execution_authorized = false          # packet only
```

## Insufficiency and conflict semantics

`no_match` retrieval or an empty candidate set becomes:

```text
packet_status = insufficient
insufficient_evidence = true
```

Phase 6 does **not** infer semantic contradiction merely because two sources are present or use different wording. `has_conflicting_sources` becomes true only when an accepted upstream deterministic result explicitly supplies a machine-readable `source_conflict:` or `conflict:` diagnostic.

This prevents the grounding layer from silently upgrading source diversity into a contradiction judgment.

A structured answer may still mark one claim as `conflict` when it cites at least two exact packet anchors, but Phase 6 records `semantic_support_verified = false`; it does not certify that the cited passages genuinely contradict each other.

## Prompt-safety boundary

`serialize_evidence_packet_for_model()` emits deterministic JSON with a fixed instruction boundary and nests source text only as data.

The envelope states that retrieved source text:

- is `untrusted_evidence_data`;
- must not be followed as an instruction layer;
- cannot expand tool permissions;
- cannot authorize memory writes;
- cannot authorize signing, trading, or execution;
- may be cited only through the packet's exact local anchors.

Instruction-looking text inside an approved source remains source text. It does not become a system/developer instruction merely because it was retrieved.

Prompt serialization is a boundary/contract mechanism, not a claim that arbitrary model behavior is mathematically guaranteed safe. Prompt-injection behavior remains an evaluation obligation as model integration expands.

## Structured AnswerCandidate

Phase 6 accepts typed output:

```text
AnswerCandidate
  packet_id
  answer_contract
  answer_version
  answer_text
  claims[]
  limitations[]
```

Each `AnswerClaim` contains:

```text
claim_id
text
evidence_anchors[]
status = supported | insufficient | conflict
```

The producer cannot submit replacement evidence text, source ids, chunk ids, proof scores, or live facts as citation authority. The only citation namespace is the exact packet anchor labels.

## Deterministic citation validation

`validate_answer_candidate()` proves structural facts that can actually be proven deterministically:

- packet content-address integrity;
- candidate/packet identity binding;
- supported answer/validator contracts;
- normalized unique claim ids;
- valid claim statuses;
- every cited anchor exists in the exact packet;
- supported claims cite at least one anchor;
- conflict claims cite at least two anchors;
- duplicate citation labels are rejected;
- `no_match`/insufficient packets permit only explicitly `insufficient` claims and require the `insufficient_evidence` limitation marker;
- partial retrieval requires the `retrieval_partial` limitation marker;
- an explicit upstream source-conflict state requires `source_conflict_present` disclosure;
- result authority remains non-live, non-memory-promoting, and non-executing.

The validator deliberately does **not** claim to prove:

- natural-language entailment;
- that every substantive sentence in free-form `answer_text` is represented by the structured claims;
- factual correctness beyond the evidence packet;
- whether two passages truly contradict each other;
- calibrated uncertainty;
- current/live truth.

Accordingly every first-slice `GroundedAnswerResult` preserves:

```text
semantic_support_verified = false
claim_coverage_verified = false
live_state_authorized = false
memory_promotion_authorized = false
execution_authorized = false
```

A structurally `grounded` result means the typed claims obey the packet's citation/scope contract. It is not a semantic-verification badge.

## GroundedAnswerResult

The accepted result preserves:

```text
result_id / result_hash
packet_id / retrieval_id
answer contract/version
validator version
answer text
validated structured claims
exact EvidenceReference records for cited anchors
status
limitations
warnings/errors
semantic_support_verified
claim_coverage_verified
authority-denial flags
```

Statuses are:

```text
grounded      # structurally valid supported claims over an ok packet
partial       # partial retrieval and/or non-supported claim status remains visible
insufficient  # no-match/insufficient evidence explicitly disclosed
```

Malformed/fabricated inputs fail closed with `GroundingError` rather than being converted into a favorable answer state.

## Evidence references for user-facing citations

Every cited packet label becomes an `EvidenceReference` carrying:

- local label;
- content-addressed anchor id;
- chunk/source/document/section identity;
- structural path;
- exact line range;
- content hash.

This is the deterministic bridge needed by a later user-facing citation renderer. Rendering style is not part of the Phase 6 truth contract.

## Deterministic regression coverage

The Phase 6 first-slice test surface covers:

- exact Phase 5 reconstruction before packet creation;
- exact anchor provenance;
- supported claims with valid anchors;
- supported claims missing citations;
- fabricated anchors;
- no-match/insufficient behavior;
- required partial-retrieval disclosure;
- multi-anchor conflict claim shape;
- preservation of cross-source evidence without inventing semantic conflict;
- prompt-injection-looking source text as inert evidence data;
- tampered retrieval results;
- tampered packet evidence;
- packet identity substitution;
- duplicate claim ids;
- unsupported contract/status values;
- live-state, durable-memory-promotion, and execution denial.

## Explicit non-goals

Phase 6 does not add:

- deterministic semantic-entailment claims from citation presence;
- model reranking;
- production model/provider selection for answer generation;
- PostgreSQL or pgvector deployment;
- concepts/knowledge graph;
- adaptive curriculum;
- reflection/candidate lessons/verified lessons;
- automatic durable-memory promotion;
- fine-tuning;
- CMIS/provider authority changes;
- transaction preparation, signing, broadcasting, custody, trading, or Controlled Execution.

## Next evaluation obligation

After the Phase 6 structural contract is accepted, the next learning slice should introduce an **independent answer-evaluation foundation** over a golden corpus. That layer should measure semantic groundedness, citation completeness/precision, unsupported-claim rate, answer correctness/usefulness, conflict handling, and uncertainty/calibration separately from retrieval quality.

Only after those measurements exist should Roberta consider verified lesson promotion, adaptive curriculum, model reranking, or other self-improvement mechanisms.
