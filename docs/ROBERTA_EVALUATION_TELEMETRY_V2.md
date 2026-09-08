# ROBERTA Evaluation Telemetry v2

Contract version: `roberta_evaluation_telemetry/v2`

## Purpose

v2 extends the accepted read-only Evaluation Telemetry v1 contract so the
independent `roberta-eval` Laboratory can grade factual/service answers that do
not legitimately produce a `roberta_human_response_decision/v1` object.

v1 remains unchanged. v2 is opt-in and versioned separately.

## Authority and query boundary

v2 may project factual claims only from the current user turn's structured
`x1_scout_investigate` result when that result is an X1 Scout report whose
source is CMIS. The projection uses the same ROBERTA graph invocation that
produced the user-facing answer.

v2 must not:

- infer claims from natural-language prose;
- query CMIS or a provider a second time;
- reuse a prior turn's Scout result as current evidence;
- force factual questions into `roberta_opinion/v1` or
  `roberta_human_response_decision/v1`;
- expose Scout `sources`, warnings, errors, credentials, prompts, or raw
  protected/provider-only internals;
- authorize execution.

Facts authority remains `chain_scout_cmis`. ROBERTA remains the user-facing
synthesis/judgment authority.

## Factual evidence projection

When gradeable current-turn structured evidence exists, v2 may add:

- `evaluation_evidence.factual_response` under
  `roberta_evaluation_factual_evidence/v1`;
- canonical claims whose `evidence_path` points only into
  `factual_response.findings.data` or `factual_response.findings.risk`;
- `evaluation_evidence.evaluation_projection_integrity` under
  `roberta_evaluation_projection_integrity/v1`;
- factual provenance showing that no second CMIS query or prose inference was
  performed;
- freshness projected only from explicit Scout/CMIS freshness structures.

The projection-integrity PASS certifies only that the emitted factual claim
values were copied from the bounded structured projection. It does not certify
provider truth and does not certify every natural-language statement.

If no gradeable structured factual field exists, `claims` remains empty and
the Laboratory must return EVIDENCE_REQUIRED rather than guessing.

## Compatibility

`roberta_evaluation_telemetry/v1` retains its existing semantics: claims come
only from the accepted Human Response Decision object, and no factual Scout
projection is added.

Normal bridge requests remain unchanged when `evaluation_mode` is absent.

Controlled Execution remains locked: `execution_authorized=false`.
