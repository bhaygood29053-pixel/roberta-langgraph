# Canonical ROBERTA Decision Object v1

Status: implementation tracer bullet for Issue #290.

## Purpose

ROBERTA needs one deterministic intelligence/decision basis before Human ROBERTA and Machine ROBERTA diverge in presentation. The canonical object is a ROBERTA-owned projection of already-validated Scout output; it is not a second blockchain fact authority.

Canonical authority remains:

```text
User / transport
  -> ROBERTA
    -> Chain Scout
      -> CMIS
        -> verified provider/source
```

The Decision Object does not call CMIS/providers and does not recalculate market facts, tokenomics, history, risk, Evidence Receipts, or Proof Scores.

## First accepted input boundary

The v1 tracer bullet is intentionally narrow. It accepts only:

```text
contract_version = instant_x1_scan_product_view/v1
product = instant_x1_scan
chain = x1
status in {ok, partial}
execution_authorized = false
```

The source view must preserve deterministic risk with `execution_authorized=false`, keep Proof Score separate from risk, and provide the required identity, market, tokenomics, holder/concentration, history, risk, evidence, limitations, warnings, and errors structures.

Wrong contracts, wrong chain/product, malformed required sections, Proof Score/risk collapse, or any execution authorization fail closed.

## Canonical object

Internal contract:

```text
roberta_decision/v1
```

The object preserves:

- request id when supplied;
- chain/workflow/status;
- requested and resolved subject identity;
- market, tokenomics, and holder/concentration facts exactly as projected by the validated Scout product view;
- deterministic risk exactly as projected by the accepted path;
- history and its completeness/coverage limitations;
- evidence state with Proof Score explicitly separate from risk;
- deterministic paths for fact wrappers that remain unverified;
- source limitations, warnings, and errors;
- observation timestamps;
- source contract identity;
- `execution_authorized=false`.

The first slice does **not** introduce a ROBERTA BUY/WAIT/BLOCK policy. `decision.recommendation` preserves the accepted source risk recommendation, `reason_codes` remains empty, and `policy_applied=false` until a separately reviewed policy contract exists.

## Machine ROBERTA projection

Machine rendering uses:

```text
roberta_intelligence/v1
```

The initial envelope exposes the same subject, decision, facts, risk, history, evidence, unknowns, limitations, timestamps, and execution denial. Null/unavailable values are retained as null/unavailable; missing facts are never converted to zero or false for client convenience.

Supported initial evidence depths:

- `standard` — canonical intelligence/evidence summary;
- `full` — same canonical content plus source contract identity.

This is an internal product tracer bullet, not a commitment to broad public API availability, authentication, quotas, or commercial packaging.

## Human ROBERTA projection

Human rendering is deterministic and answer-first. It may simplify labels, but it must preserve material uncertainty. It surfaces the accepted recommendation, key verified market facts, deterministic risk state, unverified fields/limitations, observation time, and execution denial.

Human rendering may not manufacture a fact or policy conclusion absent from the Decision Object.

## Cross-face consistency

Human and Machine outputs must be generated from the same Decision Object. Tests bind both faces to the same canonical:

- subject identity;
- numeric market facts;
- risk recommendation/score verification state;
- history state;
- evidence separation;
- explicit unknowns/limitations;
- observation time;
- execution denial.

The renderers do not mutate the canonical object.

## Explicit non-goals

No:

- direct ROBERTA -> CMIS/provider shortcut;
- new CMIS service or provider promotion;
- new risk arithmetic;
- universal ROBERTA score;
- autonomous trade recommendation policy;
- source-truth promotion from learning/memory;
- transaction construction, signing, broadcasting, custody, trading, bridge transfer, or Controlled Execution.

`execution_authorized=false`
