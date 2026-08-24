# Pyramid legacy source-provenance migration

Issue #178 / PR #179 define the migration gate for the historical local Mastering Blockchain Fourth Edition Level 1 Pyramid package.

## Purpose

The original `mastering_blockchain_4e_2023_book01` package was used for a canonical 1,000-question Level 1 run before the accepted Learning System source-provenance contract existed. That historical package and its checkpoints remain audit inputs and must not be rewritten merely to satisfy a newer contract.

The migration therefore creates a **new package**. It preserves the historical curriculum id and exercise semantics while adding the canonical Learning System source binding required for source-grounded remediation.

## Preservation contract

Migration must preserve, in original order:

- every `exercise_id`;
- every question;
- every expected answer;
- every required reasoning point and forbidden inference;
- concept/subconcept, question type, difficulty, rubric id, integrity/Boss flags, and live-data flag;
- all legacy section source refs.

The only exercise-field extension is adding `mastering_blockchain_4e_2023` to `source_refs`.

Historical checkpoint files are read-only. The migration may verify that checkpoint exercise ids still resolve in the migrated bank, but it cannot rewrite checkpoint bytes or rerun Roberta's answers.

## Page-coordinate boundary

The legacy `source_map.json` identifies its ranges as **PDF pages**. Those values are not silently upgraded to printed-book page numbers.

Source-provenance locators therefore support exactly one explicit coordinate field:

- `book_pages` for verified printed-book coordinates; or
- `pdf_pages` for PDF-document coordinates.

A locator containing both or neither fails closed. Legacy migration emits `pdf_pages` and retains the original `legacy_source_ref`. The migration also verifies that the numeric page range encoded in the legacy alias exactly matches its `source_map.json` `PDF pages X-Y:` declaration.

This coordinate metadata is provenance only. It does not create source truth, live-state truth, or any execution authority.

## Local migration

After PR #179 is accepted and pulled locally:

```bash
roberta-pyramid-migrate-provenance \
  --curriculum curricula/mastering_blockchain_4e_2023 \
  --output curricula/mastering_blockchain_4e_2023_provenance \
  --checkpoints .roberta/pyramid_regraded/mastering_blockchain_4e_2023_book01/3f5f278c645b9e73
```

Expected historical-bank result for the known local package:

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

Do not continue if any identity/preservation gate is false.

## Regenerate remediation handoffs

The pre-migration handoff JSONL binds the old exercise `source_refs`. Because the migrated exercises intentionally add the canonical source key, handoffs must be regenerated from the same regraded v2 checkpoints rather than edited in place.

Use a new output directory:

```bash
roberta-pyramid-remediate \
  --curriculum curricula/mastering_blockchain_4e_2023_provenance \
  --checkpoints .roberta/pyramid_regraded/mastering_blockchain_4e_2023_book01/3f5f278c645b9e73 \
  --output .roberta/pyramid_remediation/mastering_blockchain_4e_2023_book01/3f5f278c645b9e73-provenance \
  --practice-per-weakness 5 \
  --seed remediation-l1-20260823-01
```

For the known regrade, the expected weak-item/handoff count remains 109. The generated handoff identities may change because source refs are part of the handoff contract; the checkpoint bytes and Roberta answers do not change.

## Source-grounded reconstruction

The Mastering Blockchain source is an external exact transcript. The repository stores the immutable source identity and hashes but not the copyrighted transcript bytes.

After regeneration:

```bash
roberta-pyramid-source-reconstruct \
  --curriculum curricula/mastering_blockchain_4e_2023_provenance \
  --handoffs .roberta/pyramid_remediation/mastering_blockchain_4e_2023_book01/3f5f278c645b9e73-provenance/learning_handoffs.jsonl \
  --checkpoints .roberta/pyramid_regraded/mastering_blockchain_4e_2023_book01/3f5f278c645b9e73 \
  --output .roberta/pyramid_reconstruction/mastering_blockchain_4e_2023_book01/3f5f278c645b9e73-provenance \
  --source-transcript "$MB4E_TRANSCRIPT" \
  --top-k 5
```

The reconstruction remains remediation evidence only. It does not declare a weakness corrected, create a verified lesson, mutate HXMP, change CMIS/provider authority, or authorize Controlled Execution.

## Acceptance gates

PR acceptance requires:

1. targeted migration/provenance tests;
2. full deterministic suite: `python -m pytest -v -m 'not live and not cmis_live'`;
3. independent Spec Fidelity review;
4. independent Code/Architecture Quality review;
5. independent Authority/Safety Boundary review;
6. no unresolved blocker before merge.
