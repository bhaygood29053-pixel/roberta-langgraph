# X1 Burn Intelligence v1

Status: first X1 Scout burn-consumption tracer for Issue #293.

## Purpose

`x1_burn_intelligence/v1` is an X1 Scout product projection over the accepted CMIS `tokenomics` response. It does not create a new CMIS service and does not recalculate burn, emission, circulating-supply, historical-price, valuation, or Proof Score facts.

Canonical authority remains:

```text
User / transport
  -> ROBERTA
    -> X1 Scout
      -> CMIS tokenomics
        -> accepted X1 evidence/providers
```

## Accepted source

The source envelope must be:

```text
service = tokenomics
chain = x1
status in {ok, partial, unavailable}
```

When burn metrics are available, `data.burn_metrics` must preserve the accepted CMIS burn contract including:

- explicit `available` and status;
- explicit `lifetime_total_burn_verified`;
- 1h / 24h / 7d / 30d windows;
- per-window coverage verification;
- burn/mint amounts and event counts only where the window is verified;
- burn-to-emission, net issuance, and issuance state from CMIS;
- 24h / 7d / 30d period-over-period comparison objects;
- comparison states `AVAILABLE`, `NO_CHANGE_ZERO_BASE`, `NEW_BURN_ACTIVITY`, or `INSUFFICIENT_COVERAGE`;
- null numeric percent for `NEW_BURN_ACTIVITY` and `INSUFFICIENT_COVERAGE`;
- historical burn-time valuation and its completeness state;
- circulating-supply context and its independent verification state;
- observation/coverage metadata.

If CMIS marks burn metrics unavailable, X1 Scout preserves that unavailable state. It must not synthesize zero burn, zero events, lifetime burn, or a comparison from absence.

## Projection

The first product object contains:

```text
contract_version = x1_burn_intelligence/v1
product = x1_burn_intelligence
chain = x1
execution_authorized = false
```

It preserves:

- requested asset, when supplied;
- CMIS-resolved asset descriptor;
- the complete validated CMIS `burn_metrics` object;
- observation time;
- confidence;
- sources;
- warnings/errors;
- Evidence Receipt and Proof Score when supplied;
- explicit Proof Score/risk separation;
- execution denial.

The projection deep-copies accepted CMIS state so later mutation of a transport/test payload cannot rewrite the product result.

## Fail-closed behavior

Reject as a contract error:

- wrong service or chain;
- unsupported CMIS status;
- missing/malformed `data` or `burn_metrics`;
- non-boolean availability, coverage, completeness, or verification states where required;
- missing required windows for an available burn report;
- verified windows missing accepted burn facts;
- unverified windows mislabeled `ok`;
- unsupported or incoherent period-over-period states;
- numeric percent reported for `NEW_BURN_ACTIVITY` or `INSUFFICIENT_COVERAGE`;
- any explicit execution authorization.

## Presentation and Decision Object sequencing

This tracer establishes the Scout product contract only. Human BURN / WHAT CHANGED? rendering and protected `roberta_decision/v1` burn-workflow adaptation remain separately gated.

Those later layers may label and organize accepted values, but must not:

- relabel `verified_burned_observed` as lifetime total without lifetime proof;
- calculate a percentage from current/prior amounts;
- substitute current/nearest/interpolated prices for burn-time valuation;
- collapse native/XNT and USD valuation completeness;
- infer circulating supply;
- create a burn-derived risk score or trade recommendation.

## Non-goals

No new CMIS service, provider call, burn parser, arithmetic, valuation engine, risk score, wallet authority, token burning, transaction construction/signing/broadcasting, trading, custody, or Controlled Execution.

`execution_authorized=false`
