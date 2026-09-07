# ROBERTA Evaluation Telemetry v1

Contract version: `roberta_evaluation_telemetry/v1`

## Purpose

This contract gives the independent `roberta-eval` Laboratory a read-only, opt-in view of machine-readable structures already attached to ROBERTA's final response. It exists so a live evaluation can compare bounded canonical claims to the exact accepted response evidence without re-running ROBERTA, querying CMIS a second time, or injecting Laboratory fixtures into production truth.

## Request

Normal bridge requests remain unchanged:

```json
{"message":"Should I buy XNT?"}
```

Evaluation telemetry is requested explicitly:

```json
{
  "message":"Should I buy XNT?",
  "evaluation_mode":"roberta_evaluation_telemetry/v1"
}
```

No other evaluation-mode value is accepted.

## Response extension

When evaluation mode is requested, the normal `service`, `status`, and `reply` fields remain present and the bridge may additionally return:

- `evaluation_telemetry_version`
- `evaluation_evidence`
- `claims`
- `evidence_provenance`
- `evidence_freshness`
- `execution_authorized`

`evaluation_evidence` is limited to accepted final-message structures already produced by ROBERTA:

- `roberta_human_response_decision`
- `roberta_opinion`
- `roberta_claim_integrity`
- `roberta_human_renderer`

The public bridge does not expose raw provider credentials, hidden prompts, a second CMIS query, or a new fact engine.

## Canonical claims

v1 emits claims only from the accepted `roberta_human_response_decision/v1` object. Each claim contains an `evidence_path` into `evaluation_evidence` and the exact value found at that path.

If no accepted Human Response Decision is available, `claims` is empty. The Laboratory must treat that as evidence required rather than guessing from prose.

## Claim Integrity

A complete bounded live PASS requires the accepted final message to carry `roberta_claim_integrity/v1` with `status=PASS`.

That certificate is intentionally bounded. It does not certify upstream provider truth and does not certify every natural-language statement in the response. The Laboratory must preserve those limitations.

## Freshness

Freshness is projected only from the accepted Human Response Decision evidence profile. If no accepted freshness state is exposed there, telemetry reports `UNAVAILABLE`; it does not infer freshness from timestamps.

## Execution boundary

This contract is read-only. `execution_authorized` remains false unless an accepted final-message structure explicitly violates that invariant, in which case telemetry exposes the violation so the Laboratory can fail the run.

## Security and compatibility

- Normal bridge behavior is unchanged when `evaluation_mode` is absent.
- Existing bearer-token rules remain in force.
- Non-loopback binding still requires `ROBERTA_API_KEY`.
- Evaluation mode does not enable tool selection or provider routing controls.
- Synthetic Laboratory fixtures never become live ROBERTA evidence.
