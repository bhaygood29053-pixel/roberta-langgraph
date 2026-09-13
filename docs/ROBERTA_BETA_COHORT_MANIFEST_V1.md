# ROBERTA Beta Cohort Manifest v1

## Purpose

`roberta_beta_cohort_manifest/v1` fixes the Cohort 001 measurement ambiguity between:

- raw Ask ROBERTA response events;
- moderator-selected scored scenarios; and
- actual participant count.

The beta JSONL remains append-only and content-free. The manifest is a moderator-side accounting file used only when producing `roberta_beta_cohort_summary/v2`.

## Contract

```json
{
  "contract_version": "roberta_beta_cohort_manifest/v1",
  "participant_count": 1,
  "scenarios": [
    {
      "scenario_id": "C01",
      "automatic_event_index": 1,
      "manual_score": "PASS"
    }
  ]
}
```

### Fields

- `participant_count` is the moderator-declared number of real cohort participants represented by the selected scenario set. It is a count only; no participant identity is stored.
- `scenario_id` is a bounded moderator label such as `C01` through `C07`.
- `automatic_event_index` is the 1-based ordinal among `automatic_response_outcome` records in the append-only beta JSONL. It selects an event without persisting prompt text, response text, addresses, hashes, or user-entered identifiers.
- `manual_score` is one of `PASS`, `PARTIAL`, or `FAIL` and remains explicitly separate from the automatic evidence-state outcome (`success`, `evidence_required`, `unavailable`).

Each scenario id and automatic event index must be unique within one manifest.

## Privacy boundary

The manifest schema rejects extra fields. It therefore cannot contain participant names/ids, prompt/reply text, wallet/token addresses, transaction hashes, raw evidence, tool arguments, or cross-session tracking ids.

The v2 aggregate emits no response ids and no selected event indices. Response ids are used only transiently in memory to preserve the already-accepted feedback join for included events.

`execution_authorized=false` remains invariant.

## Summary semantics

Run:

```bash
python scripts/summarize_beta_product_proof.py \
  results/public-beta/cohort-001.jsonl \
  --manifest results/public-beta/cohort-001.manifest.json \
  --output results/public-beta/cohort-001-summary-v2.json
```

With a manifest, the CLI returns `roberta_beta_cohort_summary/v2` where:

- `cohort_size` and `participant_count` mean declared real participant count;
- `response_event_count` means every automatic response event in the JSONL;
- `included_response_event_count` means selected scored scenario events;
- `excluded_response_event_count` means setup/retry/other response events excluded from cohort scoring;
- `scenario_count` means selected scored scenarios;
- `manual_score_counts` and `by_scenario` report moderator rubric scores separately from automatic evidence state;
- workflow/outcome/evidence rates and ranked product signals use only selected scenario events;
- feedback metrics use only feedback joined to selected scenario events.

The legacy v1 summary remains available when `--manifest` is omitted, but its historical `cohort_size` field is response-event count and must not be interpreted as participant count.

## Cohort 001 use

For the first Cohort 001 pass, keep the original 13-event JSONL unchanged. Build a local manifest selecting only the seven accepted scored C01-C07 response events. Setup attempts and retries remain preserved in the append-only source but are excluded from v2 cohort metrics.

This is measurement-only. It does not change ROBERTA facts, routing, Human wording, evidence state, execution authority, or any C01-C07 prompt/rubric.
