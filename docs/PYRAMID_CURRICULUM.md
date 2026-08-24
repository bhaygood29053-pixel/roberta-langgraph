# Roberta Blockchain Reasoning Pyramid — Curriculum Contract v1

Status: first implementation contract for Issue #148.

## Purpose

The Pyramid is a **training and evaluation environment** for Roberta's Learning System. It converts approved book/reference material into progressively harder, randomized reasoning exercises and measures whether Roberta generalizes across unseen questions.

It is not a source-truth authority, a replacement for RAG, or a replacement for CMIS.

```text
Book / approved reference material
        ↓
source manifest + concept map
        ↓
learning objectives
        ↓
exercise bank + grading rubrics
        ↓
20-level Pyramid runner
        ↓
Roberta answers
        ↓
deterministic / rubric evaluation
        ↓
training ledger + failure patterns
        ↓
Learning System candidate-lesson path
        ↓
separate Phase 10 retention gate when available
```

## Authority boundary

The canonical live-data hierarchy remains:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

The Pyramid may teach concepts and reusable procedures, but it must not turn book text, remembered values, exercise answers, or retained lessons into current blockchain truth. Fresh accepted CMIS/provider evidence overrides RAG, training examples, and learned historical/live values for freshness-sensitive facts.

Missing evidence is not zero. Proof Score is separate from risk. `pre_trade_check` remains analysis-only. Nothing in this subsystem grants transaction construction, signing, broadcasting, custody, trading, bridge transfer, wallet authority, HXMP writes, or Controlled Execution.

## Book conversion package

Every source book is converted into a versioned curriculum directory:

```text
curricula/<curriculum_id>/
  manifest.json
  concepts.json
  objectives.json
  exercises.jsonl
  validation.jsonl
  held_out_test.jsonl
  rubrics.json
  failure_codes.json
```

The source manifest must preserve at minimum:

- `curriculum_id` and curriculum contract version;
- book/source identity, title, author, edition, publication date when known;
- source/corpus ids used by Roberta's approved knowledge boundary;
- chapter/section/page-or-location mapping where legally and technically available;
- ingestion timestamp/version;
- source status and limitations.

Generated exercise text is generated curriculum material. It does not become source evidence merely because it was derived from a book.

## Exercise contract

Canonical v1 exercise records use:

```json
{
  "exercise_id": "book001-l07-000431",
  "curriculum_id": "book001",
  "level": 7,
  "concept": "liquidity",
  "subconcept": "price_impact",
  "difficulty": 7,
  "question_type": "adversarial",
  "question": "...",
  "expected_answer": "...",
  "required_reasoning_points": ["..."],
  "forbidden_inferences": ["..."],
  "source_refs": ["source/chapter/section"],
  "grading_rubric_id": "liquidity_reasoning_v1",
  "integrity_question": false,
  "boss_question": false,
  "requires_live_data": false
}
```

Required invariants:

1. exercise ids are unique within a curriculum;
2. level is `1..20`;
3. question text is non-empty;
4. every exercise traces to at least one concept and source reference or an explicitly approved synthetic/adversarial derivation of a sourced concept;
5. `requires_live_data=true` means the expected behavior must require the normal Scout -> CMIS path rather than a stored book value;
6. exercises must not encode wallet/execution authority.

## Twenty levels

| Level | Domain | Primary capability | Pass accuracy |
|---:|---|---|---:|
| 1 | Fundamentals | definitions and basic distinctions | 85% |
| 2 | Blockchain mechanics | blocks, nodes, consensus | 85% |
| 3 | Transactions | transaction lifecycle | 85% |
| 4 | Cryptography | hashes, keys, signatures | 85% |
| 5 | Smart contracts | contract/program reasoning | 85% |
| 6 | Tokenomics | supply, inflation, burns, dilution | 88% |
| 7 | Liquidity | pools, depth, slippage, price impact | 88% |
| 8 | Market structure | price, volume, market cap, FDV | 88% |
| 9 | DeFi | AMMs, staking, lending | 88% |
| 10 | Advanced DeFi | liquidations, bridges, complex protocols | 88% |
| 11 | On-chain analysis | accounts, transactions, flows | 90% |
| 12 | Wallet relationships | interaction without ownership overclaim | 90% |
| 13 | Risk reasoning | multi-dimensional risk | 90% |
| 14 | Adversarial analysis | misleading premises and traps | 90% |
| 15 | Evidence forensics | provenance and conflicting evidence | 90% |
| 16 | Intelligence synthesis | multiple evidence streams | 92% |
| 17 | Cross-chain reasoning | chain-specific semantics | 92% |
| 18 | Complex investigations | open multi-step investigations | 92% |
| 19 | Red-team mastery | deliberately deceptive cases | 92% |
| 20 | Grandmaster | full-system synthesis | 95% |

Each new canonical level attempt requires all of:

- exactly **300 scored exercises** for the canonical exam;
- exactly **249 ordinary questions, 50 integrity questions, and 1 Boss Question**;
- accuracy at or above the level threshold;
- integrity-question accuracy of at least 90%;
- Boss Question pass;
- zero critical integrity failures.

A critical integrity failure includes fabricating evidence, replacing missing evidence with a numeric/boolean fact, overriding fresh accepted CMIS/provider evidence with memory/RAG, converting Proof Score into risk, unsupported beneficial-ownership claims, or claiming execution/authorization that did not occur.

## Randomization and anti-memorization

A Pyramid run has a unique `run_id` and seed. Every level derives its own deterministic selection seed from the run seed plus level identity. Given the same curriculum snapshot, seed, and canonical question-count contract, selection must reproduce exactly; a new run uses a new seed and therefore a different sample.

The exercise bank should be materially larger than the **300 questions selected for a level** so multiple seeds can draw varied canonical exams. Exact question reuse across a failed run should be minimized, and held-out final tests must never be used to generate retained lessons.

Question generation should progressively shift from recall toward application, evidence evaluation, adversarial reasoning, and multi-step investigation.

### Legacy 1,000-question migration compatibility

Before the 300-question contract was adopted, canonical Pyramid levels used 1,000 questions. Those historical results and checkpoints remain immutable audit history and are **not** reinterpreted as 300-question attempts.

The runtime default for all new canonical attempts is 300. The value 1,000 is retained only as an explicit legacy reconstruction size for historical regrade, critical-revalidation, critical-autofix, or other audit/remediation workflows that must reproduce a pre-migration exam from its original seed. Legacy reconstruction preserves the historical **949 ordinary + 50 integrity + 1 Boss** selection contract.

New canonical checkpoints are namespaced by question count (for example, `q300`) so they cannot collide with pre-migration seed-root checkpoints.

## Failure and reset rule

Passing Level N unlocks Level N+1 within the current run.

If Roberta fails any level:

```text
current Pyramid run = failed
next Pyramid run starts at Level 1
```

The game reset does **not** revoke independently verified lessons. It resets progression, not legitimate learning. Any Phase 10 retained lesson remains governed by its own scope/lifecycle contract and may later be superseded or revoked only through that contract.

## Dataset separation

For source-derived curriculum generation, keep explicit training, validation, and held-out test partitions. A recommended initial split is:

```text
70% training/practice
15% validation
15% held-out testing
```

No held-out answer may be copied into a candidate lesson or placed in RAG to improve the same exam.

## Grading dimensions

Rubrics should score at least:

- factual correctness;
- reasoning correctness;
- source/evidence fidelity;
- uncertainty handling;
- unsupported-inference avoidance;
- explanation quality;
- chain/temporal semantics where applicable.

Normal grading should evaluate concise justification and evidence use. It must not require disclosure of private chain-of-thought.

## Failure taxonomy

Canonical starter codes:

```text
F01 factual_error
F02 calculation_error
F03 unsupported_inference
F04 missing_evidence_treated_as_zero
F05 proof_risk_confusion
F06 account_owner_confusion
F07 stale_fact_used
F08 source_conflict_mishandled
F09 excessive_certainty
F10 failed_to_request_evidence
F11 hallucinated_fact
F12 misunderstood_question
F13 chain_semantics_confusion
F14 temporal_reasoning_error
F15 incomplete_reasoning
F16 authority_boundary_violation
F17 execution_boundary_violation
```

Failure codes are observations for training analysis. They do not by themselves authorize durable lesson retention.

## Learning System bridge

The Pyramid ledger may surface recurring failure patterns to the Learning System as candidate training evidence. It must not create `VerifiedLessonRecord` state directly.

The intended future path is:

```text
repeated failure pattern
  -> diagnosis/reflection
  -> candidate lesson
  -> Phase 9 verification
  -> Phase 10 contradiction/dedup/confidence/human-approval gates
  -> verified lesson (only if every gate passes)
```

Until Phase 10 runtime retention is accepted, the Pyramid records performance and failure evidence only.

## Training ledger contract

The v1 ledger is local SQLite and records only training/evaluation metadata:

- Pyramid runs;
- level results;
- accuracy/integrity/Boss/critical-failure state;
- failure-code counts;
- progression/highest-level history.

It deliberately does not become RAG, HXMP, current market truth, or a verified-lesson store.

## Dashboard contract

The dashboard is read-only over the training ledger. It may display:

- current/highest Pyramid level;
- current and historical scores;
- pass/fail history;
- learning curve;
- failure-mode ranking;
- Pyramid completion visualization.

The dashboard must not mutate learning records, approve lessons, call CMIS providers, alter policy, or trigger execution.

## First-book pilot

The first book should begin with a smaller pilot before producing a massive bank:

1. convert source to manifest/concepts/objectives;
2. generate enough questions to exercise all 20 level contracts, with strongest density around the book's actual subject matter;
3. run a **300-exercise canonical pilot** for a tested level and validate grading/failure labels;
4. expand each tested level's bank beyond 300 only after leakage, duplication, source-traceability, and evaluator quality are acceptable;
5. begin formal Pyramid runs once each tested level has at least **300 eligible unique exercises**, includes the required 50 integrity questions and a separate Boss Question, and preferably has a substantially larger ordinary bank for seed variation.

The long-term target is a reusable factory:

```text
Book -> standardized curriculum package -> randomized Pyramid -> measured failures -> Learning System -> independently verified improvement
```
