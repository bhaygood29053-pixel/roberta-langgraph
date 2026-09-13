# Cohort 001 — Interim telemetry reconciliation

Status: **PENDING LOCAL PRIVACY-SAFE SUMMARY OUTPUT**

The seven-scenario manual baseline is frozen in `docs/COHORT_001_INTERIM_MANUAL_SCORE_2026-09-13.md`.

Accepted automatic summary command:

```bash
.venv-runtime/bin/python scripts/summarize_beta_product_proof.py \
  results/public-beta/cohort-001.jsonl \
  --output results/public-beta/cohort-001-interim-summary.json
```

Before remediation starts, reconcile the generated `roberta_beta_cohort_summary/v1` aggregate against the manual baseline. In particular verify cohort size, workflow classification, automatic outcomes, evidence-required unknown counts, evidence quality, feedback coverage, privacy invariants, and `execution_authorized=false`.

Do not copy prompt text, reply text, wallet/token addresses, transaction hashes, raw evidence, tool arguments, user-entered identifiers, response ids, or persistent user identity into this checkpoint.

Final remediation/rerun order remains intentionally unset until the automatic aggregate has been reviewed.
