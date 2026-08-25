# Pyramid legacy source-provenance migration

Last reconciled: 2026-08-25 (America/New_York)

Status: **accepted / merged under Issue #178 / PR #179**.

## Purpose

The historical local *Mastering Blockchain, Fourth Edition* Level 1 Pyramid package was used for a canonical 1,000-question run before the accepted Learning System source-provenance contract existed.

The migration preserves that historical package/checkpoint history as immutable audit input and creates a **new provenance-bearing package** with the same curriculum/exercise semantics plus the canonical Learning System source binding.

## Preservation contract

The accepted migration preserves, in original order:

- every `exercise_id`;
- every question;
- every expected answer;
- every required reasoning point and forbidden inference;
- concept/subconcept, question type, difficulty, rubric id, integrity/Boss flags, and live-data flag;
- all legacy section source refs.

The intentional exercise-field extension is the canonical source key:

```text
mastering_blockchain_4e_2023
```

Historical checkpoint files remain read-only. The migration may verify checkpoint exercise IDs against the migrated bank, but it does not rewrite checkpoint bytes or rerun Roberta's answers.

## Page-coordinate boundary

The legacy source map identifies its ranges as **PDF pages**. Those values are not silently relabeled as printed-book page numbers.

Source-provenance locators support exactly one explicit coordinate basis:

```text
book_pages
pdf_pages
```

Both or neither fails closed. The MB4E legacy migration emits `pdf_pages` and retains the original legacy source-ref alias.

The range encoded in each legacy alias must agree with its source-map PDF-page declaration.

Basis-aware locator handling is available to the core reconstruction path, not only the CLI wrapper, so migrated packages behave consistently for programmatic and console callers.

## Atomic migration output

The migration validates historical input before derivation, rejects output paths equal to or nested under the historical package, writes the complete migrated package and `migration_report.json` inside staging, validates staging, and only then atomically publishes the output directory.

A failed report/package write must not leave a misleading partially published migrated package.

## Local migration reference

```bash
roberta-pyramid-migrate-provenance \
  --curriculum curricula/mastering_blockchain_4e_2023 \
  --output curricula/mastering_blockchain_4e_2023_provenance \
  --checkpoints .roberta/pyramid_regraded/mastering_blockchain_4e_2023_book01/3f5f278c645b9e73
```

For the known historical bank the expected preservation shape is:

```text
EXERCISES_BEFORE 1206
EXERCISES_AFTER 1206
PROVENANCE 1206
EXERCISE_IDS_IDENTICAL true
QUESTION_TEXT_IDENTICAL true
SEMANTIC_FIELDS_IDENTICAL true
CHECKPOINT_COMPATIBLE true
HISTORICAL_PACKAGE_MUTATED false
HISTORICAL_CHECKPOINTS_MUTATED false
PDF_PAGE_BASIS_PRESERVED true
```

## Regenerated remediation artifacts

Because `source_refs` are identity-bearing handoff data, pre-migration handoff JSONL must not be hand-edited. Remediation artifacts are regenerated from the same preserved/regraded checkpoint evidence against the migrated curriculum.

The regenerated handoff IDs may differ because the canonical source binding is part of the content-addressed handoff contract. Historical checkpoint bytes and Roberta answers remain unchanged.

## Source-grounded reconstruction

The full copyrighted MB4E transcript is not stored in the repository. Runtime reconstruction requires the exact externally supplied transcript bytes matching the pinned source integrity contract.

The reconstruction remains remediation evidence only. It does not declare a weakness mastered, promote a general verified lesson, mutate HXMP, change CMIS/provider authority, or authorize execution.

## Later accepted provenance hardening

The accepted migration is now complemented by later Pyramid provenance safeguards:

- exact PDF and transcript digest binding;
- verified PDF-page -> transcript-line alignment for supported MB4E remediation windows;
- PDF provenance scope resolution **before** lexical/vector ranking;
- fail-closed behavior for missing/tampered/unmapped page ranges;
- strict full-containment checks so candidate chunks and final evidence anchors cannot extend outside the declared provenance range;
- preservation of `book_pages` backward compatibility for sources using that coordinate basis.

These mechanisms strengthen evidence scope. They do not convert static book material into current/live blockchain truth.

## Authority boundary

The provenance migration and alignment system cannot authorize source approval changes, live-state facts, general durable-memory promotion, CMIS/provider trust mutation, governance changes, wallet signing, transaction preparation/broadcasting, custody, trading, bridge transfer, or Controlled Execution.
