# Roberta Learning Command Center — Dashboard MVP

The Pyramid dashboard is a local **read-only** view of the SQLite Pyramid training ledger.

It does not approve lessons, mutate Learning System state, call CMIS/providers, write HXMP, or trigger execution.

## Start the dashboard

After installing Roberta from this branch:

```bash
roberta-pyramid-dashboard --db .roberta/pyramid_training.sqlite3
```

Default address:

```text
http://127.0.0.1:8770
```

The server binds loopback by default. Keep it loopback-only unless a later authenticated deployment contract is accepted.

## Current views

The MVP displays:

- highest level reached across the selected ledger;
- total Pyramid runs and mastered runs;
- latest run status/curriculum;
- a 20-level Pyramid progress graphic;
- recent level-accuracy learning curve;
- ranked failure-mode bars;
- recent run history.

The JSON backing view is available at:

```text
GET /api/summary
```

Optional curriculum filtering is supported with:

```text
/?curriculum=<curriculum_id>
/api/summary?curriculum=<curriculum_id>
```

## Ledger creation

The dashboard itself never creates the database. A training process creates it through:

```python
from roberta.learning.training_ledger import PyramidTrainingLedger

ledger = PyramidTrainingLedger(".roberta/pyramid_training.sqlite3")
run_id = ledger.start_run("book001", "random-run-seed")
```

The Pyramid evaluator then records each completed level and its failure-code counts.

## Security and authority

The dashboard uses SQLite read-only mode. It is an observability surface only.

It must never be interpreted as:

- a verified-lesson retention store;
- RAG or source truth;
- current blockchain truth;
- CMIS/provider capability control;
- human lesson-retention approval;
- wallet/execution approval.

Fresh accepted CMIS/provider evidence remains authoritative for freshness-sensitive blockchain facts regardless of any score or historical lesson visible in the dashboard.

## Planned later additions

After the core runner and first book curriculum prove stable, later separately gated dashboard slices may add:

- concept mastery heat maps;
- book-library comparison;
- adversarial/evidence-discipline metrics;
- question-leakage and duplicate-rate diagnostics;
- candidate-lesson review links into the accepted Learning System retention workflow;
- Master Pyramid cross-book progress.

Any write/approval UI must remain behind the Learning System's accepted human-approval/retention contract rather than being added to this read-only dashboard by convenience.
